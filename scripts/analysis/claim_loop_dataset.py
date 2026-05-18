#!/usr/bin/env python3
"""Build claim-structure and claim-generation datasets from patent PDFs.

Purpose for the patent project:
- Rule layer: parse PDF sections and claims without an LLM.
- Evaluation layer input: provide structured payloads where claims can be masked.
- Human/LLM loop: compare generated claims against original PDF claims later.

Default input is the local G06F cache:
  data/raw/pdfs/g06f/all_110

Outputs:
  data/processed/claim_loop/<dataset>_claim_structure.jsonl
  data/processed/claim_loop/<dataset>_claim_generation_dev.jsonl
  data/processed/claim_loop/<dataset>_claim_generation_test_public.jsonl
  data/processed/claim_loop/<dataset>_claim_generation_test_answer_key.jsonl
  data/reports/pdf_analysis/<dataset>_claim_loop_dataset_report.md
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install PyMuPDF or run with: uv run --with pymupdf python scripts/analysis/claim_loop_dataset.py") from exc

CLAIM_MARK = re.compile(r"(?:【\s*)?청구항\s*(\d+)\s*(?:】)?")
CLAIM_SECTION = re.compile(r"(?:특허청구의\s*범위|청구범위|청구의\s*범위)")
# Korean patent PDFs often start the specification body with spaced headings such as
# "명 세 서" or "발명의 상세한 설명" immediately after the last claim.  If we do
# not cut there, the last claim absorbs the whole specification.
CLAIM_END = re.compile(
    r"(?:요약서|명\s*세\s*서|발명의\s*상세한\s*설명|발명의\s*설명|"
    r"발명을\s*실시하기\s*위한|도면의\s*간단한\s*설명|부호의\s*설명)"
)
PAGE_MARK = re.compile(r"\[\[PAGE\s+(\d+)\]\]")

SECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("title", re.compile(r"(?:\(54\)\s*)?발명의\s*명칭\s*[:：]?\s*(.+)")),
    ("abstract", re.compile(r"(?:\(57\)\s*)?요\s*약\s*[:：]?")),
    ("technical_field", re.compile(r"기술\s*분야")),
    ("background", re.compile(r"배경\s*기술")),
    ("problem", re.compile(r"해결\s*하려는\s*과제|발명이\s*이루고자\s*하는\s*기술적\s*과제")),
    ("solution", re.compile(r"과제의\s*해결\s*수단|과제를\s*해결하기\s*위한\s*수단")),
    ("effect", re.compile(r"발명의\s*효과")),
    ("drawing_brief", re.compile(r"도면의\s*간단한\s*설명")),
    ("detailed_description", re.compile(r"발명을\s*실시하기\s*위한\s*구체적인\s*내용|발명의\s*상세한\s*설명")),
    ("claims", CLAIM_SECTION),
]

DEPENDENCY_PATTERNS = [
    re.compile(r"제\s*(\d+)\s*항\s*에\s*있어서"),
    re.compile(r"제\s*(\d+)\s*항\s*또는\s*제\s*(\d+)\s*항\s*에\s*있어서"),
    re.compile(r"제\s*(\d+)\s*항\s*내지\s*제\s*(\d+)\s*항\s*중\s*어느\s*한\s*항\s*에\s*있어서"),
    re.compile(r"제\s*(\d+)\s*항\s*내지\s*(\d+)\s*항\s*중\s*어느\s*한\s*항\s*에\s*있어서"),
    re.compile(r"전술한\s*항\s*중\s*어느\s*한\s*항\s*에\s*있어서"),
]

GENERIC_PATENT_NOISE = re.compile(r"등록특허\s*10-\d+|공개특허\s*10-\d+|-\s*\d+\s*-|\[\[PAGE\s+\d+\]\]")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str) -> str:
    text = GENERIC_PATENT_NOISE.sub(" ", text)
    return norm(text)


def clamp(text: str, limit: int = 2500) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + " ..."


def extract_pdf_text(path: Path) -> tuple[str, int]:
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc, 1):
        pages.append(f"\n\n[[PAGE {i}]]\n" + page.get_text("text"))
    return "".join(pages), len(doc)


def find_page(text: str, char_pos: int) -> int | None:
    page = None
    for m in PAGE_MARK.finditer(text[:char_pos]):
        page = int(m.group(1))
    return page


def extract_sections(text: str) -> dict[str, str]:
    # Find heading positions, then slice between successive headings.
    hits: list[tuple[int, str, re.Match[str]]] = []
    for name, pat in SECTION_PATTERNS:
        for m in pat.finditer(text):
            hits.append((m.start(), name, m))
    hits.sort(key=lambda x: x[0])

    sections: dict[str, str] = {}
    for idx, (start, name, m) in enumerate(hits):
        if name in sections and len(sections[name]) > 80:
            continue
        end = hits[idx + 1][0] if idx + 1 < len(hits) else min(len(text), start + 7000)
        body = text[m.end() : end]
        if name == "title":
            line = m.group(1) if m.lastindex else body.splitlines()[0] if body.splitlines() else ""
            sections[name] = clamp(line, 300)
        else:
            sections[name] = clamp(body, 2500)

    # Fallback title from first page lines.
    if not sections.get("title"):
        first = text[:2500]
        m = re.search(r"발명의\s*명칭\s*[:：]?\s*(.+)", first)
        if m:
            sections["title"] = clamp(m.group(1), 300)
    return sections


def claim_region(text: str) -> tuple[str, str]:
    m = CLAIM_SECTION.search(text)
    if not m:
        return text, "no_claim_section_heading"
    region = text[m.start() :]
    first = CLAIM_MARK.search(region)
    if not first:
        return region, "claim_section_without_claim_marker"
    region = region[first.start() :]
    end = CLAIM_END.search(region)
    if end and end.start() > 500:
        return region[: end.start()], "section_bounded_cut"
    return region, "section_bounded_no_cut"


def dependency(text: str, current_no: int) -> tuple[list[int], list[str]]:
    head = text[:500]
    deps: list[int] = []
    signals: list[str] = []
    for pat in DEPENDENCY_PATTERNS:
        for m in pat.finditer(head):
            sig = norm(m.group(0))
            signals.append(sig)
            nums = [g for g in m.groups() if g]
            if "내지" in sig and len(nums) >= 2:
                try:
                    deps.extend(range(int(nums[0]), int(nums[1]) + 1))
                except ValueError:
                    pass
            else:
                deps.extend(int(n) for n in nums if n.isdigit())
    if not deps:
        m = re.search(r"제\s*(\d+)\s*항\s*의", head)
        if m:
            deps.append(int(m.group(1)))
            signals.append(norm(m.group(0)))
    deps = sorted({d for d in deps if d != current_no})
    return deps, signals[:5]


def claim_category(text: str) -> str:
    t = clean_text(text)
    tail = t[-450:]
    # Prefer the claim's terminal expression. Older PDFs often mention "프로그램" or
    # "메모리" inside a method claim, so full-text keyword matching overclassifies.
    if re.search(r"(컴퓨터\s*판독\s*가능(?:한)?\s*)?(기록\s*매체|저장\s*매체)|프로그램\s*을\s*기록", tail):
        return "medium/program"
    if re.search(r"(시스템|장치|디바이스|서버|단말|기기|칩)\s*[\.]?$", tail):
        return "system/device"
    if re.search(r"방법\s*[\.]?$", tail) or "하는 단계" in t[:1600]:
        return "method"
    if re.search(r"(컴퓨터\s*판독|기록\s*매체|저장\s*매체)", t[:800]):
        return "medium/program"
    return "unknown"


def element_candidates(text: str) -> list[str]:
    t = clean_text(text)
    clauses = re.split(r"[;；]|\s및\s|,\s*및\s|\s그리고\s", t)
    out: list[str] = []
    for c in clauses:
        c = clean_text(c)
        if len(c) < 15:
            continue
        if re.search(r"(단계|부|모듈|수단|프로세서|메모리|서버|단말|모델|데이터|인터페이스|엔진)", c):
            out.append(c[:180])
    return out[:10]


def parse_claims(text: str) -> tuple[list[dict[str, Any]], str]:
    region, note = claim_region(text)
    matches = list(CLAIM_MARK.finditer(region))
    claims: list[dict[str, Any]] = []
    for idx, m in enumerate(matches):
        no = int(m.group(1))
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(region)
        raw = region[start:end].strip()
        cut = CLAIM_END.search(raw)
        if cut and cut.start() > 120:
            raw = raw[: cut.start()].strip()
        deleted = bool(re.search(rf"청구항\s*{no}\s*삭제|삭제\s*$", clean_text(raw[:100])))
        deps, signals = dependency(raw, no)
        role = "deleted" if deleted else ("dependent" if deps else "independent")
        cat = "none" if deleted else claim_category(raw)
        issues = []
        if not deleted and len(clean_text(raw)) < 50:
            issues.append("too_short")
        if not deleted and cat == "unknown":
            issues.append("category_unknown")
        if not deleted and "[[PAGE" in raw[:500]:
            issues.append("page_marker_contamination")
        elems = [] if deleted else element_candidates(raw)
        if not deleted and not elems:
            issues.append("no_element_candidates")
        claims.append(
            {
                "claim_no": no,
                "status": "deleted" if deleted else "active",
                "role": role,
                "depends_on": deps,
                "depends_signal": signals,
                "category": cat,
                "text": clean_text(raw),
                "text_len": len(clean_text(raw)),
                "element_candidates": elems,
                "rule_issues": issues,
            }
        )
    return claims, note


def patent_id_from_file(path: Path) -> str:
    return path.stem.replace("raw_pdf-", "")


def make_prompt_payload(record: dict[str, Any], include_reference: bool) -> dict[str, Any]:
    sections = record["sections"]
    invention_context = {
        "title": sections.get("title", ""),
        "abstract": sections.get("abstract", ""),
        "technical_field": sections.get("technical_field", ""),
        "background": sections.get("background", ""),
        "problem": sections.get("problem", ""),
        "solution": sections.get("solution", ""),
        "effect": sections.get("effect", ""),
        "drawing_brief": sections.get("drawing_brief", ""),
        "detailed_description_excerpt": sections.get("detailed_description", ""),
    }
    payload: dict[str, Any] = {
        "dataset_id": record["dataset_id"],
        "split": record["split"],
        "patent_id": record["patent_id"],
        "source_pdf": record["source_pdf"],
        "task": "Write Korean patent claims from the invention/specification context. Include independent and dependent claims. Preserve patent style, but do not invent unsupported elements.",
        "invention_context": invention_context,
        "expected_output_schema": {
            "claims": [
                {
                    "claim_no": "integer",
                    "role": "independent|dependent",
                    "depends_on": "array[integer]",
                    "category": "method|system/device|medium/program|unknown",
                    "text": "Korean patent claim text",
                }
            ],
            "strategy_note": "short Korean explanation of independent/dependent claim strategy",
            "uncertainties": "missing or ambiguous source information",
        },
    }
    if include_reference:
        payload["reference_claims"] = record["claims"]
    return payload


def build_dataset(pdf_dir: Path, out_dir: Path, report_dir: Path, dataset_id: str, dev_count: int, limit: int | None) -> None:
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if limit:
        pdfs = pdfs[:limit]
    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    structure_path = out_dir / f"{dataset_id}_claim_structure.jsonl"
    dev_path = out_dir / f"{dataset_id}_claim_generation_dev.jsonl"
    test_public_path = out_dir / f"{dataset_id}_claim_generation_test_public.jsonl"
    test_key_path = out_dir / f"{dataset_id}_claim_generation_test_answer_key.jsonl"
    report_path = report_dir / f"{dataset_id}_claim_loop_dataset_report.md"

    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for idx, pdf in enumerate(pdfs):
        split = "dev" if idx < dev_count else "test"
        try:
            text, pages = extract_pdf_text(pdf)
            sections = extract_sections(text)
            claims, claim_region_note = parse_claims(text)
            active = [c for c in claims if c["status"] == "active"]
            record = {
                "dataset_id": dataset_id,
                "split": split,
                "patent_id": patent_id_from_file(pdf),
                "source_pdf": str(pdf),
                "pages": pages,
                "text_chars": len(text),
                "section_coverage": {k: bool(v) for k, v in sections.items()},
                "sections": sections,
                "claim_region_note": claim_region_note,
                "claim_stats": {
                    "total": len(claims),
                    "active": len(active),
                    "deleted": sum(1 for c in claims if c["status"] == "deleted"),
                    "independent": sum(1 for c in active if c["role"] == "independent"),
                    "dependent": sum(1 for c in active if c["role"] == "dependent"),
                    "unknown_category": sum(1 for c in active if c["category"] == "unknown"),
                    "rule_issue_count": sum(len(c["rule_issues"]) for c in claims),
                },
                "claims": claims,
            }
            records.append(record)
        except Exception as exc:  # keep batch running
            failures.append({"pdf": str(pdf), "error": repr(exc)})

    with structure_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with dev_path.open("w", encoding="utf-8") as f:
        for r in records:
            if r["split"] == "dev":
                f.write(json.dumps(make_prompt_payload(r, include_reference=True), ensure_ascii=False) + "\n")
    with test_public_path.open("w", encoding="utf-8") as f:
        for r in records:
            if r["split"] == "test":
                f.write(json.dumps(make_prompt_payload(r, include_reference=False), ensure_ascii=False) + "\n")
    with test_key_path.open("w", encoding="utf-8") as f:
        for r in records:
            if r["split"] == "test":
                key = {
                    "dataset_id": dataset_id,
                    "patent_id": r["patent_id"],
                    "source_pdf": r["source_pdf"],
                    "reference_claims": r["claims"],
                    "claim_stats": r["claim_stats"],
                }
                f.write(json.dumps(key, ensure_ascii=False) + "\n")

    dev = [r for r in records if r["split"] == "dev"]
    test = [r for r in records if r["split"] == "test"]
    total_claims = sum(r["claim_stats"]["total"] for r in records)
    total_deleted = sum(r["claim_stats"]["deleted"] for r in records)
    total_ind = sum(r["claim_stats"]["independent"] for r in records)
    total_dep = sum(r["claim_stats"]["dependent"] for r in records)

    md: list[str] = []
    md.append(f"# {dataset_id} claim loop dataset report")
    md.append("")
    md.append("## 1. 목적")
    md.append("PDF 원문에서 청구항 구조를 rule로 먼저 추출하고, 청구항을 비운 public test payload를 만들어 GPT-5.5/사람 평가 루프에 넣기 위한 데이터셋입니다.")
    md.append("")
    md.append("## 2. Split")
    md.append(f"- 입력 PDF 폴더: `{pdf_dir}`")
    md.append(f"- 처리 성공 PDF: {len(records)}건")
    md.append(f"- dev: {len(dev)}건 — rule/prompt 설계용, reference claims 포함")
    md.append(f"- test: {len(test)}건 — 청구항 비움, 별도 answer key로 평가")
    md.append(f"- 실패: {len(failures)}건")
    md.append("")
    md.append("## 3. 전체 청구항 통계")
    md.append(f"- 총 청구항: {total_claims}")
    md.append(f"- 독립항: {total_ind}")
    md.append(f"- 종속항: {total_dep}")
    md.append(f"- 삭제항: {total_deleted}")
    md.append("")
    md.append("## 4. 산출물")
    md.append(f"- 구조 전체: `{structure_path}`")
    md.append(f"- dev 생성용: `{dev_path}`")
    md.append(f"- test public, 청구항 비움: `{test_public_path}`")
    md.append(f"- test answer key, 원본 청구항: `{test_key_path}`")
    md.append("")
    md.append("## 5. 방식 기준")
    md.append("A→B→C는 단계적 고도화입니다.")
    md.append("- A: naive regex — 전체 텍스트에서 청구항 번호만 분리")
    md.append("- B: section-aware — `특허청구의 범위` 영역 중심으로 분리")
    md.append("- C: structured rule checker — B 결과에 독립/종속/삭제/category/구성요소 후보/issue를 붙임")
    md.append("")
    md.append("현재 구현은 C를 기본 데이터셋 생성 기준으로 사용합니다.")
    md.append("")
    md.append("## 6. 파일별 요약")
    md.append("")
    md.append("| split | patent_id | pages | claims | ind/dep/del | unknown | issues | section coverage |")
    md.append("|---|---|---:|---:|---|---:|---:|---|")
    for r in records:
        cov = ", ".join(k for k, v in r["section_coverage"].items() if v and k != "claims") or "none"
        s = r["claim_stats"]
        md.append(
            f"| {r['split']} | {r['patent_id']} | {r['pages']} | {s['total']} | {s['independent']}/{s['dependent']}/{s['deleted']} | {s['unknown_category']} | {s['rule_issue_count']} | {cov[:80]} |"
        )
    if failures:
        md.append("")
        md.append("## 7. Failures")
        for f in failures:
            md.append(f"- `{f['pdf']}`: {f['error']}")
    md.append("")
    md.append("## 8. 다음 loop")
    md.append("1. dev 10건으로 GPT-5.5 evaluator prompt 설계")
    md.append("2. test_public에 청구항 생성 실행")
    md.append("3. answer_key와 비교: 구조 점수 + 사람 리뷰")
    md.append("4. 틀린 케이스를 rule/schema/evaluator prompt에 반영")

    report_path.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({
        "processed": len(records),
        "dev": len(dev),
        "test": len(test),
        "failures": failures,
        "outputs": {
            "structure": str(structure_path),
            "dev": str(dev_path),
            "test_public": str(test_public_path),
            "test_answer_key": str(test_key_path),
            "report": str(report_path),
        },
    }, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", type=Path, default=Path("data/raw/pdfs/g06f/all_110"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/processed/claim_loop"))
    parser.add_argument("--report-dir", type=Path, default=Path("data/reports/pdf_analysis"))
    parser.add_argument("--dataset-id", default="g06f_claim_loop_v0")
    parser.add_argument("--dev-count", type=int, default=10)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    build_dataset(args.pdf_dir, args.out_dir, args.report_dir, args.dataset_id, args.dev_count, args.limit)


if __name__ == "__main__":
    main()
