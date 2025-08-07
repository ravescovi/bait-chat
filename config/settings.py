"""
Application configuration and settings
Central configuration management for bAIt-Chat
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    API_HOST: str = Field("0.0.0.0", env="API_HOST")
    API_PORT: int = Field(8000, env="API_PORT")
    API_BASE_URL: str = Field("http://localhost:8000", env="API_BASE_URL")
    
    # QServer Configuration
    QSERVER_URL: str = Field("http://localhost:60610", env="QSERVER_URL")
    QSERVER_API_KEY: Optional[str] = Field(None, env="QSERVER_API_KEY")
    DEFAULT_USER: str = Field("bait_chat", env="DEFAULT_USER")
    DEFAULT_USER_GROUP: str = Field("primary", env="DEFAULT_USER_GROUP")
    
    # Databroker Configuration
    DATABROKER_CATALOG: str = Field("bluesky", env="DATABROKER_CATALOG")
    DATABROKER_HOST: Optional[str] = Field(None, env="DATABROKER_HOST")
    DATABROKER_PORT: Optional[int] = Field(None, env="DATABROKER_PORT")
    
    # LLM Configuration
    LLM_PROVIDER: str = Field("openai", env="LLM_PROVIDER")  # openai, anthropic, mistral, lmstudio, ollama
    LLM_MODEL: str = Field("gpt-4", env="LLM_MODEL")
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    MISTRAL_API_KEY: Optional[str] = Field(None, env="MISTRAL_API_KEY")
    
    # Local LLM Configuration
    LMSTUDIO_BASE_URL: str = Field("http://localhost:1234/v1", env="LMSTUDIO_BASE_URL")
    OLLAMA_BASE_URL: str = Field("http://localhost:11434", env="OLLAMA_BASE_URL")
    LOCAL_MODEL_NAME: str = Field("llama2", env="LOCAL_MODEL_NAME")  # Model name for Ollama
    LOCAL_MODEL_TEMPERATURE: float = Field(0.7, env="LOCAL_MODEL_TEMPERATURE")
    LOCAL_MODEL_MAX_TOKENS: int = Field(4000, env="LOCAL_MODEL_MAX_TOKENS")
    LOCAL_MODEL_TIMEOUT: int = Field(60, env="LOCAL_MODEL_TIMEOUT")  # seconds
    
    # Vector Database Configuration
    VECTOR_DB_TYPE: str = Field("chroma", env="VECTOR_DB_TYPE")  # chroma, qdrant
    VECTOR_DB_PATH: str = Field("./vector_db", env="VECTOR_DB_PATH")
    QDRANT_URL: Optional[str] = Field(None, env="QDRANT_URL")
    QDRANT_API_KEY: Optional[str] = Field(None, env="QDRANT_API_KEY")
    
    # Knowledge Base Configuration
    KNOWLEDGE_BASE_PATH: str = Field("./knowledge_base", env="KNOWLEDGE_BASE_PATH")
    AUTO_INDEX_ON_START: bool = Field(True, env="AUTO_INDEX_ON_START")
    
    # Voice Configuration (Optional)
    ENABLE_VOICE: bool = Field(False, env="ENABLE_VOICE")
    WHISPER_MODEL: str = Field("base", env="WHISPER_MODEL")  # tiny, base, small, medium, large
    WHISPER_API_URL: Optional[str] = Field(None, env="WHISPER_API_URL")
    
    # Security Configuration
    ENABLE_AUTH: bool = Field(False, env="ENABLE_AUTH")
    AUTH_SECRET_KEY: str = Field("change-me-in-production", env="AUTH_SECRET_KEY")
    AUTH_ALGORITHM: str = Field("HS256", env="AUTH_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Plan Whitelist
    ALLOWED_PLANS: list = Field(
        default=[
            "scan", "count", "list_scan", "grid_scan", 
            "rel_scan", "spiral", "fly_scan"
        ],
        env="ALLOWED_PLANS"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field("./logs/bait_chat.log", env="LOG_FILE")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # CORS Configuration
    CORS_ORIGINS: list = Field(
        default=["http://localhost:8501", "http://localhost:3000", "*"],
        env="CORS_ORIGINS"
    )
    
    # Rate Limiting
    ENABLE_RATE_LIMIT: bool = Field(False, env="ENABLE_RATE_LIMIT")
    RATE_LIMIT_REQUESTS: int = Field(100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_PERIOD: int = Field(60, env="RATE_LIMIT_PERIOD")  # seconds
    
    # Cache Configuration
    ENABLE_CACHE: bool = Field(True, env="ENABLE_CACHE")
    CACHE_TTL: int = Field(300, env="CACHE_TTL")  # seconds
    CACHE_MAX_SIZE: int = Field(1000, env="CACHE_MAX_SIZE")
    
    # Development Settings
    DEBUG: bool = Field(False, env="DEBUG")
    RELOAD: bool = Field(True, env="RELOAD")
    
    # WebSocket Configuration (for real-time updates)
    ENABLE_WEBSOCKET: bool = Field(False, env="ENABLE_WEBSOCKET")
    WS_HEARTBEAT_INTERVAL: int = Field(30, env="WS_HEARTBEAT_INTERVAL")
    
    # Performance Settings
    MAX_WORKERS: int = Field(4, env="MAX_WORKERS")
    REQUEST_TIMEOUT: int = Field(30, env="REQUEST_TIMEOUT")  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create global settings instance
settings = Settings()


# Utility functions for configuration management

def get_log_config() -> dict:
    """Get logging configuration dictionary"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.LOG_FORMAT,
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": settings.LOG_FILE,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file"],
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
    }


def validate_settings():
    """Validate critical settings and raise errors if invalid"""
    errors = []
    
    # Check LLM configuration
    if settings.LLM_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is required when using OpenAI provider")
    elif settings.LLM_PROVIDER == "anthropic" and not settings.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is required when using Anthropic provider")
    elif settings.LLM_PROVIDER == "mistral" and not settings.MISTRAL_API_KEY:
        errors.append("MISTRAL_API_KEY is required when using Mistral provider")
    elif settings.LLM_PROVIDER in ["lmstudio", "ollama"]:
        # Local models don't require API keys but need accessible endpoints
        if settings.LLM_PROVIDER == "lmstudio" and not settings.LMSTUDIO_BASE_URL:
            errors.append("LMSTUDIO_BASE_URL is required when using LMStudio provider")
        elif settings.LLM_PROVIDER == "ollama" and not settings.OLLAMA_BASE_URL:
            errors.append("OLLAMA_BASE_URL is required when using Ollama provider")
    
    # Check QServer URL
    if not settings.QSERVER_URL:
        errors.append("QSERVER_URL is required")
    
    # Check paths exist
    paths_to_check = [
        Path(settings.KNOWLEDGE_BASE_PATH),
        Path(settings.VECTOR_DB_PATH).parent,
        Path(settings.LOG_FILE).parent
    ]
    
    for path in paths_to_check:
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {path}: {e}")
    
    if errors:
        error_msg = "Configuration errors:\n" + "\n".join(errors)
        raise ValueError(error_msg)


# Validate settings on import
if __name__ != "__main__":
    try:
        validate_settings()
    except ValueError as e:
        print(f"Warning: {e}")
        print("Some features may not work correctly.")