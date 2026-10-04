from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Student Academic Advisor API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"

    # Database: Default to local SQLite for immediate offline execution, supports PostgreSQL
    DATABASE_URL: str = Field(
        default="sqlite:///./academic_advisor.db",
        description="PostgreSQL or SQLite connection string"
    )

    # Authentication & JWT
    JWT_SECRET_KEY: str = Field(
        default="academic-advisor-super-secret-jwt-key-2026",
        description="Secret key for signing student session JWT tokens"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 30

    # Supabase Authentication
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(default="", description="Supabase anonymous public key")
    SUPABASE_JWT_SECRET: str = Field(default="", description="Supabase JWT secret for token verification")

    # Gemini AI
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key for conversational advisor")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", description="Google Gemini Model Name")

    # Claude AI
    ANTHROPIC_API_KEY: str = Field(default="", description="Claude API key for server-side recommendations")

    # Resend Production Email Delivery
    RESEND_API_KEY: str = Field(default="", description="Resend API key for production email delivery")
    EMAILS_FROM_EMAIL: str = Field(default="Student Academic Advisor <onboarding@resend.dev>", description="Verified sender email for Resend delivery")

    # Email Verification Enforcement
    ENABLE_EMAIL_VERIFICATION: bool = Field(
        default=True, 
        description="Set True to enforce verified email requirement before granting access"
    )

    # CORS
    CORS_ORIGINS: List[str] | str = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        description="List of origins or comma-separated string"
    )

    from pydantic import model_validator
    
    @model_validator(mode='before')
    @classmethod
    def parse_cors_origins(cls, data: dict) -> dict:
        if isinstance(data.get('CORS_ORIGINS'), str):
            # Parse comma-separated string into list
            val = data['CORS_ORIGINS']
            if val.startswith('[') and val.endswith(']'):
                import json
                try:
                    data['CORS_ORIGINS'] = json.loads(val)
                except Exception:
                    data['CORS_ORIGINS'] = [o.strip() for o in val.split(',')]
            else:
                data['CORS_ORIGINS'] = [origin.strip() for origin in val.split(',') if origin.strip()]
        return data

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
