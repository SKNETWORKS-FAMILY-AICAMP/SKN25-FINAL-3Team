import os
import textwrap
import graphviz
import logging
from typing import List
import os
from django.conf import settings
import uuid

# state.py에서 PyPI 플랫폼의 공통 스키마를 불러옵니다.
from agents.core.state import (
    ParsedInvention, 
    PatentDrawing, 
    ReferenceMapping, 
    PatentDrawingSpecification
)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# =========================================================
# Smart Drawing Agent (Graphviz 렌더링 엔진)
# =========================================================
class SmartDrawingAgent:
    def __init__(self):
        self.output_dir = os.path.join(settings.MEDIA_ROOT, "drawings")
        os.makedirs(self.output_dir, exist_ok=True)
        self.font_name = 'NanumGothic' # (윈도우용)

    def run(self, state: dict) -> dict:
        parsed_data: ParsedInvention = state.get("summary_data")
        if not parsed_data:
            logger.error("summary_data가 존재하지 않습니다.")
            return {"drawing_spec": None}

        drawings = []
        reference_list: List[ReferenceMapping] = []

        logger.info("도 1 (시스템 구성도) 생성을 시작합니다...")
        sys_drawing = self._build_system_block_diagram(parsed_data, "도 1", reference_list)
        drawings.append(sys_drawing)

        logger.info("도 2 (방법 흐름도) 생성을 시작합니다...")
        flow_drawing = self._build_method_flowchart(parsed_data, "도 2", reference_list)
        drawings.append(flow_drawing)

        return {
            "drawing_spec": PatentDrawingSpecification(
                drawings=drawings,
                reference_numerals=reference_list
            )
        }

    def _build_system_block_diagram(self, parsed_data: ParsedInvention, fig_no: str, ref_list: List[ReferenceMapping]) -> PatentDrawing:
        dot = graphviz.Digraph(comment='System Block Diagram')
        dot.attr(rankdir='LR', fontname=self.font_name, dpi='300') 
        dot.attr('node', shape='rect', style='rounded', fontname=self.font_name, margin='0.3,0.1')
        dot.attr('edge', fontname=self.font_name, fontsize='10')

        # 시스템 경계를 나타내는 클러스터(서브그래프)
        with dot.subgraph(name='cluster_system') as c:
            c.attr(label=f"전체 시스템 (100)", fontname=self.font_name, style='dashed', color='black')
            
            # 노드 생성 및 부호 매핑
            for idx, comp in enumerate(parsed_data.architecture.components):
                numeral = str(110 + (idx * 10))
                label = f"{comp.name}\n({numeral})"
                c.node(comp.id, label)
                
                # 다음 에이전트(명세서 작성)를 위한 명부 기록
                ref_list.append(ReferenceMapping(component_id=comp.id, name=comp.name, numeral=numeral))

        # 엣지(데이터 흐름) 연결
        for flow in parsed_data.architecture.data_flows:
            if flow.source != "INPUT" and flow.target != "OUTPUT":
                dot.edge(flow.source, flow.target, label=flow.data_name)

        # 렌더링
        unique_id = uuid.uuid4().hex[:8]  
        file_name = f"system_block_fig1_{unique_id}"
        file_path = os.path.join(self.output_dir, file_name)
        dot.render(file_path, format='png', cleanup=True)

        return PatentDrawing(
            fig_no=fig_no,
            title=f"{parsed_data.invention_metadata.title} 구성도",
            diagram_type="BLOCK_DIAGRAM",
            dot_code=dot.source,
            image_path=f"{file_path}.png"
        )


    def _build_method_flowchart(self, parsed_data: ParsedInvention, fig_no: str, ref_list: List[ReferenceMapping]) -> PatentDrawing:
        dot = graphviz.Digraph(comment='Method Flowchart')
        dot.attr(rankdir='TB', fontname=self.font_name, dpi='300')
        
        # 💡 [수정 포인트 1] fixedsize='true' 속성을 추가하고 width, height를 인치(inch) 단위로 고정합니다.
        dot.attr('node', 
                 shape='box', 
                 fontname=self.font_name, 
                 fixedsize='true', 
                 width='3.5',       # 가로 크기 고정 (필요에 따라 조절)
                 height='1.0',      # 세로 크기 고정 (필요에 따라 조절)
                 margin='0.1')
        
        steps = sorted(parsed_data.architecture.processing_steps, key=lambda x: x.step_number)
        
        # 노드 생성
        for idx, step in enumerate(steps):
            step_id = f"S{210 + (idx * 10)}"
            node_id = f"STEP_{step.step_number}"
            
            # 💡 [수정 포인트 2] 텍스트가 박스를 뚫고 나가지 않도록 일정 글자 수(예: 18자) 기준으로 자동 줄바꿈(\n) 처리
            wrapped_desc = "\n".join(textwrap.wrap(step.action_description, width=18))
            label = f"{wrapped_desc}\n({step_id})"
            
            dot.node(node_id, label)
            
            # 명부 기록 (흐름도 단계 부호)
            ref_list.append(ReferenceMapping(component_id=node_id, name=step.action_description, numeral=step_id))

        # 시간 순서에 따른 화살표 연결
        for i in range(len(steps) - 1):
            dot.edge(f"STEP_{steps[i].step_number}", f"STEP_{steps[i+1].step_number}")

        # 렌더링
        unique_id = uuid.uuid4().hex[:8]
        file_name = f"method_flow_fig2_{unique_id}"
        file_path = os.path.join(self.output_dir, file_name)
        dot.render(file_path, format='png', cleanup=True)

        return PatentDrawing(
            fig_no=fig_no,
            title=f"{parsed_data.invention_metadata.title} 방법 흐름도",
            diagram_type="FLOWCHART",
            dot_code=dot.source,
            image_path=f"{file_path}.png"
        )



# =========================================================
# 단독 실행 테스트 (Mock Data)
# =========================================================
if __name__ == "__main__":
    # 제공된 Mock 데이터
    mock_invention_dict = {
      "invention_metadata": {"title": "음성 인식 기반 레시피 추천 시스템", "category": "SYSTEM"},
      "technical_context": {
        "problem_to_solve": "기존 시스템이 재료의 유통기한을 고려하지 않아 유통기한 임박 재료를 우선적으로 소진하는 레시피 추천이 어렵다는 문제",
        "expected_effect": "음식물 쓰레기를 감소시키고 사용자 편의성을 증대하는 효과"
      },
      "architecture": {
        "components": [
          {"id": "COMP_001", "name": "음성 입력부", "type": "MODULE", "description": "사용자의 음성 명령을 수신"},
          {"id": "COMP_002", "name": "음성 인식 모듈", "type": "MODULE", "description": "음성을 텍스트로 변환"},
          {"id": "COMP_003", "name": "유통기한 대조 모듈", "type": "MODULE", "description": "임박 재료 식별"},
          {"id": "COMP_004", "name": "레시피 생성 모듈", "type": "MODULE", "description": "우선 소진 레시피 빌드"},
          {"id": "COMP_005", "name": "유통기한 DB", "type": "DATABASE", "description": "유통기한 정보 저장"}
        ],
        "data_flows": [
          {"flow_id": "FLOW_001", "source": "INPUT", "target": "COMP_001", "data_name": "사용자 음성 입력"},
          {"flow_id": "FLOW_002", "source": "COMP_001", "target": "COMP_002", "data_name": "음성 신호"},
          {"flow_id": "FLOW_003", "source": "COMP_002", "target": "COMP_003", "data_name": "음성 인식 텍스트"},
          {"flow_id": "FLOW_004", "source": "COMP_003", "target": "COMP_004", "data_name": "유통기한 임박 재료 정보"},
          {"flow_id": "FLOW_005", "source": "COMP_005", "target": "COMP_003", "data_name": "유통기한 정보"},
          {"flow_id": "FLOW_006", "source": "COMP_004", "target": "OUTPUT", "data_name": "추천 결과"}
        ],
        "processing_steps": [
          {"step_number": 1, "subject_id": "COMP_001", "action_description": "음성 입력 수신 단계", "input_data_ids": ["FLOW_001"], "output_data_ids": ["FLOW_002"]},
          {"step_number": 2, "subject_id": "COMP_002", "action_description": "텍스트 인식 단계", "input_data_ids": ["FLOW_002"], "output_data_ids": ["FLOW_003"]},
          {"step_number": 3, "subject_id": "COMP_003", "action_description": "임박 재료 추출 단계", "input_data_ids": ["FLOW_003", "FLOW_005"], "output_data_ids": ["FLOW_004"]},
          {"step_number": 4, "subject_id": "COMP_004", "action_description": "레시피 생성 단계", "input_data_ids": ["FLOW_004"], "output_data_ids": ["FLOW_006"]}
        ]
      }
    }

    # 데이터 객체화 (state.py의 ParsedInvention 스키마 검증 통과)
    parsed_invention_obj = ParsedInvention.model_validate(mock_invention_dict)
    mock_state = {"summary_data": parsed_invention_obj}

    # 에이전트 구동
    print("🚀 [PyPI Drawing Agent] Graphviz 엔진 렌더링 개시...")
    agent = SmartDrawingAgent()
    result = agent.run(mock_state)

    if result.get("drawing_spec"):
        spec: PatentDrawingSpecification = result["drawing_spec"]
        print("\n✅ 도면 생성 완료!")
        for dwg in spec.drawings:
            print(f"  - [{dwg.fig_no}] {dwg.title} -> 저장 위치: {dwg.image_path}")
        
        print("\n📋 [명세서 에이전트 전달용 도면부호 매핑 테이블]")
        for ref in spec.reference_numerals:
            print(f"  - {ref.numeral} : {ref.name}")