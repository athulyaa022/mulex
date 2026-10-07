from sqlalchemy.orm import Session

from app.models import Campaign
from app.schemas import (
    InvestigatorCampaignOverview,
    InvestigatorReport,
    InvestigatorReportItem,
)
from app.services.graph_service import get_campaign_intelligence


def build_investigator_report(
    session: Session, campaign_id: str
) -> InvestigatorReport | None:

    campaign: Campaign | None = (
        session.query(Campaign)
        .filter_by(campaign_id=campaign_id)
        .first()
    )

    if campaign is None:
        return None

    # Get Neo4j campaign intelligence
    intelligence = get_campaign_intelligence(
        session,
        campaign_id,
    )

    # ---------------------------------------------------------
    # Campaign overview
    # ---------------------------------------------------------

    overview = InvestigatorCampaignOverview(
        incident_count=(
            int(intelligence.incident_count)
            if intelligence
            else len(campaign.incidents)
        ),
        connected_accounts=(
            int(intelligence.account_count)
            if intelligence
            else 0
        ),
        connected_urls=(
            int(intelligence.url_count)
            if intelligence
            else 0
        ),
        connected_phones=(
            int(intelligence.phone_count)
            if intelligence
            else 0
        ),
        connected_upi_ids=(
            int(intelligence.upi_count)
            if intelligence
            else 0
        ),
    )

    # ---------------------------------------------------------
    # Network intelligence
    # ---------------------------------------------------------

    findings: list[str] = []
    factors: list[str] = []
    patterns: list[str] = []

    evidence = (
        list(intelligence.evidence)
        if intelligence
        else []
    )

    stats = (
        intelligence.statistics
        if intelligence
        else {}
    )

    if overview.incident_count:
        findings.append(
            f"Graph intelligence links "
            f"{overview.incident_count} incident(s) to this campaign."
        )

    if overview.connected_accounts:
        findings.append(
            f"The graph connects "
            f"{overview.connected_accounts} account(s)."
        )

    if (
        overview.connected_urls
        or overview.connected_phones
        or overview.connected_upi_ids
    ):
        findings.append(
            f"Linked identifiers: "
            f"{overview.connected_urls} URL(s), "
            f"{overview.connected_phones} phone(s), and "
            f"{overview.connected_upi_ids} UPI ID(s)."
        )

    # ---------------------------------------------------------
    # Risk factors
    # ---------------------------------------------------------

    if campaign.risk_score >= 70:
        factors.append(
            f"Application campaign risk score is "
            f"{campaign.risk_score}/100."
        )

    if stats.get("unique_senders", 0):
        factors.append(
            f"Funds arrive from "
            f"{stats['unique_senders']} distinct sender(s)."
        )

    # ---------------------------------------------------------
    # Transaction patterns
    # ---------------------------------------------------------

    if stats.get("rapid_activity"):
        patterns.append(
            f"Rapid pass-through activity observed in "
            f"{stats.get('rapid_matches', 0)} transaction pair(s)."
        )

    if (
        stats.get("incoming_transactions")
        or stats.get("outgoing_transactions")
    ):
        patterns.append(
            f"Observed "
            f"{stats.get('incoming_transactions', 0)} incoming and "
            f"{stats.get('outgoing_transactions', 0)} outgoing "
            f"transaction(s)."
        )

    # ---------------------------------------------------------
    # Linked entities
    # ---------------------------------------------------------

    linked_entities = [
        {
            "entity_id": entity.entity_id,
            "type": entity.entity_type,
            "value": entity.value,
        }
        for entity in sorted(
            {
                entity.entity_id: entity
                for incident in campaign.incidents
                for entity in incident.entities
            }.values(),
            key=lambda item: item.entity_id,
        )
    ]

    # ---------------------------------------------------------
    # Campaign reports
    #
    # IMPORTANT:
    # Investigators do NOT receive citizen identity.
    # Reports are visible only through the relevant campaign.
    # ---------------------------------------------------------

    reports: list[InvestigatorReportItem] = []

    for incident in campaign.incidents:

        for report in incident.reports:

            reports.append(
                InvestigatorReportItem(
                    report_id=report.report_id,
                    incident_id=report.incident.incident_id,

                    # Citizen identity is never exposed.
                    reporter="Anonymous Citizen",

                    description=report.description,

                    # Protect possible citizen phone information.
                    phone=_mask_phone(report.phone),

                    # These are retained because they may be useful
                    # as fraud indicators/network evidence.
                    upi_id=report.upi_id,
                    url=report.url,

                    created_at=report.created_at,
                )
            )

    # Newest reports first
    reports.sort(
        key=lambda item: item.created_at,
        reverse=True,
    )

    # ---------------------------------------------------------
    # Final risk calculation
    # ---------------------------------------------------------

    risk_score = max(
        campaign.risk_score,
        intelligence.risk_score
        if intelligence
        else 0,
    )

    if (
        intelligence
        and intelligence.risk_score >= campaign.risk_score
    ):
        risk_level = intelligence.risk_level

    elif risk_score >= 90:
        risk_level = "CRITICAL"

    elif risk_score >= 70:
        risk_level = "HIGH"

    elif risk_score >= 40:
        risk_level = "MEDIUM"

    else:
        risk_level = "LOW"

    # ---------------------------------------------------------
    # Investigator recommendations
    # ---------------------------------------------------------

    recommendations = [
        "Review accounts receiving funds from multiple unrelated sources.",
        "Compare shared UPI identifiers across linked incidents.",
    ]

    if stats.get("rapid_activity"):
        recommendations.append(
            "Review rapid pass-through transactions occurring "
            "within the observed time window."
        )

    # ---------------------------------------------------------
    # Final investigator report
    # ---------------------------------------------------------

    return InvestigatorReport(
        campaign_id=campaign.campaign_id,
        campaign_name=campaign.name,
        scam_type=campaign.scam_type,
        risk_score=risk_score,
        risk_level=risk_level,

        executive_summary=(
            f"Demo intelligence summary for {campaign.name}: "
            f"{overview.incident_count} linked incident(s), "
            f"application risk score {risk_score}/100. "
            f"This uses synthetic/demo data."
        ),

        campaign_overview=overview,

        network_findings=findings,

        risk_factors=factors,

        transaction_patterns=patterns,

        linked_entities=linked_entities,

        evidence=evidence,

        recommended_actions=recommendations,

        # Reports are available only inside this campaign.
        reports=reports,
    )


def _mask_phone(phone: str | None) -> str | None:
    """
    Protect citizen phone numbers while retaining
    enough information to show that a phone exists.
    """

    if not phone:
        return None

    digits = "".join(
        character
        for character in phone
        if character.isdigit()
    )

    if len(digits) <= 4:
        return "****"

    return f"******{digits[-4:]}"