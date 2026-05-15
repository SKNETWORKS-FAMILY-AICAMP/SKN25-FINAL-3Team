#!/usr/bin/env python3
"""Graph-mediated claim drafting workflow for masked claim tests.

For each patent:
1. Use public invention context only (reference claims removed defensively).
2. Build invention brief + internal prior-art reconstruction.
3. Build an invention graph: components, edges, data flow, mandatory/optional judgement,
   low-confidence consultation questions.
4. Build claim plan from the graph.
5. Draft claims from the graph/plan.
6. Evaluate against reference claims by component/scope/right similarity.

External prior-art search is not performed; prior-art reconstruction is PDF-internal only.
"""
from __future__ import annotations

import argparse, json, os, textwrap
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

REPO_ROOT = Path(__file__).resolve().parents[2]
if load_dotenv:
    load_dotenv(REPO_ROOT / '.env')
    load_dotenv(REPO_ROOT / 'agents/consultation/.env', override=True)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def call_json(system: str, user: str, model: str) -> dict[str, Any]:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    resp = client.chat.completions.create(
        model=model,
        messages=[{'role':'system','content':system},{'role':'user','content':user}],
        response_format={'type':'json_object'},
    )
    txt = resp.choices[0].message.content or '{}'
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return json.loads(txt[txt.find('{'):txt.rfind('}')+1])


def compact_context(ctx: dict[str, str], max_chars: int = 18000) -> str:
    order=['title','abstract','technical_field','background','problem','solution','effect','drawing_brief','detailed_description_excerpt']
    out=[]; used=0
    for k in order:
        v=(ctx.get(k) or '').strip()
        if not v: continue
        b=f'[{k}]\n{v}'
        if used >= max_chars: break
        if used+len(b)>max_chars: b=b[:max_chars-used].rstrip()+' ...'
        out.append(b); used += len(b)
    return '\n\n'.join(out)


def sys(role: str) -> str:
    return f'''너는 한국 AI/소프트웨어 특허 문서를 분석하는 변리사형 {role}이다.
외부 검색을 수행했다고 주장하지 말고, 제공된 PDF 추출 context와 중간 산출물만 근거로 판단한다.
모든 판단에는 evidence/confidence/needs_review를 최대한 포함한다.
반드시 JSON만 출력한다.'''


def brief_prompt(row: dict[str, Any]) -> str:
    return f'''
[목표]
PDF 추출 context만으로 고품질 발명 설명과 문헌 내부 기반 선행기술 재구성을 작성하라.

[patent_id]
{row['patent_id']}

[context]
{compact_context(row.get('invention_context',{}))}

[출력 JSON]
{{
  "patent_id":"...",
  "invention_brief":{{"technical_field":"","problem":"","prior_art_limitations":[],"core_solution":"","core_components":[],"operation_flow":[],"technical_effects":[],"implementation_notes":[]}},
  "internal_prior_art_report":{{"scope_note":"PDF 내부 정보 기반, 외부 검색 아님","known_background_technologies":[],"limitations_or_pain_points":[],"evidence_from_context":[]}},
  "uncertainties":[]
}}
'''


def graph_prompt(row: dict[str, Any], brief: dict[str, Any]) -> str:
    return f'''
[목표]
청구항 생성 전에 필요한 관계/추론을 invention_graph로 구조화하라.
관계가 확실하지 않으면 needs_question=true와 상담형 질문을 작성하라. 질문은 발명가 부담을 줄이는 쉬운 말로 작성한다.

[중요]
- component hierarchy, data flow, input-processing-output, mandatory/optional judgement를 분리하라.
- PDF context에 구체 항목들이 한 세트로 열거되면 mandatory_candidate로 두고, 선택사항 근거가 있을 때만 optional_candidate로 둔다.
- 종속항 후보는 하위 모듈/계산부/학습모듈/통신부/알림/그래프화 등 세부 구현을 우선한다.

[public context]
{compact_context(row.get('invention_context',{}), 10000)}

[brief]
{json.dumps(brief, ensure_ascii=False, indent=2)[:20000]}

[출력 JSON]
{{
  "patent_id":"...",
  "component_graph":[{{"id":"C1","name":"","type":"module|data|processor|output|ui|communication|storage|unknown","parent_id":null,"children":[],"function":"","evidence":[],"confidence":0.0,"needs_review":false}}],
  "relation_edges":[{{"source":"","target":"","relation_type":"has_child|receives|stores|provides|processes|outputs|notifies|learns|calculates|uses","data_or_action":"","evidence":[],"confidence":0.0,"needs_question":false,"question":null}}],
  "data_flow_graph":[{{"step":1,"source":"","target":"","data":"","action":"","evidence":[],"confidence":0.0}}],
  "mandatory_optional_judgement":[{{"item":"","judgement":"mandatory_candidate|optional_candidate|uncertain","reason":"","evidence":[],"confidence":0.0,"needs_question":false,"question":null}}],
  "independent_claim_candidates":[{{"claim_form":"system/device|method|medium/program","must_include":[],"reason":"","confidence":0.0}}],
  "dependent_claim_candidates":[{{"parent_element":"","detail_element":"","suggested_role":"dependent","reason":"","evidence":[],"confidence":0.0}}],
  "top_followup_questions":[{{"target":"","question":"","why_needed":"","priority":1}}]
}}
'''


def plan_prompt(brief: dict[str, Any], graph: dict[str, Any]) -> str:
    return f'''
[목표]
invention_graph를 바탕으로 reference-like scope reconstruction 모드의 claim_plan을 작성하라.
넓은 포트폴리오 창작보다 PDF context의 구체 구성 결합과 종속항 세부구성 회복을 우선한다.

[금지/주의]
- 구체 열거항목을 임의로 '적어도 하나/둘 이상'으로 완화하지 말 것.
- 독립항 필수 구성은 종속항으로 밀어내지 말 것.
- dependent_claim_plan에는 graph의 dependent_claim_candidates를 최대한 반영할 것.

[brief]
{json.dumps(brief, ensure_ascii=False, indent=2)[:14000]}

[invention_graph]
{json.dumps(graph, ensure_ascii=False, indent=2)[:22000]}

[출력 JSON]
{{
  "patent_id":"...",
  "drafting_mode":"graph_based_reference_like_scope_reconstruction",
  "independent_claim_plan":[{{"claim_form":"system/device|method|medium/program","must_include_elements":[],"mandatory_elements_to_keep_together":[],"scope_note":""}}],
  "dependent_claim_plan":[{{"parent_claim_form":"","detail_element":"","target_parent_element":"","drafting_instruction":"","priority":1}}],
  "anti_broadening_rules":[],
  "terms_to_use_consistently":[],
  "claim_count_guidance":"",
  "uncertainties":[]
}}
'''


def claim_prompt(brief: dict[str, Any], graph: dict[str, Any], plan: dict[str, Any]) -> str:
    return f'''
[작업]
발명 설명 + invention_graph + claim_plan만 보고 한국 특허 청구항을 작성하라. 원본 청구항은 보지 않았다.

[작성모드]
graph_based_reference_like_scope_reconstruction. 관계/필수구성/종속항 후보를 최대한 충실히 반영한다.

[주의]
- 구체 항목 세트를 '적어도 하나/둘 이상'으로 임의 완화 금지.
- 독립항에는 component_graph의 핵심 상위구성 및 mandatory_candidate를 결합한다.
- 종속항에는 dependent_claim_plan의 세부 모듈/산출부/통신부/알림/그래프화 후보를 반영한다.

[brief]
{json.dumps(brief, ensure_ascii=False, indent=2)[:12000]}

[invention_graph]
{json.dumps(graph, ensure_ascii=False, indent=2)[:18000]}

[claim_plan]
{json.dumps(plan, ensure_ascii=False, indent=2)[:18000]}

[출력 JSON]
{{"patent_id":"...","claims":[{{"claim_no":1,"role":"independent|dependent","depends_on":[],"category":"method|system/device|medium/program|unknown","text":""}}],"strategy_note":"","uncertainties":[]}}
'''


def eval_prompt(brief: dict[str, Any], graph: dict[str, Any], plan: dict[str, Any], gen: dict[str, Any], key: dict[str, Any]) -> str:
    ref=[{"claim_no":c.get('claim_no'),"status":c.get('status'),"role":c.get('role'),"depends_on":c.get('depends_on'),"category":c.get('category'),"element_candidates":c.get('element_candidates',[])[:8],"text":c.get('text','')} for c in key.get('reference_claims',[])]
    rubric={"structure_fit":20,"core_element_coverage":25,"claim_scope_similarity":20,"dependent_claim_strategy":15,"spec_support":10,"patent_style":10,"risk_penalty":5}
    return f'''
[목표]
생성 청구항을 원본 reference와 비교하라. 문장 동일성이 아니라 구성요소, 권리범위, 요구권리, 독립항 필수구성, 종속항 전략을 평가한다.

[graph]
{json.dumps(graph, ensure_ascii=False, indent=2)[:12000]}
[claim_plan]
{json.dumps(plan, ensure_ascii=False, indent=2)[:12000]}
[generated]
{json.dumps(gen, ensure_ascii=False, indent=2)[:18000]}
[reference]
{json.dumps(ref, ensure_ascii=False, indent=2)[:24000]}
[rubric]
{json.dumps(rubric, ensure_ascii=False, indent=2)}

[출력 JSON]
{{"patent_id":"...","scores":{{"structure_fit":0,"core_element_coverage":0,"claim_scope_similarity":0,"dependent_claim_strategy":0,"spec_support":0,"patent_style":0,"risk_penalty":0,"total":0}},"component_match":[],"scope_match_judgement":"","good_points":[],"bad_points":[],"missing_core_elements":[],"overclaimed_or_unsupported_elements":[],"human_review_questions":[]}}
'''


def make_md(out_dir: Path, artifacts: dict[str, Any], key: dict[str, Any]) -> None:
    lines=[]
    pid=artifacts['generated'].get('patent_id') or key.get('patent_id')
    lines += [f'# Graph Claim Workflow Report: {pid}', '', '## 요약', '']
    ev=artifacts['evaluation']; scores=ev.get('scores',{})
    lines.append(f"- 평가점수: `{scores.get('total')}`")
    lines.append(f"- PDF: `{key.get('source_pdf')}`")
    lines.append('- 외부 검색 없음: PDF 내부 기반 선행기술 재구성')
    lines.append('- 생성 입력에는 reference_claims 제거')
    lines.append('')
    for title, name in [('1. 발명 설명/내부 prior-art','brief'),('2. Invention Graph','graph'),('3. Claim Plan','plan'),('4. 생성 청구항','generated'),('5. 원본 Reference','answer_key'),('6. 평가','evaluation')]:
        obj = key if name=='answer_key' else artifacts[name]
        lines += [f'## {title}', '', '```json', json.dumps(obj, ensure_ascii=False, indent=2), '```', '']
    lines += ['## Human Review Note', '```text', '전문 리뷰어 판단:', '- ', '관계/추론 graph 수정:', '- ', '청구항 수정:', '- ', '```']
    (out_dir/'graph_claim_workflow_report.md').write_text('\n'.join(lines), encoding='utf-8')


def run_one(row: dict[str, Any], key: dict[str, Any], out_dir: Path, model: str) -> dict[str, Any]:
    row={k:v for k,v in row.items() if k!='reference_claims'}
    od=out_dir/row['patent_id']; od.mkdir(parents=True, exist_ok=True)
    write_json(od/'00_public_no_reference.json', row); write_json(od/'00_answer_key.json', key)
    brief=call_json(sys('발명 구조화 분석가'), brief_prompt(row), model); write_json(od/'01_brief_internal_prior_art.json', brief)
    graph=call_json(sys('관계 그래프 추출/추론 에이전트'), graph_prompt(row, brief), model); write_json(od/'02_invention_graph.json', graph)
    plan=call_json(sys('청구항 설계 에이전트'), plan_prompt(brief, graph), model); write_json(od/'03_claim_plan.json', plan)
    gen=call_json(sys('청구항 작성 에이전트'), claim_prompt(brief, graph, plan), model); write_json(od/'04_generated_claims.json', gen)
    ev=call_json(sys('청구항 평가자'), eval_prompt(brief, graph, plan, gen, key), model); write_json(od/'05_evaluation.json', ev)
    artifacts={'brief':brief,'graph':graph,'plan':plan,'generated':gen,'evaluation':ev}
    make_md(od, artifacts, key)
    return {'patent_id':row['patent_id'], 'score':ev.get('scores',{}).get('total'), 'claim_count':len(gen.get('claims',[])), 'out_dir':str(od)}


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--public', type=Path, default=REPO_ROOT/'data/processed/claim_loop/g06f_claim_loop_v3_claim_end_category_fix_cohort4_public.jsonl')
    ap.add_argument('--answer-key', type=Path, default=REPO_ROOT/'data/processed/claim_loop/g06f_claim_loop_v3_claim_end_category_fix_cohort4_answer_key.jsonl')
    ap.add_argument('--patent-id', action='append')
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--out-dir', type=Path, default=REPO_ROOT/'data/reports/pdf_analysis/graph_claim_workflow_cohort4')
    ap.add_argument('--model', default=os.environ.get('OPENAI_MODEL') or 'gpt-5.5')
    args=ap.parse_args()
    rows=read_jsonl(args.public); keys={r['patent_id']:r for r in read_jsonl(args.answer_key)}
    if args.patent_id:
        rows=[r for r in rows if r['patent_id'] in set(args.patent_id)]
    if args.limit: rows=rows[:args.limit]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary=[]
    for r in rows:
        summary.append(run_one(r, keys[r['patent_id']], args.out_dir, args.model))
    write_json(args.out_dir/'summary.json', summary)
    print(json.dumps({'count':len(summary),'summary':summary}, ensure_ascii=False, indent=2))

if __name__=='__main__':
    main()
