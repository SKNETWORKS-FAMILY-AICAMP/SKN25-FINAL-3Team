# main.py
import os
import json
from dotenv import load_dotenv
from graph import app
from state import PatentState

# =========================================================
# 1. 환경변수 및 LangSmith 추적 설정
# =========================================================
load_dotenv()

# LangSmith 추적을 켜는 핵심 환경 변수들 (보통 .env에 넣지만 확인차 명시)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
# os.environ["LANGCHAIN_API_KEY"] = "ls__여기에_키_입력"
os.environ["LANGCHAIN_PROJECT"] = "PyPI_Patent_Drafting_V1"

def main():
    print("🚀 [PyPI] 자동 특허 명세서 파이프라인 가동을 시작합니다...\n")

    # 2. Mock 입력 데이터 구성
    mock_input_data = {
        "title": "음성 인식 기반 레시피 추천 시스템",
        "prior_art_problem": "기존 시스템은 재료의 유통기한을 고려하지 않음",
        "problem_to_solve": "유통기한 임박 재료를 우선 소진하는 레시피 추천",
        "core_tech": "사용자 음성 입력 -> STT 모듈 -> 유통기한 DB 대조 -> LLM 레시피 생성",
        "expected_effect": "음식물 쓰레기 감소 및 사용자 편의성 증대"
    }

    # 3. 초기 상태(Initial State) 세팅
    initial_state: PatentState = {
        "mock_input_data": mock_input_data,
        "summary_data": None,
        "claims_data": None,
        "examiner_data": None,
        "drawing_spec": None
    }

    # 4. 그래프 실행 (invoke)
    print("⏳ LangGraph 실행 중... (LangSmith 대시보드에서 실시간 확인 가능)")
    final_state = app.invoke(initial_state)

    # 5. 최종 결과 확인
    print("\n" + "="*60)
    print("🎉 [최종 파이프라인 실행 결과 요약] 🎉")
    print("="*60)

    # 파싱 결과 확인
    if final_state.get("summary_data"):
        print("✅ [Summary] 발명 구조화 파싱 완료!")

    # 도면 생성 확인
    if final_state.get("drawing_spec"):
        print(f"✅ [Drawing] 도면 {len(final_state['drawing_spec'].drawings)}개 생성 완료!")

    # 최종 청구항 확인 (보정이 일어났다면 보정된 결과가 여기에 덮어씌워짐)
    if final_state.get("claims_data"):
        print(f"✅ [Claim] 최종 청구항 {len(final_state['claims_data'].claims)}개 확보!")
        
    # 심사 결과 이력 확인
    if final_state.get("examiner_data"):
        is_approved = final_state["examiner_data"].is_approved
        rev_count = final_state["examiner_data"].revision_count
        print(f"✅ [Examiner] 심사 통과 여부: {is_approved} (수정 회차: {rev_count}회)")

    print("\n💡 자세한 입출력 프롬프트와 토큰 사용량은 LangSmith 웹 콘솔에서 확인하세요.")

if __name__ == "__main__":
    main()