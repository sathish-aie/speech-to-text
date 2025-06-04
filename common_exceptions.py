class STTProviderError(Exception):
    """Custom exception for errors originating from STT providers via adapters."""
    def __init__(self, message: str, provider_name: str, status_code: int = 500):
        self.message = message
        self.provider_name = provider_name
        self.status_code = status_code
        super().__init__(f"STT Provider '{provider_name}' Error: {message}")

class AudioProcessingError(ValueError):
    """Custom exception for errors during audio processing (e.g., ffmpeg, ffprobe)."""
    pass
