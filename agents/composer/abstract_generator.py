import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .prompts import ABSTRACT_SYSTEM_PROMPT

def generate_abstract_from_claim_1(
    claim_1_text: str,
    invention_title: Optional[str] = None,
    problem: Optional[str] = None,
    solution: Optional[str] = None,
    effect: Optional[str] = None,
) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않아 요약문을 생성할 수 없습니다.")

    model_name = os.environ.get("COMPOSER_MODEL", "gpt-4o")
    llm = ChatOpenAI(model=model_name, temperature=0.2)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", ABSTRACT_SYSTEM_PROMPT),
        ("user", "청구항 1항:\n{claim_1_text}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"claim_1_text": claim_1_text})
    return response.content
