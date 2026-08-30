import json
import os
import sqlite3
from contextlib import contextmanager
from typing import List, Optional
from app.models import Team, Member, Expense

DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "budgetpro.db")

# 마이그레이션 전용: 기존 JSON 저장 방식에서 남은 파일 (최초 1회 이전 후에도 보관됨)
_LEGACY_TEAMS_FILE = os.path.join(DATA_DIR, "teams.json")
_LEGACY_EXPENSES_FILE = os.path.join(DATA_DIR, "expenses.json")

_initialized = False

def ensure_data_dir():
    """데이터 디렉토리 생성"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

@contextmanager
def get_connection():
    ensure_data_dir()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def _create_schema():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS teams (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                per_person_amount INTEGER NOT NULL,
                budget_cycle TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_reset_date TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS members (
                id TEXT PRIMARY KEY,
                team_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id TEXT PRIMARY KEY,
                team_id TEXT NOT NULL,
                member_id TEXT NOT NULL,
                member_name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                supply_amount INTEGER NOT NULL,
                vat INTEGER NOT NULL,
                total_amount INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

def _migrate_legacy_json():
    """기존 teams.json / expenses.json 데이터를 SQLite로 1회 이전"""
    if os.path.exists(_LEGACY_TEAMS_FILE):
        with open(_LEGACY_TEAMS_FILE, 'r', encoding='utf-8') as f:
            teams = [Team(**team) for team in json.load(f)]
        save_teams(teams)

    if os.path.exists(_LEGACY_EXPENSES_FILE):
        with open(_LEGACY_EXPENSES_FILE, 'r', encoding='utf-8') as f:
            expenses = [Expense(**expense) for expense in json.load(f)]
        save_expenses(expenses)

def _ensure_initialized():
    """DB 스키마를 준비하고, 최초 실행 시에만 기존 JSON 데이터를 이전"""
    global _initialized
    if _initialized:
        return
    _initialized = True

    is_new_db = not os.path.exists(DB_FILE)
    _create_schema()
    if is_new_db:
        _migrate_legacy_json()

def load_teams() -> List[Team]:
    """팀 목록 로드"""
    _ensure_initialized()
    with get_connection() as conn:
        team_rows = conn.execute("SELECT * FROM teams ORDER BY created_at").fetchall()
        member_rows = conn.execute("SELECT * FROM members ORDER BY created_at").fetchall()

    members_by_team = {}
    for row in member_rows:
        members_by_team.setdefault(row["team_id"], []).append(
            Member(id=row["id"], name=row["name"], created_at=row["created_at"])
        )

    return [
        Team(
            id=row["id"],
            name=row["name"],
            per_person_amount=row["per_person_amount"],
            budget_cycle=row["budget_cycle"],
            members=members_by_team.get(row["id"], []),
            created_at=row["created_at"],
            last_reset_date=row["last_reset_date"],
        )
        for row in team_rows
    ]

def save_teams(teams: List[Team]):
    """팀 목록 저장 (전체 교체)"""
    _ensure_initialized()
    with get_connection() as conn:
        conn.execute("DELETE FROM members")
        conn.execute("DELETE FROM teams")
        for team in teams:
            conn.execute(
                "INSERT INTO teams (id, name, per_person_amount, budget_cycle, created_at, last_reset_date) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    team.id,
                    team.name,
                    team.per_person_amount,
                    team.budget_cycle.value,
                    team.created_at.isoformat(),
                    team.last_reset_date.isoformat(),
                ),
            )
            for member in team.members:
                conn.execute(
                    "INSERT INTO members (id, team_id, name, created_at) VALUES (?, ?, ?, ?)",
                    (member.id, team.id, member.name, member.created_at.isoformat()),
                )

def load_expenses() -> List[Expense]:
    """지출 내역 로드"""
    _ensure_initialized()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM expenses ORDER BY created_at").fetchall()

    return [
        Expense(
            id=row["id"],
            team_id=row["team_id"],
            member_id=row["member_id"],
            member_name=row["member_name"],
            category=row["category"],
            description=row["description"] or "",
            supply_amount=row["supply_amount"],
            vat=row["vat"],
            total_amount=row["total_amount"],
            created_at=row["created_at"],
        )
        for row in rows
    ]

def save_expenses(expenses: List[Expense]):
    """지출 내역 저장 (전체 교체)"""
    _ensure_initialized()
    with get_connection() as conn:
        conn.execute("DELETE FROM expenses")
        for expense in expenses:
            conn.execute(
                "INSERT INTO expenses "
                "(id, team_id, member_id, member_name, category, description, supply_amount, vat, total_amount, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    expense.id,
                    expense.team_id,
                    expense.member_id,
                    expense.member_name,
                    expense.category.value,
                    expense.description,
                    expense.supply_amount,
                    expense.vat,
                    expense.total_amount,
                    expense.created_at.isoformat(),
                ),
            )

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
