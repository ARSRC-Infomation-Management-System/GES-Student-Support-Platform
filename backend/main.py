from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import engine, Base, SessionLocal
from app.models.models import Region, School, User, Resource
from app.core.security import get_password_hash
from app.api.routers import auth, admin, complaints, messages, broadcasts, resources, events, health
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import MockRateLimitMiddleware
from app.api.middleware.exception_handlers import register_exception_handlers


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API services for Ashanti Regional SRC Information Management System",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set CORS middleware using dynamic environment origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set custom middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MockRateLimitMiddleware)

# Register global exception handlers
register_exception_handlers(app)

# Register Routers
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(complaints.router, prefix=settings.API_V1_STR)
app.include_router(messages.router, prefix=settings.API_V1_STR)
app.include_router(broadcasts.router, prefix=settings.API_V1_STR)
app.include_router(resources.router, prefix=settings.API_V1_STR)
app.include_router(events.router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    return {
        "service": f"{settings.PROJECT_NAME} API",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }
