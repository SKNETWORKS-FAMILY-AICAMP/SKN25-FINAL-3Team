"""Unit tests for the current Workspace model relations and persistence rules."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from workspace.models import (
    ChatMessage,
    ConsultationState,
    InventionInput,
    PatentClaim,
    PatentDrawingFile,
    PatentProject,
    PriorArtReport,
    SpecificationDocument,
)


User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="owner", first_name="발명자", password="pw")


@pytest.fixture
def project(user):
    return PatentProject.objects.create(title="AI 분류 시스템", owner=user)


def test_project_defaults_and_owner_reverse_relation(project, user):
    assert project.status == "draft"
    assert project.owner == user
    assert list(user.projects.all()) == [project]


def test_deleting_owner_cascades_project_and_messages(project, user):
    ChatMessage.objects.create(project=project, role="user", content="안녕")

    user.delete()

    assert PatentProject.objects.count() == 0
    assert ChatMessage.objects.count() == 0


def test_invention_input_is_one_to_one_with_project(project):
    invention = InventionInput.objects.create(
        project=project,
        problem_to_solve="낮은 정확도",
        prior_art_problem="룰 기반 시스템 한계",
        core_tech="멀티모달 분류 모델",
        expected_effect="정확도 향상",
    )

    assert project.inventioninput == invention

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            InventionInput.objects.create(
                project=project,
                problem_to_solve="중복",
                prior_art_problem="중복",
                core_tech="중복",
            )


def test_consultation_state_defaults_to_phase_one(project):
    state = ConsultationState.objects.create(project=project)

    assert state.phase == 1
    assert state.collecting_steps is False
    assert project.consultation_state == state


def test_chat_message_uses_project_reverse_relation(project):
    message = ChatMessage.objects.create(project=project, role="assistant", content="응답")

    assert project.chat_messages.get() == message


def test_patent_claims_are_ordered_and_stringified(project):
    PatentClaim.objects.create(project=project, claim_no=3, category="방법", content="c")
    first = PatentClaim.objects.create(
        project=project,
        claim_no=1,
        category="시스템",
        content="a",
    )
    PatentClaim.objects.create(project=project, claim_no=2, category="방법", content="b")

    assert list(project.claims.values_list("claim_no", flat=True)) == [1, 2, 3]
    assert first.cited_claim_no == []
    assert str(first) == "[AI 분류 시스템] 청구항 1"


def test_drawing_report_and_specification_string_contracts(project):
    drawing = PatentDrawingFile.objects.create(
        project=project,
        title="구성도",
        image_url="https://example.com/drawing.png",
    )
    report = PriorArtReport.objects.create(
        project=project,
        risk_level="low",
        analysis_summary="유사 선행기술 없음",
        full_json_data={"results": []},
    )
    specification = SpecificationDocument.objects.create(
        project=project,
        markdown_content="# 발명의 명칭",
    )

    assert str(drawing) == "AI 분류 시스템 - 구성도"
    assert str(report) == "AI 분류 시스템 - 선기조 리포트"
    assert str(specification) == "AI 분류 시스템 - 명세서 본문"


def test_one_to_one_reports_are_replaced_through_update_or_create(project):
    PriorArtReport.objects.update_or_create(
        project=project,
        defaults={
            "risk_level": "medium",
            "analysis_summary": "첫 분석",
            "full_json_data": {},
        },
    )
    PriorArtReport.objects.update_or_create(
        project=project,
        defaults={
            "risk_level": "low",
            "analysis_summary": "재분석",
            "full_json_data": {"updated": True},
        },
    )

    assert PriorArtReport.objects.count() == 1
    assert PriorArtReport.objects.get(project=project).risk_level == "low"
