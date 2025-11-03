"""Configuration management for the Travel Agency Customer Service AI application."""

import logging
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # AWS Bedrock Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"

    # ChromaDB Configuration
    chroma_db_path: str = "./data/chroma_db"
    chroma_collection_name: str = "travel_agency_kb"

    # Application Configuration
    log_level: str = "INFO"
    environment: str = "development"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @property
    def chroma_db_absolute_path(self) -> Path:
        """Get absolute path to ChromaDB directory."""
        backend_dir = Path(__file__).parent.parent
        return backend_dir / self.chroma_db_path


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)


# Global settings instance
settings = Settings()

# Setup logging on import
setup_logging(settings.log_level)

# Create logger for this module
logger = logging.getLogger(__name__)

