def test_claims_returns_200(client, sample_consultation):
    response = client.post("/claims", json=sample_consultation)
    assert response.status_code == 200


def test_claims_contains_independent_claim(client, sample_consultation):
    response = client.post("/claims", json=sample_consultation)
    claims = response.json()["claims"]
    assert any(c["is_independent"] for c in claims)


def test_claims_contain_multiple_types(client, sample_consultation):
    response = client.post("/claims", json=sample_consultation)
    types = {c["claim_type"] for c in response.json()["claims"]}
    assert len(types) >= 1
