from collections.abc import Generator

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.models import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(
            status_code=401,
            detail={"code": "AUTHENTICATION_REQUIRED", "message": "Bearer token is required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise HTTPException(
            status_code=503,
            detail={"code": "AUTH_NOT_CONFIGURED", "message": "Authentication is not configured"},
        )
    try:
        claims = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "role", "exp"]},
        )
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_TOKEN", "message": "Bearer token is invalid or expired"},
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    user = session.scalar(select(User).where(User.user_id == claims["sub"]))
    if user is None or user.role != claims.get("role"):
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_TOKEN", "message": "Bearer token is invalid or expired"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_investigator(user: User = Depends(get_current_user)) -> User:
    if user.role != "INVESTIGATOR":
        raise HTTPException(
            status_code=403,
            detail={
                "code": "INVESTIGATOR_ROLE_REQUIRED",
                "message": "Investigator role is required for campaign intelligence",
            },
        )
    return user
