"""
Configuration settings for bAIt-Chat backend
"""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # QServer configuration
    qserver_url: str = "http://localhost:60610"

    # LMStudio configuration
    lmstudio_url: str = "http://127.0.0.1:1234"

    # Debug mode
    debug: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Ignore extra environment variables
    }


# Global settings instance
settings = Settings()
