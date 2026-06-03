"""환경 설정 로더. DATABASE_URL / JWT_SECRET / CORS_ORIGINS 만으로 환경 전환."""
import os

# KST 단일 시간대 가정 (스토리보드 결정 — UTC 변환 없음)
from datetime import timedelta, timezone

KST = timezone(timedelta(hours=9))


class Settings:
    # 로컬 기본값은 SQLite 파일, 운영은 Neon Postgres URL을 주입
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./taskflow.db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # 콤마 구분 허용목록. 기본: 로컬 정적 서버 + 운영 도메인
    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5500,http://localhost:8000,"
            "http://127.0.0.1:5500,https://taskflow.vercel.app",
        ).split(",")
        if o.strip()
    ]


settings = Settings()
