from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_frontend_shell_and_assets_are_served():
    page = client.get("/")
    assert page.status_code == 200
    assert "ScamGuard" in page.text

    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200
