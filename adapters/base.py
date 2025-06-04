from abc import ABC, abstractmethod
from schemas import Transcript

class AbstractTranscriber(ABC):
    MODEL_NAME: str
    
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language: str = "auto") -> Transcript:
        """
        Transcribes the given audio bytes.

        Args:
            audio_bytes: The audio data in bytes (expected to be PCM 16kHz).
            language: The language of the audio. "auto" for detection if supported by the model.

        Returns:
            A Transcript object.

        Raises:
            STTProviderError: If the transcription fails at the provider level.
        """
        pass