from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, Campaign, Entity, Incident, Report, Transaction, User


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_models_register_documented_tables() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    assert set(inspect(engine).get_table_names()) == {
        "campaigns",
        "entities",
        "incident_campaigns",
        "incident_entities",
        "incidents",
        "reports",
        "transactions",
        "users",
    }
    engine.dispose()


def test_incident_entity_and_campaign_relationships(db_session: Session) -> None:
    incident = Incident(
        incident_id="INC-001",
        risk_score=87,
        risk_level="HIGH",
        scam_type="KYC_SCAM",
        confidence=0.92,
    )
    entity = Entity(entity_id="ENT-001", entity_type="URL", value="example.test")
    campaign = Campaign(
        campaign_id="CMP-001",
        name="KYC campaign",
        risk_score=94,
        scam_type="KYC_SCAM",
    )
    incident.entities.append(entity)
    incident.campaigns.append(campaign)
    db_session.add(incident)
    db_session.commit()
    db_session.expire_all()

    loaded_incident = db_session.query(Incident).one()
    assert loaded_incident.entities[0].entity_id == "ENT-001"
    assert loaded_incident.campaigns[0].campaign_id == "CMP-001"
    assert loaded_incident in loaded_incident.entities[0].incidents
    assert loaded_incident in loaded_incident.campaigns[0].incidents


def test_public_ids_are_unique(db_session: Session) -> None:
    incident = Incident(
        incident_id="INC-001",
        risk_score=0,
        risk_level="LOW",
        scam_type="OTHER",
        confidence=0.0,
    )
    db_session.add(incident)
    db_session.flush()
    db_session.add_all(
        [
            Report(report_id="REP-001", incident=incident, description="First report"),
            Report(report_id="REP-001", incident=incident, description="Duplicate report"),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_risk_score_check_constraint(db_session: Session) -> None:
    db_session.add(
        Incident(
            incident_id="INC-001",
            risk_score=101,
            risk_level="HIGH",
            scam_type="KYC_SCAM",
            confidence=0.92,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_transaction_uses_decimal_and_timestamp(db_session: Session) -> None:
    transaction = Transaction(
        transaction_id="TXN-001",
        sender_account="masked-sender",
        receiver_account="masked-receiver",
        amount=Decimal("1250.50"),
        timestamp=datetime(2026, 10, 5, tzinfo=UTC),
    )
    db_session.add(transaction)
    db_session.commit()

    assert transaction.amount == Decimal("1250.50")