"""Shared pytest fixtures for the current patent-drafting application.

The suite never calls real LLM, AWS, patent-search, or PostgreSQL services.
Django tests use a disposable SQLite database because pytest-django is not a
project dependency.
"""

from __future__ import annotations

import os
import sys
import tempfile
import types
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from typing import Iterator

import pytest


ROOT = Path(__file__).resolve().parents[1]
DJANGO_ROOT = ROOT / "backend" / "django"

for path in (ROOT, DJANGO_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

TEST_DB_PATH = Path(tempfile.gettempdir()) / f"skn25_pytest_{os.getpid()}.sqlite3"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_DB_ENGINE"] = "django.db.backends.sqlite3"
os.environ["DJANGO_DB_NAME"] = str(TEST_DB_PATH)
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("RUNPOD_API_KEY", "test-runpod-key")
os.environ.setdefault("RDS_DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_API_KEY"] = ""
os.environ["LANGCHAIN_API_KEY"] = ""
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test-access-key")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test-secret-key")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-northeast-2")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
os.environ.setdefault("S3_BUCKET", "test-bucket")


# pyproject.toml declares xmltodict, but the checked-in virtual environment can
# be older than the lock file.  Keep test collection deterministic in that
# local-only case; a correctly synced environment uses the real dependency.
try:
    import xmltodict  # noqa: F401
except ModuleNotFoundError:
    def _element_to_value(element):
        children = list(element)
        if not children:
            return (element.text or "").strip()

        result = {}
        for child in children:
            value = _element_to_value(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(value)
            else:
                result[child.tag] = value
        return result

    xmltodict_fallback = types.ModuleType("xmltodict")
    xmltodict_fallback.parse = lambda text: {
        ElementTree.fromstring(text).tag: _element_to_value(ElementTree.fromstring(text))
    }
    sys.modules["xmltodict"] = xmltodict_fallback


# The production prior-art module is decorated for LangSmith. Unit tests replace
# those decorators before project imports so even a developer's active .env
# cannot start a tracing background thread.
import langsmith
import langsmith.wrappers


def _no_traceable(function=None, **_kwargs):
    if callable(function):
        return function

    def decorator(inner):
        return inner

    return decorator


class _NoopLangSmithClient:
    def __init__(self, *_args, **_kwargs):
        pass

    def create_feedback(self, *_args, **_kwargs):
        return None


langsmith.traceable = _no_traceable
langsmith.Client = _NoopLangSmithClient
langsmith.wrappers.wrap_openai = lambda client: client

import django

django.setup()

from django.conf import settings
from django.core.management import call_command
from django.db import connections

from agents.core.state import (
    Architecture,
    ClaimItem,
    ClaimResult,
    Component,
    DataFlow,
    ExaminerResult,
    InventionMetadata,
    ParsedInvention,
    ProcessingStep,
    RejectionDetail,
    TechnicalContext,
)


settings.MEDIA_URL = getattr(settings, "MEDIA_URL", "/media/")
settings.MEDIA_ROOT = getattr(settings, "MEDIA_ROOT", str(ROOT / ".test-media"))


@pytest.fixture(scope="session")
def django_schema() -> Iterator[None]:
    """Create the real Django schema once in an isolated SQLite database."""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    call_command("migrate", verbosity=0, interactive=False)
    yield
    connections.close_all()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
def db(django_schema) -> Iterator[None]:
    """Provide clean tables without relying on pytest-django's db fixture."""
    call_command("flush", verbosity=0, interactive=False)
    yield


@pytest.fixture
def parsed_invention() -> ParsedInvention:
    return ParsedInvention(
        invention_metadata=InventionMetadata(
            title="센서 데이터를 분석하는 시스템",
            category="SYSTEM",
        ),
        technical_context=TechnicalContext(
            problem_to_solve="센서 이상을 늦게 탐지하는 문제를 해결한다.",
            expected_effect="이상 탐지 시간을 단축한다.",
        ),
        architecture=Architecture(
            components=[
                Component(
                    id="COMP_001",
                    name="분석 모듈",
                    type="MODULE",
                    description="센서 데이터를 분석한다.",
                )
            ],
            data_flows=[
                DataFlow(
                    flow_id="FLOW_001",
                    source="INPUT",
                    target="COMP_001",
                    data_name="센서 데이터",
                )
            ],
            processing_steps=[
                ProcessingStep(
                    step_number=1,
                    subject_id="COMP_001",
                    action_description="센서 데이터를 분석하는 단계",
                    input_data_ids=["FLOW_001"],
                    output_data_ids=[],
                )
            ],
        ),
    )


@pytest.fixture
def claim_result() -> ClaimResult:
    return ClaimResult(
        claims=[
            ClaimItem(
                claim_no=1,
                is_dependent=False,
                cited_claim_no=[],
                category="시스템",
                content="센서 데이터를 분석하는 분석 모듈을 포함하는 시스템.",
            ),
            ClaimItem(
                claim_no=2,
                is_dependent=True,
                cited_claim_no=[1],
                category="시스템",
                content="제1항에 있어서, 상기 분석 모듈은 이상을 탐지하는 시스템.",
            ),
        ]
    )


@pytest.fixture
def rejected_examiner_result() -> ExaminerResult:
    return ExaminerResult(
        is_approved=False,
        rejections=[
            RejectionDetail(claims=[1], reason_text="구성요소 관계가 불명확합니다.")
        ],
        revision_count=1,
    )


@pytest.fixture
def patent_state(parsed_invention, claim_result, rejected_examiner_result) -> dict:
    return {
        "mock_input_data": {
            "title": "센서 데이터를 분석하는 시스템",
            "prior_art_problem": "탐지가 늦다.",
            "problem_to_solve": "탐지 시간을 줄인다.",
            "core_tech": "분석 모듈이 센서 데이터를 분석한다.",
            "expected_effect": "탐지 시간이 단축된다.",
        },
        "summary_data": parsed_invention,
        "claims_data": claim_result,
        "prior_art_data": None,
        "examiner_data": rejected_examiner_result,
    }
