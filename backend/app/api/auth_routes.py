from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth_schemas import (
    AuthenticationResponse,
    LoginRequest,
    RegistrationRequest,
)
from app.services.auth_service import (
    AuthenticationConfigurationError,
    DuplicateEmailError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def _auth_error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


@router.post("/register", response_model=AuthenticationResponse, status_code=201)
def register(
    request: RegistrationRequest, session: Session = Depends(get_db)
) -> AuthenticationResponse | JSONResponse:
    try:
        return register_user(session, request)
    except DuplicateEmailError:
        return _auth_error(409, "EMAIL_ALREADY_REGISTERED", "Email is already registered")
    except AuthenticationConfigurationError:
        return _auth_error(503, "AUTH_NOT_CONFIGURED", "Authentication is not configured")


@router.post("/login", response_model=AuthenticationResponse)
def login(
    request: LoginRequest, session: Session = Depends(get_db)
) -> AuthenticationResponse | JSONResponse:
    try:
        return authenticate_user(session, request)
    except InvalidCredentialsError:
        return _auth_error(401, "INVALID_CREDENTIALS", "Email or password is incorrect")
    except AuthenticationConfigurationError:
        return _auth_error(503, "AUTH_NOT_CONFIGURED", "Authentication is not configured")