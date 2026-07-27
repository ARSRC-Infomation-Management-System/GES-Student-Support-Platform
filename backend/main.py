from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import engine, Base, SessionLocal
from app.models.models import Region, School, User, Resource
from app.core.security import get_password_hash
from app.api.routers import auth, admin, complaints, messages, broadcasts, resources, events
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import MockRateLimitMiddleware
from app.api.middleware.exception_handlers import register_exception_handlers


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],  # Explicit origins are required when allow_credentials=True
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
        "status": "online",
        "message": "Welcome to Ghana Education Service (GES) Student Support & Communication Platform API",
        "version": "1.0.0"
    }
