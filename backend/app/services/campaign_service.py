from collections import Counter
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Campaign, Entity, Incident
from app.schemas import CampaignDetail, CampaignSummary

_CAMPAIGN_NAMES = {
    "KYC_SCAM": "KYC Impersonation Campaign",
    "BANK_IMPERSONATION": "Bank Impersonation Campaign",
    "UPI_SCAM": "UPI Fraud Campaign",
    "INVESTMENT_SCAM": "Investment Scam Campaign",
    "JOB_SCAM": "Job Scam Campaign",
    "DELIVERY_SCAM": "Delivery Scam Campaign",
    "TECH_SUPPORT_SCAM": "Tech Support Scam Campaign",
    "AI_IMPERSONATION": "AI Impersonation Campaign",
    "OTHER": "Other Fraud Campaign",
}


def associate_incident_with_campaign(
    session: Session,
    incident: Incident,
    extracted_entities: list[dict[str, str]],
) -> tuple[Campaign | None, list[str]]:
    shared_entities = _attach_extracted_entities(session, incident, extracted_entities)
    if not shared_entities:
        return None, []

    session.flush()
    statement = (
        select(Incident)
        .where(Incident.id != incident.id, Incident.scam_type == incident.scam_type)
        .options(selectinload(Incident.entities), selectinload(Incident.campaigns))
    )
    candidates = session.scalars(statement).all()
    shared_entity_ids = {entity.id for entity in shared_entities}
    related = [
        candidate
        for candidate in candidates
        if shared_entity_ids.intersection(entity.id for entity in candidate.entities)
    ]
    if not related:
        return None, []

    existing_campaigns = {
        campaign.campaign_id: campaign
        for candidate in related
        for campaign in candidate.campaigns
    }
    if existing_campaigns:
        campaign = existing_campaigns[sorted(existing_campaigns)[0]]
    else:
        campaign = Campaign(
            campaign_id=f"CMP-{uuid4().hex[:12].upper()}",
            name=_CAMPAIGN_NAMES.get(incident.scam_type, "Fraud Campaign"),
            risk_score=max([incident.risk_score, *(item.risk_score for item in related)]),
            scam_type=incident.scam_type,
        )
        session.add(campaign)

    for candidate in related:
        if campaign not in candidate.campaigns:
            candidate.campaigns.append(campaign)
    if campaign not in incident.campaigns:
        incident.campaigns.append(campaign)

    return campaign, sorted(candidate.incident_id for candidate in related)


def list_campaigns(session: Session) -> list[CampaignSummary]:
    statement = (
        select(Campaign)
        .options(selectinload(Campaign.incidents).selectinload(Incident.entities))
        .order_by(Campaign.created_at.desc(), Campaign.id)
    )
    campaigns = session.scalars(statement).all()
    return [
        CampaignSummary(
            campaign_id=campaign.campaign_id,
            name=campaign.name,
            risk_score=campaign.risk_score,
            incident_count=len(campaign.incidents),
            shared_entity_count=len(_shared_entities(campaign)),
        )
        for campaign in campaigns
    ]


def get_campaign(session: Session, campaign_id: str) -> CampaignDetail | None:
    statement = (
        select(Campaign)
        .where(Campaign.campaign_id == campaign_id)
        .options(selectinload(Campaign.incidents).selectinload(Incident.entities))
    )
    campaign = session.scalar(statement)
    if campaign is None:
        return None

    return CampaignDetail(
        campaign_id=campaign.campaign_id,
        name=campaign.name,
        risk_score=campaign.risk_score,
        incident_count=len(campaign.incidents),
        shared_entities=_shared_entities(campaign),
        related_incidents=sorted(incident.incident_id for incident in campaign.incidents),
    )


def _attach_extracted_entities(
    session: Session,
    incident: Incident,
    extracted_entities: list[dict[str, str]],
) -> list[Entity]:
    attached: list[Entity] = []
    for extracted in extracted_entities:
        entity_type = extracted.get("type") or extracted.get("entity_type")
        value = extracted.get("value")
        if not entity_type or not value:
            continue

        entity = session.scalar(
            select(Entity).where(Entity.entity_type == entity_type, Entity.value == value)
        )
        if entity is None:
            entity = Entity(
                entity_id=f"ENT-{uuid4().hex[:12].upper()}",
                entity_type=entity_type,
                value=value,
            )
            session.add(entity)
        if entity not in incident.entities:
            incident.entities.append(entity)
        attached.append(entity)
    return attached


def _shared_entities(campaign: Campaign) -> list[dict[str, str]]:
    entity_occurrences: Counter[str] = Counter(
        entity.entity_id
        for incident in campaign.incidents
        for entity in incident.entities
    )
    distinct_entities = {
        entity.entity_id: entity
        for incident in campaign.incidents
        for entity in incident.entities
    }
    return [
        {
            "entity_id": entity.entity_id,
            "type": entity.entity_type,
            "value": entity.value,
        }
        for entity_id, entity in sorted(distinct_entities.items())
        if entity_occurrences[entity_id] > 1
    ]