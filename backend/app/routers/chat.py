"""Chat API (3): send / poll(since_id) / delete(본인만)."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import get_current_user, require_team
from ..core.errors import AppError, not_found
from ..models import Message, Team, User
from ..schemas import MessageCreateRequest, MessageOut

router = APIRouter(tags=["Chat"])

MAX_LEN = 1000


def _to_out(m: Message) -> MessageOut:
    return MessageOut(
        id=m.id,
        user_id=m.user_id,
        user_email=m.user.email if m.user else "",
        content=m.content,
        created_at=m.created_at,
    )


@router.post(
    "/teams/{team_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED, summary="메시지 전송"
)
def send_message(
    body: MessageCreateRequest,
    team: Team = Depends(require_team),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if len(body.content) > MAX_LEN:
        raise AppError(400, "TOO_LONG", "메시지는 1000자 이내", {"limit": MAX_LEN, "actual": len(body.content)})
    msg = Message(team_id=team.id, user_id=user.id, content=body.content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return _to_out(msg)


@router.get("/teams/{team_id}/messages", response_model=list[MessageOut], summary="증분 폴링(since_id)")
def list_messages(
    team: Team = Depends(require_team),
    db: Session = Depends(get_db),
    since_id: int | None = Query(None, description="마지막으로 받은 메시지 id. 이후 메시지만 반환"),
):
    if since_id is not None:
        # 증분: id 기반 커서로 누락/중복 없이
        stmt = select(Message).where(Message.team_id == team.id, Message.id > since_id).order_by(Message.id.asc())
        return [_to_out(m) for m in db.scalars(stmt).all()]
    # 최초 진입: 최근 50개를 시간순(오름차순)으로
    stmt = select(Message).where(Message.team_id == team.id).order_by(Message.id.desc()).limit(50)
    recent = list(db.scalars(stmt).all())
    recent.reverse()
    return [_to_out(m) for m in recent]


@router.delete("/messages/{message_id}", summary="메시지 삭제(본인만)")
def delete_message(message_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msg = db.get(Message, message_id)
    if msg is None:
        raise not_found("메시지를 찾을 수 없습니다")
    # 같은 팀 확인(비멤버 차단)
    if user.team_id != msg.team_id:
        raise AppError(403, "FORBIDDEN", "이 팀의 멤버가 아닙니다")
    # owner라도 타인 메시지 삭제 불가
    if msg.user_id != user.id:
        raise AppError(403, "NOT_OWNER", "본인의 메시지만 삭제할 수 있습니다")
    db.delete(msg)
    db.commit()
    return {"ok": True}
