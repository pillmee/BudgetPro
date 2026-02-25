from datetime import datetime
from app.models import Team, BudgetCycle

def should_reset_budget(team: Team) -> bool:
    """예산을 초기화해야 하는지 확인"""
    current_date = datetime.now()
    last_reset = team.last_reset_date

    # 명세: 12월(전체 주기 종료월) 도달 시 연 1회 강제 초기화
    if current_date.month == 12 and (
        current_date.year != last_reset.year or current_date.month != last_reset.month
    ):
        return True
    
    if team.budget_cycle == BudgetCycle.MONTHLY:
        # 월이 다르면 초기화
        return current_date.month != last_reset.month or current_date.year != last_reset.year
    
    elif team.budget_cycle == BudgetCycle.QUARTERLY:
        # 분기가 다르면 초기화
        current_quarter = (current_date.month - 1) // 3
        last_quarter = (last_reset.month - 1) // 3
        return current_quarter != last_quarter or current_date.year != last_reset.year
    
    elif team.budget_cycle == BudgetCycle.HALF_YEARLY:
        # 반기가 다르면 초기화
        current_half = 0 if current_date.month <= 6 else 1
        last_half = 0 if last_reset.month <= 6 else 1
        return current_half != last_half or current_date.year != last_reset.year
    
    else:  # YEARLY
        # 연도가 다르면 초기화
        return current_date.year != last_reset.year

def calculate_accumulated_budget(team: Team) -> int:
    """누적 예산 계산"""
    current_date = datetime.now()
    start_date = team.last_reset_date
    year_start = datetime(current_date.year, 1, 1)

    # 명세: 예산 누적은 매년 1월부터 시작
    if start_date < year_start:
        start_date = year_start
    
    # 시작일부터 현재까지의 월 수 계산
    months_diff = (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month)
    
    # 안전장치: 미래 날짜 오입력 방지
    if months_diff < 0:
        months_diff = 0

    # 매월 누적된 예산 계산
    accumulated_budget = team.per_person_amount * len(team.members) * (months_diff + 1)
    
    return accumulated_budget

def get_cycle_info(team: Team) -> str:
    """현재 예산 사이클 정보 반환"""
    current_date = datetime.now()
    
    if team.budget_cycle == BudgetCycle.MONTHLY:
        return f"{current_date.strftime('%Y년 %m월')}"
    
    elif team.budget_cycle == BudgetCycle.QUARTERLY:
        quarter = (current_date.month - 1) // 3 + 1
        return f"{current_date.year}년 {quarter}분기"
    
    elif team.budget_cycle == BudgetCycle.HALF_YEARLY:
        half = "상반기" if current_date.month <= 6 else "하반기"
        return f"{current_date.year}년 {half}"
    
    else:  # YEARLY
        return f"{current_date.year}년"
