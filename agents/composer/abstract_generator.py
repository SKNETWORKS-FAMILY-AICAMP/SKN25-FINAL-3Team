import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .prompts import ABSTRACT_SYSTEM_PROMPT


def clean_abstract_text(text: str) -> str:
    text = str(text or "").strip()
    text = text.replace("【요약】", "").strip()

    if text.startswith("요약"):
        text = text.replace("요약", "", 1).strip()

    return text


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
        (
            "user",
            """
청구항 1항:
{claim_1_text}

발명의 명칭:
{invention_title}

해결하려는 과제:
{problem}

과제의 해결 수단:
{solution}

발명의 효과:
{effect}
""",
        ),
    ])

    chain = prompt | llm
    response = chain.invoke(
        {
            "claim_1_text": claim_1_text,
            "invention_title": invention_title or "",
            "problem": problem or "",
            "solution": solution or "",
            "effect": effect or "",
        }
    )
    return clean_abstract_text(response.content)
