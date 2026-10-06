from typing import Protocol

from app.models import Campaign
from app.schemas import CampaignGraphIntelligence, NetworkData


class GraphProvider(Protocol):
    def get_network(self, campaign: Campaign) -> NetworkData | None:
        """Return network data for a persisted campaign."""

    def get_campaign_intelligence(
        self, campaign: Campaign
    ) -> CampaignGraphIntelligence | None:
        """Return graph intelligence associated with an application campaign."""