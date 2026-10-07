import sys
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.models import Campaign
from app.schemas import (
    CampaignGraphIntelligence,
    NetworkData,
    NetworkEdge,
    NetworkNode,
)
from app.services.graph_service_interface import GraphProvider


class Person4GraphProviderError(RuntimeError):
    """Raised when Person 4's Neo4j provider cannot serve graph intelligence."""


class Person4GraphProvider(GraphProvider):
    def __init__(self, graph_directory: Path | None = None) -> None:
        self._graph_directory = (
            graph_directory or Path(__file__).resolve().parents[3] / "graph"
        ).resolve()

        if str(self._graph_directory) not in sys.path:
            sys.path.insert(0, str(self._graph_directory))

        try:
            from neo4j_connection import configure_credentials

            settings = get_settings()

            configure_credentials(
                settings.neo4j_uri,
                settings.neo4j_username,
                settings.neo4j_password,
            )

        except ImportError as error:
            raise Person4GraphProviderError(
                "Neo4j integration dependencies are missing; "
                "install requirements-graph.txt"
            ) from error

    def get_network(self, campaign: Campaign) -> NetworkData | None:
        try:
            graph_campaign_id = self._resolve_graph_campaign_id(campaign)

            if graph_campaign_id is None:
                return None

            from graph_service import get_campaign_network

            raw_network = get_campaign_network(graph_campaign_id)

            if raw_network is None:
                return None

            summary = raw_network.get("intelligence_summary")

            if summary is None:
                summary = self._get_raw_intelligence(graph_campaign_id)

            return NetworkData(
                campaign_id=campaign.campaign_id,
                nodes=[
                    self._map_node(node)
                    for node in raw_network.get("nodes", [])
                ],
                edges=[
                    self._map_edge(edge)
                    for edge in raw_network.get("edges", [])
                ],
                risk_score=_bounded_score(
                    raw_network.get(
                        "risk_score",
                        campaign.risk_score,
                    )
                ),
                evidence=_string_list(
                    raw_network.get("evidence", [])
                ),
                risk_level=_risk_level(
                    raw_network.get("risk_level")
                ),
                statistics=_statistics(
                    raw_network.get("statistics", {})
                ),
                intelligence_summary=self._map_intelligence(
                    summary,
                    campaign,
                ),
            )

        except Person4GraphProviderError:
            raise

        except Exception as error:
            raise Person4GraphProviderError(
                f"Person 4 graph provider failed: "
                f"{type(error).__name__}: {error}"
            ) from error

    def get_campaign_intelligence(
        self,
        campaign: Campaign,
    ) -> CampaignGraphIntelligence | None:

        try:
            graph_campaign_id = self._resolve_graph_campaign_id(campaign)

            if graph_campaign_id is None:
                return None

            raw = self._get_raw_intelligence(graph_campaign_id)

            if raw is None:
                return None

            return CampaignGraphIntelligence(
                # IMPORTANT:
                # Keep the PostgreSQL campaign ID in the API response.
                campaign_id=campaign.campaign_id,

                # Keep the application's campaign information.
                # We do NOT replace KYC_SCAM with UPI Fraud merely
                # because the graph correlation uses a UPI-heavy campaign.
                campaign_name=campaign.name,
                scam_type=campaign.scam_type,

                # These values come from the Neo4j intelligence layer.
                incident_count=int(
                    raw.get("incident_count", 0)
                ),
                account_count=int(
                    raw.get("account_count", 0)
                ),
                url_count=int(
                    raw.get("url_count", 0)
                ),
                phone_count=int(
                    raw.get("phone_count", 0)
                ),
                upi_count=int(
                    raw.get("upi_count", 0)
                ),

                severity_breakdown=_severity_breakdown(
                    raw.get("severity_breakdown", {})
                ),

                risk_score=_bounded_score(
                    raw.get("risk_score", campaign.risk_score)
                ),

                risk_level=_risk_level(
                    raw.get("risk_level")
                ),

                evidence=_string_list(
                    raw.get("evidence", [])
                ),

                statistics=_statistics(
                    raw.get("statistics", {})
                ),
            )

        except Person4GraphProviderError:
            raise

        except Exception as error:
            raise Person4GraphProviderError(
                f"Person 4 graph provider failed: "
                f"{type(error).__name__}: {error}"
            ) from error

    @staticmethod
    def _resolve_graph_campaign_id(
        campaign: Campaign,
    ) -> str | None:
        """
        Resolve the PostgreSQL application campaign to a campaign
        in the synthetic Neo4j intelligence dataset.

        PostgreSQL uses generated IDs such as:

            CMP-64C13FE3E8DA

        The Person 4 Neo4j dataset uses:

            CAMP001 ... CAMP020
        """

        campaign_id = campaign.campaign_id.upper()

        # ---------------------------------------------------------
        # 1. Direct graph campaign
        # ---------------------------------------------------------
        # If the application is already using a CAMPxxx ID,
        # use it directly.
        if campaign_id.startswith("CAMP"):
            return campaign_id

        # ---------------------------------------------------------
        # 2. Demo correlation based on scam type
        # ---------------------------------------------------------
        #
        # This is intentionally a correlation layer.
        # It does NOT change the application's original scam type.
        #
        # PostgreSQL:
        #     KYC_SCAM
        #
        # Neo4j:
        #     CAMP018 -> UPI Fraud
        #
        # CAMP018 is used because the KYC demo campaign contains
        # a UPI-related entity and CAMP018 provides a populated
        # network in the synthetic graph dataset.
        #
        scam_type = (campaign.scam_type or "").upper().strip()

        scam_type_mapping = {
            "KYC_SCAM": "CAMP018",
            "UPI_SCAM": "CAMP018",
            "UPI FRAUD": "CAMP018",

            "BANK_IMPERSONATION": "CAMP017",
            "PHISHING": "CAMP017",

            "INVESTMENT_SCAM": "CAMP006",
            "JOB_SCAM": "CAMP002",
            "LOAN_SCAM": "CAMP007",

            "MARKETPLACE_SCAM": "CAMP003",
            "ACCOUNT_TAKEOVER": "CAMP004",
            "LOTTERY_SCAM": "CAMP001",
        }

        mapped_campaign = scam_type_mapping.get(scam_type)

        if mapped_campaign:
            return mapped_campaign

        # ---------------------------------------------------------
        # 3. Existing Person 4 resolver as fallback
        # ---------------------------------------------------------
        try:
            from graph_queries import resolve_campaign_id

            entity_values = [
                entity.value
                for incident in campaign.incidents
                for entity in incident.entities
            ]

            return resolve_campaign_id(
                campaign.campaign_id,
                entity_values,
            )

        except (ImportError, AttributeError):
            return None

    @staticmethod
    def _get_raw_intelligence(
        graph_campaign_id: str,
    ) -> dict[str, Any] | None:

        from graph_queries import get_campaign_intelligence

        result = get_campaign_intelligence(
            graph_campaign_id
        )

        if result is None:
            return None

        if isinstance(result, dict) and "error" in result:
            return None

        if not isinstance(result, dict):
            raise Person4GraphProviderError(
                "Campaign graph intelligence has an invalid format"
            )

        return result

    @staticmethod
    def _map_intelligence(
        raw: Any,
        campaign: Campaign,
    ) -> dict[str, Any]:

        if not isinstance(raw, dict):
            return {
                "incident_count": len(campaign.incidents),
                "account_count": 0,
                "url_count": 0,
                "phone_count": 0,
                "upi_count": 0,
                "severity_breakdown": {},
            }

        return {
            "incident_count": int(
                raw.get("incident_count", 0)
            ),
            "account_count": int(
                raw.get("account_count", 0)
            ),
            "url_count": int(
                raw.get("url_count", 0)
            ),
            "phone_count": int(
                raw.get("phone_count", 0)
            ),
            "upi_count": int(
                raw.get("upi_count", 0)
            ),
            "severity_breakdown": _severity_breakdown(
                raw.get("severity_breakdown", {})
            ),
        }

    @staticmethod
    def _map_node(node: Any) -> NetworkNode:

        if not isinstance(node, dict):
            raise Person4GraphProviderError(
                "Graph node has an invalid format"
            )

        node_id = node.get("id")
        node_type = node.get("type") or node.get("label")
        label = node.get("label") or node_type

        if not all(
            isinstance(value, str) and value
            for value in (
                node_id,
                node_type,
                label,
            )
        ):
            raise Person4GraphProviderError(
                "Graph node is missing id/type/label"
            )

        return NetworkNode(
            id=node_id,
            type=node_type.upper(),
            label=label,
        )

    @staticmethod
    def _map_edge(edge: Any) -> NetworkEdge:

        if not isinstance(edge, dict):
            raise Person4GraphProviderError(
                "Graph edge has an invalid format"
            )

        source = edge.get("source")
        target = edge.get("target")
        relationship = edge.get("type")

        if not all(
            isinstance(value, str) and value
            for value in (
                source,
                target,
                relationship,
            )
        ):
            raise Person4GraphProviderError(
                "Graph edge is missing source/target/type"
            )

        return NetworkEdge(
            source=source,
            target=target,
            type=relationship.upper(),
        )


def _bounded_score(value: Any) -> int:

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise Person4GraphProviderError(
            "Graph risk_score must be numeric"
        )

    return max(
        0,
        min(
            100,
            round(value),
        ),
    )


def _risk_level(value: Any) -> str:

    if (
        isinstance(value, str)
        and value.upper()
        in {
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }
    ):
        return value.upper()

    return "LOW"


def _string_list(values: Any) -> list[str]:

    if not isinstance(values, list):
        return []

    return [
        value
        for value in values
        if isinstance(value, str)
    ]


def _severity_breakdown(
    value: Any,
) -> dict[str, int]:

    if not isinstance(value, dict):
        return {}

    return {
        str(key): int(count)
        for key, count in value.items()
        if isinstance(count, int)
        and not isinstance(count, bool)
    }


def _statistics(
    value: Any,
) -> dict[str, int | float | bool | None]:

    if not isinstance(value, dict):
        return {}

    allowed = {
        "incoming_transactions",
        "outgoing_transactions",
        "unique_senders",
        "unique_receivers",
        "incoming_amount",
        "outgoing_amount",
        "rapid_activity",
        "rapid_matches",
        "fastest_pass_through_minutes",
        "connected_accounts",
    }

    return {
        key: item
        for key, item in value.items()
        if key in allowed
        and (
            item is None
            or isinstance(
                item,
                (int, float, bool),
            )
        )
    }