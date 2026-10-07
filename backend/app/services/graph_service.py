from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.models import Campaign, Incident
from app.schemas import CampaignGraphIntelligence, NetworkData
from app.services.graph_service_interface import GraphProvider
from app.services.mock_graph_service import MockGraphProvider


_configured_graph_provider: GraphProvider | None = None
_mock_graph_provider = MockGraphProvider()


class GraphProviderError(RuntimeError):
    """Raised when configured graph intelligence is unavailable or invalid."""


def configure_graph_provider(provider: GraphProvider) -> None:
    global _configured_graph_provider
    _configured_graph_provider = provider


@lru_cache
def _provider_for_selection(provider_name: str) -> GraphProvider:
    if provider_name == "mock":
        return _mock_graph_provider

    if provider_name == "person4":
        from app.services.person4_graph_provider import Person4GraphProvider

        return Person4GraphProvider()

    raise ValueError(
        f"Unsupported GRAPH_PROVIDER: {provider_name}"
    )


def get_graph_provider() -> GraphProvider:
    if _configured_graph_provider is not None:
        return _configured_graph_provider

    return _provider_for_selection(
        get_settings().graph_provider.casefold()
    )


def get_network(
    session: Session,
    campaign_id: str,
) -> NetworkData | None:

    statement = (
        select(Campaign)
        .where(Campaign.campaign_id == campaign_id)
        .options(
            selectinload(Campaign.incidents)
            .selectinload(Incident.entities)
        )
    )

    campaign = session.scalar(statement)

    # Allow explicit Person 4 graph campaigns such as CAMP007
    # even when they do not exist in PostgreSQL.
    if campaign is None:

        if (
            get_settings().graph_provider.casefold() == "person4"
            and campaign_id.upper().startswith("CAMP")
        ):
            campaign = Campaign(
                campaign_id=campaign_id,
                name=campaign_id,
                risk_score=0,
                scam_type="UNKNOWN",
            )
        else:
            return None

    try:
        return get_graph_provider().get_network(campaign)

    except GraphProviderError:
        raise

    except Exception as error:
        raise GraphProviderError(
            f"Graph provider request failed: {error}"
        ) from error


def get_campaign_intelligence(
    session: Session,
    campaign_id: str,
) -> CampaignGraphIntelligence | None:

    campaign = session.scalar(
        select(Campaign).where(
            Campaign.campaign_id == campaign_id
        )
    )

    # Allow explicit Person 4 graph campaigns such as CAMP007
    # even when they do not exist in PostgreSQL.
    if campaign is None:

        if (
            get_settings().graph_provider.casefold() == "person4"
            and campaign_id.upper().startswith("CAMP")
        ):
            campaign = Campaign(
                campaign_id=campaign_id,
                name=campaign_id,
                risk_score=0,
                scam_type="UNKNOWN",
            )
        else:
            return None

    try:
        return get_graph_provider().get_campaign_intelligence(
            campaign
        )

    except GraphProviderError:
        raise

    except Exception as error:
        raise GraphProviderError(
            f"Graph provider request failed: {error}"
        ) from error