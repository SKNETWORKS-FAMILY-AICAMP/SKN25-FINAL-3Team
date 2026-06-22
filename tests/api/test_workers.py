"""FastAPI drawing, specification, and patent-search worker unit tests."""

from types import SimpleNamespace

from agents.core.state import (
    PatentDrawing,
    PatentDrawingSpecification,
    ReferenceMapping,
)
from backend.fastapi.routers import drawings, patent_search, specification


def test_main_app_registers_current_worker_routes(client):
    paths = {route.path for route in client.app.routes}

    assert {
        "/api/v1/generate-claims",
        "/api/v1/review-claims",
        "/api/v1/generate-drawings",
        "/api/v1/patent-search",
        "/api/v1/generate-specification",
    }.issubset(paths)


def test_generate_specification_returns_success(client, monkeypatch):
    monkeypatch.setattr(
        specification,
        "run_specification_agent",
        lambda state: {"status": "ok", "technical_field": state["field"]},
    )

    response = client.post(
        "/api/v1/generate-specification",
        json={"agent_state": {"field": "데이터 처리"}},
    )

    assert response.status_code == 200
    assert response.json()["result"]["technical_field"] == "데이터 처리"


def test_generate_specification_maps_failed_result_to_500(client, monkeypatch):
    monkeypatch.setattr(
        specification,
        "run_specification_agent",
        lambda _state: {"status": "failed", "warnings": ["근거 부족"]},
    )

    response = client.post("/api/v1/generate-specification", json={"agent_state": {}})

    assert response.status_code == 500
    assert "근거 부족" in response.json()["message"]


def test_generate_specification_maps_exception_to_500(client, monkeypatch):
    def fail(_state):
        raise RuntimeError("generation failed")

    monkeypatch.setattr(specification, "run_specification_agent", fail)

    response = client.post("/api/v1/generate-specification", json={"agent_state": {}})

    assert response.status_code == 500
    assert response.json()["message"] == "generation failed"


def test_generate_drawings_uploads_and_removes_local_file(client, monkeypatch, tmp_path):
    image_path = tmp_path / "drawing.png"
    image_path.write_bytes(b"png-data")
    drawing_spec = PatentDrawingSpecification(
        drawings=[
            PatentDrawing(
                fig_no="도 1",
                title="시스템 구성도",
                diagram_type="BLOCK_DIAGRAM",
                dot_code="digraph {}",
                image_path=str(image_path),
            )
        ],
        reference_numerals=[
            ReferenceMapping(component_id="COMP_001", name="분석부", numeral="110")
        ],
    )

    class Summary:
        def __init__(self, **_kwargs):
            pass

        def run(self, state):
            return {"summary_data": state["mock_input_data"]}

    class Drawing:
        def run(self, _state):
            return {"drawing_spec": drawing_spec}

    uploaded = {}
    monkeypatch.setattr(drawings, "SummaryAgent", Summary)
    monkeypatch.setattr(drawings, "SmartDrawingAgent", Drawing)
    def capture_upload(**kwargs):
        uploaded.update({key: value for key, value in kwargs.items() if key != "Body"})
        uploaded["body"] = kwargs["Body"].read()

    monkeypatch.setattr(drawings.s3_client, "put_object", capture_upload)

    response = client.post(
        "/api/v1/generate-drawings",
        json={"mock_input_data": {"title": "발명"}, "user_id": 7, "project_id": 9},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "user_7/project_9" in uploaded["Key"]
    assert uploaded["body"] == b"png-data"
    assert image_path.exists() is False


def test_generate_drawings_returns_500_when_agent_has_no_spec(client, monkeypatch):
    class Summary:
        def __init__(self, **_kwargs):
            pass

        def run(self, _state):
            return {"summary_data": None}

    class Drawing:
        def run(self, _state):
            return {"drawing_spec": None}

    monkeypatch.setattr(drawings, "SummaryAgent", Summary)
    monkeypatch.setattr(drawings, "SmartDrawingAgent", Drawing)

    response = client.post("/api/v1/generate-drawings", json={"mock_input_data": {}})

    assert response.status_code == 500
    assert "실패" in response.json()["message"]


def test_patent_search_normalizes_single_xml_item(client, monkeypatch):
    xml = """
    <response><body><items><item>
      <inventionTitle>센서 시스템</inventionTitle>
      <applicationNumber>10-2024-0000001</applicationNumber>
      <applicantName>테스트 주식회사</applicantName>
      <applicationDate>20240101</applicationDate>
      <astrtCont>센서를 이용한다.</astrtCont>
    </item></items></body></response>
    """
    monkeypatch.setattr(
        patent_search.requests,
        "get",
        lambda _url: SimpleNamespace(text=xml),
    )

    response = client.get("/api/v1/patent-search", params={"query": "센서 분석"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "title": "센서 시스템",
            "applicationNumber": "10-2024-0000001",
            "applicant": "테스트 주식회사",
            "date": "20240101",
            "abstract": "센서를 이용한다.",
        }
    ]


def test_patent_search_requires_query(client):
    assert client.get("/api/v1/patent-search").status_code == 422
