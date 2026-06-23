"""Unit tests for Workspace request validation and local persistence flows."""

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from workspace import views
from workspace.models import InventionInput, PatentClaim, PatentProject


User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="inventor", password="pw")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_create_project_requires_title(auth_client):
    response = auth_client.post(
        "/workspace/create/",
        {"problem_to_solve": "문제"},
        format="json",
    )

    assert response.status_code == 400
    assert PatentProject.objects.count() == 0


def test_create_project_saves_project_and_invention_input(auth_client, user):
    response = auth_client.post(
        "/workspace/create/",
        {
            "title": "센서 분석 시스템",
            "problem_to_solve": "탐지가 느리다.",
            "prior_art_problem": "수동 검사에 의존한다.",
            "core_tech": "분석 모듈을 사용한다.",
            "expected_effect": "탐지 시간을 줄인다.",
        },
        format="json",
    )

    assert response.status_code == 201
    project = PatentProject.objects.get(id=response.data["project_id"])
    assert project.owner == user
    assert project.inventioninput.core_tech == "분석 모듈을 사용한다."


def test_save_and_get_claims_use_current_claim_shape(auth_client, user):
    project = PatentProject.objects.create(title="발명", owner=user)
    payload = {
        "claims": [
            {
                "claim_no": 1,
                "is_dependent": False,
                "cited_claim_no": [],
                "category": "시스템",
                "content": "센서를 포함하는 시스템.",
            }
        ]
    }

    saved = auth_client.post(
        f"/workspace/workstation/{project.id}/save_claims_api/",
        payload,
        format="json",
    )
    loaded = auth_client.get(
        f"/workspace/workstation/{project.id}/manage_claims_api/"
    )

    assert saved.status_code == 200
    assert saved.data["status"] == "success"
    assert loaded.data["claims"][0]["content"] == "센서를 포함하는 시스템."
    assert PatentClaim.objects.count() == 1


def test_convert_to_markdown_format_accepts_nested_specification():
    markdown = views.convert_to_markdown_format(
        "센서 분석 시스템",
        {
            "specification": {
                "technical_field": "센서 데이터 처리 분야",
                "background_art": "수동 검사의 한계가 있다.",
                "problem_to_solve": "탐지 시간을 줄인다.",
                "means_for_solving": "분석 모듈을 포함한다.",
                "effects": "탐지 속도가 향상된다.",
                "brief_description_of_drawings": "도 1은 구성도이다.",
                "detailed_description": "분석 모듈이 데이터를 처리한다.",
            }
        },
    )

    assert "## 발명의 명칭\n센서 분석 시스템" in markdown
    assert "## 과제의 해결수단\n분석 모듈을 포함한다." in markdown
    assert markdown.endswith("분석 모듈이 데이터를 처리한다.")


def test_extract_uploaded_document_rejects_unknown_extension():
    uploaded = type("Upload", (), {"name": "paper.txt"})()

    with pytest.raises(ValueError, match="PDF, DOCX, HWP"):
        views.extract_text_from_uploaded_document(uploaded)


def test_extract_uploaded_document_uses_temp_file_and_cleans_it(monkeypatch):
    observed = {}

    class Upload:
        name = "paper.docx"

        def chunks(self):
            yield b"document-bytes"

    def fake_extract(path):
        observed["path"] = path
        observed["exists_during_extract"] = Path(path).exists()
        return "추출된 논문"

    monkeypatch.setattr(views, "extract_text_from_docx", fake_extract)

    result = views.extract_text_from_uploaded_document(Upload())

    assert result == "추출된 논문"
    assert observed["exists_during_extract"] is True
    assert Path(observed["path"]).exists() is False
