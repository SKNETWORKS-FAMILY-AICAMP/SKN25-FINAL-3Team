import pytest
from django.contrib.auth import get_user_model

from workspace.models import (
    PatentProject,
    InventionInput,
    ConsultationState,
    ChatMessage,
    PatentClaim,
    PatentDrawingFile,
    PriorArtReport,
    SpecificationDocument,
)

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="owner",
        name="발명자",
        gender="M",
        age=35,
        password="pw",
    )


@pytest.fixture
def project(user):
    return PatentProject.objects.create(title="AI 분류 시스템", owner=user)


# ── PatentProject ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_project_default_status(project):
    assert project.status == "draft"


@pytest.mark.django_db
def test_project_owner_relation(project, user):
    assert project.owner == user
    assert user.projects.count() == 1


@pytest.mark.django_db
def test_project_cascade_delete(project, user):
    ChatMessage.objects.create(project=project, role="user", content="안녕")
    user.delete()
    assert PatentProject.objects.count() == 0
    assert ChatMessage.objects.count() == 0


# ── InventionInput ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_invention_input_one_to_one(project):
    inv = InventionInput.objects.create(
        project=project,
        problem_to_solve="수동 분류의 낮은 정확도",
        prior_art_problem="기존 룰 기반 시스템 한계",
        core_tech="딥러닝 멀티모달 분류 모델",
        expected_effect="정확도 95% 이상",
    )
    assert inv.project == project
    assert project.inventioninput == inv


@pytest.mark.django_db
def test_invention_input_duplicate_raises(project):
    InventionInput.objects.create(
        project=project,
        problem_to_solve="문제1",
        prior_art_problem="기존 문제",
        core_tech="기술",
    )
    with pytest.raises(Exception):
        InventionInput.objects.create(
            project=project,
            problem_to_solve="문제2",
            prior_art_problem="기존 문제2",
            core_tech="기술2",
        )


# ── ChatMessage ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_chat_message_created(project):
    msg = ChatMessage.objects.create(project=project, role="user", content="내용")
    assert msg.role == "user"
    assert project.chat_messages.count() == 1


@pytest.mark.django_db
def test_chat_messages_cascade_on_project_delete(project):
    ChatMessage.objects.create(project=project, role="assistant", content="응답")
    project.delete()
    assert ChatMessage.objects.count() == 0


# ── PatentClaim ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_patent_claim_str(project):
    claim = PatentClaim.objects.create(
        project=project,
        claim_no=1,
        is_dependent=False,
        category="시스템",
        content="독립항 내용",
    )
    assert str(claim) == "[AI 분류 시스템] 청구항 1"


@pytest.mark.django_db
def test_patent_claims_ordered_by_claim_no(project):
    PatentClaim.objects.create(project=project, claim_no=3, category="방법", content="c")
    PatentClaim.objects.create(project=project, claim_no=1, category="시스템", content="a")
    PatentClaim.objects.create(project=project, claim_no=2, category="방법", content="b")
    nos = list(project.claims.values_list("claim_no", flat=True))
    assert nos == [1, 2, 3]


# ── PriorArtReport ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_prior_art_report_str(project):
    report = PriorArtReport.objects.create(
        project=project,
        risk_level="낮음",
        analysis_summary="유사 선행기술 없음",
        full_json_data={"results": []},
    )
    assert str(report) == "AI 분류 시스템 - 선기조 리포트"


# ── SpecificationDocument ───────────────────────────────────────────────────

@pytest.mark.django_db
def test_specification_document_str(project):
    spec = SpecificationDocument.objects.create(
        project=project,
        markdown_content="# 발명의 명칭\n...",
    )
    assert str(spec) == "AI 분류 시스템 - 명세서 본문"
