#!/usr/bin/env bash
# Smoke test: 실제 서버에 HTTP 요청을 날려 핵심 엔드포인트가 살아있는지 확인
#
# Usage:
#   ./scripts/smoke_test.sh
#   DJANGO_URL=http://localhost:8000 FASTAPI_URL=http://localhost:8080 ./scripts/smoke_test.sh

set -euo pipefail

DJANGO_URL="${DJANGO_URL:-http://localhost:8000}"
FASTAPI_URL="${FASTAPI_URL:-http://localhost:8080}"

# 테스트용 계정 (Django에 이미 있거나 없으면 signup 단계에서 생성)
SMOKE_USER="${SMOKE_USER:-smoketest_$(date +%s)}"
SMOKE_PASS="${SMOKE_PASS:-SmokePw123!}"

# ── 색상 ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

PASS=0
FAIL=0

pass() { echo -e "  ${GREEN}✓${RESET} $*"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}✗${RESET} $*"; FAIL=$((FAIL+1)); }
info() { echo -e "${CYAN}▶${RESET} $*"; }
sep()  { echo -e "${BOLD}─────────────────────────────────────────${RESET}"; }

# ── curl helper ─────────────────────────────────────────────────────────────
# check <label> <expected_status> <actual_status> [body]
check() {
  local label="$1" expected="$2" actual="$3" body="${4:-}"
  if [[ "$actual" == "$expected" ]]; then
    pass "$label → $actual"
  else
    fail "$label → 기대 $expected, 실제 $actual  |  $body"
  fi
}

get()  { curl -s -o /dev/null -w "%{http_code}" "$@" 2>/dev/null || echo "000"; }
post() { curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" "$@" 2>/dev/null || echo "000"; }

get_body()  { curl -sf "$@" 2>/dev/null || echo "{}"; }
post_body() { curl -sf -X POST -H "Content-Type: application/json" "$@" 2>/dev/null || echo "{}"; }

# ── 서버 기동 대기 ────────────────────────────────────────────────────────────
wait_for() {
  local url="$1" name="$2" max=15 i=0
  info "$name 응답 대기 중..."
  while ! curl -sf "$url" > /dev/null 2>&1; do
    i=$((i+1))
    [[ $i -ge $max ]] && { fail "$name 응답 없음 ($url)"; return 1; }
    sleep 1
  done
  info "$name 응답 확인"
}

# ── [1] FastAPI ──────────────────────────────────────────────────────────────
echo ""
sep
echo -e "${BOLD}[FastAPI] $FASTAPI_URL${RESET}"
sep

wait_for "$FASTAPI_URL/health" "FastAPI"

# Health
body=$(get_body "$FASTAPI_URL/health")
status=$(get "$FASTAPI_URL/health")
check "GET /health" "200" "$status"

# runs — 존재하지 않는 run_id
status=$(get "$FASTAPI_URL/api/runs/nonexistent-smoke-id")
check "GET /api/runs/nonexistent → 404" "404" "$status"

# pipeline/run — body 없이 보내면 422 (validation error) 정상
status=$(post "$FASTAPI_URL/api/pipeline/run" -d '{}')
check "POST /api/pipeline/run (빈 body → 422)" "422" "$status"

# ── [2] Django ──────────────────────────────────────────────────────────────
echo ""
sep
echo -e "${BOLD}[Django] $DJANGO_URL${RESET}"
sep

wait_for "$DJANGO_URL/health/" "Django"

# Health
status=$(get "$DJANGO_URL/health/")
check "GET /health/" "200" "$status"

# Signup
SIGNUP_BODY=$(cat <<JSON
{
  "username": "$SMOKE_USER",
  "name":     "스모크테스터",
  "gender":   "M",
  "age":      25,
  "password":  "$SMOKE_PASS",
  "password2": "$SMOKE_PASS"
}
JSON
)
status=$(post "$DJANGO_URL/api/auth/signup/" -d "$SIGNUP_BODY")
# 201 = 신규 생성, 400 = 이미 존재 (재실행 시 정상)
if [[ "$status" == "201" || "$status" == "400" ]]; then
  pass "POST /api/auth/signup/ → $status"
else
  fail "POST /api/auth/signup/ → 기대 201/400, 실제 $status"
fi

# Login
LOGIN_BODY="{\"username\":\"$SMOKE_USER\",\"password\":\"$SMOKE_PASS\"}"
LOGIN_RESP=$(post_body "$DJANGO_URL/api/auth/login/" -d "$LOGIN_BODY")
ACCESS_TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access',''))" 2>/dev/null || echo "")

if [[ -n "$ACCESS_TOKEN" ]]; then
  pass "POST /api/auth/login/ → 토큰 획득"
else
  fail "POST /api/auth/login/ → 토큰 없음  |  $LOGIN_RESP"
fi

# Me (인증 필요)
if [[ -n "$ACCESS_TOKEN" ]]; then
  status=$(curl -sf -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$DJANGO_URL/api/auth/me/" 2>/dev/null || echo "000")
  check "GET /api/auth/me/ (JWT)" "200" "$status"
fi

# Logout (인증 필요)
if [[ -n "$ACCESS_TOKEN" ]]; then
  REFRESH_TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('refresh',''))" 2>/dev/null || echo "")
  LOGOUT_BODY="{\"refresh\":\"$REFRESH_TOKEN\"}"
  status=$(curl -sf -o /dev/null -w "%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "$LOGOUT_BODY" \
    "$DJANGO_URL/api/auth/logout/" 2>/dev/null || echo "000")
  check "POST /api/auth/logout/" "200" "$status"
fi

# ── 최종 요약 ──────────────────────────────────────────────────────────────
echo ""
sep
TOTAL=$((PASS+FAIL))
echo -e "${BOLD}결과: ${GREEN}${PASS}${RESET}/${TOTAL} 통과  ${RED}${FAIL}${RESET} 실패${RESET}"
echo ""

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
