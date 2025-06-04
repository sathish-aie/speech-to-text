from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import JSONResponse
import logging
from typing import Annotated
from fastapi_mcp import FastApiMCP
# from stt.config import settings
# from stt.audio_utils import AudioPreprocessor, AudioProcessingError
# from stt.router import ModelRouter
# from stt.schemas import Transcript, EngineChoice
# from stt.common_exceptions import STTProviderError
from config import settings
from audio_utils import AudioPreprocessor, AudioProcessingError
from router import ModelRouter
from schemas import Transcript, EngineChoice
from common_exceptions import STTProviderError
import uvicorn
from contextlib import asynccontextmanager




logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup events
    logger.info("Application startup...")
    logger.info(f"OpenAI API Key Loaded: {'Yes' if settings.openai_api_key and settings.openai_api_key != 'sk-...' else 'No / Placeholder'}")
    logger.info(f"Groq API Key Loaded: {'Yes' if settings.groq_api_key and settings.groq_api_key != 'gk-...' else 'No / Placeholder'}")
    logger.info(f"Default engine policy: {settings.default_engine_policy}")
    logger.info(f"Default engine (fallback): {settings.default_engine}")
    logger.info(f"Max audio duration: {settings.max_audio_duration_seconds} seconds")
    yield
    # Shutdown events (if any) can go here
    logger.info("Application shutdown.")

app = FastAPI(
    title="Speech-to-Text MCP Server",
    description="A Speech-to-Text server using FastAPI, LiteLLM, and FFmpeg.",
    version="1.0.1",
    lifespan=lifespan
)

audio_preprocessor = AudioPreprocessor()
model_router = ModelRouter(app_settings=settings)


@app.exception_handler(STTProviderError)
async def stt_provider_exception_handler(request: Request, exc: STTProviderError):
    logger.error(f"STT Provider Error: {exc.message} from {exc.provider_name}", exc_info=True)
    status_code = exc.status_code if hasattr(exc, 'status_code') else 502
    return JSONResponse(
        status_code=status_code,
        content={"detail": f"Transcription error with {exc.provider_name}: {exc.message}"},
    )

@app.exception_handler(AudioProcessingError)
async def audio_processing_exception_handler(request: Request, exc: AudioProcessingError):
    logger.error(f"Audio Processing Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=400,
        content={"detail": f"Audio processing failed: {str(exc)}"},
    )


@app.post("/v1/transcribe", response_model=Transcript, operation_id="transcribe_audio")
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe."),
    engine: EngineChoice = Form(default="auto", description="Transcription engine choice. 'auto' applies configured policy."),
    language: str = Form(default="auto", description="Language of the audio (e.g., 'en', 'es', 'auto' for detection by model).")
):
    """
    Accepts an audio file and transcribes it using the specified or auto-selected engine.
    The audio duration is extracted, and the file is converted to 16kHz mono PCM.
    """
    logger.info(f"Received transcription request for file: {file.filename or 'N/A'}, size: {file.size}, content_type: {file.content_type}, engine: {engine}, language: {language}")

    if not file.content_type or not file.content_type.startswith("audio/"):
        if file.content_type != "application/octet-stream":
            logger.warning(f"File '{file.filename}' has potentially non-audio content type: {file.content_type}. Attempting processing.")

    try:
        logger.info(f"Preprocessing audio file: {file.filename or 'uploaded file'}")
        pcm_audio_bytes, audio_duration_ms = audio_preprocessor.to_pcm(file)
        logger.info(f"Audio preprocessing complete. PCM data size: {len(pcm_audio_bytes)} bytes. Duration: {audio_duration_ms}ms.")

        logger.info(f"Routing to model for transcription. Engine choice: {engine}, Language: {language}")
        
        transcript_result = await model_router.run(
            audio_bytes=pcm_audio_bytes,
            audio_duration_ms=audio_duration_ms,
            engine=engine,
            language=language
        )
        logger.info(f"Transcription successful for '{file.filename or 'uploaded_file'}'. Model used: {transcript_result.model}, Output text length: {len(transcript_result.text)}")

        return transcript_result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"An unexpected internal server error occurred during transcription for {file.filename or 'uploaded_file'}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected internal server error occurred.")
    
mcp = FastApiMCP(app, include_operations=["transcribe_audio"])

mcp.mount()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    
# if __name__ == "__main__":
#     transport = "stdio"
#     if transport == "stdio":
#         print("Running server with stdio transport")
#         mcp.run(transport="stdio")
#     elif transport == "sse":
#         print("Running server with SSE transport")
#         mcp.run(transport="sse")
#     else:
#         raise ValueError(f"Unknown transport: {transport}")