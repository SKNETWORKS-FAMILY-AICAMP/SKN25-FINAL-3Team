"""Unit tests for prior-art query and risk aggregation logic."""

import pytest

from agents.core.state import ClaimResult
from agents.prior_art_agent import prior_art_agent


def test_build_claim1_query_uses_claim_number_one(claim_result):
    assert prior_art_agent._build_claim1_query_text(claim_result) == (
        claim_result.claims[0].content
    )


def test_build_claim1_query_returns_empty_when_claim_one_missing(claim_result):
    only_second = ClaimResult(claims=[claim_result.claims[1]])

    assert prior_art_agent._build_claim1_query_text(only_second) == ""


@pytest.mark.parametrize(
    ("risks", "expected"),
    [
        (["high", "high", "low"], "high"),
        (["high", "low"], "medium"),
        (["medium", "medium"], "medium"),
        (["low", "low"], "low"),
    ],
)
def test_summarize_overall_risk_applies_thresholds(risks, expected):
    result = prior_art_agent._summarize_overall_risk(
        [{"risk_level": risk} for risk in risks]
    )

    assert result["level"] == expected
    assert sum(result["counts"].values()) == len(risks)


def test_merge_unique_preserves_first_seen_order():
    assert prior_art_agent._merge_unique([["A", "B"], ["B", "", "C"]]) == [
        "A",
        "B",
        "C",
    ]


def test_run_prior_art_agent_short_circuits_without_claims():
    result = prior_art_agent.run_prior_art_agent({"claims_data": None})

    assert result["prior_art_data"].candidates == []
    assert result["prior_art_data"].search_source == "UNKNOWN"
