import json
import os
from typing import List, Optional
from datetime import datetime
from app.models import Team, Member, Expense

DATA_DIR = "data"
TEAMS_FILE = os.path.join(DATA_DIR, "teams.json")
EXPENSES_FILE = os.path.join(DATA_DIR, "expenses.json")

def ensure_data_dir():
    """데이터 디렉토리 생성"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_teams() -> List[Team]:
    """팀 목록 로드"""
    ensure_data_dir()
    if not os.path.exists(TEAMS_FILE):
        return []
    
    with open(TEAMS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return [Team(**team) for team in data]

def save_teams(teams: List[Team]):
    """팀 목록 저장"""
    ensure_data_dir()
    with open(TEAMS_FILE, 'w', encoding='utf-8') as f:
        json.dump([team.model_dump(mode='json') for team in teams], f, ensure_ascii=False, indent=2, default=str)

def load_expenses() -> List[Expense]:
    """지출 내역 로드"""
    ensure_data_dir()
    if not os.path.exists(EXPENSES_FILE):
        return []
    
    with open(EXPENSES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return [Expense(**expense) for expense in data]

def save_expenses(expenses: List[Expense]):
    """지출 내역 저장"""
    ensure_data_dir()
    with open(EXPENSES_FILE, 'w', encoding='utf-8') as f:
        json.dump([expense.model_dump(mode='json') for expense in expenses], f, ensure_ascii=False, indent=2, default=str)

def get_team_by_id(team_id: str) -> Optional[Team]:
    """ID로 팀 조회"""
    teams = load_teams()
    for team in teams:
        if team.id == team_id:
            return team
    return None

def get_member_by_id(team_id: str, member_id: str) -> Optional[Member]:
    """ID로 팀원 조회"""
    team = get_team_by_id(team_id)
    if not team:
        return None
    
    for member in team.members:
        if member.id == member_id:
            return member
    return None
