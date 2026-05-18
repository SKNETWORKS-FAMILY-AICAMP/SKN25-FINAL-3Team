#!/usr/bin/env python3
"""Run the claim generation/evaluation loop.

This script is intentionally small and explicit. It supports:

1. dry-run: build prompts from claim_generation_test_public/dev JSONL without calling an API.
2. generate: call an OpenAI-compatible Chat Completions model and save generated claims.
3. evaluate-dry-run: build an evaluator prompt using generated claims + answer key.

Environment variables for API mode:
- OPENAI_API_KEY
- CLAIM_LOOP_MODEL, default: gpt-5.5

Example:
  uv run --with openai python scripts/analysis/claim_loop_run.py \
    --mode dry-run --input data/processed/claim_loop/g06f_claim_loop_v0_claim_generation_dev.jsonl --limit 2

  uv run --with openai python scripts/analysis/claim_loop_run.py \
    --mode generate --input data/processed/claim_loop/g06f_claim_loop_v0_claim_generation_dev.jsonl --limit 2
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
except ImportError:  # optional; API mode can still use exported env vars
    load_dotenv = None

REPO_ROOT = Path(__file__).resolve().parents[2]

if load_dotenv:
    # Load from the real repo root regardless of the caller's current working directory.
    load_dotenv(REPO_ROOT / '.env')
    load_dotenv(REPO_ROOT / 'agents/consultation/.env', override=True)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def compact_context(ctx: dict[str, str], max_chars: int = 9000) -> str:
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


def generation_system_prompt() -> str:
    return textwrap.dedent(
        """
        당신은 한국 AI/소프트웨어 특허 명세서의 청구항 초안을 작성하는 변리사형 청구항 작성 에이전트다.
        단, 제공된 발명 설명에 없는 구성요소를 임의로 만들지 않는다.
        목표는 원문 특허와 문장이 동일한 청구항이 아니라, 제공된 발명 설명에 근거한 구조적으로 타당한 청구항 세트를 만드는 것이다.

        작성 원칙:
        1. 독립항은 발명의 핵심 입력-처리-출력 또는 구성요소를 포함한다.
        2. 종속항은 독립항의 데이터, 모듈, 알고리즘, 조건, 출력, UI, 저장매체 등을 의미 있게 한정한다.
        3. AI/소프트웨어 문서라면 방법 청구항, 시스템/장치 청구항, 기록매체/프로그램 청구항 가능성을 검토한다.
        4. 청구항 문체는 한국 특허식 표현을 사용한다. 예: 상기, 포함하는, 기초하여, 산출하는.
        5. 불확실하면 uncertainties에 명시한다.
        6. 반드시 JSON만 출력한다.
        """
    ).strip()


def build_generation_prompt(row: dict[str, Any]) -> str:
    context = compact_context(row.get("invention_context", {}))
    schema = row.get("expected_output_schema", {})
    return textwrap.dedent(
        f"""
        [작업]
        아래 발명 설명 context만 근거로 한국 특허 청구항 초안을 작성하라.

        [patent_id]
        {row.get('patent_id')}

        [발명 설명 context]
        {context}

        [출력 JSON 스키마]
        {json.dumps(schema, ensure_ascii=False, indent=2)}

        [추가 요구]
        - claim_no는 1부터 순서대로 부여한다.
        - role은 independent 또는 dependent로 표시한다.
        - dependent claim은 depends_on에 상위 청구항 번호를 넣는다.
        - category는 method, system/device, medium/program, unknown 중 하나를 우선 사용한다.
        - strategy_note에는 왜 그런 독립항/종속항 구조를 잡았는지 짧게 쓴다.
        - uncertainties에는 발명 설명이 부족해서 확정하기 어려운 점을 쓴다.
        - JSON 외의 설명은 출력하지 않는다.
        """
    ).strip()


def evaluator_system_prompt() -> str:
    return textwrap.dedent(
        """
        당신은 한국 AI/소프트웨어 특허 청구항 초안을 평가하는 리뷰어다.
        평가는 법적 신규성/진보성 최종 판단이 아니라, 원본 청구항 feature 대비 생성 청구항의 구조/핵심요소/종속항 전략/명세서 대응성을 평가하는 것이다.
        반드시 JSON만 출력한다.
        """
    ).strip()


def build_evaluator_prompt(public_row: dict[str, Any], generated: dict[str, Any], answer_key: dict[str, Any]) -> str:
    context = compact_context(public_row.get("invention_context", {}), max_chars=7000)
    reference_claims = answer_key.get("reference_claims", [])
    # Keep reference compact; enough for evaluator but not huge.
    compact_ref = [
        {
            "claim_no": c.get("claim_no"),
            "status": c.get("status"),
            "role": c.get("role"),
            "depends_on": c.get("depends_on"),
            "category": c.get("category"),
            "element_candidates": c.get("element_candidates", [])[:5],
            "text": (c.get("text") or "")[:700],
        }
        for c in reference_claims
    ]
    rubric = {
        "structure_fit": 20,
        "core_element_coverage": 25,
        "dependent_claim_strategy": 15,
        "spec_support": 15,
        "patent_style": 10,
        "risk_signals": 10,
        "input_quality_penalty": 5,
    }
    return textwrap.dedent(
        f"""
        [평가 대상 patent_id]
        {public_row.get('patent_id')}

        [발명 설명 context]
        {context}

        [생성 청구항]
        {json.dumps(generated, ensure_ascii=False, indent=2)[:12000]}

        [원본 청구항 reference]
        {json.dumps(compact_ref, ensure_ascii=False, indent=2)[:16000]}

        [평가표/배점]
        {json.dumps(rubric, ensure_ascii=False, indent=2)}

        [출력 JSON]
        {{
          "patent_id": "...",
          "scores": {{
            "structure_fit": 0,
            "core_element_coverage": 0,
            "dependent_claim_strategy": 0,
            "spec_support": 0,
            "patent_style": 0,
            "risk_signals": 0,
            "input_quality_penalty": 0,
            "total": 0
          }},
          "good_points": [],
          "bad_points": [],
          "missing_core_elements": [],
          "overclaimed_or_unsupported_elements": [],
          "claim_relation_issues": [],
          "independent_claim_set_judgement": "method/system/medium set인지, 별도 발명인지 간단 판단",
          "human_review_questions": []
        }}
        """
    ).strip()


def call_openai_json(system: str, user: str, model: str) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        max_completion_tokens=4000,
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def mode_dry_run(rows: list[dict[str, Any]], out: Path, limit: int) -> None:
    selected = rows[:limit]
    out_rows = []
    for row in selected:
        out_rows.append(
            {
                "patent_id": row.get("patent_id"),
                "source_pdf": row.get("source_pdf"),
                "system_prompt": generation_system_prompt(),
                "user_prompt": build_generation_prompt(row),
            }
        )
    write_jsonl(out, out_rows)
    print(json.dumps({"mode": "dry-run", "written": len(out_rows), "output": str(out)}, ensure_ascii=False, indent=2))


def mode_generate(rows: list[dict[str, Any]], out: Path, limit: int, model: str) -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set. Use --mode dry-run first or set the key.")
    selected = rows[:limit]
    out_rows = []
    for row in selected:
        user_prompt = build_generation_prompt(row)
        generated = call_openai_json(generation_system_prompt(), user_prompt, model)
        retry_used = False
        if not isinstance(generated, dict) or not generated.get("claims"):
            retry_used = True
            retry_prompt = user_prompt + "\n\n[중요 재시도 지시]\n빈 JSON({})은 실패다. 반드시 claims 배열에 최소 3개 이상의 청구항을 작성하라. 발명 설명이 부족하면 uncertainties에 부족한 점을 쓰되, 제공된 context에 근거한 최선의 청구항 초안을 생성하라."
            generated = call_openai_json(generation_system_prompt(), retry_prompt, model)
        out_rows.append(
            {
                "patent_id": row.get("patent_id"),
                "source_pdf": row.get("source_pdf"),
                "model": model,
                "retry_used": retry_used,
                "generated": generated,
            }
        )
        write_jsonl(out, out_rows)  # incremental save
    print(json.dumps({"mode": "generate", "written": len(out_rows), "output": str(out), "model": model}, ensure_ascii=False, indent=2))


def build_evaluation_prompt_rows(public_rows: list[dict[str, Any]], generated_path: Path, answer_key_path: Path, limit: int) -> list[dict[str, Any]]:
    generated_rows = {r["patent_id"]: r for r in read_jsonl(generated_path)}
    answer_rows = {r["patent_id"]: r for r in read_jsonl(answer_key_path)}
    out_rows = []
    for row in public_rows:
        pid = row.get("patent_id")
        if pid not in generated_rows or pid not in answer_rows:
            continue
        out_rows.append(
            {
                "patent_id": pid,
                "system_prompt": evaluator_system_prompt(),
                "user_prompt": build_evaluator_prompt(row, generated_rows[pid].get("generated", generated_rows[pid]), answer_rows[pid]),
            }
        )
        if len(out_rows) >= limit:
            break
    return out_rows


def mode_evaluate_dry_run(public_rows: list[dict[str, Any]], generated_path: Path, answer_key_path: Path, out: Path, limit: int) -> None:
    out_rows = build_evaluation_prompt_rows(public_rows, generated_path, answer_key_path, limit)
    write_jsonl(out, out_rows)
    print(json.dumps({"mode": "evaluate-dry-run", "written": len(out_rows), "output": str(out)}, ensure_ascii=False, indent=2))


def mode_evaluate(public_rows: list[dict[str, Any]], generated_path: Path, answer_key_path: Path, out: Path, limit: int, model: str) -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set. Use --mode evaluate-dry-run first or set the key.")
    prompt_rows = build_evaluation_prompt_rows(public_rows, generated_path, answer_key_path, limit)
    out_rows = []
    for row in prompt_rows:
        evaluated = call_openai_json(row["system_prompt"], row["user_prompt"], model)
        out_rows.append({"patent_id": row["patent_id"], "model": model, "evaluation": evaluated})
        write_jsonl(out, out_rows)
    print(json.dumps({"mode": "evaluate", "written": len(out_rows), "output": str(out), "model": model}, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dry-run", "generate", "evaluate-dry-run", "evaluate"], required=True)
    parser.add_argument("--input", type=Path, default=Path("data/processed/claim_loop/g06f_claim_loop_v0_claim_generation_dev.jsonl"))
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--model", default=os.environ.get("CLAIM_LOOP_MODEL", "gpt-5.5"))
    parser.add_argument("--generated", type=Path, default=Path("data/reports/pdf_analysis/claim_loop_generations.jsonl"))
    parser.add_argument("--answer-key", type=Path, default=Path("data/processed/claim_loop/g06f_claim_loop_v0_claim_generation_test_answer_key.jsonl"))
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    if args.output is None:
        suffix = args.mode.replace("-", "_")
        args.output = Path(f"data/reports/pdf_analysis/claim_loop_{suffix}.jsonl")

    if args.mode == "dry-run":
        mode_dry_run(rows, args.output, args.limit)
    elif args.mode == "generate":
        mode_generate(rows, args.output, args.limit, args.model)
    elif args.mode == "evaluate-dry-run":
        mode_evaluate_dry_run(rows, args.generated, args.answer_key, args.output, args.limit)
    elif args.mode == "evaluate":
        mode_evaluate(rows, args.generated, args.answer_key, args.output, args.limit, args.model)


if __name__ == "__main__":
    main()
