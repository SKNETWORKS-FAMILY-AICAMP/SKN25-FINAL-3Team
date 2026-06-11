import os
import json
from openai import OpenAI
from django.conf import settings
from .models import PatentProject, ConsultationState, ChatMessage, AlgorithmStep, DetailElement
import logging

from dotenv import load_dotenv
load_dotenv()

#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PHASE1_INITIAL_PROMPT = """
당신은 특허법률사무소의 베테랑 변리사입니다. 발명가가 프로젝트 생성 시 입력한 초기 데이터를 바탕으로 발명의 4대 핵심 요소를 정밀하게 분석 및 요약하고, 첫 인사와 함께 이 분석이 정확한지 확인하는 명확한 질문을 작성하세요.

[초기 입력 데이터]
- 기존 기술의 문제점: {prior_art_problem}
- 해결하고자 하는 과제: {problem_to_solve}
- 핵심 기술 구성: {core_tech}
- 기대 효과: {expected_effect}

[지침]
1. 초기 데이터를 분석하여 각 요소를 특허 명세서에 쓰일 명료하고 전문적인 기술 언어로 요약하세요.
2. 요약한 내용을 가독성 좋은 리스트 형태로 포함하여, 발명가에게 이 방향성이 맞는지 확인을 구하는 친절한 인사말을 'greeting' 필드에 작성하세요.
3. 반드시 아래 JSON 형식으로만 응답하세요.

{{
    "problem": "요약된 문제점 문자열",
    "solution": "요약된 해결방법 문자열",
    "differentiation": "요약된 차별성 문자열 (데이터에서 유추 가능한 핵심 차별점이 있다면 요약, 없으면 null)",
    "effect": "요약된 기대효과 문자열",
    "greeting": "안녕하세요! 전문 변리사 AI입니다. 입력해주신 원본 데이터를 기반으로 특허 분석을 위한 핵심 4대 요소를 다음과 같이 요약 정리해보았습니다.\\n\\n📋 **[초기 발명 분석 요약]**\\n- **기존 문제점**: ...\\n- **해결 방법**: ...\\n- **핵심 구성**: ...\\n- **기대 효과**: ...\\n\\n해당 요약 내용이 발명가님이 생각하신 핵심 아이디어의 방향성과 일치하나요? 확인 후 말씀해주시면 심층 특허 상담을 이어가겠습니다!"
}}
"""

PHASE1_EXTRACT_PROMPT = """
당신은 발명가와 편안하게 대화하며 아이디어를 구체화하는 수석 변리사입니다.

[현재 파악된 발명 요소]
- 문제점: {problem}
- 해결방법: {solution}
- 차별성: {differentiation}
- 기대효과: {effect}

[지침]
1. 사용자 답변에 새로운 기술적 내용이 있다면 기존 요소에 통합하여 요약하세요. (없으면 기존 내용 유지)
2. 'ai_reply'에는 전문가다운 리액션과 함께, 아직 파악되지 않은 빈칸 항목 중 하나를 자연스럽게 묻는 대화를 작성하세요.
3. 🚨 [중요 예외 처리]: 사용자가 "ㅎㅇ", "안녕", "ㅋㅋ" 등 특허와 무관한 짧은 인사나 농담을 건넨 경우:
   - 추출 필드(problem 등)는 절대 건드리지 말고 기존 내용(또는 null)을 그대로 유지하세요.
   - 'ai_reply'에 "안녕하세요! 오늘 어떤 멋진 아이디어를 가지고 오셨나요?" 처럼 다정하게 인사하며 특허 이야기를 먼저 꺼내세요. (절대 에러나 경고를 출력하지 마세요)
4. 반드시 아래 JSON 형식으로만 응답하세요. (마크다운 블록이나 다른 텍스트는 불가)

{{
    "problem": "요약 문자열 또는 null",
    "solution": "요약 문자열 또는 null",
    "differentiation": "요약 문자열 또는 null",
    "effect": "요약 문자열 또는 null",
    "ai_reply": "사용자에게 보여질 사람 같은 자연스러운 채팅 메시지"
}}
"""

PHASE1_CHAT_PROMPT = """
당신은 친절하고 전문적인 변리사입니다. 
사용자의 최근 답변에 대해 전문적인 공감과 피드백을 해주고, 자연스럽게 다음 질문을 던지세요.
[수집 현황]
{state_summary}
[다음에 물어볼 항목]
{target_label}
[지침]
1. 사용자의 답변에 대해 전문적인 공감과 짧은 피드백을 먼저 하세요.
2. 아직 비어있는 항목 중 우선순위가 높은 항목에 대해 구체적으로 질문하세요.
3. 특히 '기대 효과' 질문 시에는 사용자가 얻을 구체적 편익을 상황 중심으로 물어보세요.
"""

PHASE2_QUESTION = """
독립항 핵심 내용 확인이 완료되었습니다. 
이제 청구항을 더욱 탄탄하게 만들 심화 정보를 여쭤볼게요. 아시는 항목만 편하게 답해 주시면 됩니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 구체적인 구현 수단 (예: YOLO v8, Python 등)
2. 데이터 파라미터 (예: 사용자 알레르기 정보 등)
3. 핵심 로직 및 수식 (예: 스코어링 가중치 함수 등)
4. 부가적/선택적 기능 (예: 자동 주문 연동 등)
5. 예외 처리 (예: 인식 실패 시 수동 입력 UI 등)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
모르시는 항목은 '없음' 또는 패스라고 하셔도 됩니다.
"""

PHASE2_EXTRACT_PROMPT = """ 
당신은 특허 전문 변리사입니다. 사용자의 입력을 분석하여 다음 2가지를 동시에 수행하세요.

[수행 규칙]
1. 사용자가 질문하거나 검수를 요청하면 'ai_reply'에 전문가적 피드백을 자연스럽게 작성하세요.
2. 사용자의 설명에서 발명의 구조를 파악하여 아래의 엄격한 JSON 스키마에 맞춰 추출하세요. 
   - components: 발명을 구성하는 모듈, DB, 장치 등
   - data_flows: 컴포넌트 간의 데이터 이동 (source와 target은 컴포넌트 ID 사용)
   - processing_steps: 시계열적인 작동 순서

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "ai_reply": "자연스러운 답변 텍스트...",
    "components": [
        {{"id": "COMP_001", "name": "명사형 명칭", "type": "MODULE", "description": "설명"}}
    ],
    "data_flows": [
        {{"flow_id": "FLOW_001", "source": "INPUT 또는 COMP_XXX", "target": "COMP_XXX", "data_name": "전달되는 데이터명"}}
    ],
    "processing_steps": [
        {{"step_number": 1, "subject_id": "COMP_001", "action_description": "~하는 단계", "input_data_ids": ["FLOW_001"], "output_data_ids": ["FLOW_002"]}}
    ]
}}
"""

PHASE2_SKIP_KEYWORDS = ["모르", "없어", "없음", "나중에", "패스", "skip", "생략"]

class DjangoPatentConsultant:
    def __init__(self, project: PatentProject):
        self.project = project
        self.state, _ = ConsultationState.objects.get_or_create(project=project)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _get_dynamic_system_prompt(self, is_extraction=False) -> str:
        if is_extraction:
            base_prompt = (
                "당신은 특허 데이터를 정밀하게 분석하는 AI 시스템입니다.\n"
                "반드시 지정된 JSON 형식으로만 응답해야 합니다. "
                "단, 사용자에게 건넬 다정하고 자연스러운 대화문은 오직 'ai_reply' 필드 안에 자유롭게 작성하세요.\n"
            )
        else:
            base_prompt = (
                "당신은 특허법률사무소의 수석 AI 변리사(Master Agent)입니다.\n"
                "발명가와 친근하고 자연스럽게 소통하며, 절대 JSON 형식이나 기계적인 에러 메시지를 출력하지 마세요.\n"
                "사용자가 'ㅎㅇ', '안녕' 등 일상적인 인사를 건네면 부드럽게 받아주고 특허 이야기로 자연스럽게 유도하세요.\n"
            )
        
        base_prompt += "\n[현재 파악된 발명의 핵심 4대 요소]\n"
        base_prompt += f"- 문제점: {self.state.ext_problem or '미파악'}\n"
        base_prompt += f"- 해결방법: {self.state.ext_solution or '미파악'}\n"
        base_prompt += f"- 차별성: {self.state.ext_differentiation or '미파악'}\n"
        base_prompt += f"- 기대효과: {self.state.ext_effect or '미파악'}\n"

        saved_claims = self.project.claims.all().order_by('claim_no')
        if saved_claims.exists():
            claims_text = "\n".join([f"제{c.claim_no}항: {c.content}" for c in saved_claims])
            base_prompt += (
                "\n================================\n"
                "[🚨 중요: 현재 발명가가 확정/수정한 특허 청구범위 내역]\n"
                f"{claims_text}\n"
                "사용자가 청구항에 대해 질문하거나 검수를 요청하면, 반드시 위 확정된 내용을 기준으로 피드백을 제공하세요.\n"
                "================================\n"
            )

        if not is_extraction:
            if self.state.phase == 3:
                base_prompt += "\n[현재 시스템 상태: 청구항 작성 완료 단계]\n사용자에게 도면 생성이나 명세서 본문 작성을 제안하거나, 발명 전반에 대한 범용적인 Q&A를 진행하세요."
            elif self.state.phase in [1, 2]:
                base_prompt += "\n[현재 시스템 상태: 발명 구체화 단계]\n사용자의 발명 내용을 경청하고, 부족한 정보(미파악된 요소)를 채우기 위한 자연스러운 질문을 던지며 상담을 이어가세요."

        return base_prompt
                
    def generate_welcome_message(self) -> str:
        if self.project.chat_messages.filter(role='assistant').exists():
            return ""
        
        try:
            inv_input = self.project.inventioninput
            initial_prompt = PHASE1_INITIAL_PROMPT.format(
                prior_art_problem=inv_input.prior_art_problem or "미입력",
                problem_to_solve=inv_input.problem_to_solve or "미입력",
                core_tech=inv_input.core_tech or "미입력",
                expected_effect=inv_input.expected_effect or "미입력"
            )
            
            ext_resp = self.client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": self._get_dynamic_system_prompt(is_extraction=True)},
                    {"role": "user", "content": initial_prompt}
                ],
                response_format={"type": "json_object"}
            )
            ext_data = json.loads(ext_resp.choices[0].message.content)

            if ext_data.get('problem'): self.state.ext_problem = ext_data['problem']
            if ext_data.get('solution'): self.state.ext_solution = ext_data['solution']
            if ext_data.get('differentiation'): self.state.ext_differentiation = ext_data['differentiation']
            if ext_data.get('effect'): self.state.ext_effect = ext_data['effect']
            self.state.save()

            greeting = ext_data.get('greeting', "초기 분석을 완료했습니다. 상담을 시작합니다.")
            
            # AI 웰컴 메시지를 DB에 즉시 생성하여 저장합니다.
            ChatMessage.objects.create(project=self.project, role='assistant', content=greeting)
            return greeting
            
        except Exception as e:
            logger.error(f"초기 원본 데이터 요약 실패: {e}")
            fallback = "안녕하세요! 입력해주신 발명 내용을 바탕으로 명세서 분석을 시작합니다. 방향성이 맞는지 확인해 주세요."
            ChatMessage.objects.create(project=self.project, role='assistant', content=fallback)
            return fallback

    def interact(self, user_input: str) -> str:
        ChatMessage.objects.create(project=self.project, role='user', content=user_input)

        has_claims = self.project.claims.exists()
        if has_claims and self.state.phase < 3:
            self.state.phase = 3
            self.state.save()

        response = ""

        if self.state.phase == 1:
            response = self._handle_phase_1(user_input)
        elif self.state.phase == 2:
            response = self._handle_phase_2(user_input)
        elif self.state.phase == 3:
            response = self._handle_phase_3(user_input) 

        ChatMessage.objects.create(project=self.project, role='assistant', content=response)
        return response
    
    def _handle_phase_1(self, user_input: str) -> str:
        # step_count = self.project.algorithm_steps.count()

        # # [모드 A] 알고리즘 스텝 수집 중일 때
        # if self.state.collecting_steps:
        #     cleaned_in = user_input.strip().lower()
        #     if cleaned_in in ALGO_EXIT_KEYWORDS or not cleaned_in:
        #         if step_count >= 3:
        #             self.state.collecting_steps = False
        #             self.state.phase = 2
        #             self.state.save()
        #             return f"훌륭합니다! 독립항 핵심 정보 수집이 완료되었습니다. \n\n{PHASE2_QUESTION}"
        #         else:
        #             return f" 특허 구성을 위해 최소 3단계 이상의 설명이 필요합니다.\n현재 **{step_count}단계**입니다. 다음 단계를 계속 말씀해 주세요."
        #     else:
        #         AlgorithmStep.objects.create(project=self.project, step_seq=step_count+1, content=user_input)
        #         if step_count + 1>=10:
        #             self.state.collecting_steps = False
        #             self.state.phase = 2
        #             self.state.save()
        #             return f"[알고리즘 10단계 수집 완료]\n\n{PHASE2_QUESTION}"
        #         else:
        #             return f"**{step_count+2}단계**를 말씀해 주세요.\n(마치시려면 '완료' 또는 '끝'이라고 입력해 주세요.)"

        # [모드 B] 일반 4대 요소 추출 모드 (GPT-4o)
        extract_prompt = PHASE1_EXTRACT_PROMPT.format(
            problem=self.state.ext_problem or "미파악",
            solution=self.state.ext_solution or "미파악",
            differentiation=self.state.ext_differentiation or "미파악",
            effect=self.state.ext_effect or "미파악"
        )
        ai_reply = "말씀해주신 내용을 잘 확인했습니다. 더 자세히 설명해주실 부분이 있나요?"

        try:
            ext_resp = self.client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": self._get_dynamic_system_prompt(is_extraction=True)},
                    {"role": "user", "content": f"{extract_prompt}\n\n사용자 입력: {user_input}"}],
                response_format={"type": "json_object"}
            )
            ext_data = json.loads(ext_resp.choices[0].message.content)

            if ext_data.get('problem'): self.state.ext_problem = ext_data['problem']
            if ext_data.get('solution'): self.state.ext_solution = ext_data['solution']
            if ext_data.get('differentiation'): self.state.ext_differentiation = ext_data['differentiation']
            if ext_data.get('effect'): self.state.ext_effect = ext_data['effect']
            if ext_data.get('empathy'): ai_empathy = ext_data['empathy']
            if ext_data.get('ai_reply'): ai_reply = ext_data['ai_reply']
            self.state.save()

        except Exception as e:
            logger.error(f"4대 요소 추출 실패: {e}")
            

        def is_valid(val):
            return bool(val and val.strip() !="미파악")
        
        all_filled = all([
        is_valid(self.state.ext_problem), 
        is_valid(self.state.ext_solution), 
        is_valid(self.state.ext_differentiation), 
        is_valid(self.state.ext_effect)
        ])
        
        # 4대 요소가 다 모였다면 알고리즘 수집 모드로 전환
        if all_filled:
            self.state.phase = 2
            self.state.save()
            return f"{ai_reply}\n\n발명의 핵심 요소 파악이 모두 완료되었습니다!\n\n{PHASE2_QUESTION}"    
            

        # if not is_valid(self.state.ext_problem):
        #     next_question = "현재 구상하신 발명이 해결하고자 하는 **기존 기술이나 상황의 문제점**은 무엇인지 편하게 말씀해 주시겠어요?"
        # elif not is_valid(self.state.ext_solution):
        #     next_question = "그 문제를 해결하기 위한 발명가님만의 **핵심 해결 방법**은 무엇인지 자세히 들려주세요."
        # elif not is_valid(self.state.ext_differentiation):
        #     next_question = "기존에 있던 비슷한 기술들과 비교했을 때, 이 발명만이 가지는 특별한 **차별성이나 장점**은 무엇일까요?"
        # elif not is_valid(self.state.ext_effect):
        #     next_question = "이 발명이 실제로 적용되었을 때 사용자가 얻게 될 구체적인 **기대 효과나 편익**은 무엇일까요?"
        # else:
        #     next_question = "추가로 덧붙이실 내용이 있나요?"

        return ai_reply # + "\n\n" + next_question
    
    def _handle_phase_2(self, user_input: str) -> str:
        if any(kw in user_input.lower() for kw in PHASE2_SKIP_KEYWORDS):
            return "건너뛰셨습니다. 다른 심화 정보를 추가하시거나 리포트를 발행해주세요."

        #algo_steps = [s.content for s in self.project.algorithm_steps.order_by('step_seq')]
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": self._get_dynamic_system_prompt(is_extraction=True)}, 
                    {"role": "user", "content": PHASE2_EXTRACT_PROMPT.format(solution=self.state.ext_solution or "", algorithm_steps="사용자 설명 참조", user_input=user_input)}
                ], 
                response_format={"type": "json_object"}
            )
            res = json.loads(resp.choices[0].message.content)
        except Exception as e:
            logger.error(f"Phase 2 파싱 에러: {e}")
            return "심화 정보 분석 중 오류가 발생했습니다. 다시 한 번 말씀해 주시겠어요?"
        
        ai_reply = res.get("ai_reply", "말씀하신 내용을 잘 확인했습니다.")
        detail_elements_to_create = []
        
        #  1. 컴포넌트(Components) 파싱 및 저장
        if res.get("components"):
            for comp in res["components"]:
                content = f"[{comp.get('type', 'MODULE')}] {comp.get('name', '미상')} - {comp.get('description', '')}"
                detail_elements_to_create.append(DetailElement(project=self.project, element_type="component", content=content))

        #  2. 데이터 흐름(Data Flows) 파싱 및 저장
        if res.get("data_flows"):
            for flow in res["data_flows"]:
                content = f"[{flow.get('flow_id', 'FLOW')}] {flow.get('source', '')} -> {flow.get('target', '')} : {flow.get('data_name', '')}"
                detail_elements_to_create.append(DetailElement(project=self.project, element_type="data_flow", content=content))

        #  3. 처리 단계(Processing Steps) 파싱 및 저장
        if res.get("processing_steps"):
            for step in res["processing_steps"]:
                content = f"[STEP {step.get('step_number', 0)}] {step.get('subject_id', '')}: {step.get('action_description', '')}"
                detail_elements_to_create.append(DetailElement(project=self.project, element_type="processing_step", content=content))


        # type_map = {
        #     "implementations": "implementation", "parameters": "parameter", 
        #     "algorithms": "algorithm", "optional_features": "optional", "error_handling": "error_handling"
        # }


        # for json_key, db_choice in type_map.items():
        #     extracted = res.get(json_key, [])
        #     validated = [item for item in extracted if item and item.strip()]
        #     for item in validated:
        #         detail_elements_to_create.append(
        #             DetailElement(
        #                 project=self.project,
        #                 element_type=db_choice,
        #                 content=item
        #             )
        #         )

        if detail_elements_to_create:
            DetailElement.objects.bulk_create(detail_elements_to_create)
            return f"{ai_reply}\n\n*(덧붙여 주신 발명 구조 정보가 완벽히 기록되었습니다. 내용이 충분하다면 우측 상단의 '청구항 작성'을 눌러주세요.)*"
        else:
            return ai_reply
        
    def _handle_phase_3(self, user_input: str) -> str:
        recent_messages = self.project.chat_messages.all().order_by('-created_at')[1:7] 
        chat_history = []
        for msg in reversed(recent_messages):
            if msg.role in ['user', 'assistant']:
                chat_history.append({"role": msg.role, "content": msg.content})

        try:
            messages = [
                {"role": "system", "content": self._get_dynamic_system_prompt(is_extraction=False)}, 
                {"role": "system", "content": (
                    "🚨 [엄격한 출력 규칙]\n"
                    "당신은 현재 사람과 1:1 메신저 대화를 하고 있습니다.\n"
                    "절대로, 무슨 일이 있어도 JSON 형식({ ... })이나 마크다운 코드 블록(```json)을 출력하지 마세요.\n"
                    "오직 사람에게 말하듯 '자연스러운 평문(Plain Text)'으로만 대답하세요.\n\n"
                    "[현재 상태]: 특허 청구항 초안이 이미 작성되어 저장된 상태입니다.\n"
                    "[지침]: \n"
                    "1. 사용자가 질문을 하거나 평가(도면, 청구항 등)를 요청하면 변리사로서 전문적이고 상세하게 답변해 주세요.\n"
                    "2. 대화 문맥상 사용자가 도면을 '생성'하고자 한다면 화면 상단의 '도면 생성' 버튼을 누르라고 안내하세요.\n"
                    "3. 사용자가 명세서(상세 설명)를 '작성'하고자 한다면 화면 상단의 '명세서 작성' 버튼을 누르라고 안내하세요."
                )}
            ]
            
            # 대화 기록 얹어주기
            messages.extend(chat_history)
            # 현재 사용자 채팅 얹어주기
            messages.append({"role": "user", "content": user_input})

            resp = self.client.chat.completions.create(
                model="gpt-4o", 
                messages=messages
            )
            raw_reply = resp.choices[0].message.content.strip()

            # 🛡️ [철통 방어] 껍데기 강제 제거기 (유지)
            if raw_reply.startswith("```json") or raw_reply.startswith("{"):
                try:
                    import re
                    json_match = re.search(r'\{.*\}', raw_reply, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group())
                        if "ai_reply" in parsed:
                            return parsed["ai_reply"]
                        return list(parsed.values())[0]
                except:
                    pass
                raw_reply = raw_reply.replace("```json", "").replace("```", "").strip()

            return raw_reply

        except Exception as e:
            logger.error(f"Phase 3 마스터 응답 실패: {e}")
            return "말씀하신 내용을 잘 들었습니다. 작성된 청구항을 검토 후 직접 수정하시거나, 화면 상단의 '도면 생성'을 진행해 보시는 것은 어떨까요?"