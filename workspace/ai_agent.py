import os
import json
from openai import OpenAI
from django.conf import settings
from .models import PatentProject, ConsultationState, ChatMessage, AlgorithmStep, DetailElement

from dotenv import load_dotenv
load_dotenv()

PHASE1_SYSTEM = "당신은 정밀한 특허 분석가입니다. 지시한 JSON 외에 어떤 텍스트도 출력하지 마세요."

PHASE1_EXTRACT_PROMPT = """
당신은 베테랑 변리사입니다. 사용자의 답변에서 발명의 4대 핵심 요소를 정밀 추출하고 요약하세요.
[현재 상태]
- 문제점: {problem}
- 해결방법: {solution}
- 차별성: {differentiation}
- 기대효과: {effect}
[지침]
1. 사용자 답변에서 새로 파악된 내용을 4대 요소에 업데이트하세요.
2. **반드시 핵심 기술적 특징 위주로 명료하고 전문적으로 요약하여 저장하세요.**
3. 추측하지 말고, 언급되지 않은 내용은 기존 상태를 유지하거나 null로 두세요.
4. 반드시 아래 JSON 형식으로만 응답하세요.
{{
    "problem": "요약된 문자열 또는 null",
    "solution": "요약된 문자열 또는 null",
    "differentiation": "요약된 문자열 또는 null",
    "effect": "요약된 문자열 또는 null"
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
독립항 핵심 내용 확인이 완료되었습니다. 🎉
이제 청구항을 더욱 탄탄하게 만들 심화 정보를 여쭤볼게요. 아시는 항목만 편하게 답해 주시면 됩니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 1. 구체적인 구현 수단 (예: YOLO v8, Python 등)
📊 2. 데이터 파라미터 (예: 사용자 알레르기 정보 등)
⚙️ 3. 핵심 로직 및 수식 (예: 스코어링 가중치 함수 등)
➕ 4. 부가적/선택적 기능 (예: 자동 주문 연동 등)
🛡️ 5. 예외 처리 (예: 인식 실패 시 수동 입력 UI 등)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
모르시는 항목은 '없음' 또는 패스라고 하셔도 됩니다.
"""

PHASE2_EXTRACT_PROMPT = """ 
당신은 특허 전문 변리사입니다. 발명가의 답변에서 심화 정보를 추출하세요. (JSON 응답)
[발명 맥락]
- 해결방법: {solution}
- 작동단계: {algorithm_steps}
사용자 입력: {user_input}
[추출 규칙]
- 사용자의 입력에서 '구현수단, 데이터, 로직, 부가기능, 예외처리'에 해당하는 항목이 있으면 리스트로 추출하세요.
- 절대로 추측하지 마세요. 언급된 내용만 추출하세요.
"""

ALGO_EXIT_KEYWORDS = ["완료", "끝", "종료", "save", "done", "complete"]
PHASE2_SKIP_KEYWORDS = ["모르", "없어", "없음", "나중에", "패스", "skip", "생략"]

class DjangoPatentConsultant:
    def __init__(self, project: PatentProject):
        self.project = project
        self.state, _ = ConsultationState.objects.get_or_create(project=project)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def interact(self, user_input: str) -> str:
        if user_input != "상담을 시작합니다.":
            ChatMessage.objects.create(project=self.project, role='user', content=user_input)

        response = ""

        if self.state.phase == 1:
            response = self._handle_phase_1(user_input)
        elif self.state.phase == 2:
            response = self._handle_phase_2(user_input)

        ChatMessage.objects.create(project=self.project, role='assistant', content=response)
        return response
    
    def _handle_phase_1(self, user_input: str) -> str:
        step_count = self.project.algorithm_steps.count()

        # [모드 A] 알고리즘 스텝 수집 중일 때
        if self.state.collecting_steps:
            cleaned_in = user_input.strip().lower()
            if cleaned_in in ALGO_EXIT_KEYWORDS or not cleaned_in:
                if step_count >= 3:
                    self.state.collecting_steps = False
                    self.state.phase = 2
                    self.state.save()
                    return f"훌륭합니다! 독립항 핵심 정보 수집이 완료되었습니다. \n\n{PHASE2_QUESTION}"
                else:
                    return f" 특허 구성을 위해 최소 3단계 이상의 설명이 필요합니다.\n현재 **{step_count}단계**입니다. 다음 단계를 계속 말씀해 주세요."
            else:
                AlgorithmStep.objects.create(project=self.project, step_seq=step_count+1, content=user_input)
                if step_count + 1>=10:
                    self.state.collecting_steps = False
                    self.state.phase = 2
                    self.state.save()
                    return f"[알고리즘 10단계 수집 완료]\n\n{PHASE2_QUESTION}"
                else:
                    return f"**{step_count+2}단계**를 말씀해 주세요.\n(마치시려면 '완료' 또는 '끝'이라고 입력해 주세요.)"
        
        # [모드 B] 일반 4대 요소 추출 모드 (GPT-4o)
        extract_prompt = PHASE1_EXTRACT_PROMPT.format(
            problem=self.state.ext_problem or "미파악",
            solution=self.state.ext_solution or "미파악",
            differentiation=self.state.ext_differentiation or "미파악",
            effect=self.state.ext_effect or "미파악"
        )
        ext_resp = self.client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": PHASE1_SYSTEM},
                {"role": "user", "content": f"{extract_prompt}\n\n사용자 입력: {user_input}"}],
            response_format={"type": "json_object"}
        )
        ext_data = json.loads(ext_resp.choices[0].message.content)

        if ext_data.get('problem'): self.state.ext_problem = ext_data['problem']
        if ext_data.get('solution'): self.state.ext_solution = ext_data['solution']
        if ext_data.get('differentiation'): self.state.ext_differentiation = ext_data['differentiation']
        if ext_data.get('effect'): self.state.ext_effect = ext_data['effect']
        self.state.save()

        all_filled = all([self.state.ext_problem, self.state.ext_solution, self.state.ext_differentiation, self.state.ext_effect])
        
        # 4대 요소가 다 모였다면 알고리즘 수집 모드로 전환
        if all_filled and step_count < 3:
            self.state.collecting_steps = True
            self.state.save()
            return "핵심 요소 파악이 순조롭습니다!  이제 이 발명이 **어떤 순서로 작동하는지(알고리즘)** 단계별로 설명 부탁드립니다.\n\n먼저 **1단계**는 무엇인가요?"

        # 4대 요소가 부족하다면, 다음 질문 생성 (GPT-4o-mini)
        recent_chats = list(self.project.chat_messages.order_by('-created_at')[:6])
        history = [{"role": msg.role, "content": msg.content} for msg in reversed(recent_chats)]
        state_summary = f"- 문제점: {self.state.ext_problem or '미파악'}\n- 해결방법: {self.state.ext_solution or '미파악'}\n- 차별성: {self.state.ext_differentiation or '미파악'}\n- 기대효과: {self.state.ext_effect or '미파악'}"
        
        target_label = "기존 문제점" if not self.state.ext_problem else "해결 방법" if not self.state.ext_solution else "차별성" if not self.state.ext_differentiation else "기대 효과"

        chat_resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PHASE1_CHAT_PROMPT.format(state_summary=state_summary, target_label=target_label)},
                *history,
                {"role": "user", "content": f"사용자의 최근 발언: {user_input}\n\n위 발언에 공감하고, 다음 단계인 '{target_label}'에 대해 질문해줘."}
            ]
        )
        return chat_resp.choices[0].message.content.strip()
    
    def _handle_phase_2(self, user_input: str) -> str:
        if any(kw in user_input.lower() for kw in PHASE2_SKIP_KEYWORDS):
            return "건너뛰셨습니다. 다른 심화 정보를 추가하시거나 리포트를 발행해주세요."

        # 심화 정보 추출 로직 (GPT-4o)
        algo_steps = [s.content for s in self.project.algorithm_steps.order_by('step_seq')]
        resp = self.client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": PHASE1_SYSTEM}, 
                {"role": "user", "content": PHASE2_EXTRACT_PROMPT.format(solution=self.state.ext_solution or "", algorithm_steps=algo_steps, user_input=user_input)}
            ], 
            response_format={"type": "json_object"}
        )
        res = json.loads(resp.choices[0].message.content)
        
        found_new = False
        type_map = {
            "implementations": "implementation", "parameters": "parameter", 
            "algorithms": "algorithm", "optional_features": "optional", "error_handling": "error_handling"
        }
        for json_key, db_choice in type_map.items():
            extracted = res.get(json_key, [])
            validated = [item for item in extracted if item and item.strip()]
            for item in validated:
                DetailElement.objects.create(project=self.project, element_type=db_choice, content=item)
                found_new = True

        if found_new:
            return "상세 정보가 잘 기록되었습니다!  추가로 덧붙일 내용이 있으신가요? 없으시면 '최종 리포트 발행'을 눌러주세요."
        else:
            return "말씀하신 내용을 검토했습니다. 더 구체적인 기술적 특징이나 예외 상황에 대해 들려주실 말씀이 있을까요?"
        