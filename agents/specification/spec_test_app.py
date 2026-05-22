import json
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.specification import run_specification_agent, SpecificationAgentConfig
from agents.schemas.specification import SpecificationAgentOutput

st.title("Specification Agent 테스트")

uploaded_file = st.file_uploader("테스트용 state JSON 업로드", type=["json"])

model = st.text_input("모델명", value="gpt-5.1")

if uploaded_file:
    state = json.load(uploaded_file)
    
    if "drafting_options" not in state:
        state["drafting_options"] = {
            "use_subheadings_in_detailed_description": False,
            "brief_drawing_description": True,
            "strict_grounding": True,
            "avoid_reference_numerals_in_means": True
        }

    st.subheader("입력 정보 확인")
    st.write("발명 명칭:", state.get("consultation", {}).get("invention_title"))
    st.write("청구항 수:", len(state.get("claims", {}).get("draft_claims", [])))
    st.write("도면 수:", len(state.get("drawings", {}).get("figures", [])))

    if st.button("명세서 에이전트 실행"):
        config = SpecificationAgentConfig(model=model)

        with st.spinner("발명의 설명 파트 생성 중..."):
            raw_output = run_specification_agent(state, config=config)
            validated = SpecificationAgentOutput.model_validate(raw_output)

        st.subheader("생성 결과")

        st.markdown("### 기술분야")
        st.write(validated.technical_field)

        st.markdown("### 배경기술")
        st.write(validated.background_art)

        st.markdown("### 해결하려는 과제")
        st.write(validated.problem_to_solve)

        st.markdown("### 과제의 해결수단")
        st.write(validated.means_for_solving)

        st.markdown("### 발명의 효과")
        st.write(validated.effects)

        st.markdown("### 도면의 간단한 설명")
        st.write(validated.brief_description_of_drawings)

        st.markdown("### 발명을 실시하기 위한 구체적인 내용")
        st.write(validated.detailed_description)

        st.subheader("검증 결과")
        st.json(validated.details.get("validation", {}))

        st.subheader("Support Matrix")
        st.dataframe(validated.details.get("support_matrix", []))

        if "_evaluation_reference" in state:
            st.subheader("원문 발명의 설명 비교용 Reference")
            st.json(state["_evaluation_reference"])