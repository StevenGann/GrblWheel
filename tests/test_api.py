"""API tests using FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient

from grblwheel.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_health(client: TestClient):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "grblwheel"


def test_root_without_frontend(client: TestClient):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "message" in data or "GrblWheel" in data.get("message", "")


def test_serial_ports(client: TestClient):
    r = client.get("/api/serial/ports")
    assert r.status_code == 200
    assert "ports" in r.json()


def test_serial_state_disconnected(client: TestClient):
    r = client.get("/api/serial/state")
    assert r.status_code == 200
    data = r.json()
    assert data["connected"] is False


def test_macros_list(client: TestClient):
    r = client.get("/api/macros")
    assert r.status_code == 200
    data = r.json()
    assert "macros" in data
    assert "zero_xy" in data["macros"] or len(data["macros"]) >= 0


def test_job_status(client: TestClient):
    r = client.get("/api/job/status")
    assert r.status_code == 200
    data = r.json()
    assert data["state"] in ("idle", "running", "paused", "done", "error")
