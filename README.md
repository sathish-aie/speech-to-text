# Speech-to-Text MCP Server

A FastAPI transcription service. Its `POST /v1/transcribe` endpoint is also exposed as an MCP tool (`transcribe_audio`) through [fastapi-mcp](https://github.com/tadata-org/fastapi_mcp), so MCP clients such as Claude Desktop or an IDE agent can call it directly.

## What it does

1. **Preprocesses audio.** It accepts any format FFmpeg can read, checks the duration with `ffprobe` (1 hour maximum by default), and converts the audio to 16 kHz mono PCM WAV.
2. **Routes to a provider** through LiteLLM:

   | `engine` | Provider call |
   | --- | --- |
   | `distil-whisper` | Groq `distil-whisper-large-v3-en` |
   | `gpt-4o`, `gpt-4o-mini` | OpenAI. Both currently call `whisper-1`; see [`adapters/openai/`](adapters/openai/). |
   | `auto` | Picked by `DEFAULT_ENGINE_POLICY`: `high_accuracy` → gpt-4o, `cheap` → distil-whisper, `gpt-4o-mini` → gpt-4o-mini |

3. **Returns** the text, the engine used, the duration and the detected language. Provider failures map to HTTP 502 and bad audio to HTTP 400.

## Project layout

```
main.py              FastAPI app, /v1/transcribe, MCP mount
router.py            engine selection and policy
adapters/            one transcriber class per provider (OpenAI, Groq)
audio_utils.py       ffprobe duration check + FFmpeg conversion
config.py            settings from .env (pydantic-settings)
schemas.py           request and response models
common_exceptions.py provider and audio errors
```

## Run it

You need Python 3.12, FFmpeg on your PATH, and OpenAI and Groq API keys. Both keys are required at startup.

```bash
pip install -r requirements.txt
printf "OPENAI_API_KEY=...\nGROQ_API_KEY=...\n" > .env
python main.py          # http://localhost:8000, MCP endpoint at /mcp
```

## Example

```bash
curl -X POST http://localhost:8000/v1/transcribe \
  -F "file=@audio.mp3" \
  -F "engine=auto" \
  -F "language=auto"
```

```json
{
  "text": "Transcribed text...",
  "duration_ms": 12345,
  "model": "gpt-4o-mini",
  "language": "en"
}
```
