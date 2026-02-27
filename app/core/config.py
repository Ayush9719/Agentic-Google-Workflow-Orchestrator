from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic Google Workspace Orchestrator"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = Field(...)
    REDIS_URL: str = Field(...)
    OPENAI_API_KEY: str | None = None
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()