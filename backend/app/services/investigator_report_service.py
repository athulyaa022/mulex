from sqlalchemy.orm import Session

from app.models import Campaign
from app.schemas import InvestigatorCampaignOverview, InvestigatorReport
from app.services.graph_service import get_campaign_intelligence


def build_investigator_report(
    session: Session, campaign_id: str
) -> InvestigatorReport | None:
    campaign: Campaign | None = session.query(Campaign).filter_by(campaign_id=campaign_id).first()
    if campaign is None:
        return None
    intelligence = get_campaign_intelligence(session, campaign_id)
    overview = InvestigatorCampaignOverview(
        incident_count=(intelligence.incident_count if intelligence else len(campaign.incidents)),
        connected_accounts=(intelligence.account_count if intelligence else 0),
        connected_urls=(intelligence.url_count if intelligence else 0),
        connected_phones=(intelligence.phone_count if intelligence else 0),
        connected_upi_ids=(intelligence.upi_count if intelligence else 0),
    )
    findings: list[str] = []
    factors: list[str] = []
    patterns: list[str] = []
    evidence = list(intelligence.evidence) if intelligence else []
    stats = intelligence.statistics if intelligence else {}
    if overview.incident_count:
        findings.append(f"Graph intelligence links {overview.incident_count} incident(s) to this campaign.")
    if overview.connected_accounts:
        findings.append(f"The graph connects {overview.connected_accounts} account(s).")
    if overview.connected_urls or overview.connected_phones or overview.connected_upi_ids:
        findings.append(
            f"Linked identifiers: {overview.connected_urls} URL(s), "
            f"{overview.connected_phones} phone(s), and {overview.connected_upi_ids} UPI ID(s)."
        )
    if campaign.risk_score >= 70:
        factors.append(f"Application campaign risk score is {campaign.risk_score}/100.")
    if stats.get("unique_senders", 0):
        factors.append(f"Funds arrive from {stats['unique_senders']} distinct sender(s).")
    if stats.get("rapid_activity"):
        patterns.append(
            f"Rapid pass-through activity observed in {stats.get('rapid_matches', 0)} transaction pair(s)."
        )
    if stats.get("incoming_transactions") or stats.get("outgoing_transactions"):
        patterns.append(
            f"Observed {stats.get('incoming_transactions', 0)} incoming and "
            f"{stats.get('outgoing_transactions', 0)} outgoing transaction(s)."
        )
    linked_entities = [
        {"entity_id": entity.entity_id, "type": entity.entity_type, "value": entity.value}
        for entity in sorted(
            {entity.entity_id: entity for incident in campaign.incidents for entity in incident.entities}.values(),
            key=lambda item: item.entity_id,
        )
    ]
    risk_score = max(campaign.risk_score, intelligence.risk_score if intelligence else 0)
    risk_level = (
        intelligence.risk_level if intelligence and intelligence.risk_score >= campaign.risk_score
        else "CRITICAL" if risk_score >= 90
        else "HIGH" if risk_score >= 70
        else "MEDIUM" if risk_score >= 40
        else "LOW"
    )
    recommendations = [
        "Review accounts receiving funds from multiple unrelated sources.",
        "Compare shared UPI identifiers across linked incidents.",
    ]
    if stats.get("rapid_activity"):
        recommendations.append(
            "Review rapid pass-through transactions occurring within the observed time window."
        )
    return InvestigatorReport(
        campaign_id=campaign.campaign_id,
        campaign_name=campaign.name,
        scam_type=campaign.scam_type,
        risk_score=risk_score,
        risk_level=risk_level,
        executive_summary=(
            f"Demo intelligence summary for {campaign.name}: {overview.incident_count} linked "
            f"incident(s), application risk score {risk_score}/100. This uses synthetic/demo data."
        ),
        campaign_overview=overview,
        network_findings=findings,
        risk_factors=factors,
        transaction_patterns=patterns,
        linked_entities=linked_entities,
        evidence=evidence,
        recommended_actions=recommendations,
    )
