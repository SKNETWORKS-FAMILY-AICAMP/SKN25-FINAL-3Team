import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------
# [핵심 수정] 프로젝트 루트 디렉토리를 sys.path에 동적으로 추가
# 현재 파일 위치: root/agents/prior_art_agent/prior_art_test.py
# parents[2]를 통해 'agents' 폴더를 감싸고 있는 'root' 폴더를 찾습니다.
# ---------------------------------------------------------
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

# 환경변수 로드 (.env 파일이 루트 폴더에 있다고 가정)
load_dotenv(project_root / ".env")

# 이제 파이썬이 'agents' 폴더를 정상적으로 인식하여 import가 가능합니다.
from agents.core.state import PatentState, ClaimResult
from agents.prior_art_agent.prior_art_agent import run_prior_art_agent

# ─────────────────────────────────────────────────────────────
# 1. 테스트용 청구항 데이터 셋업
# ─────────────────────────────────────────────────────────────

# [테스트 케이스 A]: AI 관련 청구항 -> 로컬 벡터 DB(pgvector) 호출 예상
AI_CLAIM = {
    "claims": [
        {
            "claim_no": 1,
            "is_dependent": False,
            "cited_claim_no": [],
            "category": "시스템",
            "content": (
                "복수의 사용자 댓글을 입력받는 입력부; 상기 복수의 사용자 댓글 각각을 "
                "의미 벡터로 변환하는 댓글 임베딩부; 상기 의미 벡터 간의 유사도를 산출하여 "
                "유사 댓글 그룹을 생성하는 군집화부; 및 상기 유사 댓글 그룹별로 대표 댓글을 "
                "생성하여 출력하는 대표 댓글 생성부를 포함하는 의미 기반 댓글 통합 시스템."
            )
        }
    ]
}

# [테스트 케이스 B]: 기계/물리 관련 청구항 -> 외부 API(KIPRIS) 호출 예상
NON_AI_CLAIM = {
    "claims": [
        {
            "claim_no": 1,
            "is_dependent": False,
            "cited_claim_no": [],
            "category": "시스템",
            "content": (
                "제1 부재 및 제2 부재를 포함하는 본체; 상기 제1 부재와 제2 부재 사이에 "
                "배치되어 충격을 흡수하는 탄성 댐퍼; 및 상기 탄성 댐퍼의 압축 변위를 "
                "측정하여 외부로 출력하는 스트레인 게이지를 포함하는 것을 특징으로 하는 "
                "충격 흡수 장치."
            )
        }
    ]
}

def create_mock_state(claim_dict: dict) -> PatentState:
    """테스트용 Mock State 생성기"""
    return {
        "mock_input_data": {},
        "summary_data": None,
        "claims_data": ClaimResult.model_validate(claim_dict),
        "prior_art_data": None,
        "examiner_data": None,
    }

# ─────────────────────────────────────────────────────────────
# 2. 실행 및 결과 검증
# ─────────────────────────────────────────────────────────────

def run_test():
    print("=" * 60)
    print("🚀 [TEST A] 인공지능 기술 선행기술조사 테스트 시작")
    print("=" * 60)
    state_a = create_mock_state(AI_CLAIM)
    result_a = run_prior_art_agent(state_a, top_n=3)
    
    print("\n[결과 A 요약]")
    if result_a.get("prior_art_data") and result_a["prior_art_data"].candidates:
        for c in result_a["prior_art_data"].candidates:
            print(f"- [{c.rank}위] {c.title[:30]}... (출원번호: {c.register_number})")
            print(f"  리스크 레벨: {c.risk_level}")
    else:
        print("- 검색 결과가 없습니다.")


    print("\n" + "=" * 60)
    print("🚀 [TEST B] 비-인공지능(기계) 기술 선행기술조사 테스트 시작")
    print("=" * 60)
    state_b = create_mock_state(NON_AI_CLAIM)
    result_b = run_prior_art_agent(state_b, top_n=3)
    
    print("\n[결과 B 요약]")
    if result_b.get("prior_art_data") and result_b["prior_art_data"].candidates:
        for c in result_b["prior_art_data"].candidates:
            print(f"- [{c.rank}위] {c.title[:30]}... (출원번호: {c.register_number})")
            print(f"  리스크 레벨: {c.risk_level}")
            print(f"  PDF 링크: {c.pdf_s3_url[:40]}...")
    else:
        print("- 검색 결과가 없습니다.")

if __name__ == "__main__":
    # 필수 환경변수 체크
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
    if not os.getenv("KIPRIS_API_KEY"):
        print("⚠️ KIPRIS_API_KEY가 설정되지 않았습니다.")
        
    run_test()