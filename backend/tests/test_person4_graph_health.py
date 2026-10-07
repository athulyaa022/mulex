import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient

GRAPH_DIRECTORY = Path(__file__).resolve().parents[2] / "graph"
if str(GRAPH_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(GRAPH_DIRECTORY))


def test_person4_graph_health_checks_actual_connectivity(monkeypatch) -> None:
    graph_api = importlib.import_module("api")
    monkeypatch.setattr(graph_api, "verify_connectivity", lambda: True)

    with TestClient(graph_api.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["neo4j"] == "connected"


def test_person4_graph_health_reports_neo4j_outage(monkeypatch) -> None:
    graph_api = importlib.import_module("api")

    def unavailable() -> bool:
        raise RuntimeError("connection refused")

    monkeypatch.setattr(graph_api, "verify_connectivity", unavailable)
    with TestClient(graph_api.app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["detail"]["error"] == "Neo4j unavailable"
