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
  "risk_score": 87,
  "risk_level": "HIGH",
  "scam_type": "KYC_SCAM",
  "confidence": 0.92,
  "entities": [],
  "indicators": [],
  "related_incidents": [],
  "campaign_id": null
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