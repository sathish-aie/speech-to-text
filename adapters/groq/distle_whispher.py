from adapters.base import AbstractTranscriber
from schemas import Transcript
from config import settings
from common_exceptions import STTProviderError
from litellm import transcription as litellm_transcription
import logging
import io

logger = logging.getLogger(__name__)

class DistilWhisperTranscriber(AbstractTranscriber):
    MODEL_NAME = "distil-whisper"
    LITELLM_GROQ_MODEL = "groq/distil-whisper-large-v3-en"

    async def transcribe(self, audio_bytes: bytes, language: str = "en") -> Transcript:
        effective_language = "en"
        if language.lower() not in ["en", "auto"]:
            logger.warning(
                f"Language '{language}' specified for {self.MODEL_NAME} (model {self.LITELLM_GROQ_MODEL}), "
                f"but this adapter is optimized for English. Proceeding with 'en'."
            )
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"

            response = litellm_transcription(
                model=self.LITELLM_GROQ_MODEL,
                file=audio_file,
                api_key=settings.groq_api_key,
                language=effective_language,
            )

            text_content = ""
            if isinstance(response, str):
                text_content = response
            elif hasattr(response, 'text'):
                text_content = response.text
            elif isinstance(response, dict) and 'text' in response:
                text_content = response['text']
            else:
                logger.error(f"Unexpected transcription response format from litellm for {self.MODEL_NAME} (using {self.LITELLM_GROQ_MODEL}): {type(response)} - {str(response)[:200]}")
                raise STTProviderError(
                    message="Transcription failed due to unexpected response format from provider.",
                    provider_name=self.MODEL_NAME
                )

            if text_content is None:
                 text_content = ""

            logger.info(f"{self.MODEL_NAME} (via {self.LITELLM_GROQ_MODEL}) transcription successful for language '{effective_language}'.")
            return Transcript(
                text=text_content,
                duration_ms=0,
                model=self.MODEL_NAME,
                language=effective_language
            )
        except Exception as e:
            logger.error(f"Error during {self.MODEL_NAME} (via {self.LITELLM_GROQ_MODEL}) transcription: {e}", exc_info=True)
            if isinstance(e, STTProviderError):
                raise
            raise STTProviderError(
                message=str(e),
                provider_name=self.MODEL_NAME
            )