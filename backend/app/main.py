from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.auth_routes import router as auth_router
from app.api.routes import router
from app.services.person2_ai_provider import Person2AIServiceError

app = FastAPI(title="MULEX Backend")
app.include_router(router)
app.include_router(auth_router)


@app.exception_handler(Person2AIServiceError)
async def person2_ai_error_handler(request, exc: Person2AIServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "AI_SERVICE_UNAVAILABLE",
                "message": str(exc),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
            }
        },
    )


@app.exception_handler(404)
async def not_found_error_handler(request, exc) -> JSONResponse:
    detail = getattr(exc, "detail", None)
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        error = detail
    else:
        error = {"code": "NOT_FOUND", "message": "Resource does not exist"}
    return JSONResponse(status_code=404, content={"error": error})


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "mulex-backend"}