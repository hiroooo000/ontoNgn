from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_graph_ui_endpoint() -> None:
    response = client.get("/graph")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'id="app"' in response.text
