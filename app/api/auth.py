from fastapi import APIRouter, HTTPException
import uuid
from app.models import LoginRequest, LoginResponse, Dashboard
from app.utils import get_team_by_id, get_member_by_id, load_expenses
from datetime import datetime
from dateutil.relativedelta import relativedelta

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """로그인"""
    # 팀 확인
    team = get_team_by_id(login_data.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    
    # 팀원 확인
    member = get_member_by_id(login_data.team_id, login_data.member_id)
    if not member:
        raise HTTPException(status_code=404, detail="팀원을 찾을 수 없습니다.")
    
    # 간단한 토큰 생성 (실제로는 JWT 등을 사용해야 함)
    token = str(uuid.uuid4())
    
    return LoginResponse(
        team_id=team.id,
        team_name=team.name,
        member_id=member.id,
        member_name=member.name,
        token=token
    )

@router.get("/dashboard/{team_id}", response_model=Dashboard)
async def get_dashboard(team_id: str):
    """대시보드 데이터 조회"""
    # 팀 확인
    team = get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    
    # 현재 사이클 시작일 계산
    current_date = datetime.now()
    cycle_start_date = team.last_reset_date
    
    # 사이클에 따른 월 수 계산
    if team.budget_cycle == "monthly":
        months_diff = (current_date.year - cycle_start_date.year) * 12 + (current_date.month - cycle_start_date.month)
        cycle_info = f"{current_date.strftime('%Y년 %m월')}"
    elif team.budget_cycle == "quarterly":
        months_diff = (current_date.year - cycle_start_date.year) * 12 + (current_date.month - cycle_start_date.month)
        cycle_info = f"{current_date.year}년 {(current_date.month - 1) // 3 + 1}분기"
    elif team.budget_cycle == "semi_annual":
        months_diff = (current_date.year - cycle_start_date.year) * 12 + (current_date.month - cycle_start_date.month)
        cycle_info = f"{current_date.year}년 {'상반기' if current_date.month <= 6 else '하반기'}"
    else:  # annual
        months_diff = (current_date.year - cycle_start_date.year) * 12 + (current_date.month - cycle_start_date.month)
        cycle_info = f"{current_date.year}년"
    
    # 누적 예산 계산 (시작일부터 현재까지 매월 누적)
    accumulated_budget = team.per_person_amount * len(team.members) * (months_diff + 1)
    
    # 현재 사이클의 지출 내역 조회
    expenses = load_expenses()
    team_expenses = [e for e in expenses if e.team_id == team_id]
    
    # 지출 합계 계산
    total_spent = sum(e.total_amount for e in team_expenses)
    supply_amount_spent = sum(e.supply_amount for e in team_expenses)
    vat_spent = sum(e.vat for e in team_expenses)
    
    # 잔여 예산 계산
    remaining_budget = accumulated_budget - total_spent
    remaining_budget_without_vat = accumulated_budget - supply_amount_spent
    
    # 팀원별 지출 내역
    member_expenses = {}
    for member in team.members:
        member_total = sum(e.total_amount for e in team_expenses if e.member_id == member.id)
        member_expenses[member.name] = member_total
    
    member_expenses_list = [
        {"name": name, "amount": amount}
        for name, amount in member_expenses.items()
    ]
    
    return Dashboard(
        accumulated_budget=accumulated_budget,
        total_spent=total_spent,
        supply_amount_spent=supply_amount_spent,
        vat_spent=vat_spent,
        remaining_budget=remaining_budget,
        remaining_budget_without_vat=remaining_budget_without_vat,
        current_month=current_date.strftime('%Y년 %m월'),
        budget_cycle_info=cycle_info,
        member_expenses=member_expenses_list
    )
