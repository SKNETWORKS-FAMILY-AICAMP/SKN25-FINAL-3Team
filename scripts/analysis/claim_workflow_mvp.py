#!/usr/bin/env python3
"""End-to-end MVP claim drafting workflow for one patent.

Workflow C:
1. Use deterministic extraction output as raw material.
2. Remove reference claims from generation input to avoid leakage.
3. GPT creates a high-quality invention brief + internal prior-art reconstruction.
4. GPT creates differentiation note + claim plan.
5. GPT drafts claims from those structured materials.
6. GPT evaluates generated claims against original reference claims.
7. Write JSON artifacts and a human-reviewable Markdown pack.

This is not an external prior-art search. It reconstructs prior art from the PDF's
own background/specification text.
"""

from __future__ import annotations

import argparse
import json
import os
import textwrap
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

REPO_ROOT = Path(__file__).resolve().parents[2]
if load_dotenv:
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(REPO_ROOT / "agents/consultation/.env", override=True)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def compact_context(ctx: dict[str, str], max_chars: int = 14000) -> str:
    order = [
        "title",
        "abstract",
        "technical_field",
        "background",
        "problem",
        "solution",
        "effect",
        "drawing_brief",
        "detailed_description_excerpt",
    ]
    parts: list[str] = []
    used = 0
    for key in order:
        val = (ctx.get(key) or "").strip()
        if not val:
            continue
        block = f"[{key}]\n{val}"
        remaining = max_chars - used
        if remaining <= 0:
            break
        if len(block) > remaining:
            block = block[:remaining].rstrip() + " ..."
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)


def call_openai_json(system: str, user: str, model: str) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start : end + 1])
        raise


def system_json(role: str) -> str:
    return f"""
    너는 한국 AI/소프트웨어 특허 문서를 분석하는 변리사형 {role}이다.
    외부 검색을 수행했다고 주장하지 말고, 제공된 PDF 추출 context 내부 정보만 근거로 판단한다.
    모르는 내용은 추정하지 말고 uncertainty에 남긴다.
    반드시 JSON만 출력한다.
    """.strip()


def build_brief_prompt(public_row: dict[str, Any]) -> str:
    ctx = compact_context(public_row.get("invention_context", {}), 16000)
    return textwrap.dedent(
        f"""
        [목표]
        제공된 PDF 추출 context를 바탕으로 청구항 작성 전에 사용할 고품질 발명 설명과 문헌 기반 선행기술 재구성 리포트를 작성하라.
        이것은 외부 검색이 아니라 PDF 내부 배경기술/명세서 기반 prior-art reconstruction이다.

        [patent_id]
        {public_row.get('patent_id')}

        [PDF 추출 context]
        {ctx}

        [출력 JSON]
        {{
          "patent_id": "...",
          "invention_brief": {{
            "title": "",
            "technical_field": "",
            "problem": "",
            "prior_art_limitations": [],
            "core_solution": "",
            "core_components": [],
            "operation_flow": [],
            "technical_effects": [],
            "implementation_notes": []
          }},
          "internal_prior_art_report": {{
            "scope_note": "PDF 내부 정보 기반이며 외부 검색 아님",
            "known_background_technologies": [],
            "limitations_or_pain_points": [],
            "why_improvement_needed": [],
            "evidence_from_context": []
          }},
          "quality_notes": {{
            "missing_sections": [],
            "uncertainties": [],
            "input_context_risks": []
          }}
        }}
        """
    ).strip()


def build_plan_prompt(public_row: dict[str, Any], brief: dict[str, Any]) -> str:
    schema = {
        "patent_id": "...",
        "differentiation_note": {
            "distinguishing_features": [],
            "features_that_should_be_in_independent_claim": [],
            "features_suitable_for_dependent_claims": [],
            "expected_scope_risks": [],
            "avoid_overclaiming": [],
            "mandatory_vs_optional_judgement": [
                {"feature": "", "mandatory_or_optional": "mandatory|optional|uncertain", "reason": ""}
            ],
        },
        "claim_plan": {
            "drafting_mode": "reference_like_scope_reconstruction",
            "recommended_independent_claims": [
                {
                    "claim_form": "method|system/device|medium/program",
                    "core_elements": [],
                    "mandatory_elements_to_keep_together": [],
                    "reason": "",
                }
            ],
            "dependent_claim_candidates": [],
            "must_include_elements": [],
            "optional_elements": [],
            "terms_to_define_or_use_consistently": [],
            "anti_broadening_rules": [
                "Do not weaken enumerated input/output items into 'at least one' or 'at least two' unless the source context expressly says they are alternatives.",
                "If the context lists concrete data fields as the invention's core input set, keep them together in the main independent claim.",
                "If a component has named subcomponents in the context, include the subcomponent structure in the system independent claim unless clearly optional.",
            ],
            "drafting_strategy": "",
        },
        "uncertainties": [],
    }
    return textwrap.dedent(
        f"""
        [목표]
        발명 설명과 문헌 기반 선행기술 재구성 리포트를 바탕으로 차별점 노트와 청구항 설계도(claim plan)를 작성하라.
        원본 청구항은 제공하지 않는다. 제공된 발명/배경 정보만 근거로 한다.

        [중요 작성 모드]
        이번 실험은 넓은 권리범위 창작이 아니라 reference-like scope reconstruction이다.
        즉, PDF 내부 context에 구체 입력항목/출력항목/하위구성들이 열거되어 있으면 이를 임의로 '적어도 하나', '적어도 둘 이상'으로 완화하지 말고 필수 구성 후보로 본다.
        선택사항이라고 명시된 경우에만 optional로 분리한다.

        [patent_id]
        {public_row.get('patent_id')}

        [발명 설명/내부 prior-art reconstruction]
        {json.dumps(brief, ensure_ascii=False, indent=2)[:20000]}

        [출력 JSON 스키마]
        {json.dumps(schema, ensure_ascii=False, indent=2)}
        """
    ).strip()


def build_claim_prompt(public_row: dict[str, Any], brief: dict[str, Any], plan: dict[str, Any]) -> str:
    return textwrap.dedent(
        f"""
        [작업]
        아래의 고품질 발명 설명, 문헌 기반 선행기술 재구성, 차별점 노트, claim plan만 근거로 한국 특허 청구항 초안을 작성하라.
        원본 청구항을 보지 않았으므로 문장 일치가 아니라, 차별 구성과 권리범위 설계를 중시한다.

        [patent_id]
        {public_row.get('patent_id')}

        [발명 설명 + 내부 prior-art reconstruction]
        {json.dumps(brief, ensure_ascii=False, indent=2)[:18000]}

        [차별점 노트 + claim plan]
        {json.dumps(plan, ensure_ascii=False, indent=2)[:18000]}

        [작성 원칙]
        - 독립항에는 차별점과 필수 구성요소를 넣는다.
        - 이번은 reference-like scope reconstruction 모드다. 넓게 회피 가능한 청구항보다 PDF context의 구체 구성 결합을 충실히 재현하는 청구항을 우선한다.
        - 입력 데이터 세트, 처리 조건 세트, 출력/산출 항목 세트처럼 context에 구체 항목들이 열거되어 있으면, source가 선택사항이라고 명시하지 않는 한 '중 적어도 하나', '중 적어도 둘 이상', '복수 중 어느 하나'로 임의 완화하지 않는다.
        - 하위 구성요소가 명명되어 있으면 가능한 한 시스템 독립항에 함께 결합한다.
        - 종속항은 독립항의 필수 구성을 빼앗아 가는 용도가 아니라, 추가 세부구성/학습모듈/출력형식/알림방식 등을 한정하는 용도로 작성한다.
        - 근거 없는 외부 요소는 넣지 않는다.
        - 청구항 수는 claim plan에 맞추되 과도하게 늘리지 않는다.
        - JSON만 출력한다.

        [출력 JSON]
        {{
          "patent_id": "...",
          "claims": [
            {{"claim_no": 1, "role": "independent|dependent", "depends_on": [], "category": "method|system/device|medium/program|unknown", "text": ""}}
          ],
          "strategy_note": "",
          "uncertainties": []
        }}
        """
    ).strip()


def build_eval_prompt(public_row: dict[str, Any], brief: dict[str, Any], plan: dict[str, Any], generated: dict[str, Any], answer_key: dict[str, Any]) -> str:
    ref = [
        {
            "claim_no": c.get("claim_no"),
            "status": c.get("status"),
            "role": c.get("role"),
            "depends_on": c.get("depends_on"),
            "category": c.get("category"),
            "element_candidates": c.get("element_candidates", [])[:8],
            "text": c.get("text", ""),
        }
        for c in answer_key.get("reference_claims", [])
    ]
    rubric = {
        "structure_fit": 20,
        "core_element_coverage": 25,
        "claim_scope_similarity": 20,
        "dependent_claim_strategy": 10,
        "spec_support": 10,
        "patent_style": 10,
        "risk_penalty": 5,
    }
    return textwrap.dedent(
        f"""
        [목표]
        생성 청구항을 원본 청구항 reference와 비교하라.
        문장 동일성보다 구성요소, 권리범위, 요구하는 권리, 독립항 필수 구성, 종속항 전략을 평가한다.

        [발명 설명/내부 prior-art]
        {json.dumps(brief, ensure_ascii=False, indent=2)[:12000]}

        [차별점/claim plan]
        {json.dumps(plan, ensure_ascii=False, indent=2)[:12000]}

        [생성 청구항]
        {json.dumps(generated, ensure_ascii=False, indent=2)[:16000]}

        [원본 청구항 reference]
        {json.dumps(ref, ensure_ascii=False, indent=2)[:22000]}

        [평가표]
        {json.dumps(rubric, ensure_ascii=False, indent=2)}

        [출력 JSON]
        {{
          "patent_id": "...",
          "scores": {{
            "structure_fit": 0,
            "core_element_coverage": 0,
            "claim_scope_similarity": 0,
            "dependent_claim_strategy": 0,
            "spec_support": 0,
            "patent_style": 0,
            "risk_penalty": 0,
            "total": 0
          }},
          "component_match": [],
          "scope_match_judgement": "",
          "good_points": [],
          "bad_points": [],
          "missing_core_elements": [],
          "overclaimed_or_unsupported_elements": [],
          "human_review_questions": []
        }}
        """
    ).strip()


def md_section(title: str, obj: Any) -> str:
    return f"## {title}\n\n```json\n{json.dumps(obj, ensure_ascii=False, indent=2)}\n```\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--patent-id", default="1020250193994")
    ap.add_argument("--public", type=Path, default=REPO_ROOT / "data/processed/claim_loop/g06f_claim_loop_v3_claim_end_category_fix_cohort4_public.jsonl")
    ap.add_argument("--answer-key", type=Path, default=REPO_ROOT / "data/processed/claim_loop/g06f_claim_loop_v3_claim_end_category_fix_cohort4_answer_key.jsonl")
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT / "data/reports/pdf_analysis/mvp_claim_workflow_1020250193994")
    ap.add_argument("--model", default=os.environ.get("OPENAI_MODEL") or os.environ.get("CLAIM_LOOP_MODEL") or "gpt-5.5")
    args = ap.parse_args()

    rows = read_jsonl(args.public)
    keys = read_jsonl(args.answer_key)
    public_row = next(r for r in rows if r["patent_id"] == args.patent_id)
    # Remove reference_claims defensively. Generation must not see answer key.
    public_row = {k: v for k, v in public_row.items() if k != "reference_claims"}
    answer_key = next(r for r in keys if r["patent_id"] == args.patent_id)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "00_generation_input_public_no_reference.json", public_row)
    write_json(args.out_dir / "00_answer_key_reference_claims.json", answer_key)

    brief = call_openai_json(system_json("발명 구조화 분석가"), build_brief_prompt(public_row), args.model)
    write_json(args.out_dir / "01_invention_brief_and_internal_prior_art.json", brief)

    plan = call_openai_json(system_json("차별점/청구항 설계 분석가"), build_plan_prompt(public_row, brief), args.model)
    write_json(args.out_dir / "02_differentiation_note_and_claim_plan.json", plan)

    generated = call_openai_json(system_json("청구항 작성 에이전트"), build_claim_prompt(public_row, brief, plan), args.model)
    write_json(args.out_dir / "03_generated_claims_enhanced.json", generated)

    evaluation = call_openai_json(system_json("청구항 평가자"), build_eval_prompt(public_row, brief, plan, generated, answer_key), args.model)
    write_json(args.out_dir / "04_evaluation_against_reference.json", evaluation)

    md = []
    md.append(f"# MVP Claim Workflow 결과: {args.patent_id}\n")
    md.append("## 상태\n")
    md.append("- C안 실행: deterministic 재료 추출 → GPT-5.5 발명설명/내부 prior-art 재구성 → GPT-5.5 차별점/claim plan → GPT-5.5 청구항 생성 → GPT-5.5 평가.\n")
    md.append("- 외부 검색은 수행하지 않았고, PDF 내부 정보 기반 prior-art reconstruction이다.\n")
    md.append(f"- 모델: `{args.model}`\n")
    md.append(f"- PDF: `{answer_key.get('source_pdf')}`\n")
    scores = evaluation.get("scores", {})
    md.append(f"- 평가 총점: `{scores.get('total')}`\n")
    md.append("\n")
    md.append(md_section("0. 생성 입력 public no-reference", public_row))
    md.append(md_section("1. 발명 설명 + 내부 선행기술 재구성", brief))
    md.append(md_section("2. 차별점 노트 + Claim Plan", plan))
    md.append(md_section("3. 생성 청구항", generated))
    md.append(md_section("4. 원본 청구항 Reference", answer_key))
    md.append(md_section("5. 평가 결과", evaluation))
    md.append("## Human Review Note\n\n```text\n전문 리뷰어 판단:\n- \n구성요소/권리범위 일치 여부:\n- \nclaim plan 품질:\n- \n다음 수정사항:\n- \n```\n")
    (args.out_dir / "mvp_claim_workflow_review.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"out_dir": str(args.out_dir), "score": scores.get("total"), "model": args.model}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
