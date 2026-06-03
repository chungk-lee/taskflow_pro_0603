"""인증/권한 의존성: 현재 사용자, 팀 멤버십."""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..models import Team, User
from .db import get_db
from .errors import AppError, forbidden, not_found
from .security import decode_access_token

# auto_error=False → 누락 시 우리가 직접 401 TOKEN_EXPIRED 반환
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise AppError(401, "TOKEN_EXPIRED", "인증이 만료되었습니다")
    user_id = decode_access_token(creds.credentials)
    if user_id is None:
        raise AppError(401, "TOKEN_EXPIRED", "인증이 만료되었습니다")
    user = db.get(User, user_id)
    if user is None:
        raise AppError(401, "TOKEN_EXPIRED", "인증이 만료되었습니다")
    return user


def require_team(team_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Team:
    """경로의 team_id가 사용자의 소속과 일치해야 함. 아니면 403."""
    if user.team_id != team_id:
        raise forbidden("이 팀의 멤버가 아닙니다")
    team = db.get(Team, team_id)
    if team is None:
        raise not_found("팀을 찾을 수 없습니다")
    return team
