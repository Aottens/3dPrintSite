"""
NovaPrint API - 3D Print Quoting and Order Management

This is the main FastAPI application that provides:
- File upload with STL/3MF support
- Automatic model metrics calculation
- Instant pricing with versioned rule sets
- Order management and tracking
- Admin portal for configuration
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.admin import router as admin_router
from app.api.assets import router as assets_router
from app.api.auth import router as auth_router
from app.api.materials import router as materials_router
from app.api.orders import router as orders_router
from app.api.quotes import router as quotes_router
from app.core.settings import settings
from app.db.database import engine

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan context manager."""
    # Startup
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="3D Print Quoting and Order Management API",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    if settings.debug:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Health check
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


# Include routers
app.include_router(auth_router)
app.include_router(materials_router)
app.include_router(assets_router)
app.include_router(quotes_router)
app.include_router(orders_router)
app.include_router(admin_router)


# Rate limited auth endpoints
@app.post("/api/auth/login")
@limiter.limit("10/minute")
async def rate_limited_login(request: Request):
    """This decorator is applied via the router, this is just for documentation."""
    pass


@app.post("/api/auth/register")
@limiter.limit("5/minute")
async def rate_limited_register(request: Request):
    """This decorator is applied via the router, this is just for documentation."""
    pass
