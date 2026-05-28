import os
from dotenv import load_dotenv

# 1. 🌟 환경 변수 로드 (이 한 줄이 LangSmith를 깨웁니다)
load_dotenv()

from graph import build_patent_graph

def main():
    # 2. 그래프 빌드
    app = build_patent_graph()
    
    # 3. Mock Data 준비
    mock_data = {
        "title": "음성 인식 기반 레시피 추천 시스템",
        "prior_art_problem": "기존 시스템은 재료의 유통기한을 고려하지 않음",
        "problem_to_solve": "유통기한 임박 재료를 우선 소진하는 레시피 추천",
        "core_tech": "사용자 음성 입력 -> STT 모듈 -> 유통기한 DB 대조 -> LLM 레시피 생성",
        "expected_effect": "음식물 쓰레기 감소 및 사용자 편의성 증대"
    }
    
    # 4. 그래프 실행 (LangSmith로 모든 과정이 자동 추적됨)
    print("🚀 명세서 작성 파이프라인 실행 중...")
    result = app.invoke({"mock_input_data": mock_data})
    
    print("\n✅ 최종 결과:")
    # 필요에 따라 결과 출력
    if result.get("examiner_data") and result["examiner_data"]["is_approved"]:
        print("심사 통과 및 청구항 작성 완료!")
    else:
        print("최종 거절 (루프 초과)")

if __name__ == "__main__":
    main()


# # .env 파일
# # LangSmith 추적 활성화
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
# LANGCHAIN_API_KEY="ls__여기에_발급받은_API키_입력"

# # 프로젝트 이름 (LangSmith 대시보드에 표시될 이름)
# LANGCHAIN_PROJECT="PyPI_Patent_Drafting"

# # 선택사항: OpenAI API 키 (에이전트들이 gpt-4o 등을 쓸 때 필요)
# OPENAI_API_KEY="sk-..."