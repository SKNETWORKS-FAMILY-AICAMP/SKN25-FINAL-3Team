"""
End-to-end 파이프라인 테스트.
mock 구현 기준으로 전체 흐름이 끊기지 않는지 검증합니다.
실제 구현으로 교체 후에도 이 테스트가 통과해야 합니다.
"""


def test_full_pipeline(client):
    # 1. 상담
    consult_resp = client.post("/consult", json={
        "user_input": "AI를 활용한 특허 명세서 자동 작성 시스템",
        "user_id": "user-e2e",
        "session_id": "session-e2e",
    })
    assert consult_resp.status_code == 200
    consultation = consult_resp.json()

    # 2. 청구항 작성
    claims_resp = client.post("/claims", json=consultation)
    assert claims_resp.status_code == 200
    claims = claims_resp.json()

    # 3. 청구항 검토
    examiner_resp = client.post("/examine", json=claims)
    assert examiner_resp.status_code == 200

    # 4. 도면 작성
    drawing_resp = client.post("/drawing", json=claims)
    assert drawing_resp.status_code == 200
    drawing = drawing_resp.json()

    # 5. 발명의 설명 작성
    description_resp = client.post("/description", json={**consultation, **drawing})
    assert description_resp.status_code == 200

    result = description_resp.json()
    assert "detailed_description" in result
