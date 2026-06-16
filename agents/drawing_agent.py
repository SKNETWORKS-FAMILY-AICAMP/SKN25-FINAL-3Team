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
        dot.attr('graph', pad='0.5', nodesep='0.8', ranksep='1.0')
        dot.attr('node', fontname=self.font_name, margin='0.3,0.15')
        dot.attr('edge', fontname=self.font_name, fontsize='9')

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

        # 엣지 필터링
        # 1. INPUT/OUTPUT 관련 제거
        # 2. 셀프 루프 제거 (source == target)
        # 3. 유효한 컴포넌트 ID 간 연결만 허용
        seen_edges = set()  # 중복 엣지 방지
        for flow in parsed_data.architecture.data_flows:
            src = flow.source
            tgt = flow.target

            if src == "INPUT" or tgt == "OUTPUT":
                continue
            if src == tgt:  # 셀프 루프 제거
                continue
            if src not in valid_ids or tgt not in valid_ids:  # 유효하지 않은 ID 제거
                continue

            edge_key = (src, tgt)
            if edge_key in seen_edges:  # 중복 엣지 제거
                continue

            seen_edges.add(edge_key)
            dot.edge(src, tgt)

        return self._render(dot, "system_block_fig1", fig_no,
                            f"{parsed_data.invention_metadata.title} 구성도",
                            "BLOCK_DIAGRAM")


    def _build_method_flowchart(
        self, parsed_data: ParsedInvention, fig_no: str, ref_list: List[ReferenceMapping]
    ) -> PatentDrawing:

        dot = graphviz.Digraph(comment='Method Flowchart')
        dot.attr(rankdir='TB', fontname=self.font_name, dpi='300')
        dot.attr('graph', pad='0.5', nodesep='0.6', ranksep='0.8')
        dot.attr('node', fontname=self.font_name)

        steps = sorted(parsed_data.architecture.processing_steps, key=lambda x: x.step_number)

        # 시작/종료 터미널 제거, 단계 노드만
        for idx, step in enumerate(steps):
            step_id = f"S{210 + idx * 10}"
            node_id = f"STEP_{step.step_number}"

            subject_comp = next(
                (c for c in parsed_data.architecture.components if c.id == step.subject_id),
                None
            )

            wrapped_desc = "\n".join(textwrap.wrap(step.action_description, width=20))

            if subject_comp:
                label = f"[{subject_comp.name}]\n{wrapped_desc}\n({step_id})"
            else:
                label = f"{wrapped_desc}\n({step_id})"

            dot.node(
                node_id, label,
                shape='box',
                style='rounded',
                fontname=self.font_name,
                fixedsize='true',
                width='3.8',
                height='1.2',
                margin='0.1'
            )

            ref_list.append(ReferenceMapping(
                component_id=node_id,
                name=step.action_description,
                numeral=step_id
            ))

        # 단계 간 화살표만 (시작/종료 터미널 없음)
        for i in range(len(steps) - 1):
            dot.edge(
                f"STEP_{steps[i].step_number}",
                f"STEP_{steps[i + 1].step_number}"
            )

        return self._render(dot, "method_flow_fig2", fig_no,
                            f"{parsed_data.invention_metadata.title} 방법 흐름도",
                            "FLOWCHART")

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