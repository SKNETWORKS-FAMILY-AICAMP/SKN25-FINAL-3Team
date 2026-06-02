"""프로젝트 루트 conftest.py.

pytest가 가장 먼저 로딩하는 conftest입니다.
프로젝트 루트를 sys.path에 추가해 agents/backend 임포트를 보장합니다.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# db.py가 임포트 시 DATABASE_URL이 없으면 RuntimeError를 발생시킵니다.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
