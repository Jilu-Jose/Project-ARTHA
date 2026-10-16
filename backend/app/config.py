"""
ARTHA Configuration
===================
Centralized configuration using pydantic-settings.
All settings loaded from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- NVIDIA NIM (LLM Provider) ---
    # Using NVIDIA NIM's OpenAI-compatible API with Kimi K2.6.
    # This is part of the Vectorless RAG architecture: no embedding models,
    # no vector databases. BM25 retrieves chunks, which are injected directly
    # into Kimi K2.6's 256K context window.
    NVIDIA_API_KEY: str = Field(default="", description="NVIDIA NIM API key (starts with nvapi-)")
    NVIDIA_MODEL: str = Field(
        default="moonshotai/kimi-k2.6",
        description="NVIDIA NIM model slug for Kimi K2.6"
    )
    NVIDIA_BASE_URL: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="NVIDIA NIM API base URL"
    )

    # --- Context Budget ---
    # Kimi K2.6 has a 256K token context window (262,144 tokens).
    # We reserve ~50K for system prompt + conversation history + output.
    # Safe retrieval budget: ~200K tokens.
    MAX_CONTEXT_TOKENS: int = Field(default=200000, description="Max tokens for retrieved context")
    MAX_OUTPUT_TOKENS: int = Field(default=4096, description="Max tokens for LLM output")
    LLM_TEMPERATURE: float = Field(default=0.2, description="LLM temperature (low for legal precision)")

    # --- BM25 Retrieval ---
    BM25_TOP_K: int = Field(default=15, description="Number of chunks to retrieve via BM25")
    BM25_INDEX_DIR: str = Field(default="indexes", description="Directory for serialized BM25 indexes")
    CORPUS_DIR: str = Field(default="corpus", description="Directory containing legal PDFs/documents")

    # --- Database ---
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://artha:artha_secret@localhost:5432/artha",
        description="PostgreSQL connection string (async)"
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql+psycopg2://artha:artha_secret@localhost:5432/artha",
        description="PostgreSQL connection string (sync, for Alembic)"
    )
    DB_POOL_SIZE: int = Field(default=20, description="SQLAlchemy connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="SQLAlchemy max pool overflow")

    # --- Redis ---
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    CACHE_TTL_SECONDS: int = Field(default=3600, description="Response cache TTL (1 hour)")
    RATE_LIMIT_PER_MINUTE: int = Field(default=20, description="Rate limit for free tier")

    # --- Auth (JWT) ---
    JWT_SECRET_KEY: str = Field(
        default="artha-dev-secret-change-in-production",
        description="JWT signing secret"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, description="JWT expiry (24h default)")

    # --- Admin ---
    ADMIN_EMAIL: str = Field(default="admin@artha.local", description="Admin account email")
    ADMIN_PASSWORD: str = Field(default="change-me-in-production", description="Admin account password")

    # --- Application ---
    ENVIRONMENT: str = Field(default="development", description="development | staging | production")
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://localhost:80",
        description="Comma-separated CORS origins"
    )
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    APP_TITLE: str = Field(default="ARTHA", description="Application title")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
settings = Settings()
