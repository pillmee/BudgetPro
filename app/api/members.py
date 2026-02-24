from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from app.models import Member, MemberCreate, MemberUpdate
from app.utils import load_teams, save_teams, get_team_by_id, get_member_by_id

router = APIRouter()

@router.get("/{team_id}", response_model=List[Member])
async def get_members(team_id: str):
    """특정 팀의 모든 팀원 조회"""
    team = get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    return team.members

@router.get("/{team_id}/{member_id}", response_model=Member)
async def get_member(team_id: str, member_id: str):
    """특정 팀원 조회"""
    member = get_member_by_id(team_id, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="팀원을 찾을 수 없습니다.")
    return member

@router.post("/{team_id}", response_model=Member)
async def create_member(team_id: str, member_data: MemberCreate):
    """팀원 생성"""
    teams = load_teams()
    
    team_index = None
    for i, team in enumerate(teams):
        if team.id == team_id:
            team_index = i
            break
    
    if team_index is None:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    
    # 팀원 생성
    new_member = Member(
        id=str(uuid.uuid4()),
        name=member_data.name
    )
    
    teams[team_index].members.append(new_member)
    save_teams(teams)
    
    return new_member

@router.put("/{team_id}/{member_id}", response_model=Member)
async def update_member(team_id: str, member_id: str, member_data: MemberUpdate):
    """팀원 수정"""
    teams = load_teams()
    
    team_index = None
    member_index = None
    
    for i, team in enumerate(teams):
        if team.id == team_id:
            team_index = i
            for j, member in enumerate(team.members):
                if member.id == member_id:
                    member_index = j
                    break
            break
    
    if team_index is None:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    if member_index is None:
        raise HTTPException(status_code=404, detail="팀원을 찾을 수 없습니다.")
    
    # 팀원 정보 업데이트
    teams[team_index].members[member_index].name = member_data.name
    
    save_teams(teams)
    return teams[team_index].members[member_index]

@router.delete("/{team_id}/{member_id}")
async def delete_member(team_id: str, member_id: str):
    """팀원 삭제"""
    teams = load_teams()
    
    team_index = None
    member_index = None
    
    for i, team in enumerate(teams):
        if team.id == team_id:
            team_index = i
            for j, member in enumerate(team.members):
                if member.id == member_id:
                    member_index = j
                    break
            break
    
    if team_index is None:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    if member_index is None:
        raise HTTPException(status_code=404, detail="팀원을 찾을 수 없습니다.")
    
    teams[team_index].members.pop(member_index)
    save_teams(teams)
    
    return {"message": "팀원이 삭제되었습니다."}
