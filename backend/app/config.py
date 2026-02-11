"""
UnifiedAi Configuration
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


def _default_backend_data_dir() -> Path:
    explicit = (os.getenv("UNIFIEDAI_DATA_DIR") or "").strip()
    if explicit:
        return Path(explicit)
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / "unifiedai" / "backend"
    return Path.home() / ".unifiedai" / "backend"


_BACKEND_DATA_DIR = _default_backend_data_dir()
_BACKEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
_DEFAULT_DB_URL = f"sqlite:///{(_BACKEND_DATA_DIR / 'unifiedai.db').as_posix()}"


class Settings(BaseSettings):
    # Database
    BACKEND_DATA_DIR: str = str(_BACKEND_DATA_DIR)
    DATABASE_URL: str = _DEFAULT_DB_URL
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral-large-3:675b-cloud"  # Cloud model
    OLLAMA_API_KEY: str = ""  # Optional: For cloud model authentication
    
    # Server
    BACKEND_PORT: int = 10000
    FRONTEND_URL: str = "http://localhost:10000"
    
    # CORS
    CORS_ORIGINS: list = ["*"]  # Allow all origins for development
    
    # App Info
    APP_NAME: str = "UnifiedAi"
    APP_VERSION: str = "1.0.0"

    # ActivatePrimeCOMPLETE relics - path to data folder for context/personality
    # e.g. G:\ActivatePrimeCOMPLETE\data or G:\ActivatePrimeCOMPLETE\Activate_relics
    ACTIVATEPRIME_RELICTS_PATH: str = ""

    # Directed coordinator mode: one director synthesizes multi-agent outputs.
    COORDINATOR_ENABLED: bool = True
    COORDINATOR_MAX_HISTORY_CHARS: int = 3200
    COORDINATOR_MAX_AGENT_OUTPUT_CHARS: int = 1200
    COORDINATOR_MAX_REPLY_CHARS: int = 2400

    # Arena: multi-model agent conversation system
    # Each agent uses a DIFFERENT cloud model + prediction profile.
    # All cloud models via Ollama cloud API.
    ARENA_MODEL_ANALYST: str = "qwen3-coder:480b-cloud"        # Precise structured reasoning
    ARENA_MODEL_CREATIVE: str = "gpt-oss:120b-cloud"           # Lateral thinking, novel connections
    ARENA_MODEL_CRITIC: str = "deepseek-v3.1:671b-cloud"       # Rigorous flaw-finding
    ARENA_MODEL_EMPATHIST: str = "mistral-large-3:675b-cloud"  # Warm emotional intelligence
    ARENA_MODEL_DIRECTOR: str = "mistral-large-3:675b-cloud"   # Cold synthesis, final answer

    class Config:
        env_file = ".env"

settings = Settings()

