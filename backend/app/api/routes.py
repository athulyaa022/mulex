from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Incident
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    CampaignDetail,
    CampaignList,
    IncidentDetail,
    IncidentList,
    IncidentSummary,
    NetworkData,
    ReportCreate,
    ReportSubmitted,
)
from app.services.analysis_service import analyze_and_persist
from app.services.campaign_service import get_campaign, list_campaigns
from app.services.graph_service import get_network
from app.services.report_service import create_report, get_incident, list_incidents

router = APIRouter(prefix="/api/v1")


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_text(
    request: AnalyzeRequest, session: Session = Depends(get_db)
) -> AnalyzeResponse:
    incident, analysis, campaign_id, related_incidents = analyze_and_persist(
        session, request.text
    )
    return AnalyzeResponse(
        incident_id=incident.incident_id,
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        scam_type=analysis.scam_type,
        confidence=analysis.confidence,
        entities=analysis.entities,
        indicators=analysis.indicators,
        related_incidents=related_incidents,
        campaign_id=campaign_id,
    )


@router.post("/reports", response_model=ReportSubmitted)
def submit_report(report_data: ReportCreate, session: Session = Depends(get_db)) -> ReportSubmitted:
    report = create_report(session, report_data)
    return ReportSubmitted(
        report_id=report.report_id,
        incident_id=report.incident.incident_id,
        status="received",
    )


@router.get("/incidents", response_model=IncidentList)
def get_incidents(session: Session = Depends(get_db)) -> IncidentList:
    incidents = list_incidents(session)
    return IncidentList(incidents=[IncidentSummary.model_validate(item) for item in incidents])


@router.get("/incidents/{incident_id}", response_model=IncidentDetail)
def get_incident_by_id(
    incident_id: str, session: Session = Depends(get_db)
) -> IncidentDetail:
    incident = get_incident(session, incident_id)
    if incident is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "INCIDENT_NOT_FOUND", "message": "Incident does not exist"},
        )
    return _incident_detail(incident)


@router.get("/campaigns", response_model=CampaignList)
def get_campaigns(session: Session = Depends(get_db)) -> CampaignList:
    return CampaignList(campaigns=list_campaigns(session))


@router.get("/campaigns/{campaign_id}", response_model=CampaignDetail)
def get_campaign_by_id(
    campaign_id: str, session: Session = Depends(get_db)
) -> CampaignDetail:
    campaign = get_campaign(session, campaign_id)
    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": "Campaign does not exist"},
        )
    return campaign


@router.get("/networks/{campaign_id}", response_model=NetworkData)
def get_campaign_network(
    campaign_id: str, session: Session = Depends(get_db)
) -> NetworkData:
    network = get_network(session, campaign_id)
    if network is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": "Campaign does not exist"},
        )
    return network


def _incident_detail(incident: Incident) -> IncidentDetail:
    return IncidentDetail(
        incident_id=incident.incident_id,
        risk_score=incident.risk_score,
        risk_level=incident.risk_level,
        scam_type=incident.scam_type,
        confidence=incident.confidence,
        entities=[
            {"entity_id": entity.entity_id, "type": entity.entity_type, "value": entity.value}
            for entity in incident.entities
        ],
        indicators=[],
        related_incidents=[],
        campaign_id=incident.campaigns[0].campaign_id if incident.campaigns else None,
    )