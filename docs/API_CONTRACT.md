MULEX API Contract

Base URL

Development:

"http://localhost:8000"

API prefix:

"/api/v1"

---

1. Analyze Scam

POST

"/api/v1/analyze"

Request

{
  "text": "Your bank account will be blocked. Complete KYC immediately.",
  "source": "citizen"
}

Response

{
  "incident_id": "INC-001",
  "risk_score": 55,
  "risk_level": "MEDIUM",
  "scam_type": "KYC_SCAM",
  "confidence": 0.92,
  "entities": [],
  "indicators": [],
  "related_incidents": [],
  "campaign_id": null,
  "risk_breakdown": {
    "ml_signal": 0.87,
    "deterministic_signal": 0.0,
    "weights": {
      "ml": 0.35,
      "llm": 0.25,
      "deterministic": 0.2,
      "network": 0.2
    },
    "effective_weights": {
      "ml": 0.636364,
      "deterministic": 0.363636
    },
    "final_score": 55,
    "ml_signal_is_calibrated_probability": false
  },
  "ml_signal": 0.87,
  "network_signal": null
}

---

2. Submit Report

POST

"/api/v1/reports"

Request

{
  "description": "Someone called claiming to be from my bank.",
  "phone": "+91******1234",
  "upi_id": "example@upi",
  "url": "example.com"
}

Response

{
  "report_id": "REP-001",
  "incident_id": "INC-001",
  "status": "received"
}

---

3. List Incidents

GET

"/api/v1/incidents"

Response

{
  "incidents": [
    {
      "incident_id": "INC-001",
      "risk_score": 87,
      "risk_level": "HIGH",
      "scam_type": "KYC_SCAM"
    }
  ]
}

---

4. Get Incident

GET

"/api/v1/incidents/{incident_id}"

Response

{
  "incident_id": "INC-001",
  "risk_score": 87,
  "risk_level": "HIGH",
  "scam_type": "KYC_SCAM",
  "confidence": 0.92,
  "entities": [],
  "indicators": [],
  "related_incidents": [],
  "campaign_id": "CMP-001"
}

---

5. List Campaigns

GET

"/api/v1/campaigns"

Response

{
  "campaigns": [
    {
      "campaign_id": "CMP-001",
      "name": "KYC Impersonation Campaign",
      "risk_score": 94,
      "incident_count": 17,
      "shared_entity_count": 6
    }
  ]
}

---

6. Get Campaign

GET

"/api/v1/campaigns/{campaign_id}"

Response

{
  "campaign_id": "CMP-001",
  "name": "KYC Impersonation Campaign",
  "risk_score": 94,
  "incident_count": 17,
  "shared_entities": [],
  "related_incidents": []
}

---

7. Get Network

GET

"/api/v1/networks/{campaign_id}"

Response

{
  "campaign_id": "CMP-001",
  "nodes": [
    {
      "id": "V001",
      "type": "VICTIM",
      "label": "Victim"
    },
    {
      "id": "M001",
      "type": "MULE",
      "label": "Mule Account"
    }
  ],
  "edges": [
    {
      "source": "V001",
      "target": "M001",
      "type": "TRANSFER"
    }
  ],
  "risk_score": 91,
  "evidence": []
}

Campaign listing/detail, network analysis, and investigator report endpoints
require `Authorization: Bearer <access_token>` for a user with role
`INVESTIGATOR`. `POST /api/v1/analyze` and `POST /api/v1/reports` remain
unchanged and do not require authentication in this prototype.

8. Investigator Campaign Report

GET

"/api/v1/campaigns/{campaign_id}/report"

Requires an investigator bearer token. Returns a concise demo intelligence
summary, graph findings, evidence, and recommended investigative leads. It is
based on synthetic/demo data and does not imply law-enforcement authorization,
government access, or real financial surveillance.

Example response:

```json
{
  "campaign_id": "CMP-001",
  "campaign_name": "KYC Impersonation Campaign",
  "scam_type": "KYC_SCAM",
  "risk_score": 94,
  "risk_level": "HIGH",
  "executive_summary": "Demo intelligence summary for KYC Impersonation Campaign: 17 linked incident(s), application risk score 94/100. This uses synthetic/demo data.",
  "campaign_overview": {
    "incident_count": 17,
    "connected_accounts": 23,
    "connected_urls": 4,
    "connected_phones": 7,
    "connected_upi_ids": 9
  },
  "network_findings": [],
  "risk_factors": [],
  "transaction_patterns": [],
  "linked_entities": [],
  "evidence": [],
  "recommended_actions": [
    "Review accounts receiving funds from multiple unrelated sources.",
    "Compare shared UPI identifiers across linked incidents."
  ]
}
```

---

Entity Types

Allowed entity types:

PHONE
EMAIL
URL
UPI
ACCOUNT
BANK
TRANSACTION
PERSON
ORGANIZATION

---

Scam Types

Allowed scam types:

KYC_SCAM
BANK_IMPERSONATION
UPI_SCAM
INVESTMENT_SCAM
JOB_SCAM
DELIVERY_SCAM
TECH_SUPPORT_SCAM
AI_IMPERSONATION
OTHER

---

Risk Levels

LOW
MEDIUM
HIGH
CRITICAL

---

Error Format

All API errors should follow:

{
  "error": {
    "code": "INCIDENT_NOT_FOUND",
    "message": "Incident does not exist"
  }
}

---

Contract Rule

If an endpoint, request field, response field or enum must change:

1. Update this document.
2. Notify affected teammates.
3. Update dependent code.
4. Test the complete flow.

Never silently change the contract.