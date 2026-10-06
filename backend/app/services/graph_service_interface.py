from typing import Protocol

from app.models import Campaign
from app.schemas import NetworkData


class GraphProvider(Protocol):
    def get_network(self, campaign: Campaign) -> NetworkData:
        """Return network data for a persisted campaign."""