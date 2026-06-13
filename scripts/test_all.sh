#!/usr/bin/env bash
# sh로 실행하면 배열 문법이 동작하지 않으므로 bash로 재실행
[ -z "$BASH_VERSION" ] && exec bash "$0" "$@"
# 전체 API 테스트 실행 스크립트
# Usage: ./scripts/test_all.sh [--fast] [--suite django|fastapi|agents]

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ── 색상 출력 ──────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

ok()   { echo -e "${GREEN}✓${RESET} $*"; }
fail() { echo -e "${RED}✗${RESET} $*"; }
info() { echo -e "${CYAN}▶${RESET} $*"; }
sep()  { echo -e "${BOLD}─────────────────────────────────────────${RESET}"; }

# ── 옵션 파싱 ──────────────────────────────────────────────────────────────
FAST=false
SUITE=""

for arg in "$@"; do
  case $arg in
    --fast)      FAST=true ;;
    --suite=*)   SUITE="${arg#*=}" ;;
    -h|--help)
      echo "Usage: $0 [--fast] [--suite django|fastapi|agents]"
      echo "  --fast          stdout 숨기고 결과만 표시 (-q)"
      echo "  --suite=<name>  특정 테스트 그룹만 실행"
      exit 0 ;;
    *) echo "Unknown option: $arg"; exit 1 ;;
  esac
done

PYTEST_OPTS=("--tb=short" "--no-header")
$FAST && PYTEST_OPTS+=("-q") || PYTEST_OPTS+=("-v")

# ── 가상환경 체크 ───────────────────────────────────────────────────────────
if [[ -d "$ROOT/.venv" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
  PYTEST="$ROOT/.venv/bin/pytest"
else
  PYTHON="$(command -v python3)"
  PYTEST="$(command -v pytest)"
fi

info "Python: $PYTHON"
info "pytest: $PYTEST"
sep

# ── 테스트 그룹 정의 ────────────────────────────────────────────────────────
suite_path() {
  case "$1" in
    django)  echo "tests/django" ;;
    fastapi) echo "tests/api" ;;
    agents)  echo "tests/agents" ;;
    *)       echo "" ;;
  esac
}

RESULTS=()
FAILED=0

run_suite() {
  local name="$1"
  local path="$2"

  echo ""
  echo -e "${BOLD}[ $name ]${RESET}"

  if [[ ! -d "$ROOT/$path" ]]; then
    echo -e "${YELLOW}  건너뜀: $path 디렉토리 없음${RESET}"
    RESULTS+=("SKIP  $name ($path)")
    return
  fi

  if "$PYTEST" "${PYTEST_OPTS[@]}" "$ROOT/$path" 2>&1; then
    ok "$name 통과"
    RESULTS+=("PASS  $name")
  else
    fail "$name 실패"
    RESULTS+=("FAIL  $name")
    FAILED=$((FAILED + 1))
  fi
}

# ── 실행 ───────────────────────────────────────────────────────────────────
if [[ -n "$SUITE" ]]; then
  path=$(suite_path "$SUITE")
  if [[ -z "$path" ]]; then
    echo "알 수 없는 suite: $SUITE (선택지: django fastapi agents)"
    exit 1
  fi
  run_suite "$SUITE" "$path"
else
  for suite in django fastapi agents; do
    run_suite "$suite" "$(suite_path "$suite")"
  done
fi

# ── 최종 요약 ───────────────────────────────────────────────────────────────
sep
echo ""
echo -e "${BOLD}결과 요약${RESET}"
for r in "${RESULTS[@]}"; do
  case "$r" in
    PASS*) echo -e "  ${GREEN}$r${RESET}" ;;
    FAIL*) echo -e "  ${RED}$r${RESET}" ;;
    SKIP*) echo -e "  ${YELLOW}$r${RESET}" ;;
  esac
done
echo ""

if [[ $FAILED -eq 0 ]]; then
  ok "모든 테스트 통과"
  exit 0
else
  fail "${FAILED}개 suite 실패"
  exit 1
fi
