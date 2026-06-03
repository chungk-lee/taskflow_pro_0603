"""Team API (5): create / join / get / members / leave."""
import random
import string

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import get_current_user, require_team
from ..core.errors import AppError, not_found
from ..models import Message, Task, Team, User
from ..schemas import JoinRequest, MemberOut, OkOut, TeamCreateRequest, TeamOut

router = APIRouter(tags=["Team"])


def _generate_invite_code(db: Session) -> str:
    for _ in range(20):
        code = "".join(random.choices(string.ascii_uppercase, k=4)) + "-" + "".join(random.choices(string.digits, k=4))
        if not db.scalar(select(Team).where(Team.invite_code == code)):
            return code
    raise AppError(500, "INTERNAL", "초대코드 생성에 실패했습니다")


def _team_out(team: Team, db: Session) -> TeamOut:
    owner = db.get(User, team.owner_id)
    member_count = db.scalar(select(func.count()).select_from(User).where(User.team_id == team.id)) or 0
    task_count = db.scalar(select(func.count()).select_from(Task).where(Task.team_id == team.id)) or 0
    return TeamOut(
        id=team.id,
        name=team.name,
        invite_code=team.invite_code,
        owner_id=team.owner_id,
        owner_email=owner.email if owner else "",
        member_count=member_count,
        task_count=task_count,
        created_at=team.created_at,
    )


@router.post("/teams", response_model=TeamOut, status_code=status.HTTP_201_CREATED, summary="팀 생성")
def create_team(body: TeamCreateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.team_id is not None:
        raise AppError(409, "ALREADY_IN_TEAM", "이미 다른 팀에 소속되어 있습니다")
    team = Team(name=body.name, invite_code=_generate_invite_code(db), owner_id=user.id)
    db.add(team)
    db.flush()  # team.id 확보
    user.team_id = team.id
    db.commit()
    db.refresh(team)
    return _team_out(team, db)


@router.post("/teams/join", response_model=TeamOut, summary="초대코드로 합류")
def join_team(body: JoinRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.team_id is not None:
        raise AppError(409, "ALREADY_IN_TEAM", "이미 다른 팀에 소속되어 있습니다")
    team = db.scalar(select(Team).where(Team.invite_code == body.invite_code))
    if team is None:
        raise not_found("해당 초대코드를 찾을 수 없습니다")
    user.team_id = team.id
    db.commit()
    return _team_out(team, db)


@router.get("/teams/{team_id}", response_model=TeamOut, summary="팀 정보")
def get_team(team: Team = Depends(require_team), db: Session = Depends(get_db)):
    return _team_out(team, db)


@router.get("/teams/{team_id}/members", response_model=list[MemberOut], summary="멤버 목록")
def list_members(team: Team = Depends(require_team), db: Session = Depends(get_db)):
    members = db.scalars(select(User).where(User.team_id == team.id).order_by(User.created_at)).all()
    return [
        MemberOut(
            id=m.id,
            email=m.email,
            role="owner" if m.id == team.owner_id else "member",
            joined_at=m.created_at,
        )
        for m in members
    ]


@router.delete("/teams/{team_id}/leave", response_model=OkOut, summary="팀 떠나기")
def leave_team(team: Team = Depends(require_team), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.id == team.owner_id:
        member_count = db.scalar(select(func.count()).select_from(User).where(User.team_id == team.id)) or 0
        if member_count > 1:
            raise AppError(409, "OWNER_CANNOT_LEAVE", "다른 멤버가 있어 소유자는 팀을 떠날 수 없습니다")
        # 단독 owner: 팀 삭제(tasks/messages CASCADE), 본인 team_id는 SET NULL
        db.delete(team)
        db.commit()
        return OkOut()
    user.team_id = None
    db.commit()
    return OkOut()
