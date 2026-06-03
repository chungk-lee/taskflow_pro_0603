"""Task API (6): list/create (팀 범위) + get/update/status/delete (단일)."""
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.deps import get_current_user, require_team
from ..core.errors import AppError, forbidden, not_found, validation_error
from ..models import Task, Team, User
from ..schemas import TaskCreateRequest, TaskOut, TaskStatusRequest, TaskUpdateRequest

router = APIRouter(tags=["Task"])


def _validate_assignee(assignee_id: int | None, team_id: int, db: Session) -> None:
    """assignee는 NULL 또는 같은 팀 멤버만."""
    if assignee_id is None:
        return
    assignee = db.get(User, assignee_id)
    if assignee is None or assignee.team_id != team_id:
        raise validation_error("담당자는 팀 멤버여야 합니다", {"field": "assignee_id"})


def _load_task_in_user_team(task_id: int, user: User, db: Session) -> Task:
    """단일 태스크 경로(/tasks/{id})의 공통 가드: 존재 + 같은 팀."""
    task = db.get(Task, task_id)
    if task is None:
        raise not_found("태스크를 찾을 수 없습니다")
    if user.team_id != task.team_id:
        raise forbidden("이 팀의 멤버가 아닙니다")
    return task


@router.get("/teams/{team_id}/tasks", response_model=list[TaskOut], summary="칸반 조회(필터)")
def list_tasks(
    team: Team = Depends(require_team),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    filter: Literal["all", "me", "unassigned"] = Query("all", description="all=전체, me=@me, unassigned=미할당"),
):
    stmt = select(Task).where(Task.team_id == team.id)
    if filter == "me":
        stmt = stmt.where(Task.assignee_id == user.id)
    elif filter == "unassigned":
        stmt = stmt.where(Task.assignee_id.is_(None))
    stmt = stmt.order_by(Task.created_at.desc(), Task.id.desc())
    return list(db.scalars(stmt).all())


@router.post(
    "/teams/{team_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED, summary="카드 생성"
)
def create_task(
    body: TaskCreateRequest,
    team: Team = Depends(require_team),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_assignee(body.assignee_id, team.id, db)
    task = Task(
        team_id=team.id,
        title=body.title,
        status=body.status,
        creator_id=user.id,
        assignee_id=body.assignee_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks/{task_id}", response_model=TaskOut, summary="단일 카드 상세")
def get_task(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _load_task_in_user_team(task_id, user, db)


@router.put("/tasks/{task_id}", response_model=TaskOut, summary="제목·담당자 수정")
def update_task(
    task_id: int, body: TaskUpdateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    task = _load_task_in_user_team(task_id, user, db)
    _validate_assignee(body.assignee_id, task.team_id, db)
    task.title = body.title
    task.assignee_id = body.assignee_id
    db.commit()
    db.refresh(task)
    return task


@router.patch("/tasks/{task_id}/status", response_model=TaskOut, summary="상태 이동(드래그)")
def update_status(
    task_id: int, body: TaskStatusRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    task = _load_task_in_user_team(task_id, user, db)
    task.status = body.status
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", summary="카드 삭제(creator/owner)")
def delete_task(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = _load_task_in_user_team(task_id, user, db)
    team = db.get(Team, task.team_id)
    is_owner = team is not None and team.owner_id == user.id
    if task.creator_id != user.id and not is_owner:
        raise forbidden("권한이 없습니다")
    db.delete(task)
    db.commit()
    return {"ok": True}
