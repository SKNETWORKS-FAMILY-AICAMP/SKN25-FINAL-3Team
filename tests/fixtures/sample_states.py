"""
테스트용 샘플 PatentAgentState 픽스처

각 테스트에서 직접 import하거나 conftest.py의 pytest fixture로 사용합니다.

사용법:
    from tests.fixtures.sample_states import (
        BASE_STATE,
        MID_CONVERSATION_STATE,
        LONG_CONVERSATION_STATE,
        POST_CONSULTING_STATE,
    )

멀티턴 대화 흐름:
    BASE_STATE (첫 메시지)
        → MID_CONVERSATION_STATE (2턴 진행, 아직 상담 중)
            → LONG_CONVERSATION_STATE (3턴 완료, 상담 종료 임박)
                → POST_CONSULTING_STATE (is_consultation_done=True 처리 완료)
"""

from typing import Any

# ── 최소 초기 상태 (consulting 노드 입력용) ────────────────────────────────────
BASE_STATE: dict[str, Any] = {
    "user_input": "IoT 센서를 이용한 스마트 주차 시스템입니다. "
                  "주차 공간마다 초음파 센서를 설치하고 실시간으로 빈자리 현황을 "
                  "중앙 서버에 전송하여 운전자 앱에 안내합니다.",
    "user_id": "test-user-001",
    "session_id": "test-session-001",
    # 이하 필드는 각 노드가 채움
    "is_consultation_done": False,
    "next_question": "",
    "invention_flow": "",
    "problem": "",
    "differentiation": "",
    "effect": "",
    "raw_conversation": [],
    "similar_patents": [],
    "ipc_codes": [],
    "claims": [],
    "is_registerable": None,
    "examiner_opinion": "",
    "examiner_issues": [],
    "revision_count": 0,
    "flowchart_code": "",
    "system_diagram_code": "",
    "background": "",
    "problem_statement": "",
    "solution": "",
    "drawing_description": "",
    "detailed_description": "",
}

# ── 대화 중반 상태 (2턴 진행, 아직 is_consultation_done=False) ──────────────────
MID_CONVERSATION_STATE: dict[str, Any] = {
    **BASE_STATE,
    "user_input": "초음파 센서입니다. 기존과 달리 AI로 빈자리를 예측해요.",
    "raw_conversation": [
        {"role": "user", "content": "IoT 센서를 이용한 스마트 주차 시스템입니다."},
        {"role": "assistant", "content": "어떤 센서를 사용하셨나요? 기존 시스템과의 차별점은 무엇인가요?"},
    ],
    "is_consultation_done": False,
    "next_question": "어떤 센서를 사용하셨나요? 기존 시스템과의 차별점은 무엇인가요?",
}

# ── 대화 충분 상태 (3턴, mock에서 is_consultation_done=True 반환 임박) ────────────
LONG_CONVERSATION_STATE: dict[str, Any] = {
    **BASE_STATE,
    "user_input": "주차 탐색 시간을 70% 줄일 수 있어요.",
    "raw_conversation": [
        {"role": "user", "content": "IoT 센서를 이용한 스마트 주차 시스템입니다."},
        {"role": "assistant", "content": "어떤 센서를 사용하셨나요?"},
        {"role": "user", "content": "초음파 센서입니다. AI로 빈자리를 예측해요."},
        {"role": "assistant", "content": "발명의 주요 효과나 기대 성능이 있으신가요?"},
        {"role": "user", "content": "주차 탐색 시간을 70% 줄일 수 있어요."},
        {"role": "assistant", "content": "감사합니다. 정보가 충분히 수집되었습니다."},
    ],
    "is_consultation_done": False,
    "next_question": "감사합니다. 정보가 충분히 수집되었습니다.",
}

# ── consulting 노드 완료 후 상태 (claims, patent_search 노드 입력용) ─────────────
POST_CONSULTING_STATE: dict[str, Any] = {
    **BASE_STATE,
    "is_consultation_done": True,
    "next_question": "상담이 완료되었습니다. 명세서 작성을 시작합니다.",
    "raw_conversation": LONG_CONVERSATION_STATE["raw_conversation"] + [
        {"role": "user", "content": "주차 탐색 시간을 70% 줄일 수 있어요."},
        {"role": "assistant", "content": "상담이 완료되었습니다. 명세서 작성을 시작합니다."},
    ],
    "invention_flow": "초음파 센서로 주차 공간 점유 여부 감지 → 중앙 서버 실시간 집계 → 모바일 앱으로 빈자리 안내",
    "problem": "기존 주차장은 실시간 빈자리 현황 파악이 불가능하여 운전자가 직접 순회해야 하고, 탐색 시간이 평균 8분 소요됨",
    "differentiation": "IoT 센서 기반 실시간 데이터 수집과 AI 예측 알고리즘으로 빈자리 발생을 사전에 예측하여 안내",
    "effect": "주차 탐색 시간 70% 감소, 불필요한 차량 순환으로 인한 탄소 배출 40% 저감",
}

# ── claims 노드 완료 후 상태 (examiner 노드 입력용) ───────────────────────────────
POST_CLAIMS_STATE: dict[str, Any] = {
    **POST_CONSULTING_STATE,
    "claims": [
        {
            "claim_number": 1,
            "claim_type": "method",
            "is_independent": True,
            "depends_on": 0,
            "content": "각 주차 공간에 설치된 초음파 센서로 점유 여부를 감지하는 단계; "
                       "감지 결과를 중앙 서버로 전송하는 단계; "
                       "서버에서 집계된 빈자리 정보를 모바일 앱으로 전송하는 단계를 포함하는 스마트 주차 안내 방법.",
        },
        {
            "claim_number": 2,
            "claim_type": "system",
            "is_independent": True,
            "depends_on": 0,
            "content": "각 주차 공간에 설치된 초음파 센서; "
                       "센서 데이터를 수집·집계하는 중앙 서버; "
                       "빈자리 정보를 표시하는 모바일 앱을 포함하는 스마트 주차 안내 시스템.",
        },
        {
            "claim_number": 3,
            "claim_type": "method",
            "is_independent": False,
            "depends_on": 1,
            "content": "제1항에 있어서, AI 예측 모델로 빈자리 발생 시점을 사전 예측하여 안내하는 단계를 더 포함하는 방법.",
        },
    ],
}

# ── examiner 완료 후 상태 (drawing 노드 입력용, 등록 가능 판정) ────────────────────
POST_EXAMINER_APPROVED_STATE: dict[str, Any] = {
    **POST_CLAIMS_STATE,
    "is_registerable": True,
    "examiner_opinion": "청구항 1~3은 신규성 및 진보성 요건을 충족하며 기재불비 사항 없음.",
    "examiner_issues": [],
}

# ── examiner 완료 후 상태 (등록 불가, claims 재시도용) ─────────────────────────────
POST_EXAMINER_REJECTED_STATE: dict[str, Any] = {
    **POST_CLAIMS_STATE,
    "is_registerable": False,
    "examiner_opinion": "청구항 1의 '초음파 센서' 구성이 선행특허 KR10-2022-0151974에 개시되어 신규성 결여.",
    "examiner_issues": [
        {"claim_number": 1, "reason": "신규성 결여 — KR10-2022-0151974 대비"},
    ],
    "revision_count": 1,
}
