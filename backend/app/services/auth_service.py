from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth_schemas import (
    AuthenticationResponse,
    LoginRequest,
    PublicUser,
    RegistrationRequest,
)
from app.config import get_settings
from app.models import User


_password_hash = PasswordHash.recommended()


class DuplicateEmailError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthenticationConfigurationError(Exception):
    pass


def _jwt_settings() -> tuple[str, str, int]:
    settings = get_settings()

    if (
        not settings.jwt_secret_key
        or len(settings.jwt_secret_key.encode("utf-8")) < 32
    ):
        raise AuthenticationConfigurationError(
            "JWT_SECRET_KEY must be configured with at least 32 bytes"
        )

    return (
        settings.jwt_secret_key,
        settings.jwt_algorithm,
        settings.access_token_expire_minutes,
    )


def register_user(
    session: Session,
    request: RegistrationRequest,
) -> AuthenticationResponse:

    _jwt_settings()

    email = str(request.email).casefold()

    existing_user = session.scalar(
        select(User).where(User.email == email)
    )

    if existing_user is not None:
        raise DuplicateEmailError

    # Public registration ALWAYS creates a CITIZEN.
    # Investigator accounts must be created/authorized separately.
    user = User(
        user_id=f"P-{uuid4().hex[:14]}",
        name=request.name,
        email=email,
        password_hash=_password_hash.hash(request.password),
        role="CITIZEN",
    )

    session.add(user)

    try:
        session.flush()

        user.user_id = f"USR-{user.id:03d}"

        session.commit()

    except IntegrityError as error:
        session.rollback()
        raise DuplicateEmailError from error

    session.refresh(user)

    return _authentication_response(user)


def authenticate_user(
    session: Session,
    request: LoginRequest,
) -> AuthenticationResponse:

    _jwt_settings()

    email = str(request.email).casefold()

    user = session.scalar(
        select(User).where(User.email == email)
    )

    if (
        user is None
        or not _password_hash.verify(
            request.password,
            user.password_hash,
        )
    ):
        raise InvalidCredentialsError

    return _authentication_response(user)


def _authentication_response(
    user: User,
) -> AuthenticationResponse:

    secret, algorithm, expiration_minutes = _jwt_settings()

    now = datetime.now(UTC)

    token = jwt.encode(
        {
            "sub": user.user_id,
            "role": user.role,
            "iat": now,
            "exp": now + timedelta(
                minutes=expiration_minutes
            ),
        },
        secret,
        algorithm=algorithm,
    )

    return AuthenticationResponse(
        access_token=token,
        user=PublicUser(
            user_id=user.user_id,
            name=user.name,
            email=user.email,
            role=user.role,
        ),
    )