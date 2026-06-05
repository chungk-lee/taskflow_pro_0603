"""pytest 공통 픽스처.

각 테스트는 격리된 in-memory SQLite(StaticPool 공유 커넥션)에서 동작한다.
앱의 get_db 의존성을 테스트 세션으로 오버라이드하므로 운영/로컬 DB에 영향이 없다.
JWT_SECRET/DATABASE_URL은 app import 전에 고정한다.
"""
import os

# app(=config/security/db) import 이전에 환경을 고정해야 한다.
os.environ.setdefault("DATABASE_URL", "sqlite://")  # 앱 자체 엔진은 throwaway(요청은 override로 처리)
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-bytes-long-0123456789")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app


@pytest.fixture
def client():
    """테스트마다 새 in-memory DB + TestClient."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # 단일 커넥션 공유 → in-memory가 요청 간 유지됨
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")  # CASCADE/SET NULL 동작 보장
        cur.close()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()  # in-memory DB는 커넥션 종료 시 소멸 (users↔teams 순환 FK라 drop_all 불가)


@pytest.fixture
def register(client):
    """회원가입 헬퍼: 토큰/유저/Authorization 헤더를 반환."""

    def _register(email="user@ex.com", password="password8"):
        r = client.post("/auth/signup", json={"email": email, "password": password})
        assert r.status_code == 201, r.text
        data = r.json()
        return {
            "token": data["token"],
            "user": data["user"],
            "headers": {"Authorization": f"Bearer {data['token']}"},
        }

    return _register


@pytest.fixture
def make_team(client, register):
    """팀 owner 계정 + 팀 생성 헬퍼: (account, team) 반환."""

    def _make_team(email="owner@ex.com", name="팀A"):
        acc = register(email)
        r = client.post("/teams", json={"name": name}, headers=acc["headers"])
        assert r.status_code == 201, r.text
        return acc, r.json()

    return _make_team


@pytest.fixture
def join_member(client, register):
    """초대코드로 합류한 멤버 계정 헬퍼."""

    def _join(invite_code, email="member@ex.com"):
        acc = register(email)
        r = client.post("/teams/join", json={"invite_code": invite_code}, headers=acc["headers"])
        assert r.status_code == 200, r.text
        return acc

    return _join
