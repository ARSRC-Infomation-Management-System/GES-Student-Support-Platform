import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "GES Student Support & Communication Platform"
    API_V1_STR: str = "/api/v1"
    
    # Security
    # In production, change this to a secure random key
    SECRET_KEY: str = Field(default="super_secret_ges_support_key_2026_change_me", validation_alias="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./ges_platform.db", validation_alias="DATABASE_URL")
    
    # Uploads
    UPLOAD_DIR: str = Field(default="./uploads", validation_alias="UPLOAD_DIR")

    class Config:
        case_sensitive = True

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
