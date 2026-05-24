from collections.abc import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL 환경변수가 설정되지 않았습니다. "
            ".env 파일 또는 docker-compose.yml 환경변수를 확인하세요."
        )
    return url


# 모듈 로드 시점이 아닌 첫 DB 요청 시점에 연결 — 환경변수 없어도 앱은 기동됨
def _make_session_factory():
    engine = create_engine(_get_database_url(), pool_pre_ping=True)
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)


_engine = None
_SessionLocal = None


def _get_session_local():
    global _engine, _SessionLocal
    if _SessionLocal is None:
        _engine, _SessionLocal = _make_session_factory()
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = _get_session_local()()
    try:
        yield db
    finally:
        db.close()
