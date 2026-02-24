from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from app.models import Team, TeamCreate, TeamUpdate
from app.utils import load_teams, save_teams, get_team_by_id

router = APIRouter()

@router.get("", response_model=List[Team])
async def get_teams():
    """모든 팀 조회"""
    teams = load_teams()
    return teams

@router.get("/{team_id}", response_model=Team)
async def get_team(team_id: str):
    """특정 팀 조회"""
    team = get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    return team

@router.post("", response_model=Team)
async def create_team(team_data: TeamCreate):
    """팀 생성"""
    teams = load_teams()
    
    # 팀 생성
    new_team = Team(
        id=str(uuid.uuid4()),
        name=team_data.name,
        per_person_amount=team_data.per_person_amount,
        budget_cycle=team_data.budget_cycle,
        members=[]
    )
    
    teams.append(new_team)
    save_teams(teams)
    
    return new_team

@router.put("/{team_id}", response_model=Team)
async def update_team(team_id: str, team_data: TeamUpdate):
    """팀 수정"""
    teams = load_teams()
    
    team_index = None
    for i, team in enumerate(teams):
        if team.id == team_id:
            team_index = i
            break
    
    if team_index is None:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    
    # 팀 정보 업데이트
    if team_data.name is not None:
        teams[team_index].name = team_data.name
    if team_data.per_person_amount is not None:
        teams[team_index].per_person_amount = team_data.per_person_amount
    if team_data.budget_cycle is not None:
        teams[team_index].budget_cycle = team_data.budget_cycle
    
    save_teams(teams)
    return teams[team_index]

@router.delete("/{team_id}")
async def delete_team(team_id: str):
    """팀 삭제"""
    teams = load_teams()
    
    team_index = None
    for i, team in enumerate(teams):
        if team.id == team_id:
            team_index = i
            break
    
    if team_index is None:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    
    teams.pop(team_index)
    save_teams(teams)
    
    return {"message": "팀이 삭제되었습니다."}
