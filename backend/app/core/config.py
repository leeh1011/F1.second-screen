import os

class Settings:
    PROJECT_NAME: str = "F1.GG Backend API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    OPENF1_BASE_URL: str = os.getenv("OPENF1_BASE_URL", "https://api.openf1.org/v1")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # CORS origins
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ]

settings = Settings()
