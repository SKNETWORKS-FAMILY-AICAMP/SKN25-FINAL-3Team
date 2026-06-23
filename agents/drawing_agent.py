import os
import textwrap
import graphviz
import logging
from typing import List, Dict
import uuid
from django.conf import settings
from agents.core.state import (
    ParsedInvention,
    PatentDrawing,
    ReferenceMapping,
    PatentDrawingSpecification
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Component type별 스타일 - 흑백
COMPONENT_STYLES: Dict[str, Dict[str, str]] = {
    "MODULE":   {"shape": "rect",     "style": "rounded"},
    "NETWORK":  {"shape": "rect",     "style": "rounded"},
    "STEP":     {"shape": "diamond",  "style": ""},
    "DATABASE": {"shape": "cylinder", "style": ""},
}
DEFAULT_STYLE = {"shape": "rect", "style": "rounded"}


class SmartDrawingAgent:
    def __init__(self):
        self.output_dir = os.path.join(settings.MEDIA_ROOT, "drawings")
        os.makedirs(self.output_dir, exist_ok=True)
        self.font_name = 'NanumGothic'

    def run(self, state: dict) -> dict:
        parsed_data: ParsedInvention = state.get("summary_data")
        if not parsed_data:
            logger.error("summary_data가 존재하지 않습니다.")
            return {"drawing_spec": None}

        drawings = []
        reference_list: List[ReferenceMapping] = []

        logger.info("도 1 (시스템 구성도) 생성 시작...")
        drawings.append(self._build_system_block_diagram(parsed_data, "도 1", reference_list))

        logger.info("도 2 (방법 흐름도) 생성 시작...")
        drawings.append(self._build_method_flowchart(parsed_data, "도 2", reference_list))

        return {
            "drawing_spec": PatentDrawingSpecification(
                drawings=drawings,
                reference_numerals=reference_list
            )
        }

    # =========================================================
    # 도 1: 시스템 구성도
    # =========================================================
    def _build_system_block_diagram(
        self, parsed_data: ParsedInvention, fig_no: str, ref_list: List[ReferenceMapping]
    ) -> PatentDrawing:

        dot = graphviz.Digraph(comment='System Block Diagram')
        dot.attr(rankdir='TB', fontname=self.font_name, dpi='300')
        # splines 속성을 'polyline'으로 설정하여 직선적인 흐름 유지
        dot.attr('graph', pad='0.5', nodesep='0.8', ranksep='1.0', splines='polyline')
        dot.attr('node', fontname=self.font_name, margin='0.3,0.15')
        
        # --- [수정된 부분] 화살표 스타일 개선 ---
        # 선 두께(penwidth)를 늘리고, 글자 크기(fontsize)를 줄여 흐름을 강조하고 가독성 확보
        dot.attr('edge', fontname=self.font_name, fontsize='8', penwidth='1.5', arrowsize='0.8')

        # 유효한 컴포넌트 ID 집합
        valid_ids = {comp.id for comp in parsed_data.architecture.components}

        with dot.subgraph(name='cluster_system') as c:
            c.attr(
                label=f"{parsed_data.invention_metadata.title} (100)",
                fontname=self.font_name,
                style='dashed',
                color='black'
            )

            for idx, comp in enumerate(parsed_data.architecture.components):
                numeral = str(110 + idx * 10)
                style = COMPONENT_STYLES.get(comp.type.upper(), DEFAULT_STYLE)
                label = f"{comp.name}\n({numeral})"

                c.node(
                    comp.id, label,
                    shape=style["shape"],
                    style=style["style"],
                    fontname=self.font_name,
                )

                ref_list.append(ReferenceMapping(
                    component_id=comp.id,
                    name=comp.name,
                    numeral=numeral
                ))

        # --- 화살표 렌더링 로직 ---
        seen_edges = set()
        for flow in parsed_data.architecture.data_flows:
            src = flow.source
            tgt = flow.target
            data_name = flow.data_name

            if src == tgt:  # 셀프 루프 제거
                continue
            
            # INPUT, OUTPUT 등 외부 노드는 테두리 없는 텍스트로 생성
            if src not in valid_ids:
                dot.node(src, src, shape='plaintext', fontname=self.font_name, fontcolor='#555555')
            if tgt not in valid_ids:
                dot.node(tgt, tgt, shape='plaintext', fontname=self.font_name, fontcolor='#555555')

            edge_key = (src, tgt)
            if edge_key not in seen_edges:
                # 텍스트가 길 경우 10자 단위로 줄바꿈 (유지)
                wrapped_label = "\n".join(textwrap.wrap(data_name, width=10))
                
                # 라벨 앞뒤로 공백을 주어 선과 글자가 너무 붙지 않게 조정 (유지)
                dot.edge(src, tgt, label=f" {wrapped_label} ", fontname=self.font_name)
                seen_edges.add(edge_key)

        return self._render(dot, "system_block_fig1", fig_no,
                            f"{parsed_data.invention_metadata.title} 구성도",
                            "BLOCK_DIAGRAM")

    # =========================================================
    # 공통 렌더링 헬퍼
    # =========================================================
    def _render(
        self,
        dot: graphviz.Digraph,
        file_prefix: str,
        fig_no: str,
        title: str,
        diagram_type: str
    ) -> PatentDrawing:
        unique_id = uuid.uuid4().hex[:8]
        file_name = f"{file_prefix}_{unique_id}"
        file_path = os.path.join(self.output_dir, file_name)
        dot.render(file_path, format='png', cleanup=True)

        return PatentDrawing(
            fig_no=fig_no,
            title=title,
            diagram_type=diagram_type,
            dot_code=dot.source,
            image_path=f"{file_path}.png"
        )