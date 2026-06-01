"""SQLAlchemy DB 연결 설정입니다.

DATABASE_URL이 있으면 PostgreSQL/AWS DB에 연결합니다.
DATABASE_URL이 없으면 로컬 개발/테스트용 SQLite 파일(`data/patent_agent.db`)을 씁니다.

운영 배포에서는 반드시 DATABASE_URL을 명시해야 합니다.
compose.service.yml은 기본 PostgreSQL URL을 주입합니다.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_SQLITE_URL = "sqlite:///./data/patent_agent.db"
DATABASE_URL = os.getenv("DATABASE_URL") or DEFAULT_SQLITE_URL

# SQLite fallback은 로컬 import/test/간단 demo가 DB 환경변수 없이도 깨지지 않게 하기 위한 것입니다.
# PostgreSQL은 psycopg2 driver를 사용하고, idle 연결 끊김 방지를 위해 pool_pre_ping=True를 켭니다.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
if DATABASE_URL.startswith("sqlite:///"):
    db_file = DATABASE_URL.removeprefix("sqlite:///")
    Path(db_file).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

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
