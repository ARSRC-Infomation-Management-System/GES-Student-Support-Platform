import os
import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ASHANTI REGIONAL SRC INFORMATION MANAGEMENT SYSTEM"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = Field(
        default="c9afdf545ae770b286da10431a47b75f9b69f065e1ab3abadd0a3e3ff55ca726",
        validation_alias="SECRET_KEY",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://arsrc.vercel.app",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            val = value.strip()
            if val.startswith("[") and val.endswith("]"):
                try:
                    return json.loads(val)
                except Exception:
                    pass
            return [origin.strip() for origin in val.split(",") if origin.strip()]
        return value

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/ges_student_support",
        validation_alias="DATABASE_URL",
    )

    # Uploads
    UPLOAD_DIR: str = Field(
        default="./uploads",
        validation_alias="UPLOAD_DIR",
    )

    # Cloudinary CDN
    CLOUDINARY_CLOUD_NAME: str = Field(default="", validation_alias="CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY: str = Field(default="", validation_alias="CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET: str = Field(default="", validation_alias="CLOUDINARY_API_SECRET")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)