# test_run.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))



import json
from dotenv import load_dotenv
from agents.core.state import PatentState, ParsedInvention 
from agents.core.graph import build_patent_graph

# 환경변수(API 키 등) 로드
load_dotenv()

# 1. 꽉 채워진 가짜(Mock) 데이터 딕셔너리
mock_parsed_dict = {
    "invention_metadata": {
        "title": "음성 인식 기반 레시피 추천 시스템",
        "category": "SYSTEM"
    },
    "technical_context": {
        "problem_to_solve": "기존 시스템이 재료의 유통기한을 고려하지 않아 레시피 추천이 어려운 문제",
        "expected_effect": "음식물 쓰레기 감소 효과"
    },
    "architecture": {
        "components": [
            {"id": "COMP_001", "name": "음성 입력부", "type": "MODULE", "description": "음성 수신"},
            {"id": "COMP_002", "name": "레시피 생성부", "type": "MODULE", "description": "레시피 생성"}
        ],
        "data_flows": [
            {"flow_id": "FLOW_001", "source": "INPUT", "target": "COMP_001", "data_name": "사용자 음성"},
            {"flow_id": "FLOW_002", "source": "COMP_001", "target": "COMP_002", "data_name": "음성 텍스트"},
            {"flow_id": "FLOW_003", "source": "COMP_002", "target": "OUTPUT", "data_name": "최종 레시피"}
        ],
        "processing_steps": [
            {
                "step_number": 1,
                "subject_id": "COMP_001",
                "action_description": "사용자 음성을 수신하는 단계",
                "input_data_ids": ["FLOW_001"],
                "output_data_ids": ["FLOW_002"]
            },
            {
                "step_number": 2,
                "subject_id": "COMP_002",
                "action_description": "음성 텍스트를 바탕으로 레시피를 생성하는 단계",
                "input_data_ids": ["FLOW_002"],
                "output_data_ids": ["FLOW_003"]
            }
        ]
    }
}

if __name__ == "__main__":
    print("🚀 [테스트] 청구항 생성 에이전트 가동을 시작합니다...")

    # 2. 딕셔너리를 Pydantic 객체로 변환
    mock_parsed_data = ParsedInvention.model_validate(mock_parsed_dict)

    # 3. 초기 State 구성
    initial_state: PatentState = {
        "mock_input_data": {},
        "summary_data": mock_parsed_data, 
        "claims_data": None,
        "examiner_data": None,
        "drawing_spec": None
    }

    # 4. 방금 심플하게 바꾼 그래프 컴파일 및 실행!
    graph = build_patent_graph()
    
    print("⏳ AI가 열심히 청구항을 쥐어짜고 있습니다. 잠시만 기다려주세요...\n")
    result_state = graph.invoke(initial_state)

    # 5. 결과 확인
    print("="*60)
    print("🎉 [생성된 청구항 결과] 🎉")
    print("="*60)
    
    if result_state.get("claims_data"):
        claims = result_state["claims_data"]["claims"]
        for c in claims:
            dep_type = "[종속항]" if c["is_dependent"] else "[독립항]"
            print(f"[{c['claim_no']}항] {dep_type} 카테고리: {c['category']}")
            print(f"{c['content']}\n")
    else:
        print("❌ 청구항 생성에 실패했습니다.")