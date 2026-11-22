from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import db
from app.core.errors import DomainError
from app.core.logging import safe_logger
from app.api.v1 import (
    health,
    encounters,
    programs,
    audit,
    ledger,
    dashboard,
    payouts,
    clinics,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    safe_logger.info("Initializing Nena AI Zero-Trust Backend Gateway...")
    yield
    safe_logger.info("Shutting down Nena AI Backend...")
    await db.close()


app = FastAPI(
    title="Nena AI API",
    description="Zero-Trust Subsidy Routing Ledger for community healthcare financing.",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Mpesa-Signature"],
)


# Root Landing Endpoint
@app.get("/", include_in_schema=False)
async def root():
    return {
        "app_name": settings.app_name,
        "version": "0.2.0",
        "description": "Zero-Trust Subsidy Routing Ledger for community healthcare financing",
        "documentation": "/docs",
        "health_check": f"{settings.api_v1_prefix}/health",
        "openapi_schema": "/openapi.json"
    }


# Centralized Exception Handlers
@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Sanitize validation errors to avoid leaking internal trace details
    safe_logger.warning(f"Request validation error on {request.url.path}: {len(exc.errors())} issues")
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Invalid request parameters or payload structure",
            "details": [{"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]} for err in exc.errors()]
        }
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    safe_logger.error(f"Unhandled server exception on {request.url.path}: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred. This event has been logged."
        }
    )


# API Version 1 Routers
app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(encounters.router, prefix=settings.api_v1_prefix)
app.include_router(programs.router, prefix=settings.api_v1_prefix)
app.include_router(audit.router, prefix=settings.api_v1_prefix)
app.include_router(ledger.router, prefix=settings.api_v1_prefix)
app.include_router(dashboard.router, prefix=settings.api_v1_prefix)
app.include_router(payouts.router, prefix=settings.api_v1_prefix)
app.include_router(clinics.router, prefix=settings.api_v1_prefix)
