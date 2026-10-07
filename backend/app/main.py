from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth_routes import router as auth_router
from app.api.routes import router
from app.services.person2_ai_provider import Person2AIServiceError
from app.services.graph_service import GraphProviderError
from app.services.llm_service import LLMServiceError

app = FastAPI(title="MULEX Backend")

# Allow the React/Vite frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://mulex-puce.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(auth_router)


@app.exception_handler(Person2AIServiceError)
async def person2_ai_error_handler(
    request, exc: Person2AIServiceError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "AI_SERVICE_UNAVAILABLE",
                "message": str(exc),
            }
        },
    )


@app.exception_handler(GraphProviderError)
async def graph_provider_error_handler(
    request, exc: GraphProviderError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "GRAPH_SERVICE_UNAVAILABLE",
                "message": str(exc),
            }
        },
    )


@app.exception_handler(LLMServiceError)
async def llm_service_error_handler(
    request, exc: LLMServiceError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "LLM_SERVICE_UNAVAILABLE",
                "message": str(exc),
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_error_handler(
    request, exc: HTTPException
) -> JSONResponse:
    detail = exc.detail

    error = (
        detail
        if isinstance(detail, dict)
        and "code" in detail
        and "message" in detail
        else {
            "code": "HTTP_ERROR",
            "message": str(detail),
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error},
        headers=exc.headers,
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
async def not_found_error_handler(
    request, exc
) -> JSONResponse:
    detail = getattr(exc, "detail", None)

    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        error = detail
    else:
        error = {
            "code": "NOT_FOUND",
            "message": "Resource does not exist",
        }

    return JSONResponse(
        status_code=404,
        content={"error": error},
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "mulex-backend",
    }