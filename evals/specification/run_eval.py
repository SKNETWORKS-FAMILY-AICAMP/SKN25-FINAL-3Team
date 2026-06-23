"""CLI runner for specification generation and LLM-based quality evaluation."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from evals.specification.judge import JudgeConfig, build_judge_messages, judge_specification
from evals.specification.rubric import (
    CORE_MINIMUMS,
    CRITERIA,
    PASS_SCORE,
    RUBRIC_VERSION,
    SPECIFICATION_SECTIONS,
)
from evals.specification.schemas import (
    EvaluationCase,
    EvaluationReport,
    JudgeResult,
    MechanicalResult,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="명세서 생성 결과의 실시가능성 및 품질을 평가합니다.")
    parser.add_argument("--case", type=Path, required=True, help="평가 case JSON 경로")
    parser.add_argument("--candidate", type=Path, help="기존 명세서 JSON. 생략하면 Specification Agent를 실행합니다.")
    parser.add_argument(
        "--generator-model",
        help="명세서 생성 모델. 기본값은 OPENAI_SPEC_MODEL 또는 gpt-4o",
    )
    parser.add_argument(
        "--judge-model",
        help="Judge 모델. 기본값은 OPENAI_JUDGE_MODEL 또는 gpt-4o",
    )
    parser.add_argument(
        "--api-timeout",
        type=float,
        default=float(os.getenv("OPENAI_API_TIMEOUT", "120")),
        help="생성 및 Judge API 요청 제한 시간(초). 기본값은 120",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT_DIR / ".cache" / "specification-evals",
        help="리포트 저장 폴더",
    )
    storage_group = parser.add_mutually_exclusive_group()
    storage_group.add_argument(
        "--save",
        action="store_true",
        help="candidate와 평가 리포트를 파일로 저장합니다. 기본값은 저장하지 않음",
    )
    storage_group.add_argument("--no-save", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 case와 candidate 형식만 확인합니다.")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, dict):
        raise ValueError(f"JSON 최상위 값은 객체여야 합니다: {path}")
    return value


def load_case(path: Path) -> EvaluationCase:
    return EvaluationCase.model_validate(load_json(path))


def unwrap_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept direct agent output, FastAPI output, or a previous eval report."""
    if isinstance(payload.get("result"), dict):
        payload = payload["result"]
    if isinstance(payload.get("specification"), dict):
        payload = payload["specification"]
    return payload


def generate_candidate(
    case: EvaluationCase,
    generator_model: str | None,
    timeout_seconds: float,
) -> tuple[dict[str, Any], str]:
    from openai import OpenAI

    from agents.specification import SpecificationAgentConfig
    from agents.specification import specification_agent

    resolved_model = generator_model or os.getenv("OPENAI_SPEC_MODEL", "gpt-4o")
    config = SpecificationAgentConfig(model=resolved_model)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 없어 명세서를 생성할 수 없습니다.")

    # 평가 실행에만 타임아웃이 적용되도록 Agent의 런타임 클라이언트를 설정한다.
    # 기존 agents/specification 코드는 변경하지 않는다.
    specification_agent._client = OpenAI(api_key=api_key, timeout=timeout_seconds)
    result = specification_agent.run_specification_agent(case.agent_state, config=config)
    return result, config.model


def print_stage(message: str) -> float:
    """Print a visible stage marker and return its start time."""
    print(message, flush=True)
    return time.perf_counter()


def print_elapsed(started_at: float) -> None:
    print(f"  완료 ({time.perf_counter() - started_at:.1f}초)", flush=True)


def format_failure(stage: str, exc: Exception) -> str:
    name = type(exc).__name__
    if name == "APITimeoutError":
        return (
            f"{stage} API 요청이 제한 시간을 초과했습니다: {exc}\n"
            "--api-timeout 값을 늘리거나 네트워크 및 사용 모델 상태를 확인하세요."
        )
    if name == "APIConnectionError":
        return f"{stage} API에 연결하지 못했습니다: {exc}\n네트워크 연결을 확인하세요."
    return f"{stage} 실패 ({name}): {exc}"


def independent_claim_numbers(agent_state: dict[str, Any]) -> set[str]:
    claims = (agent_state.get("claims") or {}).get("draft_claims") or []
    explicit = {
        str(number)
        for number in (agent_state.get("claims") or {}).get("independent_claim_numbers") or []
    }
    if explicit:
        return explicit

    inferred = {
        str(claim.get("claim_no"))
        for claim in claims
        if claim.get("type") == "independent" or claim.get("is_dependent") is False
    }
    if not inferred and claims:
        inferred.add(str(claims[0].get("claim_no", "1")))
    return inferred


def collect_mechanical_findings(
    case: EvaluationCase,
    specification: dict[str, Any],
) -> MechanicalResult:
    critical: list[str] = []
    warnings: list[str] = []

    status = specification.get("status")
    if status is not None and status != "ok":
        critical.append(f"Specification Agent status={status}")

    for section in SPECIFICATION_SECTIONS:
        if not str(specification.get(section) or "").strip():
            critical.append(f"필수 섹션 누락 또는 빈 값: {section}")

    details = specification.get("details") or {}
    validation = details.get("validation") or {}
    for issue in validation.get("hard_issues") or []:
        critical.append(f"기존 검증 hard issue: {issue}")
    for issue in validation.get("style_warnings") or []:
        warnings.append(f"기존 검증 style warning: {issue}")

    claims = (case.agent_state.get("claims") or {}).get("draft_claims") or []
    has_elements = any(claim.get("elements") for claim in claims)
    support_matrix = details.get("support_matrix") or []
    independent = independent_claim_numbers(case.agent_state)

    if not has_elements:
        warnings.append(
            "청구항 elements가 없어 기존 support_matrix가 제한적입니다. "
            "LLM Judge가 청구항 text 원문을 직접 분해하여 평가합니다."
        )

    for row in support_matrix:
        if row.get("supported", True):
            continue
        message = f"청구항 {row.get('claim_no')} 요소 미지원: {row.get('element')}"
        if str(row.get("claim_no")) in independent:
            critical.append(message)
        else:
            warnings.append(message)

    return MechanicalResult(
        critical_failures=list(dict.fromkeys(critical)),
        warnings=list(dict.fromkeys(warnings)),
    )


def validate_judge_scores(judge: JudgeResult) -> int:
    expected = {criterion["id"]: criterion for criterion in CRITERIA}
    returned = {criterion.criterion_id: criterion for criterion in judge.criteria}

    if len(returned) != len(judge.criteria):
        raise ValueError("Judge가 중복된 criterion_id를 반환했습니다.")
    if set(returned) != set(expected):
        raise ValueError(
            f"Judge 평가 항목 불일치: expected={sorted(expected)}, returned={sorted(returned)}"
        )

    total = 0
    for criterion_id, definition in expected.items():
        result = returned[criterion_id]
        if result.max_score != definition["max_score"]:
            raise ValueError(f"{criterion_id} max_score가 rubric과 다릅니다.")
        if result.score > result.max_score:
            raise ValueError(f"{criterion_id} score가 max_score를 초과했습니다.")

        expected_subs = {sub["id"]: sub for sub in definition["subcriteria"]}
        returned_subs = {sub.subcriterion_id: sub for sub in result.subcriteria}
        if len(returned_subs) != len(result.subcriteria) or set(returned_subs) != set(expected_subs):
            raise ValueError(f"{criterion_id} 세부 평가 항목이 rubric과 다릅니다.")

        sub_total = 0
        for sub_id, sub_definition in expected_subs.items():
            sub_result = returned_subs[sub_id]
            if sub_result.max_score != sub_definition["max_score"]:
                raise ValueError(f"{criterion_id}.{sub_id} max_score가 rubric과 다릅니다.")
            if sub_result.score > sub_result.max_score:
                raise ValueError(f"{criterion_id}.{sub_id} score가 max_score를 초과했습니다.")
            sub_total += sub_result.score

        if result.score != sub_total:
            raise ValueError(f"{criterion_id} score가 세부 점수 합과 다릅니다.")
        total += result.score

    return total


def grade_for(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    return "D"


def finalize_report(
    case: EvaluationCase,
    specification: dict[str, Any],
    candidate_source: str,
    generator_model: str,
    judge_model: str,
    mechanical: MechanicalResult,
    judge: JudgeResult,
) -> EvaluationReport:
    total_score = validate_judge_scores(judge)
    criterion_scores = {criterion.criterion_id: criterion.score for criterion in judge.criteria}
    reasons: list[str] = []

    if total_score < PASS_SCORE:
        reasons.append(f"총점 {total_score}점으로 합격 기준 {PASS_SCORE}점 미달")
    for criterion_id, minimum in CORE_MINIMUMS.items():
        actual = criterion_scores[criterion_id]
        if actual < minimum:
            reasons.append(f"{criterion_id} {actual}점으로 필수 기준 {minimum}점 미달")
    if mechanical.critical_failures:
        reasons.append(f"기계적 중대 실패 {len(mechanical.critical_failures)}건")
    if judge.critical_failures:
        reasons.append(f"Judge 중대 실패 {len(judge.critical_failures)}건")
    if judge.confidence == "low":
        reasons.append("Judge confidence가 low이므로 전문가 검토 필요")

    passed = not reasons
    if passed:
        reasons.append("총점, 핵심 항목, 중대 실패 및 신뢰도 기준을 모두 충족")

    return EvaluationReport(
        case_id=case.case_id,
        rubric_version=RUBRIC_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
        candidate_source=candidate_source,
        generator_model=generator_model,
        judge_model=judge_model,
        total_score=total_score,
        grade=grade_for(total_score),
        passed=passed,
        decision_reasons=reasons,
        mechanical=mechanical,
        judge=judge,
        specification=specification,
        legal_notice=(
            "이 결과는 제공된 자료와 버전 고정 평가표에 따른 품질 지표이며, "
            "특허 등록 가능성이나 법적 유효성에 관한 전문가 의견을 대체하지 않습니다."
        ),
    )


def render_markdown(report: EvaluationReport) -> str:
    lines = [
        f"# 명세서 품질 평가: {report.case_id}",
        "",
        f"- 결과: **{'PASS' if report.passed else 'FAIL'}**",
        f"- 총점: **{report.total_score}/100 ({report.grade})**",
        f"- Rubric: `{report.rubric_version}`",
        f"- 생성 모델: `{report.generator_model}`",
        f"- Judge 모델: `{report.judge_model}`",
        f"- Judge 신뢰도: `{report.judge.confidence}`",
        "",
        "## 항목별 점수",
        "",
        "| 항목 | 점수 | 판단 요약 |",
        "|---|---:|---|",
    ]
    for criterion in report.judge.criteria:
        reason = criterion.reason.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {criterion.criterion_id} | {criterion.score}/{criterion.max_score} | {reason} |"
        )

    lines.extend(["", "## 최종 판단", ""])
    lines.extend(f"- {reason}" for reason in report.decision_reasons)

    if report.mechanical.critical_failures:
        lines.extend(["", "## 기계적 중대 실패", ""])
        lines.extend(f"- {item}" for item in report.mechanical.critical_failures)
    if report.judge.critical_failures:
        lines.extend(["", "## Judge 중대 실패", ""])
        lines.extend(f"- {item.description}" for item in report.judge.critical_failures)
    if report.judge.agent_issues:
        lines.extend(["", "## Agent 문제", ""])
        lines.extend(f"- {item.description}" for item in report.judge.agent_issues)
    if report.judge.input_gaps:
        lines.extend(["", "## 입력 자료 부족", ""])
        lines.extend(f"- {item.description}" for item in report.judge.input_gaps)

    lines.extend(["", "## 평가 요약", "", report.judge.summary, "", f"> {report.legal_notice}"])
    return "\n".join(lines) + "\n"


def save_report(report: EvaluationReport, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    stem = f"{report.case_id}-{timestamp}"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    json_path.write_text(
        json.dumps(report.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def save_candidate_checkpoint(
    case_id: str,
    candidate: dict[str, Any],
    output_dir: Path,
) -> Path:
    """Persist a generated candidate before Judge evaluation can fail."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = output_dir / f"{case_id}-{timestamp}-candidate.json"
    path.write_text(
        json.dumps(candidate, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def print_terminal_report(report: EvaluationReport) -> None:
    """Show the complete useful result without requiring report files."""
    criterion_names = {criterion["id"]: criterion["name"] for criterion in CRITERIA}

    print(
        f"\n{report.case_id}: "
        f"{'PASS' if report.passed else 'FAIL'} {report.total_score}/100 ({report.grade})"
    )
    print("\n항목별 점수")
    for criterion in report.judge.criteria:
        name = criterion_names.get(criterion.criterion_id, criterion.criterion_id)
        print(f"- {name}: {criterion.score}/{criterion.max_score} — {criterion.reason}")

    print("\n최종 판단")
    for reason in report.decision_reasons:
        print(f"- {reason}")

    if report.mechanical.warnings:
        print("\n기계적 검사 경고")
        for warning in report.mechanical.warnings:
            print(f"- {warning}")
    if report.judge.agent_issues:
        print("\nAgent 문제")
        for issue in report.judge.agent_issues:
            print(f"- {issue.description}")
    if report.judge.input_gaps:
        print("\n입력 자료 부족")
        for gap in report.judge.input_gaps:
            print(f"- {gap.description}")

    print(f"\nJudge 요약\n{report.judge.summary}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    load_dotenv(ROOT_DIR / ".env")
    case = load_case(args.case)

    candidate: dict[str, Any] | None = None
    if args.candidate:
        candidate = unwrap_candidate(load_json(args.candidate))

    if args.dry_run:
        print(f"case OK: {case.case_id} ({case.technology_profile}, filing_date={case.filing_date})")
        if candidate is not None:
            mechanical = collect_mechanical_findings(case, candidate)
            print(f"candidate sections checked: {len(SPECIFICATION_SECTIONS)}")
            print(f"mechanical critical={len(mechanical.critical_failures)}, warnings={len(mechanical.warnings)}")
            build_judge_messages(case, candidate)
            print("judge prompt serialization OK")
        else:
            print("candidate omitted: live run will generate a specification before judging")
        return 0

    try:
        if candidate is None:
            stage = "명세서 생성"
            started_at = print_stage(
                f"[1/3] Specification Agent로 명세서 생성 중 "
                f"(API timeout={args.api_timeout:g}초)..."
            )
            candidate, generator_model = generate_candidate(
                case,
                args.generator_model,
                args.api_timeout,
            )
            print_elapsed(started_at)
            candidate_source = "generated"
            if args.save:
                checkpoint_path = save_candidate_checkpoint(
                    case.case_id,
                    candidate,
                    args.output_dir,
                )
                print(f"  Candidate checkpoint: {checkpoint_path}", flush=True)
        else:
            stage = "candidate 로드"
            started_at = print_stage(f"[1/3] 저장된 명세서 불러옴: {args.candidate}")
            generator_model = args.generator_model or "pre-generated"
            candidate_source = str(args.candidate)
            print_elapsed(started_at)

        stage = "기계적 검사"
        started_at = print_stage("[2/3] 필수 섹션과 기존 validation 결과 검사 중...")
        mechanical = collect_mechanical_findings(case, candidate)
        print_elapsed(started_at)

        stage = "LLM Judge 평가"
        judge_config = JudgeConfig(
            model=args.judge_model or "",
            timeout_seconds=args.api_timeout,
        )
        started_at = print_stage(
            f"[3/3] LLM Judge 평가 중 "
            f"(model={judge_config.model}, API timeout={args.api_timeout:g}초)..."
        )
        judge_result = judge_specification(case, candidate, config=judge_config)
        print_elapsed(started_at)
    except KeyboardInterrupt:
        print(f"\n{stage}을(를) 사용자가 중단했습니다.", file=sys.stderr, flush=True)
        return 130
    except Exception as exc:
        print(format_failure(stage, exc), file=sys.stderr, flush=True)
        return 2

    report = finalize_report(
        case=case,
        specification=candidate,
        candidate_source=candidate_source,
        generator_model=generator_model,
        judge_model=judge_config.model,
        mechanical=mechanical,
        judge=judge_result,
    )

    print_terminal_report(report)

    if args.save:
        json_path, markdown_path = save_report(report, args.output_dir)
        print(f"JSON report: {json_path}")
        print(f"Markdown report: {markdown_path}")
    else:
        print("\n평가 파일은 저장하지 않았습니다. 저장이 필요하면 --save를 사용하세요.")

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
