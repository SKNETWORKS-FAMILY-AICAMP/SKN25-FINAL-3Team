"""SQLAlchemy DB 연결 설정입니다.

DATABASE_URL은 필수입니다.
로컬/배포 모두 PostgreSQL 연결값을 명시해야 하며, 값이 없으면 서버 시작 시 바로 실패합니다.
compose.service.yml은 기본 PostgreSQL URL을 주입합니다.
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is required. PostgreSQL 연결값을 .env 또는 compose 환경변수에 설정하세요."
    )

# PostgreSQL은 psycopg2 driver를 사용하고, idle 연결 끊김 방지를 위해 pool_pre_ping=True를 켭니다.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 세션 팩토리: 실제 DB 작업 단위(트랜잭션)를 나타냅니다.
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """모든 SQLAlchemy 모델이 상속할 기본 클래스입니다."""


def get_db():
    """FastAPI 의존성 주입용 DB 세션 제공 함수입니다.

    사용 방법:
        @router.get("/something")
        def endpoint(db: Session = Depends(get_db)):
            run = db.query(Run).filter(...).first()

    yield 뒤의 finally 블록은 요청이 끝날 때 자동 실행되어 세션을 닫습니다.
    에러가 나도 finally는 반드시 실행됩니다.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
