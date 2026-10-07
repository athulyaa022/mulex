import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.models import Campaign
from app.schemas import FraudAnalysis
from app.services import graph_service
from app.services.graph_service import GraphProviderError
from app.services.person4_graph_provider import Person4GraphProvider, Person4GraphProviderError


def _campaign() -> Campaign:
    return Campaign(
        campaign_id="CMP-app-1",
        name="KYC Impersonation Campaign",
        risk_score=84,
        scam_type="KYC_SCAM",
        incidents=[],
    )


def _install_fake_graph(monkeypatch: pytest.MonkeyPatch, *, campaign_id: str | None = "CAMP003") -> None:
    connection = types.ModuleType("neo4j_connection")
    connection.configure_credentials = lambda *credentials: None
    queries = types.ModuleType("graph_queries")
    queries.resolve_campaign_id = lambda app_id, values: campaign_id
    queries.get_campaign_intelligence = lambda graph_id: {
        "campaign_id": graph_id,
        "campaign_name": "Synthetic graph campaign",
        "scam_type": "UPI Fraud",
        "incident_count": 4,
        "account_count": 5,
        "url_count": 2,
        "phone_count": 3,
        "upi_count": 4,
        "severity_breakdown": {"High": 3, "Medium": 1},
        "risk_score": 76,
        "risk_level": "HIGH",
    }
    graph_module = types.ModuleType("graph_service")
    graph_module.get_campaign_network = lambda graph_id: {
        "graph_campaign_id": graph_id,
        "nodes": [
            {"id": "ACC0001", "type": "Account", "label": "Account"},
            {"id": "TXN0001", "type": "Transaction", "label": "Transaction"},
        ],
        "edges": [{"source": "ACC0001", "target": "TXN0001", "type": "SENT"}],
        "risk_score": 88,
        "risk_level": "HIGH",
        "evidence": ["Synthetic rapid pass-through evidence"],
        "statistics": {"unique_senders": 7, "rapid_activity": True, "rapid_matches": 2},
        "intelligence_summary": {"incident_count": 4, "account_count": 5},
    }
    monkeypatch.setitem(sys.modules, "graph_queries", queries)
    monkeypatch.setitem(sys.modules, "graph_service", graph_module)
    monkeypatch.setitem(sys.modules, "neo4j_connection", connection)


def test_person4_provider_maps_graph_contract_to_application_campaign(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_fake_graph(monkeypatch)
    provider = Person4GraphProvider(graph_directory=tmp_path)

    network = provider.get_network(_campaign())
    intelligence = provider.get_campaign_intelligence(_campaign())

    assert network is not None
    assert network.campaign_id == "CMP-app-1"
    assert network.risk_score == 88
    assert network.risk_level == "HIGH"
    assert network.nodes[0].type == "ACCOUNT"
    assert network.edges[0].type == "SENT"
    assert network.statistics["rapid_activity"] is True
    assert network.intelligence_summary["incident_count"] == 4
    assert intelligence is not None
    assert intelligence.campaign_id == "CMP-app-1"
    assert intelligence.account_count == 5


def test_person4_missing_graph_campaign_returns_none(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _install_fake_graph(monkeypatch, campaign_id=None)
    provider = Person4GraphProvider(graph_directory=tmp_path)

    assert provider.get_network(_campaign()) is None
    assert provider.get_campaign_intelligence(_campaign()) is None


def test_person4_malformed_node_is_a_clear_provider_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_fake_graph(monkeypatch)
    graph_module = sys.modules["graph_service"]
    graph_module.get_campaign_network = lambda graph_id: {
        "nodes": [{"properties": {"neo4j_internal": "hidden"}}],
        "edges": [],
        "risk_score": 10,
        "evidence": [],
    }
    provider = Person4GraphProvider(graph_directory=tmp_path)

    with pytest.raises(Person4GraphProviderError, match="Graph node is missing"):
        provider.get_network(_campaign())


def test_graph_provider_selection_is_mock_by_default_and_person4_on_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.config import get_settings
    from app.services.person4_graph_provider import Person4GraphProvider

    graph_service.configure_graph_provider(None)
    monkeypatch.setenv("GRAPH_PROVIDER", "mock")
    get_settings.cache_clear()
    try:
        assert graph_service.get_graph_provider().__class__.__name__ == "MockGraphProvider"
        monkeypatch.setenv("GRAPH_PROVIDER", "person4")
        get_settings.cache_clear()
        assert isinstance(graph_service.get_graph_provider(), Person4GraphProvider)
    finally:
        get_settings.cache_clear()
        graph_service.configure_graph_provider(None)


def test_graph_provider_failure_is_raised_not_mocked():
    class FailedProvider:
        def get_network(self, campaign):
            raise RuntimeError("Neo4j unavailable")

        def get_campaign_intelligence(self, campaign):
            raise RuntimeError("Neo4j unavailable")

    previous = graph_service.get_graph_provider()
    graph_service.configure_graph_provider(FailedProvider())
    try:
        with pytest.raises(GraphProviderError, match="Neo4j unavailable"):
            graph_service.get_network(
                SimpleNamespace(scalar=lambda statement: _campaign()), "CMP-1"
            )
    finally:
        graph_service.configure_graph_provider(previous)
