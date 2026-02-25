from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from app.models import Expense, ExpenseCreate, ExpenseResponse
from app.utils import load_expenses, save_expenses, get_team_by_id, get_member_by_id

router = APIRouter()

@router.get("", response_model=List[ExpenseResponse])
async def get_expenses(team_id: str = None):
    """지출 내역 조회 (팀별 필터링 가능)"""
    expenses = load_expenses()
    
    if team_id:
        expenses = [e for e in expenses if e.team_id == team_id]
    
    return expenses

@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(expense_id: str):
    """특정 지출 내역 조회"""
    expenses = load_expenses()
    
    for expense in expenses:
        if expense.id == expense_id:
            return expense
    
    raise HTTPException(status_code=404, detail="지출 내역을 찾을 수 없습니다.")

@router.post("", response_model=ExpenseResponse)
async def create_expense(expense_data: ExpenseCreate):
    """지출 내역 생성"""
    # 팀과 팀원 확인
    team = get_team_by_id(expense_data.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    
    if expense_data.member_id == "admin":
        raise HTTPException(
            status_code=400,
            detail="관리자 모드에서는 지출을 등록할 수 없습니다. 팀원을 추가한 뒤 팀원으로 로그인해주세요."
        )

    member = get_member_by_id(expense_data.team_id, expense_data.member_id)
    if not member:
        raise HTTPException(
            status_code=404,
            detail="선택된 팀원을 찾을 수 없습니다. 다시 로그인 후 시도해주세요."
        )
    
    # 공급가액과 부가세 계산
    # 총액 = 공급가액 + 부가세(10%)
    # 총액 = 공급가액 * 1.1
    # 공급가액 = 총액 / 1.1
    supply_amount = int(expense_data.total_amount / 1.1)
    vat = expense_data.total_amount - supply_amount
    
    expenses = load_expenses()
    
    # 지출 생성
    new_expense = Expense(
        id=str(uuid.uuid4()),
        team_id=expense_data.team_id,
        member_id=expense_data.member_id,
        member_name=member.name,
        category=expense_data.category,
        description=expense_data.description,
        supply_amount=supply_amount,
        vat=vat,
        total_amount=expense_data.total_amount
    )
    
    expenses.append(new_expense)
    save_expenses(expenses)
    
    return new_expense

@router.delete("/{expense_id}")
async def delete_expense(expense_id: str):
    """지출 내역 삭제"""
    expenses = load_expenses()
    
    expense_index = None
    for i, expense in enumerate(expenses):
        if expense.id == expense_id:
            expense_index = i
            break
    
    if expense_index is None:
        raise HTTPException(status_code=404, detail="지출 내역을 찾을 수 없습니다.")
    
    expenses.pop(expense_index)
    save_expenses(expenses)
    
    return {"message": "지출 내역이 삭제되었습니다."}
