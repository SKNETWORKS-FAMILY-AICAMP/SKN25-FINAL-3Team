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
당신은 특허법률사무소의 베테랑 변리사입니다. 발명가가 입력한 초기 데이터를 바탕으로 발명의 4대 핵심 요소를 특허 명세서 및 청구항 작성에 최적화된 형태로 재구조화하고, 첫 인사와 함께 이 분석이 정확한지 확인하는 질문을 작성하세요.

[초기 입력 데이터]
- 기존 기술의 문제점: {prior_art_problem}
- 해결하고자 하는 과제: {problem_to_solve}
- 핵심 기술 구성: {core_tech}
- 기대 효과: {expected_effect}

[지침]
1. 입력 데이터의 내용을 절대 압축하거나 생략하지 마세요. 모든 세부 구성요소(입력값, 처리방식, 출력값, 구성요소 간 관계 등)를 빠짐없이 유지하면서, 특허 명세서에 쓰이는 명료하고 전문적인 기술 언어로 재표현하세요.
2. '요약'이 아닌 '재구조화'가 목표입니다. 입력된 정보가 청구항의 구성요소로 바로 활용될 수 있도록, 발명의 구성요소·작동 방식·기술적 효과가 명확히 드러나게 정리하세요.
3. 각 필드는 이후 독립항·종속항 작성의 재료가 되므로, 기술적 특징을 구체적이고 풍부하게 기술하세요.
4. 요약 내용을 가독성 좋은 리스트 형태로 포함하여, 발명가에게 이 방향성이 맞는지 확인을 구하는 친절한 인사말을 'greeting' 필드에 작성하세요.
5. 반드시 아래 JSON 형식으로만 응답하세요.

{{
    "problem": "종래 기술의 구성과 그 한계, 그로 인해 발생하는 기술적 문제점을 구체적으로 기술한 문자열 (입력 내용 전체 반영)",
    "solution": "발명의 주요 구성요소, 입력값, 처리 방식, 출력값, 구성요소 간 작동 관계를 모두 포함하여 구체적으로 기술한 문자열",
    "differentiation": "종래 기술 대비 본 발명의 핵심 기술적 차별점 문자열 (유추 가능한 차별점 포함, 없으면 null)",
    "effect": "본 발명으로 달성되는 기술적 효과를 구체적으로 기술한 문자열",
    "greeting": "안녕하세요! 전문 변리사 AI입니다. 입력해주신 원본 데이터를 기반으로 특허 청구항 작성을 위한 핵심 4대 요소를 다음과 같이 구조화하였습니다.\\n\\n📋 **[발명 구조화 분석]**\\n- **기존 문제점**: ...\\n- **해결 방법 및 구성**: ...\\n- **핵심 차별성**: ...\\n- **기대 효과**: ...\\n\\n위 내용이 발명가님이 생각하신 핵심 아이디어의 방향성과 일치하나요? 확인 후 말씀해주시면 청구항 작성을 이어가겠습니다!"
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
발명의 4대 핵심 요소가 완벽하게 정리되었습니다! 
이제 특허의 권리 범위를 튼튼하게 설계하기 위해, 발명이 실제로 어떻게 굴러가는지 **'뼈대(아키텍처)'**를 세워볼 차례입니다.

아래 질문들을 가볍게 이야기해 주시면, 제가 특허 명세서용 기술 용어(모듈, 데이터, 단계)로 예쁘게 변환하겠습니다.

1. 🧩 **주요 구성 요소**: 이 발명을 구현하려면 어떤 장치나 모듈이 필요한가요?
   (예: 사용자 단말, 데이터 수집 모듈, 특징 벡터 추출부, 매칭 엔진 등)
2. 🔄 **데이터의 흐름**: 사용자가 입력한 데이터는 시스템 내부에서 어떻게 가공되고 전달되나요?
   (예: 음성 데이터가 텍스트로 변환되어 검색 DB로 전달됨 등)
3. ⚙️ **핵심 작동 순서**: 시스템이 작동하는 첫 단계부터 최종 결과물이 나올 때까지의 과정을 순서대로 설명해 주신다면?

기술적인 용어나 코드가 아니어도 좋습니다. 아시는 만큼만 줄글로 편하게 설명해 주세요! 
(만약 이미 앞서 충분히 설명하셨다면, "바로 청구항 작성해줘"라고 말씀해 주셔도 됩니다.)
"""

PHASE2_EXTRACT_PROMPT = """ 
당신은 특허 전문 변리사입니다. 사용자의 입력을 분석하여 다음 작업을 수행하세요.

[지침]
1. 사용자의 설명에서 발명의 기술적 구조(컴포넌트, 데이터 흐름, 처리 단계)가 파악되면 추출하세요. 기술적인 추가 내용이 없다면 빈 배열([])을 반환하세요.
2. 'ai_reply'에는 기계적인 답변이 아닌, 자연스럽고 전문적인 대화를 작성하세요.
3. 🚨 [중요: 대화 처리 및 액션 트리거]:
   - 사용자가 "모르겠다", "없다", "패스" 등으로 추가 설명이 없다고 하거나, "청구항 작성해줘"라고 명시적으로 요청하면: 'ai_reply'에 "알겠습니다! 지금까지 수집된 정보를 바탕으로 바로 청구항 작성을 시작하겠습니다. 잠시만 기다려주세요 🚀"라고 자연스럽게 작성하세요. (🚨주의: 화면의 버튼을 누르라는 말은 절대 하지 마세요.)
   - 새로운 기술 정보를 제공했다면: 해당 정보를 잘 기록하겠다고 피드백한 뒤, "내용이 충분하다면 '청구항 작성해줘'라고 말씀해 주세요!"라고 안내하세요.
   - 단순한 질문이라면 추출 필드는 비워두고 친절하게 답변해 주세요.
4. 반드시 아래 JSON 형식으로만 응답하세요.

{{
    "ai_reply": "자연스러운 답변 텍스트",
    "action": "사용자가 청구항 작성을 명시적으로 동의/요청하면 'GENERATE_CLAIMS', 아니면 null",
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

PHASE2_PROACTIVE_DRAFT_PROMPT = """
당신은 특허청 심사관 출신의 수석 특허 아키텍트입니다.
발명가가 앞서 대답한 핵심 4대 요소를 바탕으로, 이 발명이 실제로 작동하기 위한 '가상의 표준 시스템 구조(Architecture) 초안'을 먼저 스케치하여 제안하세요.

[발명 4대 요소]
- 문제점: {problem}
- 해결방법: {solution}
- 차별성: {differentiation}
- 기대효과: {effect}

[작성 지침]
위 해결방법을 구현하기 위해 아주 합리적이고 전형적인 시스템 뼈대를 아래 3가지 파트로 스케치하세요.
(너무 지엽적인 코드 라이브러리 언급은 피하고 '데이터 수집부', '분석 엔진', '저장 DB', '사용자 매핑부' 등의 기능적 명사를 사용하세요)

출력 포맷:
---
💡 **AI 변리사가 스케치해 본 시스템 구조 초안**

1. 🧩 **주요 구성 요소 (Modules)**
   - **[모듈명 A]**: (역할 한 줄 설명)
   - **[모듈명 B]**: (역할 한 줄 설명)

2. 🔄 **데이터의 흐름 (Data Flow)**
   - [입력 데이터] ➔ (모듈 A) ➔ [중간 산출물] ➔ (모듈 B) ➔ [최종 결과]

3. ⚙️ **핵심 작동 순서 (Step-by-step)**
   - **S100**: (1단계 로직)
   - **S200**: (2단계 로직)
---

오직 위 포맷의 마크다운 텍스트만 깔끔하게 출력하세요. JSON 껍데기를 씌우지 마세요.
"""

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

    def interact(self, user_input: str) -> tuple[str, str]:
        ChatMessage.objects.create(project=self.project, role='user', content=user_input)

        if self.project.claims.exists() and self.state.phase < 3:
            self.state.phase = 3
            self.state.save()

        response = ""
        action = None

        if self.state.phase == 1:
            response = self._handle_phase_1(user_input)
        elif self.state.phase == 2:
            response, action = self._handle_phase_2(user_input)
        elif self.state.phase == 3:
            response, action = self._handle_phase_3(user_input) 

        ChatMessage.objects.create(project=self.project, role='assistant', content=response)
        return response, action
    
    def _generate_proactive_sketch(self) -> str:
            prompt = PHASE2_PROACTIVE_DRAFT_PROMPT.format(
                problem=self.state.ext_problem,
                solution=self.state.ext_solution,
                differentiation=self.state.ext_differentiation,
                effect=self.state.ext_effect
            )
            try:
                resp = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "당신은 특허 명세서용 아키텍처 초안을 작성하는 수석 변리사입니다. 평문 마크다운으로만 답하세요."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"가상 아키텍처 초안 생성 실패: {e}")
                return "> *(시스템 구성도 초안을 스케치하는 중 오류가 발생했습니다. 머릿속에 그리신 시스템의 주요 모듈들을 자유롭게 말씀해 주세요!)*"

    def _handle_phase_1(self, user_input: str) -> str:
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
            #return f"{ai_reply}\n\n발명의 핵심 요소 파악이 모두 완료되었습니다!\n\n{PHASE2_QUESTION}"    
        
            # 뇌빼고 대답할 수 있게 초안을 미리 그려서 던져줌!
            proactive_architecture_draft = self._generate_proactive_sketch()

            return (
                f"{ai_reply}\n\n"
                "🎉 **발명의 핵심 4대 요소 파악이 모두 완료되었습니다!**\n\n"
                "이제 특허의 권리 범위를 튼튼하게 지키기 위해 시스템의 **'뼈대(아키텍처)'**를 설계할 차례입니다. "
                "설명하시기 편하도록, **지금까지 주신 정보를 바탕으로 제가 표준 시스템 구성도 초안을 먼저 스케치해 보았습니다.**\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{proactive_architecture_draft}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "위 구조에서 **수정하거나 더 추가하고 싶은 모듈/단계**가 있다면 편하게 말씀해 주세요!\n"
                "*(예: '여기서 회원 DB 조회하는 모듈 하나 추가해줘', '데이터 흐름 2번 단계 뒤에 암호화 거치는 거 넣어줘')*\n\n"
                "만약 이 뼈대 그대로 가도 충분하다면, **'이대로 청구항 작성해줘'**라고 말씀해 주시면 바로 초안을 뽑겠습니다! 🚀"
            )

        return ai_reply
    
    def _handle_phase_2(self, user_input: str) -> tuple[str, str | None]:
        # 1. 이전 대화 기록 가져오기 (문맥 파악용)
        recent_messages = self.project.chat_messages.all().order_by('-created_at')[1:5] 
        chat_history = []
        for msg in reversed(recent_messages):
            if msg.role in ['user', 'assistant']:
                chat_history.append({"role": msg.role, "content": msg.content})

        try:
            # 2. 히스토리와 함께 GPT 호출
            messages = [
                {"role": "system", "content": self._get_dynamic_system_prompt(is_extraction=True)}, 
                {"role": "system", "content": PHASE2_EXTRACT_PROMPT}
            ]
            messages.extend(chat_history)
            messages.append({"role": "user", "content": user_input})

            resp = self.client.chat.completions.create(
                model="gpt-4o", 
                messages=messages, 
                response_format={"type": "json_object"}
            )
            res = json.loads(resp.choices[0].message.content)
        except Exception as e:
            logger.error(f"Phase 2 파싱 에러: {e}")
            return (
                "심화 정보 분석 중 오류가 발생했습니다. 다시 한 번 말씀해 주시겠어요?",
                None
            )
        
        # 3. AI가 문맥에 맞게 알아서 작성한 답변 꺼내기
        ai_reply = res.get("ai_reply", "말씀하신 내용을 잘 확인했습니다. 지금 바로 청구항 작성을 시작하겠습니다")
        action = res.get("action")
        detail_elements_to_create = []
        
        # 4. 기술 정보가 있으면 DB에 저장 (빈 배열이면 자연스럽게 패스됨)
        if res.get("components"):
            for comp in res["components"]:
                content = f"[{comp.get('type', 'MODULE')}] {comp.get('name', '미상')} - {comp.get('description', '')}"
                detail_elements_to_create.append(DetailElement(project=self.project, element_type="component", content=content))

        if res.get("data_flows"):
            for flow in res["data_flows"]:
                content = f"[{flow.get('flow_id', 'FLOW')}] {flow.get('source', '')} -> {flow.get('target', '')} : {flow.get('data_name', '')}"
                detail_elements_to_create.append(DetailElement(project=self.project, element_type="data_flow", content=content))

        if res.get("processing_steps"):
            for step in res["processing_steps"]:
                content = f"[STEP {step.get('step_number', 0)}] {step.get('subject_id', '')}: {step.get('action_description', '')}"
                detail_elements_to_create.append(DetailElement(project=self.project, element_type="processing_step", content=content))

        # 5. 추출된 정보가 있을 때만 DB 저장
        if detail_elements_to_create:
            DetailElement.objects.bulk_create(detail_elements_to_create)

        return ai_reply, action
        
    def _handle_phase_3(self, user_input: str) -> tuple[str, str | None]:
        recent_messages = self.project.chat_messages.all().order_by('-created_at')[1:7] 
        chat_history = []
        for msg in reversed(recent_messages):
            if msg.role in ['user', 'assistant']:
                chat_history.append({"role": msg.role, "content": msg.content})

        tools = [{
            "type": "function",
            "function": {
                "name": "trigger_generate_claims",
                "description": "사용자가 청구항 작성을 명시적으로 지시하거나 승인했을 때 호출합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }]
        action = None
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
                messages=messages,
                tools=tools
            )
            msg = resp.choices[0].message
            
            #raw_reply = resp.choices[0].message.content.strip()

            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    if tool_call.function.name == "trigger_generate_claims":
                        action = "GENERATE_CLAIMS"
                raw_reply = (
                    "훌륭합니다! 지금까지 준비된 정보를 바탕으로 "
                    "청구항 초안을 작성해 보겠습니다!"
                )
            else:
                raw_reply = (msg.content or "").strip()

            # [철통 방어] 껍데기 강제 제거기 (유지)
            if raw_reply.startswith("```json") or raw_reply.startswith("{"):
                try:
                    import re
                    json_match = re.search(r'\{.*\}', raw_reply, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group())
                        if "ai_reply" in parsed:
                            return parsed["ai_reply"], action
                        return list(parsed.values())[0], action
                except Exception as e:
                    logger.warning(f"JSON 제거기 파싱 실패: {e}")
                raw_reply = raw_reply.replace("```json", "").replace("```", "").strip()

            return raw_reply, action

        except Exception as e:
            logger.error(f"Phase 3 마스터 응답 실패: {e}")
            return "말씀하신 내용을 잘 들었습니다. 작성된 청구항을 검토 후 직접 수정하시거나, 화면 상단의 '도면 생성'을 진행해 보시는 것은 어떨까요?", action