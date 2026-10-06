from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    Column,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_users_user_id"),
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint("role IN ('CITIZEN', 'INVESTIGATOR')", name="ck_users_role"),
        Index("ix_users_role", "role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


incident_entities = Table(
    "incident_entities",
    Base.metadata,
    Column(
        "incident_id",
        Uuid(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "entity_id",
        Uuid(as_uuid=True),
        ForeignKey("entities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("ix_incident_entities_entity_id", "entity_id"),
)

incident_campaigns = Table(
    "incident_campaigns",
    Base.metadata,
    Column(
        "incident_id",
        Uuid(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "campaign_id",
        Uuid(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("ix_incident_campaigns_campaign_id", "campaign_id"),
)


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("report_id", name="uq_reports_report_id"),
        Index("ix_reports_incident_id", "incident_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    report_id: Mapped[str] = mapped_column(String(64), nullable=False)
    incident_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("incidents.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(255))
    upi_id: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    incident: Mapped["Incident"] = relationship(back_populates="reports")


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        UniqueConstraint("incident_id", name="uq_incidents_incident_id"),
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="ck_incidents_risk_score"),
        CheckConstraint(
            "risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_incidents_risk_level",
        ),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_incidents_confidence"),
        Index("ix_incidents_risk_score", "risk_score"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    scam_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    entities: Mapped[list["Entity"]] = relationship(
        secondary=incident_entities, back_populates="incidents"
    )
    campaigns: Mapped[list["Campaign"]] = relationship(
        secondary=incident_campaigns, back_populates="incidents"
    )
    reports: Mapped[list[Report]] = relationship(back_populates="incident")


class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (
        UniqueConstraint("entity_id", name="uq_entities_entity_id"),
        UniqueConstraint("type", "value", name="uq_entities_type_value"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column("type", String(32), nullable=False)
    value: Mapped[str] = mapped_column(String(2048), nullable=False)

    incidents: Mapped[list[Incident]] = relationship(
        secondary=incident_entities, back_populates="entities"
    )


class Campaign(Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        UniqueConstraint("campaign_id", name="uq_campaigns_campaign_id"),
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="ck_campaigns_risk_score"),
        Index("ix_campaigns_risk_score", "risk_score"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    campaign_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    scam_type: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    incidents: Mapped[list[Incident]] = relationship(
        secondary=incident_campaigns, back_populates="campaigns"
    )


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("transaction_id", name="uq_transactions_transaction_id"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    transaction_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sender_account: Mapped[str] = mapped_column(String(255), nullable=False)
    receiver_account: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)