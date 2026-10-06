# MULEX Backend

Phase 1 provides the FastAPI application, health check, PostgreSQL connection
dependency, and a minimal test suite. The health check does not require the
database to be running.

## Setup

From the `backend` directory, create and activate a virtual environment in
PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `DATABASE_URL` to your local PostgreSQL connection URL. The
example value is a placeholder, not a real credential. PostgreSQL is needed
when a route or service requests a database session; Phase 1's health check does
not open a database connection.

Set `JWT_SECRET_KEY` to a private, randomly generated value of at least 32 bytes
before using the authentication endpoints. Do not commit `.env` or share this
key. The example value in `.env.example` is only a placeholder and must be
replaced.

## Authentication

Register and log in with `POST /api/v1/auth/register` and
`POST /api/v1/auth/login`. Supported roles are `CITIZEN` and `INVESTIGATOR`;
investigator registration is not a claim of government or police authorization.
Passwords are stored as Argon2 hashes. The returned bearer token is a signed JWT.

For an existing PostgreSQL database, apply `migrations/0001_create_users.sql`
once before using registration or login. It creates only the new `users` table.

## Fraud Analysis Provider

The default `AI_PROVIDER=mock` keeps the deterministic backend mock enabled.
To select Person 2's AI implementation, install the optional dependencies from
the `backend` directory:

```powershell
python -m pip install -r requirements-ai.txt
```

Then set `AI_PROVIDER=person2` in `.env` and restart the backend. The model is
loaded in a persistent worker on the first analysis request, not during backend
module import. First use may download the SentenceTransformer model unless it is
already cached. Worker and model errors return a structured 503; they do not
silently fall back to the mock provider.

## Graph Intelligence and Risk Fusion

PostgreSQL remains the authoritative store for application reports, incidents,
and campaigns. Neo4j is an optional graph/network intelligence provider; select
it with `GRAPH_PROVIDER=person4` and set `NEO4J_URI`, `NEO4J_USERNAME`, and
`NEO4J_PASSWORD` in `.env`. Install the optional Python dependencies from the
`backend` directory with:

```powershell
python -m pip install -r requirements-graph.txt
```

The default is `GRAPH_PROVIDER=mock`. Selecting Person 4's provider does not
silently fall back if Neo4j fails; graph operations return a structured 503.
Application campaign IDs are resolved to graph campaigns only through an exact
ID match or shared URL/UPI/phone identifier. If the graph contains no matching
identifier, graph enrichment is unavailable for that application campaign.

The risk engine combines the normalized Person 2 risk score, deterministic
indicator coverage, optional graph signals, and an optional LLM signal. The
Person 2 score divided by 100 is a normalized AI risk signal, not a calibrated
probability. `LLM_PROVIDER=none` is the default and emits no LLM signal. To use
the OpenAI-compatible adapter, explicitly set `LLM_PROVIDER=openai_compatible`,
`LLM_API_URL`, `LLM_API_KEY`, and `LLM_MODEL`; the key must remain in the local
`.env`, never in source control. Without an LLM provider, available risk
component weights are renormalized; the backend does not fabricate an LLM
result.

Campaign/network endpoints and the investigator report require a valid bearer
token for a `INVESTIGATOR` account. This prototype role is not government or
police authorization. Reports and graph data are synthetic/demo intelligence;
the system does not access private banking data or perform real financial
surveillance.

The integration separates responsibilities: PostgreSQL is the application
record and campaign source of truth; Person 2 AI provides fraud analysis; the
risk engine fuses available normalized signals; optional LLM reasoning is
separate and disabled by default; Person 4's Neo4j provider supplies graph
network intelligence; and the investigator report service summarizes campaign
evidence for demo use.

## Run

From the `backend` directory:

```powershell
uvicorn app.main:app --reload
```

The health endpoint is available at `http://localhost:8000/health` and returns:

```json
{
  "status": "ok",
  "service": "mulex-backend"
}
```

## Test

Install the test dependencies and run the suite from the `backend` directory:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```