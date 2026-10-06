from collections.abc import Generator

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db.session import get_db
from app.main import app
from app.models import Base, User

TEST_JWT_SECRET = "test-secret-key-that-is-long-enough-for-hs256"


@pytest.fixture
def db_engine() -> Generator:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(
    db_engine, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    get_settings.cache_clear()

    def override_get_db() -> Generator[Session, None, None]:
        with Session(db_engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def _register(client: TestClient, *, role: str = "CITIZEN", email: str = "citizen@example.com"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "name": "Demo User",
            "email": email,
            "password": "demo-password",
            "role": role,
        },
    )


@pytest.mark.parametrize(
    ("role", "email"),
    [
        ("CITIZEN", "citizen@example.com"),
        ("INVESTIGATOR", "investigator@example.com"),
    ],
)
def test_registration_returns_token_and_public_user(
    client: TestClient, role: str, email: str
) -> None:
    response = _register(client, role=role, email=email)

    assert response.status_code == 201
    payload = response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
    assert payload["user"] == {
        "user_id": "USR-001",
        "name": "Demo User",
        "email": email,
        "role": role,
    }
    assert "password" not in payload
    assert "password_hash" not in payload


def test_registration_stores_only_password_hash(
    client: TestClient, db_engine
) -> None:
    response = _register(client)

    assert response.status_code == 201
    with Session(db_engine) as session:
        user = session.query(User).one()
        assert user.password_hash != "demo-password"
        assert "demo-password" not in user.password_hash
        assert user.email == "citizen@example.com"


def test_duplicate_email_is_rejected_case_insensitively(client: TestClient) -> None:
    assert _register(client).status_code == 201
    response = _register(client, email="CITIZEN@example.com")

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "EMAIL_ALREADY_REGISTERED",
            "message": "Email is already registered",
        }
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "Demo", "email": "not-an-email", "password": "demo-password", "role": "CITIZEN"},
        {"name": "Demo", "email": "demo@example.com", "password": "short", "role": "CITIZEN"},
        {"name": "Demo", "email": "demo@example.com", "password": "demo-password", "role": "ADMIN"},
        {"name": "   ", "email": "demo@example.com", "password": "demo-password", "role": "CITIZEN"},
    ],
)
def test_invalid_registration_data_returns_validation_error(
    client: TestClient, payload: dict[str, str]
) -> None:
    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    ("role", "email"),
    [
        ("CITIZEN", "citizen@example.com"),
        ("INVESTIGATOR", "investigator@example.com"),
    ],
)
def test_login_returns_token_for_each_role(
    client: TestClient, role: str, email: str
) -> None:
    assert _register(client, role=role, email=email).status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "demo-password"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == role
    assert response.json()["token_type"] == "bearer"
    assert "password_hash" not in response.json()


def test_login_rejects_incorrect_password(client: TestClient) -> None:
    _register(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "citizen@example.com", "password": "incorrect-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_rejects_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "demo-password"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "INVALID_CREDENTIALS",
            "message": "Email or password is incorrect",
        }
    }


def test_access_token_contains_stable_user_claims(client: TestClient) -> None:
    response = _register(client, role="INVESTIGATOR")

    claims = jwt.decode(
        response.json()["access_token"], TEST_JWT_SECRET, algorithms=["HS256"]
    )
    assert claims["sub"] == response.json()["user"]["user_id"] == "USR-001"
    assert claims["role"] == "INVESTIGATOR"
    assert "exp" in claims