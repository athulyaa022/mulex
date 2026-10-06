from app.models import Campaign, Incident
from app.schemas import CampaignGraphIntelligence, NetworkData, NetworkEdge, NetworkNode
from app.services.graph_service_interface import GraphProvider


class MockGraphProvider(GraphProvider):
    def get_network(self, campaign: Campaign) -> NetworkData:
        nodes: list[NetworkNode] = []
        edges: list[NetworkEdge] = []
        for incident in sorted(campaign.incidents, key=lambda item: item.incident_id):
            victim_id = f"VICTIM-{incident.incident_id}"
            nodes.extend(
                [
                    NetworkNode(id=victim_id, type="VICTIM", label="Synthetic Victim"),
                    NetworkNode(
                        id=incident.incident_id,
                        type="INCIDENT",
                        label=f"{incident.scam_type.replace('_', ' ').title()} Incident",
                    ),
                ]
            )
            edges.extend(
                [
                    NetworkEdge(source=victim_id, target=incident.incident_id, type="REPORTED"),
                    NetworkEdge(
                        source=incident.incident_id,
                        target=campaign.campaign_id,
                        type="PART_OF",
                    ),
                ]
            )

        mule_id = f"MULE-{campaign.campaign_id}"
        transaction_id = f"TRANSACTION-{campaign.campaign_id}-01"
        layering_account_id = f"ACCOUNT-{campaign.campaign_id}-LAYER-01"
        beneficiary_id = f"BENEFICIARY-{campaign.campaign_id}"
        nodes.extend(
            [
                NetworkNode(id=campaign.campaign_id, type="CAMPAIGN", label=campaign.name),
                NetworkNode(id=mule_id, type="MULE", label="Masked Mule Account"),
                NetworkNode(id=transaction_id, type="TRANSACTION", label="Synthetic Transfer"),
                NetworkNode(
                    id=layering_account_id,
                    type="ACCOUNT",
                    label="Masked Layering Account",
                ),
                NetworkNode(
                    id=beneficiary_id,
                    type="BENEFICIARY",
                    label="Synthetic Beneficiary",
                ),
            ]
        )
        edges.extend(
            [
                NetworkEdge(source=campaign.campaign_id, target=mule_id, type="LINKED_TO"),
                NetworkEdge(source=mule_id, target=transaction_id, type="TRANSFERRED"),
                NetworkEdge(
                    source=transaction_id,
                    target=layering_account_id,
                    type="TRANSFERRED_TO",
                ),
                NetworkEdge(
                    source=layering_account_id,
                    target=beneficiary_id,
                    type="TRANSFERRED_TO",
                ),
            ]
        )

        shared_entities = _shared_entities(campaign.incidents)
        evidence = [
            f"{len(campaign.incidents)} incident(s) linked to this campaign.",
            "Synthetic transaction path illustrates a mule, layering account, and beneficiary.",
        ]
        if shared_entities:
            evidence.append(
                f"{len(shared_entities)} shared identifier(s) connect the incidents."
            )

        return NetworkData(
            campaign_id=campaign.campaign_id,
            nodes=nodes,
            edges=edges,
            risk_score=campaign.risk_score,
            evidence=evidence,
            risk_level="HIGH" if campaign.risk_score >= 70 else "MEDIUM" if campaign.risk_score >= 40 else "LOW",
            statistics={
                "incoming_transactions": 0,
                "outgoing_transactions": 0,
                "unique_senders": 0,
                "unique_receivers": 0,
                "incoming_amount": 0.0,
                "outgoing_amount": 0.0,
                "rapid_activity": False,
                "rapid_matches": 0,
                "fastest_pass_through_minutes": None,
                "connected_accounts": 3,
            },
        )

    def get_campaign_intelligence(
        self, campaign: Campaign
    ) -> CampaignGraphIntelligence:
        shared_entity_count = len(_shared_entities(campaign.incidents))
        entities = [entity for incident in campaign.incidents for entity in incident.entities]
        severity = (
            "CRITICAL" if campaign.risk_score >= 90 else
            "HIGH" if campaign.risk_score >= 70 else
            "MEDIUM" if campaign.risk_score >= 40 else "LOW"
        )
        return CampaignGraphIntelligence(
            campaign_id=campaign.campaign_id,
            campaign_name=campaign.name,
            scam_type=campaign.scam_type,
            incident_count=len(campaign.incidents),
            account_count=3 if campaign.incidents else 0,
            url_count=sum(entity.entity_type == "URL" for entity in entities),
            phone_count=sum(entity.entity_type == "PHONE" for entity in entities),
            upi_count=sum(entity.entity_type == "UPI" for entity in entities),
            severity_breakdown={severity: len(campaign.incidents)},
            risk_score=campaign.risk_score,
            risk_level="HIGH" if campaign.risk_score >= 70 else "MEDIUM" if campaign.risk_score >= 40 else "LOW",
            evidence=[
                f"{len(campaign.incidents)} application incident(s) linked.",
                f"{shared_entity_count} shared identifier(s) found in application data.",
            ],
            statistics={
                "incoming_transactions": 0,
                "outgoing_transactions": 0,
                "unique_senders": 0,
                "unique_receivers": 0,
                "incoming_amount": 0.0,
                "outgoing_amount": 0.0,
                "rapid_activity": False,
                "rapid_matches": 0,
                "fastest_pass_through_minutes": None,
            },
        )


def _shared_entities(incidents: list[Incident]) -> set[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    shared: set[tuple[str, str]] = set()
    for incident in incidents:
        incident_entities = {
            (entity.entity_type, entity.value) for entity in incident.entities
        }
        shared.update(seen.intersection(incident_entities))
        seen.update(incident_entities)
    return shared