"""SQLAlchemy 엔진/세션. SQLite↔Postgres 호환, SQLite는 FK(CASCADE) 강제."""
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

# Neon/일반 Postgres URL은 psycopg(v3) 드라이버를 쓰도록 스킴 정규화
_url = settings.DATABASE_URL
if _url.startswith("postgres://"):
    _url = "postgresql+psycopg://" + _url[len("postgres://") :]
elif _url.startswith("postgresql://"):
    _url = "postgresql+psycopg://" + _url[len("postgresql://") :]

_is_sqlite = _url.startswith("sqlite")
connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(
    _url,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)


# SQLite는 기본적으로 외래키 제약을 끄므로 연결마다 켠다 (CASCADE/SET NULL 동작 보장)
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    if _is_sqlite:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
