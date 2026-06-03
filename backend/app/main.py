"""TaskFlow 백엔드 진입점. uvicorn app.main:app --reload."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.db import Base, engine
from .core.errors import register_error_handlers
from .routers import auth, chat, tasks, teams

# MVP: 부팅 시 스키마 생성 (마이그레이션 도구는 추후 도입 가능)
from . import models  # noqa: F401  (모델 등록)

# 부팅 시 스키마 생성. DB 미연결(env 누락) 시에도 import가 깨지지 않도록 방어.
try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:  # pragma: no cover
    print("[startup] create_all skipped:", exc)

tags_metadata = [
    {"name": "Auth", "description": "회원가입·로그인·로그아웃·현재 사용자. JWT 24h, stateless logout."},
    {"name": "Team", "description": "팀 생성·합류·조회·멤버·떠나기. 1인 1팀, owner/member 권한."},
    {"name": "Task", "description": "칸반 태스크 CRUD·상태 이동(드래그)·필터(전체/@me/미할당)."},
    {"name": "Chat", "description": "팀 채팅 전송·증분 폴링(since_id)·삭제(본인만)."},
]

app = FastAPI(
    title="TaskFlow API",
    version="0.1.0",
    description=(
        "소규모 팀(≤5명) 칸반 + 실시간 채팅 MVP. "
        "모든 에러는 `{ error: { code, message, meta } }` 형태. 시각은 KST(+09:00)."
    ),
    openapi_tags=tags_metadata,
)

# CORS 허용목록
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(tasks.router)
app.include_router(chat.router)


@app.get("/health", tags=["Meta"], summary="헬스 체크")
def health():
    return {"status": "ok"}
