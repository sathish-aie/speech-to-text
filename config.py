from pydantic_settings import BaseSettings
# from stt.schemas import EngineChoice
from schemas import EngineChoice
from typing import Literal
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    default_engine_policy: Literal["gpt-4o-mini", "high_accuracy", "cheap"] = "gpt-4o-mini"
    default_engine: EngineChoice = "gpt-4o-mini"
    max_audio_duration_seconds: int = 3600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()