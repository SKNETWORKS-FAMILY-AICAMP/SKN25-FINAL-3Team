def test_examiner_returns_200(client, sample_claims):
    response = client.post("/examine", json=sample_claims)
    assert response.status_code == 200


def test_examiner_has_registerable_field(client, sample_claims):
    response = client.post("/examine", json=sample_claims)
    data = response.json()
    assert "is_registerable" in data
    assert isinstance(data["is_registerable"], bool)
