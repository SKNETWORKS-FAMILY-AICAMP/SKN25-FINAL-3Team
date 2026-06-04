"""specification agent 내부에서 사용하는 헬퍼 유틸리티.

JSON 파싱, 검증, 용어 정규화 등을 담당한다.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Any


# ---------------------------------------------------------------------------
# 1. Config
# ---------------------------------------------------------------------------

@dataclass
class SpecificationAgentConfig:
    model: str = ""
    temperature: float = 0.1
    max_repair_attempts: int = 2

    def __post_init__(self):
        if not self.model:
            self.model = os.getenv("OPENAI_SPEC_MODEL", "gpt-5.1")


# ---------------------------------------------------------------------------
# 2. JSON 파싱 유틸리티
# ---------------------------------------------------------------------------

def safe_parse_json(text: str) -> Optional[dict]:
    """LLM 응답에서 JSON 객체를 안전하게 추출한다."""
    text = text.strip()

    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# 3. 참조부호/공개번호 탐지 및 정규화
# ---------------------------------------------------------------------------

_REF_COMPONENT_PATTERN = re.compile(r"([가-힣a-zA-Z\s]+?)\s*\(\d{1,4}[a-zA-Z]?\)")
_REF_NUM_PATTERN = re.compile(r"\((\d{1,4}[A-Za-z]?)\)")

_PUB_NO_PATTERNS = [
    re.compile(r"KR\s?\d{2}[-\s]?\d{4}[-\s]?\d{5,7}\s?[A-Z]?", re.IGNORECASE),
    re.compile(r"\b\d{2}[-\s]\d{4}[-\s]\d{5,7}\b", re.IGNORECASE),
    re.compile(
        r"(?:US|JP|CN|EP|WO|DE|GB|FR)[\s\-]?\d{4,}[\s\-]?\d*[\s\-]?[A-Z]?\d*",
        re.IGNORECASE,
    ),
]


def detect_reference_numerals(text: str) -> set[str]:
    return set(_REF_NUM_PATTERN.findall(text))


def normalize_pub_no(s: str) -> str:
    return re.sub(r"[\s\-]", "", s.upper().strip())


def detect_publication_numbers(text: str) -> set[str]:
    found = set()
    for pattern in _PUB_NO_PATTERNS:
        for m in pattern.findall(text):
            found.add(normalize_pub_no(m.strip()))
    return found


def normalize_reference_numerals(refs) -> dict:
    """list 또는 dict 형태의 reference_numerals를 dict로 정규화한다."""
    if isinstance(refs, dict):
        return refs
    if isinstance(refs, list):
        out = {}
        for item in refs:
            number = str(item.get("number", "")).strip()
            if not number:
                continue
            out[number] = {
                "number": number,
                "term": item.get("term") or item.get("label", ""),
                "figure": item.get("figure", ""),
                "component_id": item.get("component_id", ""),
                "description": item.get("description", ""),
            }
        return out
    return {}


def detect_numeric_claims(text: str) -> set[str]:
    """정량 수치가 포함된 휴리스틱 탐지"""
    return set(re.findall(r"\d+(?:\.\d+)?\s*(?:%|배|초|분|시간|건|회|명|개)", text))


# ---------------------------------------------------------------------------
# 4. 문단 분리 / 중복 제거
# ---------------------------------------------------------------------------

def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]


def split_sentences(text: str) -> list[str]:
    # 영문/한국어 문장 분리
    sentences = re.split(r"(?<=[.!?。])\s+|(?<=다\.)", text)
    return [s.strip() for s in sentences if s.strip()]


def deduplicate_list(items: list) -> list:
    seen: set = set()
    out: list = []
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, dict) else str(item)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


# ---------------------------------------------------------------------------
# 5. 허용 목록 빌더
# ---------------------------------------------------------------------------

def build_allowed_ref_numerals(state: dict) -> set[str]:
    drawings = state.get("drawings") or {}
    refs = normalize_reference_numerals(drawings.get("reference_numerals") or {})
    nums = set(refs.keys())
    
    doc_links = state.get("document_links") or {}
    nums |= set((doc_links.get("reference_numeral_map") or {}).keys())
    return nums


def build_allowed_publication_numbers(state: dict) -> set[str]:
    prior_art = state.get("prior_art") or {}
    details = prior_art.get("details") or {}
    candidates = prior_art.get("candidates") or []
    extras = details.get("candidates_extra") or []

    nums = set()
    for c in candidates:
        if c.get("publication_no"):
            nums.add(normalize_pub_no(c["publication_no"]))

    for e in extras:
        if e.get("publication_no"):
            nums.add(normalize_pub_no(e["publication_no"]))

    return nums


def build_allowed_terms(state: dict) -> dict[str, str]:
    terms: dict[str, str] = {}
    
    # 1) Claims
    claims = state.get("claims") or {}
    for dc in claims.get("draft_claims") or []:
        for el in dc.get("elements") or []:
            terms[el] = el
            
    # 2) Drawings
    drawings = state.get("drawings") or {}
    refs = normalize_reference_numerals(drawings.get("reference_numerals") or {})
    for _k, rn in refs.items():
        t = rn.get("term", "")
        if t and t not in terms:
            terms[t] = t
            
    # 3) Consultation or Summary components and aliases
    consultation = state.get("consultation") or {}
    summary = state.get("summary") or {}
    structured = summary.get("structured_invention") or {}
    
    consultation_components = consultation.get("components") or []
    structured_components = structured.get("components") or []
    comps = deduplicate_list(consultation_components + structured_components)
    
    for comp in comps:
        name = comp.get("name", "")
        if name:
            terms[name] = name
        for alias in comp.get("aliases") or []:
            if alias:
                terms[alias] = name or alias
                
    # 4) Document Links term_registry
    doc_links = state.get("document_links") or {}
    term_registry = doc_links.get("term_registry") or []
    
    # term_registry가 dict인 경우 values 순회, list인 경우 그대로 순회
    if isinstance(term_registry, dict):
        term_registry_items = term_registry.values()
    else:
        term_registry_items = term_registry

    for reg in term_registry_items:
        if not isinstance(reg, dict):
            continue
        canonical = reg.get("canonical_name", "")
        if canonical:
            terms[canonical] = canonical
        for alias in reg.get("aliases") or []:
            if alias:
                terms[alias] = canonical or alias
                
    return terms


# ---------------------------------------------------------------------------
# 6. SpecificationMaterial
# ---------------------------------------------------------------------------

@dataclass
class SpecificationMaterial:
    invention_title: str = ""
    technical_field_natural: str = ""
    problem: str = ""
    solution: str = ""
    differentiation: str = ""
    effect: str = ""
    components: list[dict] = field(default_factory=list)
    process_steps: list[dict] = field(default_factory=list)
    claim_like_features: list[str] = field(default_factory=list)
    missing_slots: list[str] = field(default_factory=list)
    draft_claims: list[dict] = field(default_factory=list)
    figures: list[dict] = field(default_factory=list)
    reference_numerals: dict[str, dict] = field(default_factory=dict)
    ipc_focus: list[str] = field(default_factory=list)
    prior_art_candidates: list[dict] = field(default_factory=list)
    overlap_points: list[str] = field(default_factory=list)
    difference_points: list[str] = field(default_factory=list)
    novelty_risk: str = "unknown"
    inventive_step_risk: str = "unknown"
    analysis_summary: str = ""
    limitations: list[str] = field(default_factory=list)
    invention_graph: dict = field(default_factory=dict)
    drafting_options: dict = field(default_factory=dict)
    allowed_ref_numerals: set[str] = field(default_factory=set)
    allowed_pub_numbers: set[str] = field(default_factory=set)
    allowed_terms: dict[str, Any] = field(default_factory=dict)
    independent_claim_numbers: list[int] = field(default_factory=list)
    dependent_claim_numbers: list[int] = field(default_factory=list)
    source_brief_description_of_drawings: str = ""


def merge_prior_art_candidate_extras(candidates: list, candidates_extra: list) -> list:
    extra_map = {ex.get("patent_id"): ex for ex in candidates_extra if ex.get("patent_id")}
    seen = set()
    merged = []

    for c in candidates:
        pid = c.get("patent_id")
        if pid:
            seen.add(pid)
        c_copy = dict(c)
        if pid and pid in extra_map:
            c_copy.update(extra_map[pid])
        merged.append(c_copy)

    for ex in candidates_extra:
        pid = ex.get("patent_id")
        if pid and pid not in seen:
            merged.append(dict(ex))

    return merged


def as_text(value) -> str:
    if isinstance(value, list):
        parts = []
        for v in value:
            if isinstance(v, dict):
                parts.append(str(
                    v.get("text")
                    or v.get("description")
                    or v.get("name")
                    or v.get("effect")
                    or v.get("value")
                    or ""
                ))
            elif v:
                parts.append(str(v))
        return "\n".join(p for p in parts if p)
    if isinstance(value, dict):
        return str(
            value.get("text")
            or value.get("description")
            or value.get("name")
            or value.get("effect")
            or value.get("value")
            or ""
        )
    return str(value or "")


def build_specification_material(state: dict) -> SpecificationMaterial:
    summary = state.get("summary") or {}
    structured = summary.get("structured_invention") or {}
    c = state.get("consultation") or {}
    pa = state.get("prior_art") or {}
    pa_details = pa.get("details") or {}
    cl = state.get("claims") or {}
    dr = state.get("drawings") or {}
    ig = state.get("invention_graph") or {}
    do = state.get("drafting_options") or {}
    existing_spec = state.get("specification") or {}

    ipc_focus = pa.get("ipc_focus") or pa_details.get("ipc_focus") or []
    analysis_summary = pa.get("analysis_summary") or pa_details.get("analysis_summary", "")
    novelty_risk = pa.get("novelty_risk") or pa_details.get("novelty_risk", "unknown")
    inventive_step_risk = pa.get("inventive_step_risk") or pa_details.get("inventive_step_risk", "unknown")
    limitations = pa.get("limitations") or pa_details.get("limitations") or []
    
    candidates = pa.get("candidates") or []
    candidates_extra = pa_details.get("candidates_extra") or []
    merged_candidates = merge_prior_art_candidate_extras(candidates, candidates_extra)
    
    effect = (
        as_text(c.get("effect"))
        or as_text(c.get("effects"))
        or as_text(structured.get("expected_effects"))
        or ""
    )
    differentiation = (
        as_text(c.get("differentiation"))
        or as_text(c.get("differentiators"))
        or ""
    )
    solution = (
        as_text(c.get("solution"))
        or as_text(c.get("solutions"))
        or as_text(structured.get("solution"))
        or ""
    )
    invention_title = c.get("invention_title") or structured.get("title") or structured.get("invention_title") or ""
    technical_field_natural = c.get("technical_field_natural", "")
    
    consultation_components = c.get("components") or []
    structured_components = structured.get("components") or []
    components = deduplicate_list(consultation_components + structured_components)
    
    process_steps = deduplicate_list(
        (c.get("process_steps") or []) + (structured.get("process_steps") or [])
    )
    
    problem = c.get("problem") or structured.get("problem") or ""

    claim_like_features = (
        c.get("claim_like_features")
        or structured.get("claim_like_features")
        or structured.get("technical_features")
        or []
    )
    missing_slots = c.get("missing_slots") or structured.get("missing_slots") or []

    return SpecificationMaterial(
        invention_title=invention_title,
        technical_field_natural=technical_field_natural,
        problem=problem,
        solution=solution,
        differentiation=differentiation,
        effect=effect,
        components=components,
        process_steps=process_steps,
        claim_like_features=claim_like_features,
        missing_slots=missing_slots,
        draft_claims=cl.get("draft_claims") or [],
        figures=dr.get("figures") or [],
        reference_numerals=normalize_reference_numerals(dr.get("reference_numerals") or {}),
        ipc_focus=ipc_focus,
        prior_art_candidates=merged_candidates,
        overlap_points=pa.get("overlap_points") or pa_details.get("overlap_points") or [],
        difference_points=pa.get("difference_points") or pa_details.get("difference_points") or [],
        novelty_risk=novelty_risk,
        inventive_step_risk=inventive_step_risk,
        analysis_summary=analysis_summary,
        limitations=limitations,
        invention_graph=ig,
        drafting_options=do,
        allowed_ref_numerals=build_allowed_ref_numerals(state),
        allowed_pub_numbers=build_allowed_publication_numbers(state),
        allowed_terms=build_allowed_terms(state),
        independent_claim_numbers=cl.get("independent_claim_numbers") or [],
        dependent_claim_numbers=cl.get("dependent_claim_numbers") or [],
        source_brief_description_of_drawings=existing_spec.get("brief_description_of_drawings", ""),
    )


_STEP_LABEL_PATTERN = re.compile(
    r"(\([a-zA-Z가-힣]\)|단계\s*\([a-zA-Z가-힣]\)|\([0-9]+\))"
)

def has_method_step_labels(text: str) -> bool:
    return bool(_STEP_LABEL_PATTERN.search(text or ""))

def get_labeled_method_independent_claims(material: SpecificationMaterial) -> list[dict]:
    results = []
    independent_claim_numbers = {str(n) for n in material.independent_claim_numbers or []}
    for dc in material.draft_claims:
        claim_no = str(dc.get("claim_no", ""))
        is_independent = (
            dc.get("type") == "independent"
            or claim_no in independent_claim_numbers
            or (not independent_claim_numbers and claim_no == "1")
        )
        category_type = str(
            dc.get("claim_type")
            or dc.get("claim_category")
            or dc.get("category")
            or ""
        ).lower()
        if is_independent and ("method" in category_type or "방법" in category_type):
            text = dc.get("text", "")
            if has_method_step_labels(text):
                results.append(dc)
    return results


def get_independent_claim_elements(material: SpecificationMaterial) -> list[str]:
    elems = []
    independent_claim_numbers = {str(n) for n in material.independent_claim_numbers or []}
    for dc in material.draft_claims:
        claim_no = str(dc.get("claim_no", ""))
        is_independent = (
            dc.get("type") == "independent"
            or claim_no in independent_claim_numbers
            or (not independent_claim_numbers and claim_no == "1")
        )
        if is_independent:
            elems.extend(dc.get("elements") or [])
    return deduplicate_list(elems)


# ---------------------------------------------------------------------------
# 7. 검증기
# ---------------------------------------------------------------------------

def detect_repeated_phrases(text: str) -> list[str]:
    issues = []
    
    repeated_word_pattern = re.compile(r"\b([가-힣A-Za-z0-9_\-]+)\s+\1\b")
    for m in repeated_word_pattern.finditer(text):
        issues.append(m.group(0))
        
    tokens = re.findall(r"[가-힣A-Za-z0-9_\-]+", text)
    for n in range(2, 6):
        for i in range(len(tokens) - 2 * n + 1):
            if tokens[i:i+n] == tokens[i+n:i+2*n]:
                issues.append(" ".join(tokens[i:i+n]))
                
    return sorted(set(issues))


def is_style_warning(issue: str) -> bool:
    return "[style_warning]" in issue


@dataclass
class ValidationResult:
    passed: bool = True
    issues: list[str] = field(default_factory=list)


_SPEC_REQUIRED = [
    "technical_field", "background_art", "problem_to_solve",
    "means_for_solving", "effects", "brief_description_of_drawings",
    "detailed_description",
]


def validate_specification(
    state: dict,
    spec: dict,
    raw_output: dict,
    material: SpecificationMaterial,
) -> ValidationResult:
    r = ValidationResult()
    
    # 누락 검증 (hard issue 성격)
    for key in _SPEC_REQUIRED:
        if not spec.get(key):
            r.issues.append(f"필수 섹션 '{key}' 누락 또는 빈 값입니다.")

    # IPC 코드 직접 노출 검증 (style_warning)
    _IPC_CODE_PATTERN = re.compile(r"\b[A-HY]\d{2}[A-Z]?\s*\d+/\d+\b")
    technical_field = spec.get("technical_field", "")
    if _IPC_CODE_PATTERN.search(technical_field):
        r.issues.append(
            "[style_warning] 기술분야에 IPC 코드가 직접 노출되어 있습니다. IPC는 자연어 기술분야로 풀어 쓰는 것이 적절합니다."
        )

    # 배경기술(background_art) 검증 (style_warning)
    background_art = spec.get("background_art", "")
    if re.search(r"(관련 기술로는|관련 선행문헌으로|조사되었다|검색되었다|등이 조사|등이 검색)", background_art):
        r.issues.append(
            "[style_warning] 배경기술에 선행기술조사 보고서식 표현이 포함되어 있습니다. 배경기술은 선행기술의 내용을 자연어로 풀어 쓰는 것이 적절합니다."
        )

    if detect_publication_numbers(background_art):
        r.issues.append(
            "[style_warning] 배경기술에 선행문헌번호가 직접 나열되어 있습니다. 선행문헌번호는 선행기술문헌 항목에서 처리하고, 배경기술에는 종래기술의 내용과 문제점을 자연어로 작성하는 것이 적절합니다."
        )

    tf = spec.get("technical_field", "")
    if len(split_paragraphs(tf)) > 1:
        r.issues.append("[style_warning] technical_field는 가급적 한 문단이어야 합니다.")

    ba = spec.get("background_art", "")
    if len(split_paragraphs(ba)) > 1:
        r.issues.append("[style_warning] background_art는 여러 문단일 수 있으나 가급적 1~2문단이 권장됩니다.")

    combined_text = "\n".join([
        spec.get("technical_field", ""),
        spec.get("background_art", ""),
        spec.get("problem_to_solve", ""),
        spec.get("means_for_solving", ""),
        spec.get("effects", ""),
        spec.get("brief_description_of_drawings", ""),
        spec.get("detailed_description", ""),
    ])

    for step in material.process_steps:
        name = (step.get("name") or "").strip()
        if name and len(name) >= 5 and name in combined_text:
            if "단계" in name:
                r.issues.append(f"[style_warning] process_steps.name이 본문에 직접 노출됨(자연어로 풀어쓸 것 권장): {name}")
            else:
                r.issues.append(f"process_steps.name이 본문에 직접 노출됨: {name}")

    INTERNAL_STEP_PHRASES = [
        "속성 변경 정보 존재 판단",
        "속성 변경 정보 조회",
        "속성 변경 정보 기반 최종 카드 속성 정보 생성",
        "판독된 카드 속성 정보 기반 최종 카드 속성 정보 생성",
        "활성정보 포함 여부 판단",
    ]
    for phrase in INTERNAL_STEP_PHRASES:
        if phrase in combined_text:
            r.issues.append(f"state 내부 식별자/명사구가 본문에 그대로 노출됨: {phrase}")

    UNSUPPORTED_EXPANSION_PHRASES = [
        "새로운 테이블을 생성",
        "새 테이블을 생성",
        "신규 테이블을 생성",
        "최초 레코드를 등록",
        "확장 처리",
    ]
    
    source_text = json.dumps({
        "process_steps": material.process_steps,
        "figures": material.figures,
        "draft_claims": material.draft_claims,
    }, ensure_ascii=False)

    for phrase in UNSUPPORTED_EXPANSION_PHRASES:
        if phrase in combined_text and phrase not in source_text:
            r.issues.append(f"도면/state에 없는 임의 확장 처리 가능성: {phrase}")

    EFFECTS_PROCEDURE_PHRASES = [
        "캐쉬 히트",
        "캐쉬 미스",
        "존재 여부를 판단",
        "데이터를 수신",
        "캐쉬 영역에 저장",
        "단말로 전송",
        "요청 데이터를",
        "서버 또는 인접단말",
    ]
    effects_text = spec.get("effects", "")
    if sum(1 for p in EFFECTS_PROCEDURE_PHRASES if p in effects_text) >= 2:
        r.issues.append(
            "[style_warning] 발명의 효과에 상세 처리 절차가 과도하게 포함되어 있습니다. 효과는 최종 기술적 효과 중심으로 압축하는 것이 적절합니다."
        )

    UNSUPPORTED_IMPLEMENTATION_DETAIL_PHRASES = [
        "요청 단말의 식별 정보",
        "접속 상태",
        "위치 정보",
        "적합한 인접단말",
        "적합한 단말",
        "관리 시스템으로부터",
        "요청·응답 메시지",
        "요청 응답 메시지",
        "식별 정보를 추출",
    ]
    
    source_text_detail = json.dumps({
        "consultation": state.get("consultation") or {},
        "process_steps": material.process_steps,
        "figures": material.figures,
        "reference_numerals": material.reference_numerals,
        "draft_claims": material.draft_claims,
        "invention_graph": material.invention_graph,
    }, ensure_ascii=False)
    
    detail_text = spec.get("detailed_description", "")
    for phrase in UNSUPPORTED_IMPLEMENTATION_DETAIL_PHRASES:
        if phrase in detail_text and phrase not in source_text_detail:
            r.issues.append(
                f"[style_warning] state/도면 근거가 약한 구현 세부사항이 상세한 설명에 포함될 수 있습니다: {phrase}"
            )

    tf_text = spec.get("technical_field", "")
    if re.search(r"(프로그램|기록매체|컴퓨터로 읽을 수 있는)", tf_text):
        title = material.invention_title or ""
        source_tf = material.technical_field_natural or ""
        if not re.search(r"(프로그램|기록매체|컴퓨터로 읽을 수 있는)", title + " " + source_tf):
            r.issues.append(
                "[style_warning] 기술분야에 프로그램/기록매체가 포함되어 있습니다. 원문 기술분야나 발명 명칭에 명시되지 않았다면 대표 발명인 장치/방법 중심으로 줄이는 것이 적절합니다."
            )

    all_text = " ".join(spec.get(k, "") for k in _SPEC_REQUIRED)
    found_pubs = detect_publication_numbers(all_text)
    illegal_pubs = found_pubs - material.allowed_pub_numbers
    if illegal_pubs:
        r.issues.append(f"허용되지 않은 선행문헌번호: {illegal_pubs}")

    found_refs = detect_reference_numerals(all_text)
    if not material.allowed_ref_numerals and found_refs:
        r.issues.append(f"참조부호가 제공되지 않았는데 참조부호가 사용되었습니다: {found_refs}")
    elif material.allowed_ref_numerals:
        illegal_refs = found_refs - material.allowed_ref_numerals
        if illegal_refs:
            r.issues.append(f"허용되지 않은 참조부호: {illegal_refs}")

    means_text = spec.get("means_for_solving", "").lower()
    detail_text = spec.get("detailed_description", "").lower()

    def check_element_presence(el_text: str, target_text: str) -> bool:
        if el_text.lower() in target_text:
            return True
        # Check canonical/aliases
        canon = material.allowed_terms.get(el_text)
        if canon and str(canon).lower() in target_text:
            return True
        for alias, c_name in material.allowed_terms.items():
            if str(c_name) == el_text or str(c_name) == str(canon):
                if str(alias).lower() in target_text:
                    return True
        return False

    # means_for_solving 자체 검증
    for el in get_independent_claim_elements(material):
        if not check_element_presence(el, means_text):
            r.issues.append(f"독립항 구성요소 '{el}'이(가) 해결수단에 명확히 반영되지 않았습니다. (동의어 포함 미발견)")

    # detailed_description 자체 검증
    independent_claim_numbers = {str(n) for n in material.independent_claim_numbers or []}
    for dc in material.draft_claims:
        claim_no = str(dc.get("claim_no", ""))
        is_independent = (
            dc.get("type") == "independent"
            or claim_no in independent_claim_numbers
            or (not independent_claim_numbers and claim_no == "1")
        )
        for el in dc.get("elements") or []:
            if not check_element_presence(el, detail_text):
                if is_independent:
                    r.issues.append(f"독립항 요소 '{el}'이(가) 상세한 설명(실시예)에 미등장.")
                else:
                    r.issues.append(f"[style_warning] 종속항 요소 '{el}'이(가) 상세한 설명에 명확히 등장하지 않습니다.")

    # 참조부호 검증
    if material.allowed_ref_numerals:
        refs_in_detail = detect_reference_numerals(spec.get("detailed_description", ""))
        if not refs_in_detail:
            r.issues.append("참조부호가 제공되었지만 상세한 설명에서 참조부호가 사용되지 않았습니다.")

    # 길이 검증
    detail = spec.get("detailed_description", "")
    if len(material.draft_claims) > 0 and len(split_sentences(detail)) <= 2 and len(detail) < 400:
        r.issues.append("상세한 설명이 실시예로 보기에는 지나치게 짧습니다.")
                
    allowed_numeric_text = " ".join([
        as_text(material.effect),
        as_text(material.solution),
        as_text(material.differentiation),
        as_text(material.overlap_points),
        as_text(material.difference_points),
    ])
    allowed_nums = detect_numeric_claims(allowed_numeric_text)
    found_nums = detect_numeric_claims(
        spec.get("effects", "") + " " + spec.get("detailed_description", "")
    )
    illegal_nums = found_nums - allowed_nums
    if illegal_nums:
        r.issues.append(f"state에 없는 정량 수치가 사용되었습니다: {illegal_nums}")

    # 섹션 길이 검증 가이드 (warning 성격)
    if len(split_sentences(tf)) >= 3 or len(tf) > 300:
        r.issues.append("[style_warning] 기술분야가 과도하게 상세합니다. 기술분야는 기술분야 중심의 1~2문장이 적절합니다.")
        
    if len(split_sentences(ba)) >= 5 or len(ba) > 500:
        r.issues.append("[style_warning] 배경기술이 과도하게 상세합니다. 배경기술은 선행기술 또는 종래기술 문제 중심의 한 문단이 적절합니다.")
        
    brief_desc = spec.get("brief_description_of_drawings", "")
    figures_count = len(material.figures)
    if figures_count > 0:
        sentences = split_sentences(brief_desc)
        if len(sentences) > figures_count * 1.5:
            r.issues.append("[style_warning] 도면의 간단한 설명이 도면 수 대비 너무 많은 문장으로 작성되었습니다. 각 도면당 1문장으로 간결하게 작성하세요.")
        elif len(brief_desc) > figures_count * 150:
            r.issues.append("[style_warning] 도면의 간단한 설명 문장이 지나치게 깁니다. 참조부호나 세부 동작을 빼고 도면의 목적/제목 수준으로 줄이세요.")

    detail = spec.get("detailed_description", "")
    use_subheadings = material.drafting_options.get("use_subheadings_in_detailed_description", False)
    if not use_subheadings and re.search(r"\[.+?\]", detail):
        r.issues.append("[style_warning] drafting_options에서 소제목 사용이 금지되었으나 detailed_description에 대괄호 소제목이 포함되어 있습니다.")

    detail_paragraphs = split_paragraphs(detail)
    if len(detail_paragraphs) != len(set(detail_paragraphs)) and len(detail_paragraphs) > 0:
        r.issues.append("[style_warning] detailed_description에 완전히 동일한 문단이 중복 사용되었습니다.")
        
    means = spec.get("means_for_solving", "")
    avoid_ref_in_means = material.drafting_options.get("avoid_reference_numerals_in_means", True)
    if avoid_ref_in_means and re.search(r"\(\d{1,4}[a-zA-Z]?\)", means):
        r.issues.append("[style_warning] 해결수단에 참조부호가 포함되어 있습니다. 참조부호 기반 설명은 상세한 설명으로 이동하는 것이 적절합니다.")

    if re.search(r"\(\d{1,4}[a-zA-Z]?\)", brief_desc):
        r.issues.append("[style_warning] 도면의 간단한 설명에 참조부호가 포함되어 있습니다. 도면 설명은 제목/목적 수준으로 간략히 작성하는 것이 적절합니다.")

    effects_text = spec.get("effects", "")
    if effects_text and re.search(r"(정확성|품질|성능|안정성|효율성)\s*향상", effects_text):
        evidence_text = " ".join([
            as_text(material.effect),
            as_text(material.overlap_points),
            as_text(material.difference_points),
            as_text(material.limitations),
        ])
        if not re.search(r"(정확성|품질|성능|안정성|효율성)", evidence_text):
            r.issues.append("[style_warning] 발명의 효과에 입력 근거가 약한 일반 효과 표현이 포함될 수 있습니다.")

    # 반복 표현 검증 (warning 성격)
    for key in _SPEC_REQUIRED:
        repeated = detect_repeated_phrases(spec.get(key, ""))
        if repeated:
            r.issues.append(f"[style_warning] [{key}] 반복 표현 의심: {', '.join(repeated)}")

    # 청구항 elements 누락 경고
    if material.draft_claims and not any(dc.get("elements") for dc in material.draft_claims):
        r.issues.append("[style_warning] 청구항 elements가 제공되지 않아 support_matrix 품질이 제한됩니다.")

    hard_issues = [i for i in r.issues if not is_style_warning(i)]
    r.passed = len(hard_issues) == 0
    return r


# ---------------------------------------------------------------------------
# 8. 용어 통일 (Pure function)
# ---------------------------------------------------------------------------

def is_safe_alias(alias: str, canonical: str, all_canonicals: list[str]) -> bool:
    alias = (alias or "").strip()
    canonical = (canonical or "").strip()

    if not alias or not canonical:
        return False
    if alias == canonical:
        return False
    if alias in canonical:
        return False
    if sum(1 for term in all_canonicals if alias in term) >= 2:
        return False
    if len(alias) < 2:
        return False
    return True


def safe_replace_term(text: str, alias: str, canonical: str) -> str:
    pattern = re.compile(
        rf"(?<![가-힣A-Za-z0-9_\-]){re.escape(alias)}(?![가-힣A-Za-z0-9_\-])"
    )
    return pattern.sub(canonical, text)

def normalize_terms_across_outputs(
    state: dict,
    spec: dict,
    material: SpecificationMaterial,
) -> tuple[dict, dict]:
    """spec 본문의 alias를 canonical_name으로 치환하고 새로운 dict를 반환한다."""
    new_spec = dict(spec)
    
    alias_map: dict[str, str] = {}
    consultation = state.get("consultation") or {}
    summary = state.get("summary") or {}
    structured = summary.get("structured_invention") or {}
    
    consultation_components = consultation.get("components") or []
    structured_components = structured.get("components") or []
    components = deduplicate_list(consultation_components + structured_components)
    
    for comp in components:
        canonical = comp.get("name", "")
        for alias in comp.get("aliases") or []:
            if alias != canonical:
                alias_map[alias] = canonical

    claims = state.get("claims") or {}
    drawings = state.get("drawings") or {}
    claim_elements_lower = {}
    for dc in claims.get("draft_claims") or []:
        for el in dc.get("elements") or []:
            claim_elements_lower[el.lower()] = el
            
    refs = normalize_reference_numerals(drawings.get("reference_numerals") or {})
    for _k, rn in refs.items():
        t = rn.get("term", "")
        tl = t.lower()
        if tl in claim_elements_lower and claim_elements_lower[tl] != t:
            alias_map[t] = claim_elements_lower[tl]

    term_normalization_record = {"normalized_terms": {}}

    all_canonicals = list(set(alias_map.values()))
    safe_alias_map = {
        a: c for a, c in alias_map.items() 
        if is_safe_alias(a, c, all_canonicals)
    }

    if not safe_alias_map:
        return new_spec, term_normalization_record

    sorted_aliases = sorted(safe_alias_map.keys(), key=len, reverse=True)
    text_keys = [
        "technical_field", "background_art", "problem_to_solve",
        "means_for_solving", "effects", "brief_description_of_drawings",
        "detailed_description",
    ]
    for key in text_keys:
        txt = new_spec.get(key, "")
        for alias in sorted_aliases:
            if alias in txt:
                before_repeated = len(detect_repeated_phrases(txt))
                new_txt = safe_replace_term(txt, alias, safe_alias_map[alias])
                after_repeated = len(detect_repeated_phrases(new_txt))
                
                if after_repeated <= before_repeated and new_txt != txt:
                    txt = new_txt
                    term_normalization_record["normalized_terms"][alias] = safe_alias_map[alias]
        new_spec[key] = txt
        
    return new_spec, term_normalization_record


# ---------------------------------------------------------------------------
# 9. document_links_patch & support_matrix
# ---------------------------------------------------------------------------

def build_document_links_patch_and_support_matrix(
    state: dict,
    spec: dict,
    material: SpecificationMaterial,
) -> tuple[dict, list]:
    
    paragraph_anchors = []
    sections = [
        "technical_field", "background_art", "problem_to_solve",
        "means_for_solving", "effects", "brief_description_of_drawings",
        "detailed_description"
    ]
    
    claims = state.get("claims") or {}
    all_elements = []
    for dc in claims.get("draft_claims") or []:
        all_elements.extend(dc.get("elements") or [])
    all_elements.sort(key=len, reverse=True)
    
    pid_counter = 1
    anchor_by_sec_idx = {}
    
    for sec in sections:
        text = spec.get(sec, "")
        paragraphs = split_paragraphs(text)
        for p_idx, p_text in enumerate(paragraphs):
            pid = f"P{pid_counter:03d}"
            pid_counter += 1
            
            found_entity = sec
            for el in all_elements:
                if el in p_text:
                    found_entity = el
                    break
                    
            anchor_id = f"specification.{sec}.{pid}"
            anchor_info = {
                "anchor_id": anchor_id,
                "section": sec,
                "paragraph_id": pid,
                "entity": found_entity,
                "text": p_text[:100] + "..." if len(p_text) > 100 else p_text
            }
            paragraph_anchors.append(anchor_info)
            anchor_by_sec_idx[(sec, p_idx)] = anchor_id

    spec_support_links = []
    support_matrix = []
    
    for dc in claims.get("draft_claims") or []:
        claim_no = dc.get("claim_no", "?")
        for el in dc.get("elements") or []:
            found = False
            best_sec = ""
            best_p_text = ""
            best_anchor = ""
            
            # 우선순위: detailed_description > means_for_solving
            for sec in ["detailed_description", "means_for_solving"]:
                text = spec.get(sec, "")
                paragraphs = split_paragraphs(text)
                for p_idx, p_text in enumerate(paragraphs):
                    if el.lower() in p_text.lower():
                        found = True
                        best_sec = sec
                        best_p_text = p_text
                        best_anchor = anchor_by_sec_idx.get((sec, p_idx), f"specification.{sec}")
                        break
                if found:
                    break
                    
            if found:
                evidence_text = best_p_text[:200] + "..." if len(best_p_text) > 200 else best_p_text
                support_type = "embodiment" if best_sec == "detailed_description" else "means"
                
                support_matrix.append({
                    "claim_no": claim_no,
                    "element": el,
                    "supported": True,
                    "support_type": support_type,
                    "section": best_sec,
                    "paragraph_id": best_anchor.split(".")[-1],
                    "evidence": evidence_text
                })
                
                for sec in ["means_for_solving", "detailed_description"]:
                    text = spec.get(sec, "")
                    paragraphs = split_paragraphs(text)
                    for p_idx, p_text in enumerate(paragraphs):
                        if el.lower() in p_text.lower():
                            anchor_id = anchor_by_sec_idx.get((sec, p_idx), f"specification.{sec}")
                            ev_text = p_text[:200] + "..." if len(p_text) > 200 else p_text
                            stype = "embodiment" if sec == "detailed_description" else "means"
                            spec_support_links.append({
                                "source": anchor_id,
                                "target": f"claims.claim_no[{claim_no}].elements.{el}",
                                "relation": "supports",
                                "support_type": stype,
                                "evidence": ev_text,
                                "confidence": 0.85,
                                "review_flag": "",
                            })
            else:
                spec_support_links.append({
                    "source": "specification",
                    "target": f"claims.claim_no[{claim_no}].elements.{el}",
                    "relation": "support_missing",
                    "support_type": "missing",
                    "evidence": "",
                    "confidence": 0.2,
                    "review_flag": "명세서에서 해당 청구항 요소를 명확히 찾지 못함",
                })
                
                support_matrix.append({
                    "claim_no": claim_no,
                    "element": el,
                    "supported": False,
                    "support_type": "missing",
                    "section": "",
                    "paragraph_id": "",
                    "evidence": "",
                    "issue": "명세서에서 해당 청구항 요소 설명을 찾지 못함"
                })

    term_registry_updates = {}
    consultation = state.get("consultation") or {}
    summary = state.get("summary") or {}
    structured = summary.get("structured_invention") or {}
    drawings = state.get("drawings") or {}
    refs = normalize_reference_numerals(drawings.get("reference_numerals") or {})
    
    consultation_components = consultation.get("components") or []
    structured_components = structured.get("components") or []
    components = deduplicate_list(consultation_components + structured_components)
    
    for comp in components:
        cid = comp.get("id", comp.get("name", ""))
        canonical = comp.get("name", "")
        
        used_in = []
        for anchor in paragraph_anchors:
            if canonical and canonical in anchor["text"]:
                used_in.append(anchor["anchor_id"])
        
        # TODO: 추후 consultation과 summary components의 출처(source)를 추적하여 first_defined_in에 정확히 반영할 것
        term_registry_updates[cid] = {
            "canonical_name": canonical,
            "type": comp.get("type", "component"),
            "aliases": comp.get("aliases") or [],
            "reference_no": "",
            "first_defined_in": "consultation.components",
            "used_in": used_in,
            "source_component_id": comp.get("id", ""),
        }
        
    for num, rn in refs.items():
        for _cid, entry in term_registry_updates.items():
            if entry.get("canonical_name") == rn.get("term"):
                entry["reference_no"] = num
                break

    document_links_patch = {
        "paragraph_anchors": paragraph_anchors,
        "spec_support_links": deduplicate_list(spec_support_links),
        "term_registry_updates": term_registry_updates,
    }
    
    return document_links_patch, support_matrix


# ---------------------------------------------------------------------------
# 10. Trace 이벤트 빌더
# ---------------------------------------------------------------------------

def build_trace_event(
    action: str,
    summary: str,
    inputs: dict | None = None,
    outputs: dict | None = None,
) -> dict:
    return {
        "agent": "specification",
        "node": "specification_agent",
        "action": action,
        "summary": summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs or {},
        "outputs": outputs or {},
    }
