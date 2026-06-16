import logging
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# SummaryAgent가 기대하는 5가지 입력 데이터 규격
class PaperMockData(BaseModel):
    title: str = Field(description="논문의 원제목을 그대로 쓰지 않고, 핵심 기술을 파악하여 한국 특허청 형식의 발명의 명칭(예: '~를 위한 장치 및 방법')으로 새롭게 창작한 제목")
    prior_art_problem: str = Field(description="Introduction에 기재된 기존 기술의 한계점")
    problem_to_solve: str = Field(description="본 논문이 해결하고자 하는 과제")
    core_tech: str = Field(description="논문에서 제안하는 전체 아키텍처, 알고리즘 수식, 파라미터, 구체적인 동작 단계를 하나도 빠짐없이 상세히 나열한 텍스트")
    expected_effect: str = Field(description="실험 결과(Experiments)의 정확도 등 구체적인 수치 기반 효과")

class PaperAnalyzerAgent:
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0, max_tokens=8192)
        self.structured_llm = self.llm.with_structured_output(PaperMockData, method="json_schema", strict=True)

    def extract_from_paper(self, paper_text: str) -> dict:
        logger.info("[Paper Analyzer] 논문 텍스트 분석 및 모의 데이터(mock_input_data) 생성 시작...")
        
        if not paper_text:
            logger.error("paper_text가 제공되지 않았습니다.")
            return {}

        # [전처리] 참고문헌(References) 이후 텍스트 제거 (토큰 최적화 및 노이즈 방지)
        split_match = list(re.finditer(r'\n\s*(References|REFERENCES|Bibliography|참고문헌)\s*\n', paper_text))
        if split_match:
            last_match_idx = split_match[-1].start()
            paper_text = paper_text[:last_match_idx]

        system_prompt = """당신은 논문을 분석하여 특허 명세서 작성의 근간이 되는 5대 핵심 요소로 분류해 내는 [수석 특허 변리사 AI]입니다.
논문 전체를 읽고 제공된 JSON 형식에 맞춰 데이터를 생성하세요.

[🚨 절대 원칙 - 언어 및 용어 번역]
1. 입력된 논문이 영어나 기타 외국어이더라도, **기본적으로 모든 출력은 한국어로 작성**해야 합니다.
2. 단, 'Self-Attention', 'Convolution', 'Transformer' 등 해당 기술 분야에서 널리 통용되는 전문 용어나 고유 명사는 무리하게 직역(예: '자기 주의')하지 마세요. 업계 표준 한글 표기(예: '셀프 어텐션')를 사용하거나, 번역이 모호한 경우 영문 원어를 그대로 사용(또는 한글 표기 뒤에 괄호로 병기)하여 특허 명세서로서의 기술적 의미가 왜곡되지 않도록 하십시오.
3. 'title' 필드는 논문의 원문 제목(예: "Attention Is All You Need")을 번역하거나 그대로 쓰지 말고, 발명의 핵심 기술 특징이 드러나도록 **"~를 위한 [방법/장치/시스템]" 형태의 한국 특허청 표준 발명의 명칭**으로 새롭게 명명하십시오.

[🚨 절대 원칙 - 과요약 방지]
1. 'core_tech' 항목을 작성할 때는 절대로 내용을 요약하거나 추상화하지 마세요.
2. 논문의 제안 방법(Proposed Method)에 등장하는 모든 모듈의 이름, 수학적 수식, 하이퍼파라미터 조건, 데이터 전처리 수치, 알고리즘 처리 단계를 빠짐없이 상세히 나열해야 합니다. 이 텍스트가 다음 단계에서 특허 청구항의 재료가 되므로, 자연스러운 한국어 특허 용어로 번역하여 상세히 기술하세요.
3. 수식에 사용된 기호나 파라미터가 있다면 한글로 그 의미를 구체적으로 풀어서 'core_tech'에 반드시 포함시키세요.
"""

        human_prompt = """다음 논문 텍스트를 분석하여 5대 요소로 추출하라.
디테일이 생명이다. 'core_tech'에는 논문의 기술적 세부사항을 꽉 채워서 담아라.

[논문 텍스트]
{paper_text}
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        chain = prompt | self.structured_llm
        
        try:
            result: PaperMockData = chain.invoke({"paper_text": paper_text})
            logger.info("[Paper Analyzer] 논문 기반 mock_input_data 생성 완료.")
            
            # 추출된 Pydantic 모델을 dict로 변환하여 즉시 반환
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"[Paper Analyzer] 에러 발생: {str(e)}")
            return {}