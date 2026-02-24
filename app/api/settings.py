from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List
import json
import os
from datetime import datetime
from app.models import Settings, BudgetCycle
from app.utils import load_teams, save_teams, load_expenses, save_expenses, get_team_by_id, DATA_DIR

router = APIRouter()

@router.get("/{team_id}", response_model=Settings)
async def get_settings(team_id: str):
    """팀 설정 조회"""
    team = get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    
    return Settings(
        per_person_amount=team.per_person_amount,
        budget_cycle=team.budget_cycle
    )

@router.put("/{team_id}", response_model=Settings)
async def update_settings(team_id: str, settings: Settings):
    """팀 설정 수정"""
    teams = load_teams()
    
    team_index = None
    for i, team in enumerate(teams):
        if team.id == team_id:
            team_index = i
            break
    
    if team_index is None:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    
    # 설정 업데이트
    teams[team_index].per_person_amount = settings.per_person_amount
    teams[team_index].budget_cycle = settings.budget_cycle
    
    save_teams(teams)
    
    return settings

@router.post("/{team_id}/reset-budget")
async def reset_budget(team_id: str):
    """예산 초기화"""
    teams = load_teams()
    
    team_index = None
    for i, team in enumerate(teams):
        if team.id == team_id:
            team_index = i
            break
    
    if team_index is None:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    
    # 지출 내역 삭제
    expenses = load_expenses()
    expenses = [e for e in expenses if e.team_id != team_id]
    save_expenses(expenses)
    
    # 초기화 날짜 업데이트
    teams[team_index].last_reset_date = datetime.now()
    save_teams(teams)
    
    return {"message": "예산이 초기화되었습니다."}

@router.get("/{team_id}/download-expenses")
async def download_expenses(team_id: str):
    """지출 정보 JSON 다운로드"""
    team = get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    
    expenses = load_expenses()
    team_expenses = [e for e in expenses if e.team_id == team_id]
    
    # 임시 파일 생성
    temp_file = os.path.join(DATA_DIR, f"expenses_{team_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump([e.model_dump(mode='json') for e in team_expenses], f, ensure_ascii=False, indent=2, default=str)
    
    return FileResponse(
        path=temp_file,
        filename=f"expenses_{team.name}_{datetime.now().strftime('%Y%m%d')}.json",
        media_type="application/json"
    )

@router.post("/{team_id}/upload-expenses")
async def upload_expenses(team_id: str, file: UploadFile = File(...)):
    """지출 정보 JSON 업로드"""
    team = get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    
    try:
        # 파일 읽기
        content = await file.read()
        uploaded_data = json.loads(content)
        
        # 리스트인지 확인
        if not isinstance(uploaded_data, list):
            raise HTTPException(status_code=400, detail="JSON 파일은 배열 형식이어야 합니다.")
        
        # 기존 지출 내역 로드
        expenses = load_expenses()
        
        # 해당 팀의 기존 지출 내역 삭제
        expenses = [e for e in expenses if e.team_id != team_id]
        
        # 업로드된 지출 내역 추가
        from app.models import Expense
        for exp_data in uploaded_data:
            if isinstance(exp_data, dict):
                # team_id 강제 설정 (보안을 위해)
                exp_dict = exp_data.copy()
                exp_dict['team_id'] = team_id
                expenses.append(Expense(**exp_dict))
            else:
                continue
        
        save_expenses(expenses)
        
        return {"message": f"{len(uploaded_data)}개의 지출 내역이 복구되었습니다."}
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="올바른 JSON 파일이 아닙니다.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")
