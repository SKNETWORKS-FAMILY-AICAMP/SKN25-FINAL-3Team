#!/usr/bin/env python3
"""Claim-skeleton mediated drafting workflow.

Generalized flow:
public/no-reference context -> brief+internal prior-art -> relation router+graph -> claim skeleton
-> claim drafting -> evaluator against reference claims.

No external prior-art search. No domain-specific hardcoding.
"""
from __future__ import annotations
import argparse, json, os, re
from pathlib import Path
from typing import Any
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv=None
REPO_ROOT=Path(__file__).resolve().parents[2]
if load_dotenv:
    load_dotenv(REPO_ROOT/'.env')
    load_dotenv(REPO_ROOT/'agents/consultation/.env', override=True)

def read_jsonl(p:Path): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def write_json(p:Path,o:Any): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def call_json(system:str,user:str,model:str):
    from openai import OpenAI
    r=OpenAI(api_key=os.environ.get('OPENAI_API_KEY')).chat.completions.create(
        model=model,messages=[{'role':'system','content':system},{'role':'user','content':user}],response_format={'type':'json_object'})
    t=r.choices[0].message.content or '{}'
    try: return json.loads(t)
    except json.JSONDecodeError: return json.loads(t[t.find('{'):t.rfind('}')+1])

def compact(ctx:dict[str,str],max_chars=16000):
    order=['title','abstract','technical_field','background','problem','solution','effect','drawing_brief','detailed_description_excerpt']
    out=[]; used=0
    for k in order:
        v=(ctx.get(k) or '').strip()
        if not v: continue
        b=f'[{k}]\n{v}'
        if used+len(b)>max_chars: b=b[:max_chars-used].rstrip()+' ...'
        out.append(b); used+=len(b)
        if used>=max_chars: break
    return '\n\n'.join(out)

def sys(role):
    return f"""너는 한국 AI/소프트웨어 특허 문서를 분석하는 변리사형 {role}이다.
제공된 PDF 추출 context만 근거로 한다. 외부 검색을 수행했다고 주장하지 않는다.
모든 중간 판단에는 evidence/confidence/needs_review를 둔다. JSON만 출력한다."""

def prompt_brief(row):
    return f"""
[목표]
청구항을 보지 않는 public context만으로 발명 설명과 문헌 내부 기반 선행기술 재구성을 작성하라.

[patent_id] {row['patent_id']}
[context]
{compact(row.get('invention_context',{}),17000)}

[출력 JSON]
{{"patent_id":"","brief":{{"title":"","technical_field":"","problem":"","prior_art_limitations":[],"core_solution":"","core_components":[],"input_data":[],"processing_steps":[],"outputs":[],"technical_effects":[],"uncertainties":[]}},"internal_prior_art":{{"scope_note":"PDF 내부 정보 기반, 외부 검색 아님","background_technologies":[],"limitations":[],"evidence":[]}}}}
"""

def prompt_graph(row,brief):
    return f"""
[목표]
발명의 관계/추론을 일반화된 graph로 만든다. 특정 도메인 예시에 끌리지 말고 relation pattern을 먼저 라우팅하라.

[라우팅 후보]
protocol_message_sequence, parallel_pipeline, data_mapping_uri, ai_optimization, ui_interaction, sensor_control, model_training_inference, storage_indexing, generic_software_system

[relation_type 후보]
has_child, receives, stores, provides, processes, outputs, transmits, notifies, updates, requests, downloads, groups, maps_to, corresponds_to, runs_in_parallel, calculates, selects, compares, trains, infers, controls, validates, iterates

[중요]
- 구성요소 목록만 만들지 말고 관계/흐름/cardinality/대응관계를 보존한다.
- '적어도 N', '상이한', '병렬', '그룹화 후 전송', 'A에 대응하는 B' 같은 표현은 graph에 별도 보존한다.
- 애매하면 발명가에게 물을 top 질문 최대 3개만 만든다.

[public context]
{compact(row.get('invention_context',{}),11000)}
[brief]
{json.dumps(brief,ensure_ascii=False,indent=2)[:18000]}

[출력 JSON]
{{"patent_id":"","relation_route":{{"primary":"","secondary":[],"reason":"","confidence":0.0}},"component_graph":[{{"id":"C1","name":"","type":"module|data|processor|message|step|output|storage|ui|communication|model|unknown","parent_id":null,"children":[],"function":"","evidence":[],"confidence":0.0}}],"relation_edges":[{{"source":"","target":"","relation_type":"","data_or_action":"","cardinality_or_condition":"","evidence":[],"confidence":0.0,"needs_review":false}}],"data_flow":[{{"step":1,"source":"","target":"","data":"","action":"","condition":"","evidence":[],"confidence":0.0}}],"mandatory_optional":[{{"item":"","judgement":"mandatory_candidate|optional_candidate|uncertain","reason":"","evidence":[],"confidence":0.0,"question_if_uncertain":null}}],"dependent_detail_candidates":[{{"theme":"","parent_element":"","detail_elements":[],"merge_group_reason":"","evidence":[],"confidence":0.0}}],"top_followup_questions":[{{"priority":1,"target":"","question":"","why_needed":""}}]}}
"""

def infer_complexity_hint(row: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    """Cheap local policy hint. Does not look at reference claims."""
    ctx = row.get('invention_context', {}) or {}
    text = ' '.join(str(ctx.get(k, '')) for k in ['abstract','problem','solution','effect','drawing_brief','detailed_description_excerpt'])
    route = (graph.get('relation_route') or {}).get('primary', '')
    nodes = len(graph.get('component_graph') or [])
    edges = len(graph.get('relation_edges') or [])
    details = len(graph.get('dependent_detail_candidates') or [])
    data_flow = len(graph.get('data_flow') or [])
    signal_patterns = {
        'cardinality': r'적어도|이상|이하|복수|다수|각각|서로 다른|상이한|하나 이상|둘 이상',
        'parallel': r'병렬|동시에|동시|parallel|각각 수행',
        'protocol': r'요청|응답|전송|수신|송신|메시지|패킷|세션|프로토콜',
        'mapping': r'대응|매핑|연결|식별자|URI|URL|주소|인덱스|테이블',
        'ai_processing': r'학습|추론|모델|인공지능|AI|신경망|예측|분류|최적화'
    }
    signals = [name for name, pat in signal_patterns.items() if re.search(pat, text, re.I)]
    score = nodes + edges + details + data_flow + 2 * len(signals)
    if route in {'protocol_message_sequence','parallel_pipeline','data_mapping_uri','model_training_inference'}:
        score += 4
    if score <= 10:
        level, rng = 'simple', [4, 8]
    elif score <= 20:
        level, rng = 'medium', [8, 14]
    elif score <= 34:
        level, rng = 'complex', [14, 22]
    else:
        level, rng = 'very_complex', [20, 28]
    families = ['method']
    if re.search(r'시스템|장치|서버|단말|모듈|부|프로세서|메모리', text):
        families.append('system/device')
    if re.search(r'기록매체|저장매체|프로그램|명령어|컴퓨터 판독', text):
        families.append('medium/program')
    if route in {'protocol_message_sequence','parallel_pipeline'} and 'system/device' not in families:
        families.append('system/device')
    return {
        'complexity_level': level,
        'recommended_claim_count_range': rng,
        'signals': signals,
        'counts': {'graph_nodes': nodes, 'graph_edges': edges, 'dependent_detail_candidates': details, 'data_flow_steps': data_flow, 'score': score},
        'recommended_families': families,
        'policy_note': 'Do not use a fixed 4-8 or 6-claim cap. Claim count must scale with complexity and family count.'
    }

def prompt_claim_design(row, brief, graph):
    hint = infer_complexity_hint(row, graph)
    return f"""
[목표]
청구항 생성 전 중간산출물 claim_design을 만든다. 청구항 1을 최우선으로 설계하고, 이후 relation/family/dependent 범위를 잡는다.
원문 청구항은 보지 않는다. public context, brief, graph만 근거로 한다.

[원칙]
- 청구항 1은 발명의 핵심 구조/프로세스/권리범위를 담는 core independent claim이다.
- 길이보다 구성요소/단계/관계/조건 보존이 우선이다.
- 케이스는 다양하므로 method/system/medium 형태를 고정하지 말고, 필요한 family만 설계한다.
- 그래프DB가 아니라 JSON 관계정리 산출물이다. 짧고 명확하게 쓴다.

[local_complexity_hint]
{json.dumps(hint,ensure_ascii=False,indent=2)}
[brief]
{json.dumps(brief,ensure_ascii=False,indent=2)[:6000]}
[graph]
{json.dumps(graph,ensure_ascii=False,indent=2)[:12000]}

[출력 JSON]
{{"patent_id":"","claim1_core":{{"claim_form":"method|system/device|medium/program|unknown","core_subject":"","inputs":[],"essential_components":[],"essential_steps_or_functions":[],"data_objects":[],"relations":[],"cardinality_or_conditions":[],"outputs_or_effects":[],"must_not_drop":[]}},"family_plan":[{{"family":"method|system/device|medium/program","need":"required|optional|not_needed","mirror_from_claim1":true,"conversion_rule":""}}],"dependent_theme_candidates":[{{"theme":"","category":"implementation_environment|processing_detail|data_object|relation_condition|effect_purpose","parent_family_hint":"method|system/device|medium/program|any","elements":[],"why_needed":""}}],"claim_count_hint":{{"complexity_level":"","target_total_min":0,"target_total_max":0,"reason":""}},"uncertainties":[]}}
"""

def prompt_skeleton(row,brief,graph,design):
    hint = infer_complexity_hint(row, graph)
    return f"""
[목표]
claim skeleton을 만든다. 이것은 청구항 문장 전의 중간 산출물이다.
구성요소+관계+필수성+독립/종속 배치+청구항 수 제어를 명시한다.

[청구항 수 정책 - 중요]
- 고정 4~8항/6항 압축 금지. PDF/발명 복잡도에 따라 청구항 수가 달라져야 한다.
- simple은 4~8항, medium은 8~14항, complex는 14~22항, very_complex는 20~28항을 우선 검토한다.
- method/system-device/medium-program 같은 claim family가 필요하면 독립항 family를 분리한다.
- complex 이상에서 하나의 독립항과 소수 종속항으로 모든 관계를 압축하지 않는다.
- 세부 항목 하나당 종속항 하나를 기계적으로 만들지는 않되, 서로 다른 기술적 조건/효과/관계는 별도 종속항 후보로 보존한다.
- 독립항에는 핵심 상위 구성/핵심 단계/핵심 cardinality를 넣는다.
- 독립항 1은 가장 중요하다. 먼저 구성요소/단계/관계가 충분한지 판단하고, 그 다음 문체와 길이를 조정한다.
- system/device 및 medium/program family가 method family를 mirror하는 구조라면, method 독립항의 핵심 limitation을 각 family 독립항에도 변환해 반영한다.
- 종속항은 입력 세부, 처리 세부, 학습/계산 세부, 전송/출력 세부, mapping/cardinality/protocol 세부를 필요에 따라 분리한다.
- 도면 참조번호는 지금 단계에서 강제하지 않는다.
- 출력은 짧은 JSON만. 긴 설명/마크다운 작성 금지.

[local_complexity_hint]
{json.dumps(hint,ensure_ascii=False,indent=2)}

[claim_design]
{json.dumps(design,ensure_ascii=False,indent=2)[:10000]}

[brief]
{json.dumps(brief,ensure_ascii=False,indent=2)[:6000]}
[graph]
{json.dumps(graph,ensure_ascii=False,indent=2)[:10000]}

[출력 JSON]
{{"patent_id":"","claim_count_control":{{"complexity_level":"simple|medium|complex|very_complex","target_total_min":0,"target_total_max":0,"reason":"","required_families":[],"avoid_under_generation_rules":[],"avoid_over_generation_rules":[]}},"independent_skeletons":[{{"claim_no_hint":1,"claim_form":"system/device|method|medium/program","must_include_components":[],"must_include_relations":[],"must_preserve_cardinality_or_conditions":[],"relationship_flow":[],"scope_note":""}}],"dependent_skeletons":[{{"claim_no_hint":2,"depends_on_hint":1,"theme":"","grouped_elements":[],"relation_to_parent":"","drafting_instruction":"","merge_reason":""}}],"do_not_split_into_separate_claims":[],"uncertainties":[]}}
"""

def normalize_skeleton(row: dict[str, Any], graph: dict[str, Any], skeleton: dict[str, Any]) -> dict[str, Any]:
    """Guardrail after LLM skeleton: ensure count/family policy is not ignored."""
    if not isinstance(skeleton, dict):
        return skeleton
    hint = infer_complexity_hint(row, graph)
    ccc = skeleton.setdefault('claim_count_control', {})
    ccc.setdefault('complexity_level', hint['complexity_level'])
    ccc.setdefault('target_total_min', hint['recommended_claim_count_range'][0])
    ccc.setdefault('target_total_max', hint['recommended_claim_count_range'][1])
    ccc.setdefault('required_families', hint['recommended_families'])
    if not ccc.get('target_total_min') or int(ccc.get('target_total_min', 0)) < hint['recommended_claim_count_range'][0]:
        ccc['target_total_min'] = hint['recommended_claim_count_range'][0]
    if not ccc.get('target_total_max') or int(ccc.get('target_total_max', 0)) < int(ccc['target_total_min']):
        ccc['target_total_max'] = hint['recommended_claim_count_range'][1]
    required = list(dict.fromkeys((ccc.get('required_families') or []) + hint['recommended_families']))
    ccc['required_families'] = required
    indeps = skeleton.setdefault('independent_skeletons', [])
    deps = skeleton.setdefault('dependent_skeletons', [])
    existing_forms = {x.get('claim_form') for x in indeps if isinstance(x, dict)}
    next_no = 1
    for x in indeps + deps:
        if isinstance(x, dict) and isinstance(x.get('claim_no_hint'), int):
            next_no = max(next_no, x['claim_no_hint'] + 1)
    for fam in required:
        if fam not in existing_forms:
            indeps.append({
                'claim_no_hint': next_no,
                'claim_form': fam,
                'must_include_components': [],
                'must_include_relations': ['same invention core adapted to this claim family'],
                'must_preserve_cardinality_or_conditions': [],
                'relationship_flow': [],
                'scope_note': f'{fam} family must not be collapsed into another independent claim.'
            })
            existing_forms.add(fam); next_no += 1
    target_min = int(ccc.get('target_total_min') or 0)
    total = len(indeps) + len(deps)
    detail_sources = []
    for d in graph.get('dependent_detail_candidates') or []:
        detail_sources.append(('detail', d.get('theme') or d.get('parent_element') or 'dependent detail', d.get('detail_elements') or [], d.get('merge_group_reason') or ''))
    for e in graph.get('relation_edges') or []:
        rel = e.get('relation_type') or e.get('data_or_action') or 'relation detail'
        cond = e.get('cardinality_or_condition') or ''
        detail_sources.append(('relation', rel, [e.get('source'), e.get('target'), e.get('data_or_action'), cond], cond))
    for f in graph.get('data_flow') or []:
        detail_sources.append(('flow', f"flow step {f.get('step')}", [f.get('source'), f.get('target'), f.get('data'), f.get('action'), f.get('condition')], f.get('condition') or ''))
    if not detail_sources:
        detail_sources = [('detail', name, [], '') for name in hint['signals'] or ['input detail','processing detail','output detail','condition detail']]
    family_parent = {}
    for x in indeps:
        if isinstance(x, dict):
            family_parent[x.get('claim_form')] = x.get('claim_no_hint', 1)
    def choose_parent(theme: Any, elems: list[Any]) -> tuple[int, str]:
        s = ' '.join([str(theme)] + [str(e) for e in elems if e])
        if re.search(r'매체|프로그램|명령어|컴퓨터 판독|저장', s) and family_parent.get('medium/program'):
            return family_parent['medium/program'], 'medium/program'
        if re.search(r'시스템|장치|서버|단말|모듈|프로세서|회로|메모리|통신 경로', s) and family_parent.get('system/device'):
            return family_parent['system/device'], 'system/device'
        return family_parent.get('method') or (indeps[0].get('claim_no_hint', 1) if indeps else 1), 'method'
    i = 0
    while total < target_min:
        kind, theme, elems, reason = detail_sources[i % len(detail_sources)]
        elems = [x for x in elems if x]
        parent, parent_family = choose_parent(theme, elems)
        deps.append({
            'claim_no_hint': next_no,
            'depends_on_hint': parent,
            'parent_family': parent_family,
            'theme': str(theme)[:80],
            'grouped_elements': elems[:6],
            'relation_to_parent': f'Preserve {kind} from graph without over-compressing complex invention.',
            'drafting_instruction': f'Draft as a {parent_family} dependent claim. Do not change category away from parent family.',
            'merge_reason': reason or 'complexity-based claim count guardrail'
        })
        next_no += 1; total += 1; i += 1
    skeleton['_local_normalization'] = {
        'applied': True,
        'reason': 'LLM skeleton may under-generate; enforced complexity/family/count guardrail without using reference claims.',
        'hint': hint,
        'final_skeleton_items': len(indeps) + len(deps)
    }
    return skeleton

def prompt_claim(brief,graph,design,skeleton):
    ccc = skeleton.get('claim_count_control', {}) if isinstance(skeleton, dict) else {}
    target_min = int(ccc.get('target_total_min') or 0)
    target_max = int(ccc.get('target_total_max') or 0)
    return f"""
[작업]
claim skeleton만 충실히 따라 한국 특허 청구항을 작성하라.
이번 출력 claims 배열 길이는 반드시 {target_min}개 이상, {target_max}개 이하로 작성한다. {target_min}개 미만이면 실패다.

[제약]
- 우선순위는 길이가 아니라 구성요소/단계/관계 충실도다. 먼저 핵심 limitation을 빠뜨리지 말고, 그 다음 문체와 길이를 조정한다.
- 청구항 1이 가장 중요하다. 청구항 1에는 입력, 제1 처리, 제2 처리, 출력/효과, 핵심 cardinality/병렬 관계를 반드시 포함한다.
- skeleton의 target_total_min~target_total_max 범위를 지킨다. complex/very_complex인데 6항 내외로 압축하지 않는다.
- required_families가 있으면 각 family의 독립항을 분리한다. 단, independent_skeletons에 없는 추가 독립항을 만들지 않는다.
- 독립항 수는 claim_skeleton.independent_skeletons 개수와 동일해야 한다. 나머지는 모두 해당 family 독립항에 종속시키며, 새로운 발명군처럼 독립항을 추가하지 않는다.
- 모든 종속항은 반드시 "제N항에 있어서," 형식으로 시작하고 depends_on과 문장 내 제N항이 일치해야 한다.
- 종속항 category는 부모 독립항 family와 일치시킨다. 예: 제3항(system/device)에 종속되면 system/device 문장, 제4항(medium/program)에 종속되면 매체/프로그램 문장.
- medium/program 청구항은 장치 구성요소를 직접 "포함하는 매체"처럼 쓰지 말고, "명령어가 ... 단계를 수행하도록 하는 컴퓨터 판독가능 기록매체" 형태로 쓴다.
- system/device 청구항은 방법 단계 문장으로 끝내지 말고, 구성요소와 그 동작 관계를 recite한다.
- do_not_split_into_separate_claims 항목은 하나의 종속항/독립항 내부에 묶는다.
- 구체 열거항목을 임의로 '적어도 하나/둘 이상'으로 완화하지 않는다.
- 중복 종속항을 만들지 않는다. 같은 theme은 병합하되, 서로 다른 기술적 조건/효과/관계는 보존한다.
- 너무 얇은 종속항 금지: "복수의 입력을 제공"처럼 효과 없는 1문장 항은 조건/대상/처리결과를 결합해 한정한다.
- 도면 참조번호는 현재 청구항 단독 실험이므로 강제하지 않는다.
- 출력은 JSON만. 긴 해설/마크다운 작성 금지.

[brief]
{json.dumps(brief,ensure_ascii=False,indent=2)[:5000]}
[claim_design]
{json.dumps(design,ensure_ascii=False,indent=2)[:10000]}
[graph]
{json.dumps(graph,ensure_ascii=False,indent=2)[:6000]}
[claim_skeleton]
{json.dumps(skeleton,ensure_ascii=False,indent=2)[:20000]}

[출력 JSON]
{{"patent_id":"","claims":[{{"claim_no":1,"role":"independent|dependent","depends_on":[],"category":"method|system/device|medium/program|unknown","skeleton_theme":"","text":""}}],"strategy_note":"","uncertainties":[]}}
"""

def prompt_eval(graph,skeleton,gen,key):
    ref=[{k:c.get(k) for k in ['claim_no','status','role','depends_on','category','text']} for c in key.get('reference_claims',[])]
    return f"""
[목표]
생성 청구항을 reference 청구항과 비교한다. 문장 동일성보다 구성요소/관계/cardinality/권리범위/요구권리/청구항 수 전략을 평가한다.

[graph]
{json.dumps(graph,ensure_ascii=False,indent=2)[:10000]}
[skeleton]
{json.dumps(skeleton,ensure_ascii=False,indent=2)[:12000]}
[generated]
{json.dumps(gen,ensure_ascii=False,indent=2)[:16000]}
[reference]
{json.dumps(ref,ensure_ascii=False,indent=2)[:24000]}

[점수 기준]
모든 점수는 100점 만점 환산으로 출력한다. 각 하위 항목도 0~100 범위로 채점하고, total도 0~100 범위의 종합점수로 산출한다.

[출력 JSON]
{{"patent_id":"","scores":{{"structure_fit":0,"core_element_coverage":0,"relation_cardinality_preservation":0,"claim_scope_similarity":0,"claim_count_strategy":0,"dependent_claim_grouping":0,"patent_style":0,"risk_penalty":0,"total":0}},"good_points":[],"bad_points":[],"missing_core_elements":[],"overclaimed_or_unsupported_elements":[],"duplicate_or_over_split_claims":[],"human_review_questions":[]}}
"""

def make_md(od,arts,key,full: bool=False):
    """Default to compact markdown so API/report loops do not create 3000-line files."""
    if full:
        lines=[f"# Claim Skeleton Workflow Report: {key.get('patent_id')}","",f"- score: `{arts.get('evaluation',{}).get('scores',{}).get('total')}`",f"- pdf: `{key.get('source_pdf')}`","- reference claims hidden from generation; used only for evaluation",""]
        for title,name in [('1 brief','brief'),('2 graph','graph'),('3 claim_skeleton','skeleton'),('4 generated','generated'),('5 reference','key'),('6 evaluation','evaluation')]:
            obj=key if name=='key' else arts.get(name,{})
            lines += [f"## {title}","```json",json.dumps(obj,ensure_ascii=False,indent=2),"```",""]
    else:
        sk=arts.get('skeleton',{}) or {}; gen=arts.get('generated',{}) or {}; ev=arts.get('evaluation',{}) or {}
        ccc=sk.get('claim_count_control',{}) or {}
        claims=gen.get('claims',[]) or []
        ref=key.get('reference_claims',[]) or []
        indep=[c for c in claims if c.get('role')=='independent']
        dep=[c for c in claims if c.get('role')=='dependent']
        lines=[
            f"# Compact Claim Loop: {key.get('patent_id')}","",
            "## Count", 
            f"- reference_claims: {len(ref)}",
            f"- generated_claims: {len(claims)}",
            f"- generated_independent/dependent: {len(indep)}/{len(dep)}",
            f"- target_range: {ccc.get('target_total_min')}~{ccc.get('target_total_max')} ({ccc.get('complexity_level')})",
            f"- score: {ev.get('scores',{}).get('total') if ev else 'not_run'}","",
            "## Required families", 
            json.dumps(ccc.get('required_families',[]),ensure_ascii=False),"",
            "## Generated claim heads"
        ]
        for c in claims[:30]:
            txt=(c.get('text') or '').replace('\n',' ')
            lines.append(f"- {c.get('claim_no')} {c.get('role')} {c.get('category')}: {txt[:220]}")
        if ev:
            lines += ["", "## Evaluation bad points", *[f"- {x}" for x in ev.get('bad_points',[])[:10]], "", "## Missing core elements", *[f"- {x}" for x in ev.get('missing_core_elements',[])[:10]]]
    (od/'claim_skeleton_workflow_report.md').write_text('\n'.join(lines),encoding='utf-8')

def remove_from_stage(od: Path, stage: str):
    order = [
        ('brief', '01_brief.json'),
        ('graph', '02_graph.json'),
        ('design', '02b_claim_design.json'),
        ('skeleton', '03_claim_skeleton.json'),
        ('claims', '04_generated_claims.json'),
        ('eval', '05_evaluation.json'),
    ]
    active = False
    for name, fn in order:
        if name == stage:
            active = True
        if active:
            p = od / fn
            if p.exists():
                p.unlink()

def run(row,key,out_dir,model,force_from: str|None=None,run_eval: bool=False,full_report: bool=False):
    row={k:v for k,v in row.items() if k!='reference_claims'}
    od=out_dir/row['patent_id']; od.mkdir(parents=True,exist_ok=True)
    if force_from:
        remove_from_stage(od, force_from)
    write_json(od/'00_public_no_reference.json',row); write_json(od/'00_answer_key.json',key)
    def load_or_call(path: Path, role: str, prompt: str) -> dict[str, Any]:
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
        obj = call_json(sys(role), prompt, model)
        write_json(path, obj)
        return obj
    brief=load_or_call(od/'01_brief.json','발명 구조화 분석가',prompt_brief(row))
    graph=load_or_call(od/'02_graph.json','관계 라우터/그래프 추출가',prompt_graph(row,brief))
    design=load_or_call(od/'02b_claim_design.json','청구항 1 우선 설계자',prompt_claim_design(row,brief,graph))
    skeleton=load_or_call(od/'03_claim_skeleton.json','claim skeleton 설계자',prompt_skeleton(row,brief,graph,design))
    skeleton=normalize_skeleton(row,graph,skeleton)
    write_json(od/'03_claim_skeleton.json',skeleton)
    gen=load_or_call(od/'04_generated_claims.json','청구항 작성자',prompt_claim(brief,graph,design,skeleton))
    ev={}
    if run_eval:
        ev=load_or_call(od/'05_evaluation.json','청구항 평가자',prompt_eval(graph,skeleton,gen,key))
    elif (od/'05_evaluation.json').exists():
        ev=json.loads((od/'05_evaluation.json').read_text(encoding='utf-8'))
    make_md(od,{'brief':brief,'graph':graph,'skeleton':skeleton,'generated':gen,'evaluation':ev},key,full=full_report)
    ccc=skeleton.get('claim_count_control',{}) if isinstance(skeleton,dict) else {}
    return {'patent_id':row['patent_id'],'score':ev.get('scores',{}).get('total') if ev else None,'claims':len(gen.get('claims',[])),'target_min':ccc.get('target_total_min'),'target_max':ccc.get('target_total_max'),'complexity':ccc.get('complexity_level'),'out_dir':str(od)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--public',type=Path,required=True); ap.add_argument('--answer-key',type=Path,required=True)
    ap.add_argument('--patent-id',action='append'); ap.add_argument('--limit',type=int)
    ap.add_argument('--out-dir',type=Path,default=REPO_ROOT/'data/reports/pdf_analysis/claim_skeleton_workflow_test5')
    ap.add_argument('--model',default=os.environ.get('OPENAI_MODEL') or 'gpt-5.5')
    ap.add_argument('--force-from',choices=['brief','graph','design','skeleton','claims','eval'],help='Delete cached artifacts from this stage onward before running')
    ap.add_argument('--run-eval',action='store_true',help='Also call evaluator. Default skips evaluator to save API cost.')
    ap.add_argument('--full-report',action='store_true',help='Write old full markdown report. Default writes compact report only.')
    a=ap.parse_args(); rows=read_jsonl(a.public); keys={r['patent_id']:r for r in read_jsonl(a.answer_key)}
    if a.patent_id: rows=[r for r in rows if r['patent_id'] in set(a.patent_id)]
    if a.limit: rows=rows[:a.limit]
    out=[]
    for r in rows: out.append(run(r,keys[r['patent_id']],a.out_dir,a.model,force_from=a.force_from,run_eval=a.run_eval,full_report=a.full_report))
    write_json(a.out_dir/'summary.json',out); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
