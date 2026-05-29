import os
import re
import json
import logging
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from state import RejectionDetail, ExaminerResult, PatentState, ClaimResult, ClaimItem

# ==========================================
# 0. 로깅 및 환경 설정
# ==========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


# ==========================================
# 1. 🛠️ 파싱 구조대 (Regex + JSON Fallback)
# -> 아직 파인튜닝이 완전하지 않아, Output 형식이 깨져서 파싱 구조대가 필요. 추후 보완예정
# ==========================================
def salvage_via_regex(text: str) -> dict:
    """JSON 문법이 깨진 텍스트에서 정규식으로 데이터 추출"""
    is_app_match = re.search(r'\"?is_approved\"?\s*:\s*(true|false)', text, re.IGNORECASE)
    is_app = False
    if is_app_match:
        is_app = (is_app_match.group(1).lower() == 'true')
        
    claims_matches = re.finditer(r'\"?claims\"?\s*:\s*\[(.*?)\]', text)
    rejections = []
    
    for match in claims_matches:
        nums = re.findall(r'\d+', match.group(1))
        if nums:
            claims_list = [int(n) for n in nums]
            rejections.append({
                "claims": claims_list,
                "reason_text": "정규식 복구됨: 심사 모델이 거절 사유를 생성했으나 포맷 오류로 상세 텍스트를 불러오지 못했습니다."
            })
            
    return {"is_approved": is_app, "rejections": rejections}

def extract_payload(text: str) -> dict:
    """1차 JSON 파싱 시도 -> 실패 시 2차 정규식 구조대 투입"""
    if not isinstance(text, str):
        text = str(text)
        
    text = text.replace('```json', '').replace('```', '').strip()
    
    start_idx = text.find('{')
    if start_idx != -1:
        decoder = json.JSONDecoder()
        try:
            obj, _ = decoder.raw_decode(text[start_idx:])
            
            while isinstance(obj, dict) and "examiner_result" in obj:
                obj = obj["examiner_result"]
                
            if isinstance(obj, bool):
                return {"is_approved": obj, "rejections": []}
                
            is_app = obj.get("is_approved", False)
            rejs = obj.get("rejections", [])
            return {"is_approved": is_app, "rejections": rejs}
            
        except (json.JSONDecodeError, AttributeError):
            pass 

    logger.warning("[Examiner Agent] JSON 파싱 실패! 정규식 구조대를 투입합니다.")
    return salvage_via_regex(text)

# ==========================================
# 2. 심사관 에이전트 클래스
# ==========================================
class ExaminerAgent:
    def __init__(self):
        vllm_base_url = os.getenv("RUNPOD_VLLM_URL", "https://api.runpod.ai/v2/삭제/openai/v1")
        vllm_api_key = os.getenv("RUNPOD_API_KEY", "key")
        
        # ==========================================
        # 🛠️ [핵심] vLLM에 등록된 실제 모델 이름 동적 확인
        # ==========================================
        actual_model_name = "silverstone1004/exaone-3.5-7.8B-custom" # 실패 시 사용할 기본값
        try:
            headers = {"Authorization": f"Bearer {vllm_api_key}"}
            # RunPod vLLM 서버에 등록된 모델 리스트를 요청
            response = requests.get(f"{vllm_base_url}/models", headers=headers)
            if response.status_code == 200:
                models_data = response.json().get("data", [])
                if models_data:
                    # 서버가 응답한 첫 번째 모델의 진짜 이름을 가져옴
                    actual_model_name = models_data[0]["id"]
                    logger.info(f"💡 RunPod vLLM 실제 등록 모델명 확인됨: {actual_model_name}")
        except Exception as e:
            logger.warning(f"모델명 조회 실패, 기본값으로 시도합니다: {e}")

        # 알아낸 진짜 모델 이름(actual_model_name)으로 ChatOpenAI 초기화
        self.llm = ChatOpenAI(
            model=actual_model_name, 
            temperature=0.1,
            openai_api_base=vllm_base_url,
            openai_api_key=vllm_api_key,
            max_tokens=4096
        )

    def format_claims_for_prompt(self, claims_data) -> str:
        formatted_text = ""
        for claim in claims_data.claims:
            formatted_text += f"청구항 {claim.claim_no}\n{claim.content}\n\n"
        return formatted_text.strip()

    def run(self, state: dict) -> dict:
        logger.info("[Examiner Agent] 특허 명확성 심사 시작...")
        
        claims_data = state.get("claims_data")
        if not claims_data or not claims_data.claims:
            logger.error("심사할 청구항 데이터가 없습니다.")
            return {"examiner_data": None}

        claims_text = self.format_claims_for_prompt(claims_data)

        system_prompt = """당신은 대한민국 특허청(KIPO) 소속의 컴퓨터·인공지능(AI) 분야 베테랑 특허 심사관입니다. 제시된 [청구범위]를 아래의 법령 및 심사지침에 의거하여 엄격하게 심사하고, 그 결과를 지정된 JSON 스키마 형식으로 출력하십시오.

---
[심사 기준: 특허법 제42조 제4항 제2호 (명확성)]
- 청구항은 발명이 명확하고 간결하게 적혀 있어야 합니다.
- 판단 기준: '통상의 기술자'가 출원 당시의 '기술상식'을 고려하여, 발명의 설명이나 도면을 참작했을 때 청구범위로부터 특허받고자 하는 발명을 명확하게 파악할 수 있는지 개별적으로 판단합니다.

[AI/소프트웨어 분야 핵심 거절 기준 (Rejection Rules)]
1. 구성요소 간 결합관계 부재: 각 구성요소(모듈, 데이터, 인프라 등)가 단순히 나열되어 있을 뿐, 이들 간의 시계열적 처리 관계나 유기적 결합관계가 기재되지 않아 발명이 불명확한 경우 거절합니다.
2. 기능적 표현의 한계: AI/BM 발명 특성상 기능이나 효과 위주로 청구항이 기재된 경우, 발명의 설명과 도면을 참작하더라도 그 기능적 표현의 의미 내용을 명확하게 확정할 수 없다면 발명이 불명확한 것으로 봅니다.
3. 수치한정 및 모호한 표현: '주로', '많은', '높은', '대략' 등 비교 기준이 불명확한 표현을 사용하거나, 수치한정 발명에서 상한/하한이 없는 모호한 기재로 권리범위를 불명확하게 한 경우 거절합니다.
4. 카테고리 불비 및 중복 기재: 독립항의 카테고리(예: 방법)와 이를 인용하는 종속항의 카테고리(예: 장치, CRM)가 서로 달라 인용관계가 모호하거나, 동일 내용이 너무 장황하게 중복 기재된 경우 거절합니다.

[오기 구제 가이드라인 (거절 예외 조항)]
- 의미상 대응: 지시하는 문언과 지시대상이 완전히 일치하지 않더라도, 발명의 설명을 참작하여 의미상 서로 대응됨이 명확히 알 수 있는 경우 적법한 기재로 봅니다.

---
[출력 규칙]
- 심사 결과 기재불비 사항이 발견되면 전체 'examiner_result.is_approved'를 반드시 'false'로 설정하고, rejections 배열에 청구항 번호, 의견서 톤의 거절 이유(reason_text)를 작성하십시오.
- 결격 사유가 전혀 없다면 'is_approved'를 'true'로, 'rejections'는 빈 배열 '[]'로 출력하십시오.
- 내용이 '삭제' 또는 '삭제항'인 청구항은 분석 대상에서 완전히 제외하고 claims 배열에 포함하지 마십시오."""

        human_prompt = f"다음 청구범위에 대한 특허법 제42조제4항제2호 명확성 요건 심사를 진행하고 결과를 JSON으로 출력하세요.\n\n[청구범위]\n{claims_text}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        chain = prompt | self.llm 
        
        try:
            raw_response = chain.invoke({})
            raw_text = raw_response.content
            logger.info(f"[Examiner Agent] 모델 응답 수신 완료. (길이: {len(raw_text)})")
            
            parsed_dict = extract_payload(raw_text)
            
            current_revision = 1
            if state.get("examiner_data"):
                current_revision = state["examiner_data"].revision_count + 1

            rejections_pydantic = [
                RejectionDetail(claims=r.get("claims", []), reason_text=r.get("reason_text", ""))
                for r in parsed_dict.get("rejections", [])
            ]
            
            examiner_result = ExaminerResult(
                is_approved=parsed_dict.get("is_approved", False),
                rejections=rejections_pydantic,
                revision_count=current_revision
            )
            
            logger.info(f"[Examiner Agent] 심사 완료. 승인 여부: {examiner_result.is_approved}, 거절 건수: {len(examiner_result.rejections)}")
            return {"examiner_data": examiner_result}
            
        except Exception as e:
            logger.error(f"[Examiner Agent] 에러 발생: {str(e)}")
            fallback_result = ExaminerResult(is_approved=False, rejections=[], revision_count=1)
            return {"examiner_data": fallback_result}

# ==========================================
# 4. 단독 실행 및 테스트 코드
# ==========================================
if __name__ == "__main__":
    from pydantic import dataclasses
    
    class MockClaim:
        def __init__(self, no, content):
            self.claim_no = no
            self.content = content
            
    class MockClaimResult:
        def __init__(self):
            # 💡 [수정됨] 제공해주신 청구항 전체 텍스트 반영
            self.claims = [
                MockClaim(1, "적어도 하나의 프로세서에 의해 수행되는, 거대 언어모델(large language model) 기반 인공지능 모델 시뮬레이션 방법에 있어서, 거대 언어모델을 이용하여 사고(accident)와 연관된 시뮬레이션 시나리오를 생성하는 단계; 상기 생성된 시뮬레이션 시나리오에 기초하여 상기 사고와 연관된 시뮬레이션 환경을 생성하는 단계; 및 상기 생성된 시뮬레이션 환경에 기초하여 인공지능 모델을 시뮬레이션하는 단계를 포함하는, 인공지능 모델 시뮬레이션 우하하하하."),
                MockClaim(2, "제1항에 있어서, 상기 시뮬레이션 시나리오를 생성하는 단계는, 상기 거대 언어모델을 이용하여 상기 사고가 발생한 배경 정보를 생성하는 단계; 상기 거대 언어모델을 이용하여 상기 사고와 연관된 인물 정보를 생성하는 단계; 및 상기 거대 언어모델을 이용하여 상기 배경 정보 및 상기 인물 정보에 기초하여 상기 사고와 연관된 시뮬레이션 시나리오를 생성하는 단계를 포함하는, 인공지능 모델 시뮬레이션 방법.")
            ]
            
    # Mock State
    initial_state = {
        "claims_data": MockClaimResult(),
        "examiner_data": None
    }
    
    agent = ExaminerAgent()
    result_update = agent.run(initial_state)
    
    print("\n" + "="*60)
    print("🌟 [심사 결과 (ExaminerResult)] 🌟")
    print("="*60)
    
    if result_update.get("examiner_data"):
        data = result_update["examiner_data"]
        print(f"최종 승인 여부 (is_approved): {data.is_approved}")
        print(f"수정 회차 (revision_count): {data.revision_count}")
        print("-" * 60)
        if not data.is_approved:
            for i, rej in enumerate(data.rejections, 1):
                print(f"[거절 사유 {i}] 대상 청구항: {rej.claims}")
                print(f"사유: {rej.reason_text}\n")
    else:
        print("심사 실패")