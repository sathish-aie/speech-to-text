# Speech-to-Text MCP Server

A high-performance Speech-to-Text server built with FastAPI that implements the Model Context Protocol (MCP) architecture. This server provides a unified interface for multiple STT providers (OpenAI Whisper, Groq) while following MCP standards for model serving and context management.

## 🎯 About MCP

The Model Context Protocol (MCP) is a standardized protocol for model serving that:
- Defines how AI models should expose their capabilities
- Manages model contexts and state
- Provides consistent interfaces across different model providers
- Enables seamless model switching and fallback strategies

Our STT server implements MCP through FastAPI-MCP, allowing:
- Standardized model routing
- Unified context handling
- Consistent error management
- Provider-agnostic model serving

## 🌟 Features

- **MCP Implementation**: 
  - Full Model Context Protocol support
  - FastAPI-MCP integration
  - Standardized model interfaces
  - Context-aware request handling
- **Multi-Provider Support**: 
  - OpenAI Whisper
  - Groq
  - Extensible architecture for adding more providers
- **Audio Processing**:
  - Automatic audio format conversion
  - Sample rate normalization (16kHz)
  - Duration validation
  - Support for multiple input formats (wav, mp3, ogg, flac, m4a)
- **API Features**:
  - Fast async processing
  - MCP-compliant provider selection
  - Language detection and specification
  - Comprehensive error handling
  - Detailed logging

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- FFmpeg installed on your system
- Poetry for dependency management
- API keys for providers (OpenAI, Groq)

### Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd stt
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Set up environment variables:
```bash
# Create .env file
cp .env.example .env

# Edit .env with your API keys
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gk-...
```

### Running the Server

```bash
poetry run uvicorn stt.main:app --reload
```

The server will start at `http://localhost:8000`

## 📝 API Usage

### Transcribe Audio

```bash
curl -X POST "http://localhost:8000/v1/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3" \
  -F "engine=auto" \
  -F "language=auto"
```

#### Parameters:

- `file`: Audio file to transcribe
- `engine`: Transcription engine choice (auto, openai, groq)
- `language`: Language of the audio (auto for detection)

#### Response:

```json
{
  "text": "Transcribed text content...",
  "model": "openai/whisper-1",
  "duration_ms": 12345,
  "language": "en"
}
```

## ⚙️ Configuration

### MCP Configuration
```python
# config.py
MCP_CONFIG = {
    "protocol_version": "1.0",
    "provider_configs": {
        "openai": {
            "context_window": 240000,  # 4 minutes in ms
            "max_tokens": None,  # No token limit for audio
        },
        "groq": {
            "context_window": 300000,  # 5 minutes in ms
            "max_tokens": None,
        }
    }
}
```

### General Settings
- `max_audio_duration_seconds`: Maximum allowed audio duration
- `default_engine_policy`: MCP-based policy for selecting transcription engine
- `default_engine`: Fallback engine if policy fails

## 🔧 Development

### Project Structure

```
stt/
├── adapters/         # MCP-compliant provider implementations
├── audio_utils.py    # Audio processing utilities
├── config.py         # MCP and general configuration
├── main.py          # FastAPI application and MCP routes
├── router.py        # MCP-based model routing logic
├── schemas.py       # Pydantic models and MCP schemas
└── common_exceptions.py  # MCP-compliant exceptions
```

### Adding a New Provider

1. Create a new MCP-compliant adapter in `adapters/`
2. Implement the MCP provider interface:
   ```python
   class NewProviderAdapter(MCPModelAdapter):
       async def process_context(self, context: MCPContext) -> MCPResponse:
           # Implementation
   ```
3. Register the provider in `router.py`
4. Update MCP configuration as needed

### MCP Integration Example

```python
from fastapi_mcp import FastApiMCP, MCPContext

@app.post("/v1/transcribe")
async def transcribe_audio(context: MCPContext):
    # MCP handles provider selection and execution
    response = await mcp_router.process(context)
    return response
```

## 📚 Documentation

For more detailed information about MCP and its implementation:

- [Model Context Protocol Specification](https://mcp-docs.example.com)
- [FastAPI-MCP Documentation](https://fastapi-mcp.readthedocs.io/)
- [MCP Provider Implementation Guide](https://mcp-docs.example.com/provider-guide)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- [Model Context Protocol](https://github.com/model-context-protocol/specification)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI-MCP Documentation](https://fastapi-mcp.readthedocs.io/)
- [LiteLLM Documentation](https://docs.litellm.ai/) 