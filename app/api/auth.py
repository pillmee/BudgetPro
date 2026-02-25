from fastapi import APIRouter, HTTPException
import uuid
from app.models import LoginRequest, LoginResponse, Dashboard
from app.utils import get_team_by_id, get_member_by_id, load_expenses, save_expenses, load_teams, save_teams
from app.budget_calculator import should_reset_budget, calculate_accumulated_budget, get_cycle_info
from datetime import datetime

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
    teams = load_teams()
    team_index = None
    for i, saved_team in enumerate(teams):
        if saved_team.id == team_id:
            team_index = i
            break

    if team_index is None:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")

    team = teams[team_index]

    # 주기/연말 기준 자동 초기화
    if should_reset_budget(team):
        expenses = load_expenses()
        expenses = [e for e in expenses if e.team_id != team_id]
        save_expenses(expenses)

        teams[team_index].last_reset_date = datetime.now()
        save_teams(teams)
        team = teams[team_index]

    current_date = datetime.now()
    cycle_info = get_cycle_info(team)
    accumulated_budget = calculate_accumulated_budget(team)
    
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
