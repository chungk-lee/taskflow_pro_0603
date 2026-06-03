"""요청/응답 pydantic 스키마. 시각은 KST(+09:00)로 직렬화."""
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, PlainSerializer

from .core.config import KST


def _to_kst_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
    return dt.astimezone(KST).isoformat()


# 모든 응답 시각은 +09:00 offset 포함 ISO 8601로 직렬화
KSTDatetime = Annotated[datetime, PlainSerializer(_to_kst_iso, return_type=str, when_used="json")]


# ---- Auth ----
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    team_id: int | None
    created_at: KSTDatetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    token: str
    user: UserOut


# ---- Team ----
class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=30)


class JoinRequest(BaseModel):
    invite_code: str = Field(pattern=r"^[A-Z]{4}-[0-9]{4}$")


class TeamOut(BaseModel):
    id: int
    name: str
    invite_code: str
    owner_id: int
    owner_email: str
    member_count: int
    task_count: int
    created_at: KSTDatetime


class MemberOut(BaseModel):
    id: int
    email: str
    role: Literal["owner", "member"]
    joined_at: KSTDatetime


# ---- Task ----
class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    assignee_id: int | None = None
    status: Literal["TODO", "DOING", "DONE"] = "TODO"


class TaskUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    assignee_id: int | None = None


class TaskStatusRequest(BaseModel):
    status: Literal["TODO", "DOING", "DONE"]


class TaskOut(BaseModel):
    id: int
    team_id: int
    title: str
    status: str
    creator_id: int
    assignee_id: int | None
    created_at: KSTDatetime

    model_config = {"from_attributes": True}


# ---- Chat ----
class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)  # 1000자 초과는 라우터에서 TOO_LONG으로 처리


class MessageOut(BaseModel):
    id: int
    user_id: int
    user_email: str
    content: str
    created_at: KSTDatetime


# ---- 공통 ----
class OkOut(BaseModel):
    ok: bool = True
