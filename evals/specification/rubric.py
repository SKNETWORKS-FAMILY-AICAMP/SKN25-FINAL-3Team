"""Versioned rubric for Korean patent-description quality evaluation."""

from __future__ import annotations

RUBRIC_VERSION = "kr-spec-enablement-v1"

SPECIFICATION_SECTIONS = (
    "technical_field",
    "background_art",
    "problem_to_solve",
    "means_for_solving",
    "effects",
    "brief_description_of_drawings",
    "detailed_description",
)

CRITERIA = (
    {
        "id": "enablement",
        "name": "실시가능성",
        "max_score": 40,
        "description": (
            "출원 시점의 통상의 기술자가 과도한 실험이나 특수한 지식을 "
            "부가하지 않고 발명을 정확히 이해하고 재현할 수 있는지를 평가한다."
        ),
        "subcriteria": (
            {"id": "accurate_understanding", "max_score": 10, "question": "목적, 구성, 결합관계와 작동 원리를 정확히 이해할 수 있는가?"},
            {"id": "reproducibility", "max_score": 10, "question": "명세서만으로 생산·사용 또는 방법 수행 절차를 재현할 수 있는가?"},
            {"id": "experimentation_burden", "max_score": 10, "question": "누락된 세부사항을 통상의 지식으로 보충할 수 있으며 과도한 실험이 필요하지 않은가?"},
            {"id": "full_scope_enablement", "max_score": 10, "question": "일부 실시예가 아니라 청구된 기술적 범위까지 실시할 근거가 있는가?"},
        ),
    },
    {
        "id": "claim_support",
        "name": "청구항 뒷받침",
        "max_score": 25,
        "description": (
            "청구항의 필수 구성과 기술적 관계에 대응하는 사항이 발명의 설명에 "
            "기재되고, 개시 내용을 청구범위까지 합리적으로 확장·일반화할 수 있는지를 평가한다."
        ),
        "subcriteria": (
            {"id": "essential_element_correspondence", "max_score": 15, "question": "독립항의 필수 구성요소와 관계가 해결수단 및 상세한 설명에 대응하는가?"},
            {"id": "scope_generalization", "max_score": 10, "question": "개시된 실시형태를 청구범위까지 확장·일반화할 기술적 근거가 있는가?"},
        ),
    },
    {
        "id": "grounding",
        "name": "입력 근거 충실성",
        "max_score": 15,
        "description": "입력 자료에 없는 핵심 구성, 수치, 효과, 도면부호 또는 실시형태를 창작하지 않았는지 평가한다.",
        "subcriteria": (
            {"id": "unsupported_additions", "max_score": 10, "question": "입력에 없는 기술적 신규사항이나 정량 효과가 추가되지 않았는가?"},
            {"id": "evidence_use", "max_score": 5, "question": "입력에 제공된 핵심 기술 자료를 누락 없이 적절히 활용했는가?"},
        ),
    },
    {
        "id": "clarity_consistency",
        "name": "명확성·일관성",
        "max_score": 10,
        "description": "발명의 설명에서 용어, 인과관계, 구성 간 연결과 섹션별 역할이 명확하고 일관적인지 평가한다.",
        "subcriteria": (
            {"id": "terminology", "max_score": 4, "question": "동일 구성요소가 일관된 용어로 표현되는가?"},
            {"id": "technical_logic", "max_score": 4, "question": "구성 간 관계와 작동의 인과관계가 명확한가?"},
            {"id": "section_role", "max_score": 2, "question": "각 섹션이 중복 없이 고유한 역할을 수행하는가?"},
        ),
    },
    {
        "id": "domain_specificity",
        "name": "기술분야별 충실도",
        "max_score": 10,
        "description": "해당 기술분야에서 통상의 기술자가 실시하기 위해 필요한 특수 정보가 충분한지 평가한다.",
        "subcriteria": (
            {"id": "domain_requirements", "max_score": 10, "question": "선택된 기술분야 프로필의 핵심 기재사항이 충족되는가?"},
        ),
    },
)

CORE_MINIMUMS = {
    "enablement": 32,
    "claim_support": 20,
    "grounding": 12,
}

PASS_SCORE = 80

DOMAIN_REQUIREMENTS = {
    "general": (
        "핵심 구성요소와 결합관계",
        "구성요소별 기능과 전체 작동 과정",
        "발명의 효과가 발생하는 기술적 인과관계",
    ),
    "ai_software": (
        "입력 데이터와 출력 데이터의 정의 및 기술적 상관관계",
        "필요한 경우 학습 데이터의 특징과 전처리 방법",
        "학습 또는 추론 모델의 구체적 구조와 처리 흐름",
        "필요한 경우 손실 함수 또는 학습 목표",
        "소프트웨어 정보처리가 하드웨어를 이용해 구체적으로 실현되는 방식",
    ),
    "bio_pharma": (
        "재료, 조성, 투여 또는 처리 조건",
        "약리효과나 생물학적 효과를 뒷받침하는 데이터",
        "통상의 기술자가 결과를 재현할 수 있는 실험 절차",
    ),
    "parameter": (
        "파라미터의 정의",
        "측정 방법과 측정 조건",
        "해당 파라미터를 만족하는 물건의 제조 또는 선택 방법",
        "청구된 수치범위 전체를 실시할 수 있는 근거",
    ),
}


def rubric_payload() -> dict:
    """Return a JSON-serializable copy used in Judge prompts and reports."""
    return {
        "version": RUBRIC_VERSION,
        "pass_score": PASS_SCORE,
        "core_minimums": CORE_MINIMUMS,
        "criteria": list(CRITERIA),
    }
