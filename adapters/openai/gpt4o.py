from adapters.base import AbstractTranscriber
from schemas import Transcript
from config import settings
from litellm import transcription as litellm_transcription
from common_exceptions import STTProviderError
import logging
import io

logger = logging.getLogger(__name__)

class Gpt4oTranscriber(AbstractTranscriber):
    MODEL_NAME = "gpt-4o"
    LITELLM_MODEL = "whisper-1"

    async def transcribe(self, audio_bytes: bytes, language: str = "auto") -> Transcript:
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"
            litellm_lang_param = language if language != "auto" else None
            response = litellm_transcription(
                model=self.LITELLM_MODEL,
                file=audio_file,
                api_key=settings.openai_api_key,
                language=litellm_lang_param,
            )

            text_content = ""
            if isinstance(response, str):
                text_content = response
            elif hasattr(response, 'text'):
                text_content = response.text
            elif isinstance(response, dict) and 'text' in response:
                text_content = response['text']
            else:
                logger.error(f"Unexpected transcription response format from litellm for {self.MODEL_NAME} (using {self.LITELLM_MODEL}): {type(response)} - {str(response)[:200]}")
                raise STTProviderError(
                    message="Transcription failed due to unexpected response format from provider.",
                    provider_name=self.MODEL_NAME
                )
            
            if text_content is None:
                 text_content = ""

            logger.info(f"{self.MODEL_NAME} (via {self.LITELLM_MODEL}) transcription successful for language '{language}'.")
            return Transcript(
                text=text_content,
                duration_ms=0,
                model=self.MODEL_NAME,
                language=language
            )
        except Exception as e:
            logger.error(f"Error during {self.MODEL_NAME} (via {self.LITELLM_MODEL}) transcription: {e}", exc_info=True)
            if isinstance(e, STTProviderError):
                raise
            raise STTProviderError(
                message=str(e),
                provider_name=self.MODEL_NAME
            )