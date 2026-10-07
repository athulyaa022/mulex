from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReportCreate(BaseModel):
    description: str = Field(min_length=1, max_length=10000)
    phone: str | None = Field(default=None, max_length=255)
    upi_id: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=2048)

    @field_validator("description")
    @classmethod
    def description_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("description must not be blank")
        return value


class ReportSubmitted(BaseModel):
    report_id: str
    incident_id: str
    status: str


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    source: str = Field(min_length=1, max_length=64)

    @field_validator("text", "source")
    @classmethod
    def values_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value


class FraudAnalysis(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    scam_type: Literal[
        "KYC_SCAM",
        "BANK_IMPERSONATION",
        "UPI_SCAM",
        "INVESTMENT_SCAM",
        "JOB_SCAM",
        "DELIVERY_SCAM",
        "TECH_SUPPORT_SCAM",
        "AI_IMPERSONATION",
        "OTHER",
    ]
    confidence: float = Field(ge=0, le=1)
    entities: list[dict[str, str]]
    indicators: list[str]


class AnalyzeResponse(FraudAnalysis):
    incident_id: str
    related_incidents: list[str]
    campaign_id: str | None
    risk_breakdown: dict[str, object] = Field(default_factory=dict)
    ml_signal: float = Field(ge=0, le=1)
    network_signal: float | None = Field(default=None, ge=0, le=1)


class IncidentSummary(BaseModel):
    incident_id: str
    risk_score: int
    risk_level: str
    scam_type: str

    model_config = ConfigDict(from_attributes=True)


class IncidentList(BaseModel):
    incidents: list[IncidentSummary]


class CampaignSummary(BaseModel):
    campaign_id: str
    name: str
    risk_score: int
    incident_count: int
    shared_entity_count: int


class CampaignList(BaseModel):
    campaigns: list[CampaignSummary]


class CampaignDetail(BaseModel):
    campaign_id: str
    name: str
    risk_score: int
    incident_count: int
    shared_entities: list[dict[str, str]]
    related_incidents: list[str]


class NetworkNode(BaseModel):
    id: str
    type: str
    label: str


class NetworkEdge(BaseModel):
    source: str
    target: str
    type: str


class NetworkData(BaseModel):
    campaign_id: str
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
    risk_score: int
    evidence: list[str]
    risk_level: str | None = None
    statistics: dict[str, int | float | bool | None] | None = None
    intelligence_summary: dict[str, object] | None = None


class CampaignGraphIntelligence(BaseModel):
    campaign_id: str
    campaign_name: str
    scam_type: str
    incident_count: int
    account_count: int
    url_count: int
    phone_count: int
    upi_count: int
    severity_breakdown: dict[str, int]
    risk_score: int = Field(ge=0, le=100)
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    evidence: list[str] = Field(default_factory=list)
    statistics: dict[str, int | float | bool | None] = Field(default_factory=dict)


class LLMAnalysis(BaseModel):
    llm_score: float = Field(ge=0, le=1)
    reasoning: list[str] = Field(default_factory=list, max_length=8)
    signals: list[str] = Field(default_factory=list, max_length=12)


class IncidentDetail(IncidentSummary):
    confidence: float
    entities: list[dict[str, str]]
    indicators: list[str]
    related_incidents: list[str]
    campaign_id: str | None


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class InvestigatorCampaignOverview(BaseModel):
    incident_count: int
    connected_accounts: int
    connected_urls: int
    connected_phones: int
    connected_upi_ids: int


class InvestigatorReportItem(BaseModel):
    report_id: str
    incident_id: str

    # Citizen identity is intentionally not exposed.
    reporter: str = "Anonymous Citizen"

    description: str
    phone: str | None = None
    upi_id: str | None = None
    url: str | None = None
    created_at: datetime


class InvestigatorReport(BaseModel):
    campaign_id: str
    campaign_name: str
    scam_type: str
    risk_score: int
    risk_level: str
    executive_summary: str
    campaign_overview: InvestigatorCampaignOverview
    network_findings: list[str]
    risk_factors: list[str]
    transaction_patterns: list[str]
    linked_entities: list[dict[str, str]]
    evidence: list[str]
    recommended_actions: list[str]

    # Reports are accessed through the campaign rather than
    # presenting investigators with a separate global report feed.
    reports: list[InvestigatorReportItem] = Field(default_factory=list)