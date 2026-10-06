MULEX Integration Rules

Architecture

                    FRONTEND
                       |
                       | REST API
                       v
                    FASTAPI
                       |
          +------------+------------+
          |            |            |
          v            v            v
     PostgreSQL       AI          Neo4j
          |            |            |
          +------------+------------+
                       |
                 MULEX INTELLIGENCE

---

Component Ownership

Backend Owner

Owns:

- FastAPI
- API routes
- Pydantic schemas
- PostgreSQL
- service orchestration
- API documentation

---

AI Owner

Owns:

- scam classification
- entity extraction
- similarity analysis
- risk scoring
- campaign intelligence

AI must return structured data.

AI should NOT directly modify frontend code.

---

Frontend Owner

Owns:

- pages
- components
- dashboard
- charts
- network visualization
- user interaction

Frontend communicates with the backend.

Frontend must NOT directly access:

- PostgreSQL
- Neo4j
- AI provider APIs

---

Graph Owner

Owns:

- Neo4j
- graph models
- relationship analysis
- network detection
- mule/network scoring

Graph functionality is exposed through backend APIs.

---

Communication Rule

The components communicate through defined interfaces.

Frontend
    ↓
API Contract
    ↓
Backend
    ↓
Service Interfaces
    ↓
AI / PostgreSQL / Neo4j

---

AI Output Contract

AI analysis must return:

{
  "risk_score": 87,
  "risk_level": "HIGH",
  "scam_type": "KYC_SCAM",
  "confidence": 0.92,
  "entities": [],
  "indicators": []
}

Backend converts this into the public API response.

---

Graph Output Contract

Graph service must provide:

{
  "nodes": [],
  "edges": [],
  "risk_score": 91,
  "evidence": []
}

The frontend only consumes this structure.

Backend integration architecture:

```text
Frontend
    ↓
FastAPI
    ↓
Person 2 AI provider
    ↓
Risk engine  ← optional configured LLM contextual signal
    ↓
PostgreSQL campaign service (application campaign source of truth)
    ↓
Person 4 graph provider
    ↓
Neo4j
    ↓
Investigator report service
```

PostgreSQL stores application data; Neo4j supplies graph/network intelligence.
Person 2 AI performs fraud analysis. An optional LLM contributes a separate,
structured contextual signal and is disabled unless configured. The risk engine
fuses available signals; Person 2's risk score normalized to 0..1 is an AI risk
signal, not a calibrated probability. Investigator reports are demo intelligence
based on synthetic data only. Campaign/network and investigator-report endpoints
require an authenticated `INVESTIGATOR` role; this role does not represent
government or law-enforcement authorization.

---

Change Management

Before changing a shared interface:

1. Tell the affected person.
2. Update API_CONTRACT.md.
3. Update implementation.
4. Test dependent components.

---

File Ownership

Do not modify another person's main working area unless necessary.

If integration requires a change:

- tell the owner
- keep the change minimal
- document it

---

Shared Dependencies

Do not independently install different versions of the same package.

If a dependency is added:

1. Add it to the appropriate requirements/package file.
2. Notify the team.
3. Test the project.

---

Environment

Everyone uses the same environment variable names.

Example:

DATABASE_URL=
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
AI_API_KEY=

Never commit real credentials.

---

Integration Testing

The complete system should support:

Submit Scam
    ↓
AI Analysis
    ↓
Incident Created
    ↓
Entities Extracted
    ↓
Related Incidents Found
    ↓
Campaign Identified
    ↓
Network Retrieved
    ↓
Frontend Displays Explanation

This is the primary end-to-end test.

---

Definition of Done

A feature is complete only when:

- implementation works
- API contract is respected
- dependent components still work
- tests pass
- documentation is updated if necessary
- no secrets are committed