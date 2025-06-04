# from stt.config import Settings
# from stt.schemas import Transcript, EngineChoice
# from stt.adapters.base import AbstractTranscriber
# from stt.adapters.openai.gpt4o_mini import Gpt4oMiniTranscriber
# from stt.adapters.openai.gpt4o import Gpt4oTranscriber
# from stt.adapters.groq.distle_whispher import DistilWhisperTranscriber
# from stt.common_exceptions import STTProviderError  
import logging
from config import Settings
from schemas import Transcript, EngineChoice
from adapters.base import AbstractTranscriber
from adapters.openai.gpt4o_mini import Gpt4oMiniTranscriber
from adapters.openai.gpt4o import Gpt4oTranscriber
from adapters.groq.distle_whispher import DistilWhisperTranscriber
from common_exceptions import STTProviderError  

logger = logging.getLogger(__name__)

class ModelRouter:
    def __init__(self, app_settings: Settings):
        self.app_settings = app_settings
        self._transcribers: dict[EngineChoice, AbstractTranscriber] = {
            "gpt-4o-mini": Gpt4oMiniTranscriber(),
            "gpt-4o": Gpt4oTranscriber(),
            "distil-whisper": DistilWhisperTranscriber(),
        }
        logger.info(f"ModelRouter initialized with default policy: {app_settings.default_engine_policy}, default engine: {app_settings.default_engine}")

    def _get_transcriber(self, engine_name: EngineChoice) -> AbstractTranscriber:
        transcriber = self._transcribers.get(engine_name)
        if not transcriber:
            logger.error(f"Invalid engine name: {engine_name}. Falling back to default engine from config: {self.app_settings.default_engine}")
            transcriber = self._transcribers.get(self.app_settings.default_engine)
            if not transcriber:
                 logger.critical(f"Default engine {self.app_settings.default_engine} also not found! This is a configuration error.")
                 raise ValueError(f"Invalid engine name '{engine_name}' and configured default engine '{self.app_settings.default_engine}' is also unavailable.")
        return transcriber

    async def run(self, audio_bytes: bytes, audio_duration_ms: int, engine: EngineChoice, language: str = "auto") -> Transcript:
        """
        Selects the engine based on the 'engine' parameter and policy, then transcribes.
        The audio_duration_ms obtained from preprocessing is passed to populate the Transcript object.
        """
        selected_engine_name: EngineChoice

        if engine != "auto":
            selected_engine_name = engine
            logger.info(f"Engine parameter specified: '{engine}'. Using this engine directly.")
        else:
            policy = self.app_settings.default_engine_policy
            logger.info(f"Engine parameter is 'auto'. Applying policy: '{policy}'.")
            if policy == "high_accuracy":
                selected_engine_name = "gpt-4o"
            elif policy == "cheap":
                selected_engine_name = "distil-whisper"
            elif policy == "gpt-4o-mini":
                selected_engine_name = "gpt-4o-mini"
            else:
                logger.warning(f"Unknown policy '{policy}'. Falling back to 'default_engine' from settings: '{self.app_settings.default_engine}'.")
                selected_engine_name = self.app_settings.default_engine
        
        logger.info(f"Selected engine for transcription: '{selected_engine_name}' with language '{language}'")
        transcriber = self._get_transcriber(selected_engine_name)
        
        try:
            transcript_result = await transcriber.transcribe(audio_bytes, language=language)
            final_transcript = Transcript(
                text=transcript_result.text,
                duration_ms=audio_duration_ms,
                model=selected_engine_name,
                language=transcript_result.language
            )
            return final_transcript
        except STTProviderError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in ModelRouter.run for engine {selected_engine_name}: {e}", exc_info=True)
            raise STTProviderError(
                message=f"Internal router error while processing with {selected_engine_name}: {str(e)}",
                provider_name=selected_engine_name
            )