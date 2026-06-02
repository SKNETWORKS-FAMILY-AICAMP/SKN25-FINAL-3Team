"""initial patent_runs table

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create_all()로 이미 생성된 DB에서는 테이블이 존재할 수 있으므로 체크 후 생성
    if not inspect(op.get_bind()).has_table("patent_runs"):
        op.create_table(
            "patent_runs",
            sa.Column("run_id", sa.String(36), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("user_input", sa.Text(), nullable=False),
            sa.Column(
                "state",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column(
                "errors",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("run_id"),
        )


def downgrade() -> None:
    op.drop_table("patent_runs")
