from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://resumeuser:resumepass@localhost:5432/resumedb"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 30

    # LaTeX
    LATEX_TIMEOUT_SECONDS: int = 60
    LATEX_MAX_RUNS: int = 2
    LATEX_OUTPUT_DIR: str = os.path.join(os.path.dirname(__file__), "..", "output")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
