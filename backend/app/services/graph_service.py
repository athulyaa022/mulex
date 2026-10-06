from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Campaign, Incident
from app.schemas import NetworkData
from app.services.graph_service_interface import GraphProvider
from app.services.mock_graph_service import MockGraphProvider

_graph_provider: GraphProvider = MockGraphProvider()


def configure_graph_provider(provider: GraphProvider) -> None:
    global _graph_provider
    _graph_provider = provider


def get_graph_provider() -> GraphProvider:
    return _graph_provider


def get_network(session: Session, campaign_id: str) -> NetworkData | None:
    statement = (
        select(Campaign)
        .where(Campaign.campaign_id == campaign_id)
        .options(selectinload(Campaign.incidents).selectinload(Incident.entities))
    )
    campaign = session.scalar(statement)
    if campaign is None:
        return None
    return get_graph_provider().get_network(campaign)