def test_consult_returns_200(client):
    response = client.post("/consult", json={
        "user_input": "스마트폰으로 실시간 번역하는 장치를 발명했습니다",
        "user_id": "user-001",
        "session_id": "session-001",
    })
    assert response.status_code == 200


def test_consult_response_has_required_fields(client):
    response = client.post("/consult", json={
        "user_input": "테스트 발명",
        "user_id": "user-001",
        "session_id": "session-001",
    })
    data = response.json()
    assert "invention_flow" in data
    assert "problem" in data
    assert "differentiation" in data
    assert "effect" in data


def test_consult_missing_field_returns_422(client):
    response = client.post("/consult", json={"user_input": "테스트"})
    assert response.status_code == 422
