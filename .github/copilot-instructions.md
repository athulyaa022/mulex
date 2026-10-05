MULEX — AI Coding Instructions

Project

MULEX is an AI-powered fraud network intelligence platform.

Core flow:

Citizen Report
→ AI Fraud Analysis
→ Incident
→ Entity Extraction
→ Related Incidents
→ Campaign
→ Transaction Network
→ Explainable Risk

The goal is to connect fragmented fraud signals and reveal coordinated fraud campaigns and networks.

---

Team Components

The project has four components:

1. Backend/API
2. AI/Fraud Intelligence
3. Frontend
4. Graph/Network Intelligence

Keep these components modular.

---

CRITICAL RULES

1. Inspect before coding

Before modifying anything:

- inspect the repository
- inspect existing files
- inspect relevant documentation
- reuse existing implementations
- do not create duplicate functionality

Never assume something does not exist.

2. Do not change architecture without approval

Do not introduce:

- new frameworks
- new databases
- new major dependencies
- new API patterns
- new folder structures

unless explicitly requested.

3. Do not modify another person's component unnecessarily

Respect ownership:

Backend → backend/API
AI → AI/fraud analysis
Frontend → UI
Graph → Neo4j/network analysis

Integration changes must be discussed.

---

Technology

Backend:

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic

Graph:

- Neo4j

Frontend:

- Use the existing project framework.

AI:

- Use the team's selected AI/ML tools.

---

API

All APIs use:

/api/v1/

Important endpoints:

POST /api/v1/analyze
POST /api/v1/reports
GET /api/v1/incidents
GET /api/v1/incidents/{incident_id}
GET /api/v1/campaigns
GET /api/v1/campaigns/{campaign_id}
GET /api/v1/networks/{campaign_id}

Do not change API contracts silently.

---

Naming

Use:

incident_id
report_id
campaign_id
entity_id
transaction_id

Risk:

risk_score
risk_level

Allowed risk levels:

LOW
MEDIUM
HIGH
CRITICAL

---

Data

Prototype financial data is synthetic.

Never claim that the prototype accesses private banking data.

Use masked identifiers in demonstrations.

---

Security

Never hard-code:

- API keys
- passwords
- database credentials
- tokens
- secrets

Use environment variables.

Never commit ".env".

Provide ".env.example".

---

Code Quality

Prefer:

- small functions
- modular code
- type hints
- validation
- reusable services
- meaningful names

Avoid:

- duplicated logic
- giant functions
- unnecessary abstractions
- unused dependencies
- dead code

---

AI-generated code

The assistant must not:

- rewrite working code unnecessarily
- delete files without approval
- create duplicate implementations
- change public APIs silently
- install unnecessary packages
- invent credentials
- modify unrelated components

Before major changes, explain the planned files and impact.

---

Testing

Before declaring a task complete:

1. Run the application.
2. Test affected functionality.
3. Check imports.
4. Check API responses.
5. Check database connectivity if relevant.
6. Report any remaining issues.

---

Git

Use feature branches.

Examples:

feature/backend-api
feature/ai-analysis
feature/frontend-dashboard
feature/graph-network

Use clear commits:

feat: add incident analysis API
feat: add campaign network
fix: resolve incident lookup
docs: update API contract

Do not directly modify main unless the team agrees.

---

Final Response

After completing a task, report:

Changed files

List modified files.

What changed

Brief summary.

Dependencies

List new dependencies.

Integration impact

Mention anything another teammate must know.

Testing

State what was tested and the result.

---

Priority

1. Working end-to-end system
2. Reliable APIs
3. AI intelligence
4. Network analysis
5. Explainability
6. UI polish
7. Extra features

Do not sacrifice the core demo for unnecessary features.