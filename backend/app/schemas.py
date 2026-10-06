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