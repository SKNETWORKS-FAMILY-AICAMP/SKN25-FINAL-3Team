import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture
def sample_consultation():
    return {
        "invention_flow": "사용자 입력을 받아 AI가 특허 명세서를 자동 생성하는 흐름",
        "problem": "기존 특허 작성 방식은 전문 지식 없이 접근하기 어렵다",
        "differentiation": "자연어 입력만으로 법적 요건을 갖춘 명세서를 자동 생성",
        "effect": "특허 진입 장벽 완화 및 출원 시간 단축",
    }


@pytest.fixture
def sample_claims(sample_consultation):
    return {
        "claims": [
            {
                "claim_number": 1,
                "claim_type": "method",
                "is_independent": True,
                "depends_on": 0,
                "content": "자연어를 입력받아 특허 명세서를 생성하는 방법",
            }
        ]
    }
