"""
Application Configuration Module
Autonomous Agentic AI Marketing & Revenue Operations Platform
"""

from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Autonomous Agentic AI Marketing & Revenue Operations Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Paths
    API_V1_PREFIX: str = "/api/v1"
    
    # Security & JWT
    SECRET_KEY: str = "aipnt-super-secure-production-jwt-secret-key-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./marketing_platform.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "https://aipnt.in",
    ]
    
    # LLM Settings
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "gemini-1.5-flash"
    CHEAP_LLM_MODEL: str = "gpt-4o-mini"
    REASONING_LLM_MODEL: str = "gpt-4o"
    GEMINI_FLASH_MODEL: str = "gemini-1.5-flash"
    GEMINI_PRO_MODEL: str = "gemini-1.5-flash"
    
    # Enterprise Guardrails
    ENABLE_TENANT_ISOLATION: bool = True
    REQUIRE_APPROVAL_HIGH_RISK: bool = True

    # Real Integrations Configuration (Salesforce, Slack, Calendar)
    SALESFORCE_INSTANCE_URL: str = ""
    SALESFORCE_ACCESS_TOKEN: str = ""
    SALESFORCE_CLIENT_ID: str = ""
    SALESFORCE_CLIENT_SECRET: str = ""
    SALESFORCE_USERNAME: str = ""
    SALESFORCE_PASSWORD: str = ""
    SALESFORCE_SECURITY_TOKEN: str = ""

    SLACK_WEBHOOK_URL: str = ""
    SLACK_BOT_TOKEN: str = ""
    SLACK_DEFAULT_CHANNEL: str = "#growth-alerts"

    CALENDLY_API_KEY: str = ""
    GOOGLE_CALENDAR_TOKEN: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )


settings = Settings()
