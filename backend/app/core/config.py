from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "F1.GG Backend API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    REPLAY_DATA_DIR: Path = Path(__file__).resolve().parents[2] / "data/rebuild_20261125_v3/processed"
    REPLAY_MODEL_PATH: str = ""
    OVERTAKE_MODEL_PATH: str = "data/rebuild_20261125_v3/forward_reports/20261125T023939Z_2c3ab6/session_11404/latest/models/xgboost.joblib"
    OVERTAKE_MODEL_VARIANT: Literal["raw", "sigmoid"] = "raw"

    DATABASE_URL: str = "sqlite:///./data/f1gg.db"

    OPENF1_BASE_URL: str = "https://api.openf1.org/v1"
    GEMINI_API_KEY: str = ""

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()