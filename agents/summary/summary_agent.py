"""Summary Agent runner for the middle-presentation MVP.

역할:
- 5개 inventor input을 받아 사람이 확인할 요약본과 structured_invention을 만든다.
- 후속 claim/drawing/prior_art/specification agent가 읽기 좋은 구조로 정리한다.
- 상담형 재질문/slot filling은 하지 않는다.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

try:  # optional during tests
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

from agents.schemas.summary import InventorInput, SummaryAgentOutput
from agents.validation import normalize_to_schema_shape

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = os.getenv("SUMMARY_AGENT_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-5.4"


def _load_env() -> None:
    if load_dotenv is not None:
        load_dotenv(REPO_ROOT / ".env")


def _read_claim_rule_subset() -> str:
    """Summary에 필요한 claim rule 일부만 반환한다. 전체 YAML을 넣지 않아 토큰을 줄인다."""
    path = REPO_ROOT / "rules" / "claim_rules.yaml"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    # Keep only compact, stable rules needed for structured_invention.
    wanted = [
        "claim_classification:",
        "claim_element_extraction:",
        "style:",
    ]
    lines = text.splitlines()
    chunks: list[str] = []
    capture = False
    for line in lines:
        top_level = bool(line and not line.startswith(" ") and not line.startswith("#"))
        if top_level:
            capture = any(line.startswith(w) for w in wanted)
        if capture:
            chunks.append(line)
        if len("\n".join(chunks)) > 2200:
            break
    return "\n".join(chunks).strip()


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _unique_keep_order(items: list[str], limit: int) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        item = _clean(item)
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
        if len(out) >= limit:
            break
    return out


def _normalize_component_candidate(item: str) -> str:
    """긴 수식절에서 실제 구성요소 head를 보수적으로 분리한다.

    예: '... 로부터 수신된 제로 탐지 결과를 저장하는 제로 레지스터'
        -> '제로 레지스터'
    """
    item = _clean(item)
    item = re.sub(r"\[[0-9]{4}\]", "", item).strip()
    item = re.sub(r"^(상기|및|또는|와|과|를|을|에|의|로|으로|로서|로부터)\s*", "", item)
    item = re.sub(
        r"^.*?(?:저장하는|제어하는|수행하는|포함하는|생성하는|판단하는|대체하는|선택하는|누적\s*저장하는|인가되는|전달하는|배치된)\s+",
        "",
        item,
    )
    heads = r"(?:부|모듈|수단|서버|단말|장치|시스템|플랫폼|엔진|모델|분류기|처리부|생성부|분석부|저장부|통신부|인터페이스|데이터베이스|DB|프로세서|메모리|회로|레지스터|게이트|누산기|곱셈기|제어기|선택기)"
    matches = re.findall(rf"([가-힣A-Za-z0-9·/()\-\s]{{1,28}}?{heads})", item)
    if matches:
        item = _clean(matches[-1])
    return item.strip(" ,.;；")


def _is_bad_component_candidate(item: str) -> bool:
    item = _clean(item)
    bad_suffixes = ("로부", "으로부", "여부", "적용여부", "내부", "외부")
    if item.endswith(bad_suffixes):
        return True
    if len(item) < 3 or len(item) > 70:
        return True
    if re.search(r"^(상기|및|또는|와|과|를|을|에|의|로|으로|로서|로부터)\s", item):
        return True
    if re.search(r"(여부|결과|값|신호|정보)$", item) and not re.search(r"(회로|레지스터|모듈|부|장치|시스템|제어기|선택기)$", item):
        return True
    return False


def _normalize_relation_target(target: str) -> str:
    target = _clean(target).strip(" ,.;；")
    target = re.sub(r"\[[0-9]{4}\]", "", target).strip()
    target = re.sub(r"^상기\s+", "", target)
    if "로부터 수신된" in target:
        target = target.split("로부터 수신된", 1)[1].strip()
    if "기초하" in target and "신호" in target:
        m = re.search(r"([^,]{2,50}?신호)$", target)
        if m:
            target = m.group(1)
    target = re.sub(r"^상기\s+", "", target)
    return target[:80]


def _extract_relation_edges(core: str, component_candidates: list[str]) -> list[dict[str, Any]]:
    """중간발표 데모용 invention_graph seed를 보수적으로 만든다."""
    edges: list[dict[str, Any]] = []
    patterns = [
        (r"(?P<target>[^.;；]{3,60}?)를\s+저장하는\s+(?P<source>[^.;；]{2,40}?(?:레지스터|저장부|메모리))", "stores"),
        (r"(?P<target>[^.;；]{3,70}?)를\s+제어하는\s+(?P<source>[^.;；]{2,45}?(?:회로|제어기|모듈|부))", "controls"),
        (r"(?P<target>[^.;；]{3,70}?)를\s+판단하는\s+(?P<source>[^.;；]{2,45}?(?:회로|모듈|부|모델))", "determines"),
        (r"(?P<target>[^.;；]{3,70}?)를\s+선택(?:적으로)?\s*대체하는\s+(?P<source>[^.;；]{2,45}?(?:선택기|회로|모듈|부))", "selects_or_replaces"),
        (r"(?P<source>[^.;；]{2,45}?(?:회로|제어기|모듈|부))[^.;；]{0,80}?기초하여[^.;；]{0,70}?(?P<target>[^.;；]{3,60}?신호)를\s+제어", "controls_based_on"),
        (r"(?P<source>[^.;；]{2,45}?(?:회로|모듈|부|제어기))[^.;；]{0,80}?(?P<target>[^.;；]{3,60}?결과)를\s+재사용", "reuses"),
    ]
    for pat, rel in patterns:
        for m in re.finditer(pat, core):
            source = _normalize_component_candidate(m.group("source"))
            target = _normalize_relation_target(m.group("target"))
            if _is_bad_component_candidate(source) or not target:
                continue
            evidence = _clean(m.group(0))[:180]
            edges.append({
                "source": source,
                "target": target,
                "relation": rel,
                "direction": "source_to_target",
                "evidence": evidence,
                "confidence": 0.72,
                "mandatory": source in component_candidates,
                "review_flag": "regex_seed_review",
            })
    return edges[:10]


def _extract_sequence_edges(process_candidates: list[str]) -> list[dict[str, Any]]:
    """방법 발명에서 처리 단계 간 선후관계 seed를 만든다."""
    if not process_candidates:
        return []
    steps: list[str] = []
    for cand in process_candidates:
        parts = re.split(r",\s*|;|；|\s+및\s+", cand)
        for p in parts:
            p = _clean(p)
            p = re.sub(r"^(상기|및|또는)\s*", "", p)
            if len(p) >= 12 and re.search(r"(수신|획득|검색|입력|생성|분석|추출|구조화|변환|저장|출력|제공|전송|판단|제어)", p):
                steps.append(p[:90])
    steps = _unique_keep_order(steps, 8)
    edges: list[dict[str, Any]] = []
    for idx in range(len(steps) - 1):
        edges.append({
            "source": steps[idx],
            "target": steps[idx + 1],
            "relation": "next_step",
            "direction": "source_to_target",
            "evidence": f"{steps[idx]} -> {steps[idx + 1]}",
            "confidence": 0.6,
            "mandatory": False,
            "review_flag": "sequence_seed_review",
        })
    return edges[:7]


def regex_preanalyze_inventor_input(inventor_input: InventorInput) -> dict[str, Any]:
    """5-field input을 rule-first로 가볍게 분해한다.

    목적은 LLM을 대체하는 것이 아니라, 긴 입력에서 구성/단계/데이터 후보를
    놓치지 않게 하는 힌트 제공이다. 특정 PDF/도메인 단어를 하드코딩하지 않는다.
    """
    core = _clean(inventor_input.core_technology)
    combined = _clean(" ".join(inventor_input.model_dump().values()))

    clauses = _unique_keep_order(
        [c for c in re.split(r"[;；]|(?:\s+및\s+)|(?:,\s*및\s*)", core) if len(_clean(c)) >= 18],
        12,
    )
    process_candidates = _unique_keep_order(
        re.findall(r"([^.;；]{8,160}?(?:하는|수행하는|생성하는|변환하는|산출하는|도출하는|분류하는|검출하는|인식하는|제공하는)\s*단계|[^.;；]{8,160}?단계)", core),
        10,
    )
    raw_components = re.findall(
        r"([가-힣A-Za-z0-9·/()\-\s]{2,45}?(?:부|모듈|수단|서버|단말|장치|시스템|플랫폼|엔진|모델|분류기|처리부|생성부|분석부|저장부|통신부|인터페이스|데이터베이스|DB|프로세서|메모리|회로|레지스터|게이트|누산기|곱셈기|제어기|선택기))",
        core,
    )
    component_candidates = _unique_keep_order(
        [c for c in (_normalize_component_candidate(x) for x in raw_components) if not _is_bad_component_candidate(c)],
        14,
    )
    data_candidates = _unique_keep_order(
        re.findall(
            r"([가-힣A-Za-z0-9·/()\-\s]{2,40}?(?:데이터|정보|영상|이미지|문서|질문|토큰|벡터|임베딩|신호|요청|응답|콘텐츠|프레임|문장|확률|결과))",
            combined,
        ),
        14,
    )
    relation_candidates = _unique_keep_order(
        re.findall(
            r"([^.;；]{8,140}?(?:입력|수신|생성|변환|분류|산출|도출|전송|저장|비교|매핑|정규화|검출|인식|학습|분석|제공|출력)[^.;；]{0,80})",
            core,
        ),
        12,
    )

    relation_edges = _extract_relation_edges(core, component_candidates)
    sequence_edges = _extract_sequence_edges(process_candidates)

    route = "unknown"
    if re.search(r"방법|단계", core[-700:]) or process_candidates:
        route = "method_like"
    if re.search(r"시스템|장치|서버|단말|프로세서|연산\s*소자|PE|회로|레지스터", core) and component_candidates:
        route = "system_like" if route == "unknown" else "method_and_system_like"
    if re.search(r"기록\s*매체|저장\s*매체|비일시적\s*저장매체|프로그램", core):
        route = "storage_medium_related" if route == "unknown" else route + "+storage_medium_related"

    return {
        "route_hint": route,
        "component_candidates": component_candidates,
        "process_candidates": process_candidates,
        "data_candidates": data_candidates,
        "relation_candidates": relation_candidates,
        "invention_graph_seed": {
            "relation_edges": relation_edges,
            "sequence_edges": sequence_edges,
            "note": "document_links/invention_graph에 올리기 전 단계의 후보. source/target/relation/evidence를 사람이 검토 가능하게 제공한다.",
        },
        "clause_candidates": clauses[:8],
        "caution": "정규표현식 후보는 힌트일 뿐이다. 입력 근거가 불명확하거나 기능 단위가 아니면 structured_invention에 넣지 않는다.",
    }


def build_summary_prompt(
    inventor_input: InventorInput,
    feedback_history: list[str] | None = None,
    rule_subset: str | None = None,
) -> list[dict[str, str]]:
    """저토큰 Summary prompt를 만든다."""
    feedback_history = feedback_history or []
    rule_subset = rule_subset if rule_subset is not None else _read_claim_rule_subset()
    regex_hints = regex_preanalyze_inventor_input(inventor_input)

    system = (
        "너는 한국어 특허 작성 파이프라인의 Summary Agent다. "
        "입력 5개 필드만 근거로 readable_summary와 structured_invention을 만든다. "
        "재질문, slot filling, 청구항 문장 작성은 하지 않는다. "
        "입력에 없는 구체 수치/구성/효과를 만들지 말고, 불명확하면 warnings에 적어라. "
        "출력은 compact JSON으로 작성하고 전체 응답은 1800자 내외로 제한한다. "
        "반드시 JSON object 하나만 반환한다."
    )

    user_obj: dict[str, Any] = {
        "task": "5-field inventor input을 중간발표 MVP용 SummaryAgentOutput JSON으로 변환",
        "inventor_input": inventor_input.model_dump(),
        "feedback_history": feedback_history,
        "deterministic_preanalysis": regex_hints,
        "preanalysis_usage_rule": "정규표현식 후보는 긴 입력을 놓치지 않기 위한 route/hint다. 후보를 그대로 복사하지 말고, 5개 입력의 문맥상 발명 구성/단계/데이터로 타당한 것만 채택하라. invention_graph_seed는 관계/제한사항/선후관계 후보이며, 확정 불가하면 warnings에 남겨라.",
        "output_constraints": {
            "readable_summary": "한국어 3~5문장",
            "compactness": "notes/evidence/details는 특별한 내용 없으면 빈 배열/빈 객체로 둔다. 각 문자열은 120자 이하를 원칙으로 한다.",
            "structured_invention": [
                "components는 입력에 근거가 있는 기능 단위/처리 단위/하드웨어·소프트웨어 단위 중심으로 최대 6개",
                "상위 포괄어(시스템/서버/장치/플랫폼/단말/모듈 등) 안에 명시된 내부 기능 단위가 있으면, 특정 명칭을 예시로 고정하지 말고 입력 문장의 근거가 있는 경우에만 별도 component로 분리",
                "상위 구성과 내부 구성의 관계는 component.role 또는 evidence에 짧게 표시",
                "process_steps는 최대 6개, 데이터/신호/요청/문서/이미지 등의 흐름 순서가 보일 때만 작성",
                "input_data/output_result/technical_features/differentiators/expected_effects는 각 최대 5개",
                "warnings는 최대 4개",
            ],
            "generalization_policy": [
                "특정 PDF의 도메인 단어를 규칙처럼 반복하지 않는다",
                "구성요소 후보는 이름 패턴이 아니라 기능·입출력·관계 근거로 판단한다",
                "입력에 없는 내부 모듈, 알고리즘, 성능 수치는 생성하지 않는다",
                "상위 구성만 있고 내부 처리가 불명확하면 분리하지 말고 warnings에 남긴다",
            ],
            "do_not": [
                "청구항 문장 작성 금지",
                "입력에 없는 세부 구성 invent 금지",
                "마케팅식 표현만 반복 금지",
                "JSON 외 설명 금지",
            ],
        },
        "compact_rule_reference": rule_subset,
        "expected_top_level_keys": [
            "status", "summary", "warnings", "notes", "evidence", "details",
            "project_name", "problem_to_solve", "prior_art_problem", "core_technology", "expected_effect",
            "readable_summary", "structured_invention", "feedback_applied",
        ],
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user_obj, ensure_ascii=False)},
    ]


def _normalize_summary_raw(raw: Any) -> Any:
    """Summary 전용 최소 보정만 수행한다.

    공통 타입/shape 보정은 agents.validation.normalize_to_schema_shape()가
    Pydantic schema annotation 기반으로 처리한다. 여기서는 Summary 의미상
    필요한 key 보존/별칭 처리만 둔다.
    """
    if not isinstance(raw, dict):
        return raw
    si = raw.get("structured_invention")
    if isinstance(raw.get("evidence"), dict):
        raw.setdefault("details", {})["evidence_map"] = raw.get("evidence")
        raw["evidence"] = []
    if isinstance(si, dict) and not si.get("title") and raw.get("project_name"):
        si["title"] = raw.get("project_name")
    return raw


def run_summary_agent(
    inventor_input: InventorInput,
    feedback_history: list[str] | None = None,
    model: str | None = None,
    max_completion_tokens: int = 900,
) -> SummaryAgentOutput:
    """OpenAI-compatible Chat Completions로 Summary Agent 1회 실행 후 Pydantic 검증."""
    _load_env()
    model = model or os.getenv("SUMMARY_AGENT_MODEL") or os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    from openai import OpenAI

    messages = build_summary_prompt(inventor_input, feedback_history)
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        max_completion_tokens=max_completion_tokens,
    )
    content = resp.choices[0].message.content or "{}"
    raw = json.loads(content)
    raw = _normalize_summary_raw(raw)
    raw = normalize_to_schema_shape(raw, SummaryAgentOutput)
    output = SummaryAgentOutput.model_validate(raw)
    output.details.setdefault("model", model)
    output.details.setdefault("regex_preanalysis", regex_preanalyze_inventor_input(inventor_input))
    usage = getattr(resp, "usage", None)
    if usage:
        output.details.setdefault("usage", {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        })
    return output


def estimate_prompt_size(inventor_input: InventorInput, feedback_history: list[str] | None = None) -> dict[str, int]:
    messages = build_summary_prompt(inventor_input, feedback_history)
    chars = sum(len(m["content"]) for m in messages)
    return {"prompt_chars": chars, "rough_prompt_tokens": max(1, chars // 3)}
