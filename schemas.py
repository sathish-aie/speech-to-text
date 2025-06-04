from pydantic import BaseModel
from typing import Optional, Literal

EngineChoice = Literal["auto", "gpt-4o-mini", "gpt-4o", "distil-whisper"]

class Transcript(BaseModel):
    text: str
    duration_ms: int
    model: str
    language: Optional[str] = None

class TranscriptionRequest(BaseModel):
    engine: EngineChoice = "auto"
    language: Optional[str] = "auto"
