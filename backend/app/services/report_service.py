from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Incident, Report
from app.schemas import ReportCreate


@dataclass(frozen=True)
class PlaceholderAnalysis:
    risk_score: int = 0
    risk_level: str = "LOW"
    scam_type: str = "OTHER"
    confidence: float = 0.0


def _new_public_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"


def create_report(session: Session, report_data: ReportCreate) -> Report:
    analysis = PlaceholderAnalysis()
    incident = Incident(
        incident_id=_new_public_id("INC"),
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        scam_type=analysis.scam_type,
        confidence=analysis.confidence,
    )
    report = Report(
        report_id=_new_public_id("REP"),
        description=report_data.description,
        phone=report_data.phone,
        upi_id=report_data.upi_id,
        url=report_data.url,
        incident=incident,
    )

    session.add(report)
    session.commit()
    session.refresh(report)
    return report


def list_incidents(session: Session) -> list[Incident]:
    statement = select(Incident).order_by(Incident.created_at.desc(), Incident.id)
    return list(session.scalars(statement))


def get_incident(session: Session, incident_id: str) -> Incident | None:
    statement = (
        select(Incident)
        .where(Incident.incident_id == incident_id)
        .options(selectinload(Incident.entities), selectinload(Incident.campaigns))
    )
    return session.scalar(statement)