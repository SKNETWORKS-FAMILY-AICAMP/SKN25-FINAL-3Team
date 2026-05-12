def test_drawing_returns_200(client, sample_claims):
    response = client.post("/drawing", json=sample_claims)
    assert response.status_code == 200


def test_drawing_returns_mermaid_code(client, sample_claims):
    response = client.post("/drawing", json=sample_claims)
    data = response.json()
    assert "flowchart_code" in data
    assert "flowchart" in data["flowchart_code"]
