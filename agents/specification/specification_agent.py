"""발명의 설명 파트 생성 에이전트.

이 모듈은 Composer가 최종 특허 문서에 포함할 발명의 설명 각 섹션을 생성하며, DB 관련 작업이나 state를 직접 변경하는 
부수 효과(side effects)를 가지지 않습니다.
대신 SpecificationAgentOutput 스키마에 맞는 dict를 반환합니다.
최종 패키지 구성(final_package)과 DB 저장(save_specification_to_db)은 
외부 Graph나 Master에서 처리합니다.

사용법:
    from agents.specification.specification_agent import run_specification_agent
    from agents.schemas.specification import SpecificationAgentOutput

    raw_output = run_specification_agent(state)
    validated = SpecificationAgentOutput.model_validate(raw_output)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from openai import OpenAI

# 내부 헬퍼
from agents.specification.spec_helpers import (
    SpecificationAgentConfig,
    SpecificationMaterial,
    ValidationResult,
    safe_parse_json,
    build_specification_material,
    validate_specification,
    normalize_terms_across_outputs,
    build_document_links_patch_and_support_matrix,
    build_trace_event,
    normalize_reference_numerals,
    is_style_warning,
    as_text,
    get_labeled_method_independent_claims,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OpenAI 클라이언트
# ---------------------------------------------------------------------------
_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")
        _client = OpenAI(api_key=api_key)
    return _client


# =====================================================================
# LLM 프롬프트 빌더 & 호출
# =====================================================================

def build_system_prompt(material: SpecificationMaterial) -> str:
    allowed_refs = sorted(material.allowed_ref_numerals) if material.allowed_ref_numerals else []
    allowed_pubs = sorted(material.allowed_pub_numbers) if material.allowed_pub_numbers else []

    ref_section = (
        f"허용된 참조부호: {', '.join(allowed_refs)}\n" if allowed_refs
        else "허용된 참조부호: 없음 (참조부호를 사용하지 마라)\n"
    )
    pub_section = (
        f"허용된 선행문헌번호: {', '.join(allowed_pubs)}\n" if allowed_pubs
        else "허용된 선행문헌번호: 없음 (선행문헌번호를 만들지 마라)\n"
    )

    # allowed_terms에 등록된 모든 용어를 사용하도록 기준 변경
    allowed_component_names = []
    
    for c in material.components:
        if c.get("name"):
            allowed_component_names.append(c.get("name"))
            
    for key, value in material.allowed_terms.items():
        if isinstance(value, dict):
            name = value.get("canonical_name") or value.get("name") or key
        else:
            name = str(key)
        if name:
            allowed_component_names.append(name)
            
    components_str = ", ".join(sorted(set(allowed_component_names))) or "없음"

    use_subheadings = material.drafting_options.get("use_subheadings_in_detailed_description", False)
    brief_drawing_description = material.drafting_options.get("brief_drawing_description", True)
    strict_grounding = material.drafting_options.get("strict_grounding", True)
    avoid_ref_in_means = material.drafting_options.get("avoid_reference_numerals_in_means", True)
    
    subheadings_rule = (
        "- 대괄호 [ ] 형태의 소제목을 사용하여 문단을 구분한다." if use_subheadings
        else "- 대괄호 [ ] 형태의 소제목을 사용하지 않는다. 소제목 없이도 흐름이 자연스럽게 전체 시스템 개요 → 구성요소 설명 → 핵심 동작 → 실시예 순서로 이어지게 작성한다."
    )
    
    grounding_rule = (
        "- 적용 분야, 사용 예, 입력 데이터 유형, 출력 데이터 유형, 구체 예시는 state에 제공된 경우에만 작성한다. state에 없는 구체 도메인('토큰', '이미지', '의료', '음성' 등) 예시를 임의로 만들지 않는다." if strict_grounding
        else "- 발명의 이해를 돕기 위해 필요한 경우 자연스러운 범위 내에서 일반적인 적용 분야나 예시를 추가할 수 있다."
    )

    brief_drawings_rule = (
        "- brief_description_of_drawings: source_brief_description_of_drawings가 제공된 경우, brief_description_of_drawings는 새로 생성하지 말고 원문 표현을 가능한 한 그대로 사용한다. 오탈자나 불필요한 공백 정도만 정리하고, 도면 제목/목적을 임의로 바꾸지 않는다. source_brief_description_of_drawings가 없을 때만 figures[].brief_description_text 또는 brief_title을 이용해 생성한다. 참조부호, 서브구성, 처리 단계, 알고리즘 설명은 절대 넣지 않는다." if brief_drawing_description
        else "- brief_description_of_drawings: 각 도면을 설명한다."
    )
    
    means_ref_rule = (
        "참조부호를 사용하지 않는다." if avoid_ref_in_means
        else "필요시 참조부호를 사용할 수 있다."
    )

    labeled_methods = get_labeled_method_independent_claims(material)
    method_step_enabled = material.drafting_options.get("method_step_format", {}).get("enabled", False)
    
    means_method_rule = ""
    if method_step_enabled and labeled_methods:
        means_method_rule = "방법 독립항 text에 단계 라벨이 이미 포함되어 있으면, means_for_solving에서 해당 단계 라벨을 유지하여 청구항식 문장으로 작성한다. 이 경우 일반 서술문으로 풀어 없애지 말고, 원 청구항의 단계 순서와 라벨을 보존한다. "

    return f"""당신은 한국 특허 명세서 작성 전문 변리사입니다.

【절대 규칙 — 위반 시 전체 출력이 무효화됩니다】
1. state에 없는 구성요소를 새로 만들지 마라. 허용된 구성요소: {components_str}
2. {ref_section}위 목록에 없는 참조부호를 만들지 마라.
3. {pub_section}위 목록에 없는 공개번호/등록번호를 만들지 마라.
4. 수치 효과가 제공되지 않았으면 임의 정량 수치를 만들지 마라.
5. 출력은 반드시 JSON 객체로만 반환하라. JSON 외 텍스트 금지.

【발명의 설명 작성 원칙】
발명의 설명은 크게 다음 3축으로 작성하되, 섹션별 성격에 맞게 분량과 내용을 조절한다.

1. 기술분야 / 배경기술
- technical_field: invention_title과 technical_field_natural을 함께 사용하여, 발명의 명칭과 핵심 기술수단 중심으로 1문단(1~2문장)만 작성한다. 기술분야는 대표 발명 카테고리 중심으로 작성한다. recording medium, program, computer-readable medium, 기록매체, 프로그램 청구항은 독립항 또는 말미 청구항으로 존재하더라도, invention_title이나 원문 technical_field에 명시되어 있지 않으면 technical_field에 과도하게 포함하지 않는다. 기술분야에는 "장치 및 방법" 또는 발명 명칭 중심으로 쓰고, 프로그램/기록매체는 detailed_description 말미나 means_for_solving에서 필요한 경우 간략히 언급한다. 제공된 IPC 코드는 의미만 참고하고, IPC 분류코드 문자열 자체(예: G06F 1/16 등)는 본문에 직접 노출하지 않는다. 대신 "디스플레이 장치의 지지 또는 방향 조절 구조", "인공지능 기반 데이터 처리"와 같이 해당 기술분야를 자연어로 서술한다. 청구항 구성요소나 세부 동작을 넣지 않는다.
- background_art: 관련 선행문헌 또는 종래기술에서 확인되는 사용 환경, 일반 구조, 기술적 한계 또는 문제점을 자연스럽게 작성한다. 원칙적으로 1~2문단으로 작성하되, 종래기술의 한계나 문제점이 명확히 나뉘는 경우 (1), (2)와 같은 구조로 작성하는 것도 허용된다. publication_no, 공개번호, 등록번호를 background_art 본문에 기계적으로 나열하지 않는다. 선행문헌의 summary, overlap_points, limitations, analysis_summary가 제공된 경우에는 해당 내용을 자연어로 풀어 종래기술 설명에 반영한다. publication_no만 제공되고 구체 정보가 부족한 경우에는 해당 문헌번호를 background_art에 언급하지 않는다. "관련 기술로는 ... 조사되었다", "관련 선행문헌으로 ... 조사되었다", "... 등이 검색되었다", "... 등이 조사되었다" 같은 표현은 사용하지 않는다. 선행문헌번호 목록은 Specification Agent가 아니라 Composer의 선행기술문헌 항목에서 처리한다.

2. 해결하고자 하는 과제 / 해결수단 / 효과
- problem_to_solve: 종래기술의 문제점과 발명의 목적만 작성한다. 구성요소, 테이블 구조, 조회/갱신/삭제 절차 등 해결수단에 해당하는 내용은 절대 쓰지 않는다. 실시예 설명과 중복되지 않게 한다.
- means_for_solving: 청구항의 독립항을 최우선 근거로 사용하여 작성한다. 장치/시스템 독립항은 핵심 구성요소를 "~를 포함한다" 문체로 작성하고, 방법 독립항은 method_step_format.enabled가 true일 때 다음과 같이 단계 라벨을 사용한다: 1) 청구항의 method 독립항 텍스트를 최우선으로 사용한다. 2) 부족한 경우 process_steps.description을 사용한다. 3) process_steps.name은 마지막 fallback으로만 사용한다. 4) process_steps.label 또는 method 청구항에 (a), (b) 등의 라벨이 있을 때만 단계 라벨을 사용한다. 5) 장치/시스템 중심 발명이거나 method 청구항/ordered process_steps가 없으면 단계 라벨을 사용하지 않는다. {means_method_rule}method_step_format.enabled가 false일 때는 어떠한 경우에도 (a), (b), (c) 표현을 사용하지 않는다. 도면번호, 참조부호, 세부 처리 단계, 서브구성의 순차적 동작 설명은 detailed_description에서 작성하며, 여기서는 {means_ref_rule} 단, 청구항 문언 자체에 필수적으로 포함된 구성요소명은 유지한다.
- effects: cause-effect 관계는 내부 근거로만 사용하고, 최종 본문은 원칙적으로 2문단으로 압축한다. 단, effect state가 매우 풍부하고 서로 독립적인 효과가 3개 이상 명확한 경우에만 3문단까지 허용한다. effects에는 캐쉬 히트/캐쉬 미스 판단, 서버 또는 인접단말 데이터 수신, 캐쉬 저장 및 전송 같은 구체적 처리 절차를 쓰지 않는다. 그런 절차는 detailed_description으로 보낸다. effects는 "정보전달속도 향상", "트래픽 분산", "통신망 효율 향상", "서버/통신경로 부하 감소"처럼 최종 기술적 효과 중심으로 압축한다. 원문 효과가 source specification에 제공되어 있으면, 그 효과 문체와 길이를 우선 참고한다.

3. 도면의 간단한 설명 / 실시예
{brief_drawings_rule}
- detailed_description: 도면 순서대로 설명한다. 실시예에 해당하므로 가장 구체적이고 풍부하게 작성하되, flowchart 도면에 표시된 분기 결과(예: 판단 결과에 따른 분기)를 그대로 보존한다. 도면이나 state에 없는 "새 테이블 생성", "확장 처리" 등의 내용을 임의로 추가하지 않는다. detailed_description에서는 state.figures.description, drawings.reference_numerals.description, claims text, consultation.components/process_steps에 명시된 정보만 사용한다. 일반적인 구현 추론으로 새로운 입력 데이터, 선택 기준, 상태 정보, 식별 정보를 추가하지 않는다. 예를 들어 "요청 단말의 식별 정보", "접속 상태", "위치 정보", "적합한 단말 선택" 등은 state에 명시되어 있을 때만 작성한다. "~등"을 이용해 state에 없는 데이터 항목을 확장하지 않는다. 도면이 있으면 도면을 참조하며, 참조부호가 있으면 처음 도입 시 "구성요소명(참조부호)" 형식으로 표시한다. 종속항의 세부 구성과 구체적 동작은 여기서 도면부호와 함께 설명한다. 청구항을 그대로 반복하지 않고 실제 구현/동작/처리 흐름을 설명하는 문체로 작성한다.

【detailed_description 작성 순서 (일반 구조)】
{subheadings_rule}
가능한 경우 다음 순서로 흐름을 구성한다:
1) 적용 예 또는 사용 환경 (application_domain, use_cases 등 정보가 있을 때만)
2) 전체 시스템 또는 전체 방법의 개요 (대표 도면 참조하여 구조/흐름 설명)
3) 주요 구성요소별 설명 (도면부호 및 청구항 요소 기준. 처음 도입 후에는 자연스럽게 지칭)
4) 핵심 동작 또는 알고리즘 설명 (입력-처리-출력 관계, 단계별 설명)
5) 기타 독립항(저장매체, 방법 등) 실시예 간략 설명

【용어 및 문체 규칙】
- detailed_description은 알고리즘 교과서 설명이 아니라 실시예 설명 문체로 작성한다. 수학적 원리나 일반 기술 상식 설명을 장황하게 반복하지 않는다.
- state 내부 용어 식별자(예: "속성 변경 정보 존재 판단", "속성 변경 정보 조회", "속성 변경 정보 기반 최종 카드 속성 정보 생성 단계" 등)가 본문에 그대로 노출되지 않도록, 반드시 "속성 변경 정보가 존재하는지 판단하고", "속성 변경 정보를 조회하는"과 같이 자연어 문장으로 풀어쓴다.
- 청구항 구성요소가 도면에서 어떻게 연결되고 동작하는지 중심으로 설명하며, 동일한 어텐션 계산, 동일한 입력-처리-출력 구조 등 동일한 설명을 여러 문단에서 반복하지 않는다.
- 청구항 구성요소명은 가능한 한 유지하되, 동일 명사구를 기계적으로 반복하지 않는다.
- 이미 설명한 구성은 "상기 구성", "상기 계층", "상기 모듈", "상기 메커니즘" 등 자연스러운 특허 문체로 지칭한다. 단, 새로운 구성요소나 제공된 적 없는 동의어를 만들지는 않는다.
- "A A", "A B A B"처럼 동일 단어나 구가 연속 반복되는 표현을 만들지 않는다.
- 같은 문단에서 동일한 전체 명사구를 과도하게 반복하지 않는다.
- "~할 수 있다", "~하도록 구성될 수 있다" 등 특허 문체를 사용하고 과장 표현은 금지한다.
- 선행기술 관련 내용은 리스크/가능성으로 표현하고 법적 단정은 피한다.
{grounding_rule}

【출력 JSON 키】
- "technical_field", "background_art", "problem_to_solve", "means_for_solving", "effects", "brief_description_of_drawings", "detailed_description"
- "embodiment_notes": 정보가 부족한 사항을 기록하는 문자열 배열"""


def build_user_prompt(material: SpecificationMaterial) -> str:
    comp_lines = []
    for c in material.components:
        name = c.get("name", "")
        role = c.get("role", "")
        comp_lines.append(f"  - {name}: {role}")
    comp_str = "\n".join(comp_lines) if comp_lines else "  (없음)"

    # 처리 단계: LLM이 name을 그대로 반복하지 않도록 description과 함께 제공
    step_lines = []
    for s in material.process_steps:
        name = s.get('name', '')
        desc = s.get('description', '')
        # name만 있고 description이 없는 경우 LLM이 name을 그대로 쓰지 않도록 주의 표시
        if desc:
            step_lines.append(f"  {s.get('order', '?')}단계: {desc}  [내부식별자(본문직접사용금지): {name}]")
        else:
            step_lines.append(f"  {s.get('order', '?')}단계: [내부식별자(본문직접사용금지): {name}] — 자연어 문장으로 풀어 쓸 것")
    step_str = "\n".join(step_lines) if step_lines else "  (없음)"

    # 청구항: 독립항/종속항 분류, 방법항 표시
    claim_lines = []
    independent_claim_numbers = {str(n) for n in material.independent_claim_numbers or []}
    for dc in material.draft_claims:
        no = str(dc.get("claim_no", "?"))
        tp = dc.get("type", "")
        category_type = (
            dc.get("claim_type")
            or dc.get("claim_category")
            or dc.get("category")
            or ""
        )
        is_independent = (
            tp == "independent"
            or no in independent_claim_numbers
            or (not independent_claim_numbers and no == "1")
        )
        category = "독립항" if is_independent else "종속항"
        type_label = f"/{category_type}" if category_type else ""
        claim_lines.append(f"  【제{no}항】({category}{type_label}) {dc.get('text', '')}")
        
    labeled_methods = get_labeled_method_independent_claims(material)
    if labeled_methods:
        claim_lines.append("\n  【방법 독립항 단계 라벨 원문 — means_for_solving에서 가능한 한 유지】")
        for m in labeled_methods:
            claim_lines.append(f"  제{m.get('claim_no', '?')}항: {m.get('text', '')}")
            
    claim_str = "\n".join(claim_lines) if claim_lines else "  (없음)"

    # 도면: brief_description_text(원문 추출값) 우선 표시
    fig_lines = []
    if material.source_brief_description_of_drawings:
        fig_lines.append(f"  【원문 도면의 간단한 설명 — 가능한 한 그대로 사용할 것】\n  {material.source_brief_description_of_drawings}\n")
    for f in material.figures:
        b_title = f.get('brief_title') or f.get('title', '')
        brief_text = f.get('brief_description_text') or f.get('brief_description') or ''  # 원문 추출 간단 설명
        lines = [f"  도 {f.get('fig_no', '?')}:"]
        if brief_text:
            lines.append(f"    - 원문 간단 설명(최우선 사용): {brief_text}")
        else:
            lines.append(f"    - 간단 설명용(brief_title): {b_title}")
        lines.append(f"    - 상세 설명용 (detailed_description 활용):")
        if f.get("purpose"): lines.append(f"      * 목적: {f.get('purpose')}")
        if f.get("description"): lines.append(f"      * 설명: {f.get('description')}")
        if f.get("components"): lines.append(f"      * 구성요소: {as_text(f.get('components'))}")
        if f.get("steps"): lines.append(f"      * 단계: {as_text(f.get('steps'))}")
        fig_lines.append("\n".join(lines))
    fig_str = "\n".join(fig_lines) if fig_lines else "  (없음)"

    ref_lines = []
    refs = normalize_reference_numerals(material.reference_numerals)
    for num, rn in refs.items():
        ref_lines.append(f"  ({num}) {rn.get('term', '')}")
    ref_str = "\n".join(ref_lines) if ref_lines else "  (없음)"

    # technical_field_natural 추출 (state에서 직접 접근 불가하므로 material.drafting_options 등 활용)
    technical_field_natural = (
        getattr(material, "technical_field_natural", "")
        or material.drafting_options.get("technical_field_natural", "")
    )

    ipc_str = ", ".join(material.ipc_focus) if material.ipc_focus else "없음"
    pa_lines = []
    for c in material.prior_art_candidates[:5]:
        pub = c.get("publication_no")
        patent_id = c.get("patent_id", "")
        if pub:
            label = pub
        elif patent_id:
            label = f"문헌 후보 {patent_id}"
        else:
            label = "번호 없는 선행문헌 후보"
        title = c.get("title") or ""
        summary = c.get("summary") or c.get("analysis_summary") or ""
        overlaps = c.get("overlap_points") or c.get("matched_points") or []

        if not title and not summary and not overlaps:
            pa_lines.append(
                f"  - {label}: 구체 요약 정보 없음. publication_no만 제공됨. 문헌 내용을 추정하지 말고, background_art에 문헌번호를 나열하지 말 것."
            )
        else:
            pa_lines.append(
                f"  - {label}: {title} (요약: {summary[:120]}, 겹침: {', '.join(overlaps[:2])})"
            )
    pa_str = "\n".join(pa_lines) if pa_lines else "  (없음)"

    limitations_str = as_text(material.limitations) if material.limitations else "없음"
    missing_slots_str = as_text(material.missing_slots) if material.missing_slots else "없음"
    overlap_points_str = as_text(material.overlap_points) if material.overlap_points else "없음"
    difference_points_str = as_text(material.difference_points) if material.difference_points else "없음"

    method_step_enabled = material.drafting_options.get("method_step_format", {}).get("enabled", False)
    if method_step_enabled:
        method_step_note = (
            "\n※ method_step_format.enabled=true:\n"
            "- method 독립항 text에 (a), (b), (c) 라벨이 있으면 means_for_solving에서 라벨을 유지한다.\n"
            "- method 독립항 text가 있으면 process_steps.description보다 method 독립항 text를 우선한다.\n"
            "- process_steps.name은 마지막 fallback으로만 사용한다.\n"
            "- method 독립항에 라벨이 없고 process_steps.label도 없으면 억지로 (a), (b), (c)를 만들지 않는다.\n"
            "- 장치/시스템 중심 발명이고 method 독립항이 없으면 단계 라벨을 사용하지 않는다."
        )
    else:
        method_step_note = "\n※ method_step_format.enabled=false: 어떤 경우에도 (a), (b), (c) 표현을 사용하지 않는다."

    return f"""다음 정보를 바탕으로 특허 명세서의 각 섹션을 작성하세요.

【발명 명칭】 {material.invention_title or '(미정)'}
【기술수단 자연어 설명】 {technical_field_natural or '(없음 — invention_title 기반으로 기술분야 기술)'}
※ technical_field는 위 발명 명칭과 기술수단 자연어 설명을 함께 활용하여 발명의 명칭과 핵심 기술수단 중심으로 1~2문장만 작성하세요.

【상담 결과】
- 문제(종래기술 문제점/발명 목적만 사용 → problem_to_solve): {material.problem}
- 미충족 수요 / 해결수단(→ means_for_solving): {material.solution}
- 누락된 슬롯: {missing_slots_str}
- 차별성: {material.differentiation}
- 효과(cause-effect 기반 → effects 원칙적으로 2문단 압축): {material.effect}
- 구성요소:
{comp_str}
- 처리 단계(내부 식별자는 본문에 직접 노출 금지 — 자연어로 풀어 쓸 것):
{step_str}{method_step_note}

【기술분야 참고자료】
- IPC 코드: {ipc_str}
※ IPC 코드는 technical_field 작성 시 의미만 참고하고, 코드 문자열 자체는 본문에 직접 쓰지 마세요.

【선행기술 후보】
{pa_str}
※ publication_no는 선행기술문헌 항목 작성을 위한 참고자료이며, background_art 본문에 그대로 나열하지 마세요.
※ background_art에서는 선행문헌번호가 아니라, summary / overlap_points / limitations / analysis_summary에서 확인되는 종래기술의 내용과 문제점을 자연어로 풀어 쓰세요.
※ 구체 요약 정보가 부족한 문헌은 번호를 언급하지 말고, 제공된 문제점과 한계만 일반적인 종래기술 설명에 반영하세요.
- 겹치는 점: {overlap_points_str}
- 차이점: {difference_points_str}

【선행기술 분석】
- 분석 요약: {material.analysis_summary or '없음'}
- 한계점: {limitations_str}
- 신규성 리스크: {material.novelty_risk}
- 진보성 리스크: {material.inventive_step_risk}
※ 위 리스크 정보는 작성 참고자료이며, 법적 판단처럼 단정하지 말고 배경기술/과제 작성 시 참고하라.

【청구항 — means_for_solving 작성 시 독립항 text를 우선 근거로 사용하세요】
{claim_str}

【도면 — 원문 간단 설명이 있으면 brief_description_of_drawings에 최우선 사용】
{fig_str}

【참조부호】
{ref_str}

【작성상 중요 지시】
- problem_to_solve: 종래기술 문제점과 발명 목적만 기술. 구성요소, 테이블 구조, 조회/갱신/삭제 절차 등 해결수단은 일절 포함하지 마세요.
- means_for_solving: 위 청구항의 독립항 text를 우선 근거로 사용하세요. 장치·시스템 독립항은 핵심 구성요소를 "~를 포함한다" 문체로 쓰고, 방법 독립항은 method_step_format 설정에 따라 작성하세요.
- effects: cause-effect 관계는 내부 근거로만 참고하고, 최종 본문은 원칙적으로 2문단으로 압축하세요. 단, 서로 독립적인 효과가 3개 이상 명확한 경우에만 3문단까지 허용합니다. 세부 조회/판단/수신/저장/전송 절차는 effects가 아니라 detailed_description에만 기술하세요.
- brief_description_of_drawings: 제공된 기존 명세서 원문 도면 간단 설명(source_brief_description_of_drawings)을 최우선으로 참고하고, 없을 경우 도면별 원문 간단 설명을 참고하며 최후수단으로 brief_title을 사용하세요.
- detailed_description: 도면 번호 순서대로 기술. flowchart 분기 결과를 그대로 보존하고, 도면 또는 state에 없는 "새 테이블 생성", "확장 처리" 같은 내용을 임의로 추가하지 마세요.
- process_steps.name 등 state 내부 식별자를 본문에 그대로 노출하지 마세요. 반드시 자연어 문장으로 풀어 쓰세요(예: "속성 변경 정보 존재 판단" -> "속성 변경 정보가 존재하는지 판단하고").
- 제공된 state에 없는 내용을 임의로 만들지 마세요. 정보가 부족한 부분은 embodiment_notes에 기록하세요.

위 정보만을 사용하여 JSON 형식으로 명세서를 작성하세요."""


def call_openai_json(
    system_prompt: str,
    user_prompt: str,
    config: SpecificationAgentConfig,
) -> dict:
    client = _get_client()
    response = client.chat.completions.create(
        model=config.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=config.temperature,
    )
    raw = response.choices[0].message.content or "{}"
    parsed = safe_parse_json(raw)
    if parsed is None:
        raise ValueError(f"LLM 응답을 JSON으로 파싱할 수 없습니다: {raw[:200]}")
    return parsed


def extract_specification_state(llm_output: dict) -> dict:
    notes = llm_output.get("embodiment_notes", [])
    if isinstance(notes, str):
        notes = [notes]

    return {
        "technical_field": llm_output.get("technical_field", ""),
        "background_art": llm_output.get("background_art", ""),
        "problem_to_solve": llm_output.get("problem_to_solve", ""),
        "means_for_solving": llm_output.get("means_for_solving", ""),
        "effects": llm_output.get("effects", ""),
        "brief_description_of_drawings": llm_output.get("brief_description_of_drawings", ""),
        "detailed_description": llm_output.get("detailed_description", ""),
        "embodiment_notes": notes,
    }


def repair_specification_with_llm(
    spec: dict,
    validation: ValidationResult,
    material: SpecificationMaterial,
    config: SpecificationAgentConfig,
) -> dict:
    issues_text = "\n".join(f"- {i}" for i in validation.issues)
    repair_prompt = f"""이전에 생성한 명세서에 다음 문제가 있습니다:

{issues_text}

이전 출력:
{json.dumps(spec, ensure_ascii=False, indent=2)}

위 문제를 수정하여 동일한 JSON 키 구조로 다시 작성하세요.
【수정 지시사항】
- 반복된 명사구와 중복 치환으로 보이는 표현을 자연스럽게 정리하라.
- "A A", "A B A B"와 같은 반복 표현을 제거하라.
- 청구항 구성요소 자체를 삭제하지 말고 자연스러운 특허 문체로 정리하라.
- technical_field와 background_art가 과도하게 길면 짧게 줄여라.
- technical_field에 IPC 코드 문자열이 직접 포함되어 있다면 이를 자연어 기술분야 표현으로 바꾸어라 (예: "G06F 1/16에 관한 것으로" -> "디스플레이 장치의 방향 조절 구조에 관한 것으로"). 단 예시는 참고용이며 분야에 맞게 유연하게 작성하라.
- background_art에 publication_no가 단순 나열되어 있으면 삭제하고, 선행기술의 내용 또는 종래기술의 문제점 중심으로 다시 작성하라. "관련 기술로는 ... 조사되었다", "... 등이 검색되었다" 같은 선행기술조사 보고서식 표현은 삭제하라. 선행문헌번호 자체는 Composer의 선행기술문헌 항목에서 처리된다고 가정하라. 선행문헌의 구체 내용이 충분히 제공된 경우에만 그 내용을 자연어로 풀어 background_art에 반영하고, publication_no만 제공된 문헌은 background_art에서 언급하지 말라.
- problem_to_solve에 구성요소, 테이블 구조, 조회/갱신/삭제 절차 등 해결수단이 포함되어 있으면 제거하고, 종래기술 문제와 발명의 목적만 남겨라.
- process_steps.name 또는 내부 단계명이 본문에 그대로 노출되어 있으면 자연어 문장으로 풀어써라.
- method 독립항 text에 (a), (b), (c) 단계 라벨이 있는 경우 means_for_solving에서 해당 라벨과 단계 순서를 유지하라.
- flowchart 도면의 분기 결과를 임의로 바꾸지 마라. state 또는 도면에 없는 "새 테이블 생성", "확장 처리", "최초 레코드 등록" 등의 내용을 삭제하라.
- means_for_solving이 종속항 세부사항을 과도하게 반복하면 독립항 중심으로 2~3문단으로 정리하고, 도면부호가 포함되어 있다면(옵션 활성화 시) 모두 제거하라.
- brief_description_of_drawings에 참조부호, 서브구성, 상세 동작이 포함되어 있다면 모두 제거하고, "도 N은 ...을 나타내는 도면이다." 수준으로 아주 짧게 수정하라.
- source_brief_description_of_drawings가 제공된 경우 brief_description_of_drawings는 가능한 한 원문 표현을 유지하라.
- detailed_description이 교과서적 원리를 장황하게 설명하고 있다면 실제 도면과 실시예 중심의 문체로 간결히 정리하라.
- detailed_description에 state나 도면에 없는 구현 세부사항이 있으면 삭제하라. 특히 요청 단말 식별 정보, 접속 상태, 위치 정보, 적합한 인접단말 선택 등은 state에 명시된 경우에만 사용하라.
- detailed_description에 대괄호 소제목이 포함되어 있고 옵션에서 소제목 사용이 금지되었다면 대괄호 소제목을 삭제하라.
- effects에 구체적인 근거 없는 일반적 효과("정확성 향상" 등)가 포함되었다면 근거 기반으로 수정하거나 삭제하라.
- effects에 캐쉬 히트/캐쉬 미스 판단, 데이터 수신, 캐쉬 저장, 단말 전송 같은 절차 설명이 과도하게 들어가 있으면 삭제하고 최종 기술적 효과 중심으로 2문단 내외로 압축하라.
- state에 제공되지 않은 구체 예시(적용 도메인 등)를 임의로 지어냈다면 일반적인 표현으로 수정하거나 삭제하라.
- 선행문헌의 구체 내용이 제공되지 않았으면 추정 표현을 삭제하라.
- technical_field에 프로그램/기록매체가 과도하게 포함되어 있으면 발명 명칭과 핵심 장치/방법 중심으로 줄여라.
- 절대 규칙을 위반하지 마라 (허용되지 않은 참조부호/선행문헌번호/구성요소/임의수치 생성 금지)."""

    system_prompt = build_system_prompt(material)
    return call_openai_json(system_prompt, repair_prompt, config)


# =====================================================================
# 메인 실행 함수
# =====================================================================

def run_specification_agent(
    state: dict[str, Any],
    config: Optional[SpecificationAgentConfig] = None,
) -> dict[str, Any]:
    """발명의 설명 각 섹션 파트를 생성하고, 검증한 뒤 SpecificationAgentOutput 형식의 dict를 반환한다.
    주의: 이 함수는 입력 state를 변경하지 않으며, DB에 직접 저장하지도 않습니다.
    """
    if config is None:
        config = SpecificationAgentConfig()

    warnings = []
    notes = []
    trace_events = []

    trace_events.append(build_trace_event("start", "명세서 에이전트 실행 시작"))

    try:
        material = build_specification_material(state)
        trace_events.append(build_trace_event("build_material", "명세서 재료 수집 완료"))
        
        if material.drafting_options.get("method_step_format", {}).get("enabled"):
            notes.append("method_step_format enabled: 방법항 단계 라벨 사용 가능")
        if not material.reference_numerals:
            notes.append("참조부호 정보 없음: detailed_description에서 참조부호 사용 제한")
        
        has_brief_text = any(f.get('brief_description_text') or f.get('brief_description') for f in material.figures)
        if getattr(material, "source_brief_description_of_drawings", ""):
            notes.append("기존 명세서 원문 도면 간단 설명 있음: brief_description_of_drawings에 최우선 사용됨")
        elif has_brief_text:
            notes.append("도면 리스트 간단 설명 있음: brief_description_of_drawings에 우선 사용됨")
            
        if not getattr(material, "technical_field_natural", ""):
            notes.append("technical_field_natural 없음: invention_title 기반 기술분야 작성")
        
        llm_output = generate_specification_with_llm(material, config)
        trace_events.append(build_trace_event("llm_generate", "LLM 발명의 설명 파트 생성 완료"))
        
        specification = extract_specification_state(llm_output)
        
        if getattr(material, "source_brief_description_of_drawings", ""):
            specification["brief_description_of_drawings"] = material.source_brief_description_of_drawings
            
        validation = validate_specification(state, specification, llm_output, material)
        trace_events.append(build_trace_event("validate", f"검증 {'통과' if validation.passed else '실패'}"))

        if not validation.passed:
            for attempt in range(config.max_repair_attempts):
                logger.info(f"명세서 수정 시도 {attempt + 1}/{config.max_repair_attempts}")
                repaired_output = repair_specification_with_llm(
                    specification, validation, material, config,
                )
                specification = extract_specification_state(repaired_output)
                
                if getattr(material, "source_brief_description_of_drawings", ""):
                    specification["brief_description_of_drawings"] = material.source_brief_description_of_drawings
                    
                validation = validate_specification(state, specification, repaired_output, material)
                trace_events.append(build_trace_event("repair", f"수정 시도 {attempt + 1} ({'성공' if validation.passed else '실패'})"))
                if validation.passed:
                    break

            if not validation.passed:
                # MVP 정책: 검증 실패 시 파이프라인 진행을 보장하기 위해 status="ok"로 반환하되, 
                # warnings와 details["validation"]에 이슈를 담아 다음 단계(composer/review)에서 참고하게 한다.
                logger.warning(f"명세서 검증 미통과 (남은 이슈 {len(validation.issues)}건).")
                warnings.append(f"명세서 검증 미통과: {'; '.join(validation.issues[:3])}")

        pre_issues = set(validation.issues)
        specification, term_norm_record = normalize_terms_across_outputs(state, specification, material)
        
        if getattr(material, "source_brief_description_of_drawings", ""):
            specification["brief_description_of_drawings"] = material.source_brief_description_of_drawings
        
        post_validation = validate_specification(state, specification, specification, material)
        new_post_issues = [i for i in post_validation.issues if i not in pre_issues]
        
        if new_post_issues:
            for issue in new_post_issues:
                if is_style_warning(issue):
                    tagged = issue.replace("[style_warning]", "[style_warning][post_normalization]", 1)
                else:
                    tagged = f"[post_normalization] {issue}"
                validation.issues.append(tagged)
                
            hard_new_issues = [i for i in new_post_issues if not is_style_warning(i)]
            if hard_new_issues:
                validation.passed = False
                warnings.append(f"용어 정규화 후 신규 검증 이슈: {'; '.join(hard_new_issues[:3])}")

        doc_links_patch, support_matrix = build_document_links_patch_and_support_matrix(state, specification, material)
        
        for issue in support_matrix:
            if not issue.get("supported"):
                warnings.append(f"청구항 요소 미지원: {issue.get('element')}")

        trace_events.append(build_trace_event("complete", "명세서 에이전트 실행 성공"))

        all_issues = validation.issues
        style_warnings = [i for i in all_issues if is_style_warning(i)]
        hard_issues = [i for i in all_issues if not is_style_warning(i)]

        return {
            "status": "ok",
            "summary": "발명의 설명 파트 생성 완료",
            "technical_field": specification.get("technical_field", ""),
            "background_art": specification.get("background_art", ""),
            "problem_to_solve": specification.get("problem_to_solve", ""),
            "means_for_solving": specification.get("means_for_solving", ""),
            "effects": specification.get("effects", ""),
            "brief_description_of_drawings": specification.get("brief_description_of_drawings", ""),
            "detailed_description": specification.get("detailed_description", ""),
            "warnings": warnings,
            "notes": notes,
            "details": {
                "embodiment_notes": specification.get("embodiment_notes", []),
                "validation": {
                    "passed": validation.passed,
                    "issues": validation.issues,
                    "hard_issues": hard_issues,
                    "style_warnings": style_warnings,
                },
                "support_matrix": support_matrix,
                "document_links_patch": doc_links_patch,
                "term_normalization": term_norm_record,
                "trace_events": trace_events,
            }
        }

    except Exception as e:
        logger.exception("명세서 에이전트 실행 중 오류 발생")
        trace_events.append(build_trace_event("error", f"오류 발생: {str(e)}"))
        
        return {
            "status": "failed",
            "summary": "발명의 설명 파트 생성 중 오류 발생",
            "technical_field": "",
            "background_art": "",
            "problem_to_solve": "",
            "means_for_solving": "",
            "effects": "",
            "brief_description_of_drawings": "",
            "detailed_description": "",
            "warnings": [str(e)],
            "notes": [],
            "details": {
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                },
                "validation": {
                    "passed": False,
                    "issues": [str(e)],
                    "hard_issues": [str(e)],
                    "style_warnings": []
                },
                "embodiment_notes": [],
                "document_links_patch": {},
                "support_matrix": [],
                "term_normalization": {},
                "trace_events": trace_events,
            }
        }

def generate_specification_with_llm(
    material: SpecificationMaterial,
    config: SpecificationAgentConfig,
) -> dict:
    system_prompt = build_system_prompt(material)
    user_prompt = build_user_prompt(material)
    return call_openai_json(system_prompt, user_prompt, config)
