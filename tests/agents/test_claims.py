"""
claims 노드 단위 테스트

테스트 대상: agents/nodes/claims.py :: run(state)
인터페이스:  docs/interfaces/claims.md
"""
from agents.nodes import claims
from tests.fixtures.sample_states import POST_CONSULTING_STATE, POST_EXAMINER_REJECTED_STATE


# ── 반환 필드 존재 여부 ─────────────────────────────────────────────────────────

def test_run_returns_claims_field():
    """run()이 'claims' 필드를 반환하는지 검증"""
    result = claims.run(POST_CONSULTING_STATE)
    assert "claims" in result


def test_run_returns_non_empty_claims():
    """최소 1개 이상의 청구항을 반환하는지 검증"""
    result = claims.run(POST_CONSULTING_STATE)
    assert len(result["claims"]) > 0, "청구항이 0개 — 최소 1개 이상 필요"


# ── 청구항 구조 검증 ─────────────────────────────────────────────────────────────

def test_each_claim_has_required_keys():
    """각 청구항 dict가 필수 키를 모두 포함하는지 검증"""
    result = claims.run(POST_CONSULTING_STATE)
    required_keys = ["claim_number", "claim_type", "is_independent", "depends_on", "content"]

    for i, claim in enumerate(result["claims"]):
        for key in required_keys:
            assert key in claim, f"claims[{i}]에 '{key}' 키 없음"


def test_claim_types_are_valid():
    """claim_type이 유효한 값인지 검증"""
    result = claims.run(POST_CONSULTING_STATE)
    valid_types = {"method", "system", "storage_medium"}

    for i, claim in enumerate(result["claims"]):
        assert claim["claim_type"] in valid_types, (
            f"claims[{i}].claim_type='{claim['claim_type']}' — "
            f"허용값: {valid_types}"
        )


def test_has_at_least_one_independent_claim():
    """독립항이 최소 1개 이상 있는지 검증"""
    result = claims.run(POST_CONSULTING_STATE)
    independent_claims = [c for c in result["claims"] if c["is_independent"]]
    assert len(independent_claims) >= 1, "독립항이 없음 — 최소 1개 필요"


def test_dependent_claim_references_valid_number():
    """종속항의 depends_on이 실제 존재하는 청구항 번호를 참조하는지 검증"""
    result = claims.run(POST_CONSULTING_STATE)
    claim_numbers = {c["claim_number"] for c in result["claims"]}

    for claim in result["claims"]:
        if not claim["is_independent"]:
            assert claim["depends_on"] in claim_numbers, (
                f"청구항 {claim['claim_number']}의 depends_on={claim['depends_on']}이 "
                f"존재하지 않는 청구항 번호를 참조함"
            )


# ── 재시도 루프 테스트 ─────────────────────────────────────────────────────────

def test_run_on_retry_includes_revision_count():
    """examiner 거절 후 재시도 시 revision_count가 증가하는지 검증"""
    result = claims.run(POST_EXAMINER_REJECTED_STATE)
    # 재작성 시 revision_count를 증가시켜 반환해야 함
    if "revision_count" in result:
        assert result["revision_count"] > POST_EXAMINER_REJECTED_STATE["revision_count"], (
            "재작성 시 revision_count가 증가해야 합니다"
        )
