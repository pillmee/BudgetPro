from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class BudgetCycle(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half-yearly"
    YEARLY = "yearly"

class ExpenseCategory(str, Enum):
    DINING = "회식"
    BEVERAGE = "음료"
    OFFICE_SUPPLIES = "사무용품"
    OTHER = "기타"

# 팀원 모델
class Member(BaseModel):
    id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.now)

class MemberCreate(BaseModel):
    name: str

class MemberUpdate(BaseModel):
    name: str

# 팀 모델
class Team(BaseModel):
    id: str
    name: str
    per_person_amount: int = Field(default=100000, description="인별 할당액")
    budget_cycle: BudgetCycle = Field(default=BudgetCycle.MONTHLY, description="예산 초기화 주기")
    members: List[Member] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    last_reset_date: datetime = Field(default_factory=datetime.now, description="마지막 예산 초기화 날짜")

class TeamCreate(BaseModel):
    name: str
    per_person_amount: int = 100000
    budget_cycle: BudgetCycle = BudgetCycle.MONTHLY

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    per_person_amount: Optional[int] = None
    budget_cycle: Optional[BudgetCycle] = None

# 지출 모델
class Expense(BaseModel):
    id: str
    team_id: str
    member_id: str
    member_name: str
    category: ExpenseCategory
    description: Optional[str] = ""
    supply_amount: int = Field(description="공급가액")
    vat: int = Field(description="부가세 (10%)")
    total_amount: int = Field(description="총 지출액")
    created_at: datetime = Field(default_factory=datetime.now)

class ExpenseCreate(BaseModel):
    team_id: str
    member_id: str
    category: ExpenseCategory
    description: Optional[str] = ""
    total_amount: int = Field(description="총 지출액 (부가세 포함)")

class ExpenseResponse(Expense):
    pass

# 로그인 모델
class LoginRequest(BaseModel):
    team_id: str
    member_id: str

class LoginResponse(BaseModel):
    team_id: str
    team_name: str
    member_id: str
    member_name: str
    token: str

# 대시보드 모델
class Dashboard(BaseModel):
    accumulated_budget: int = Field(description="누적 예산")
    total_spent: int = Field(description="현재 총 지출")
    supply_amount_spent: int = Field(description="공급가액 지출")
    vat_spent: int = Field(description="부가세 지출")
    remaining_budget: int = Field(description="잔여 예산")
    remaining_budget_without_vat: int = Field(description="잔여 예산 (부가세 제외)")
    current_month: str = Field(description="현재 월")
    budget_cycle_info: str = Field(description="예산 사이클 정보")
    member_expenses: List[dict] = Field(description="팀원별 지출 내역")

# 설정 모델
class Settings(BaseModel):
    per_person_amount: int
    budget_cycle: BudgetCycle
