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