"""SQLAlchemy 테이블 모델 정의입니다.

patent_runs 테이블: 파이프라인 실행 기록을 저장합니다.
main.py startup 이벤트에서 Base.metadata.create_all()로 자동 생성됩니다.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.fastapi.app.db import Base

# 운영 PostgreSQL에서는 JSONB, 로컬 SQLite fallback에서는 JSON으로 저장합니다.
JSON_STATE_TYPE = JSONB().with_variant(JSON(), "sqlite")


class Run(Base):
    """파이프라인 실행 하나를 나타내는 테이블입니다.

    ─ 저장 내용 ─
    - run_id   : UUID, 이 실행의 고유 식별자
    - status   : 현재 상태 (running / completed / failed / wait_user)
    - user_input: 사용자가 입력한 발명 설명
    - state    : 전체 PatentAgentState JSON (workflow.trace에 완료된 agent 목록 포함)
    - errors   : 파이프라인 에러 목록
    - created_at / updated_at: 생성/수정 시각

    ─ JSONB란? ─
    PostgreSQL의 JSON 저장 타입입니다.
    일반 TEXT와 달리 JSON 구조로 인덱싱/조회가 가능합니다.
    state처럼 크고 구조화된 데이터를 저장하는 데 적합합니다.
    """

    __tablename__ = "patent_runs"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    user_input: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # 전체 PatentAgentState를 JSON으로 저장합니다.
    # state["workflow"]["trace"]로 완료된 agent 목록을 확인할 수 있습니다.
    state: Mapped[dict | None] = mapped_column(JSON_STATE_TYPE, nullable=True)

    # 파이프라인 에러 목록 (state["workflow"]["errors"]와 동일한 내용)
    # 빠른 조회를 위해 별도 컬럼으로도 저장합니다.
    errors: Mapped[list | None] = mapped_column(JSON_STATE_TYPE, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
