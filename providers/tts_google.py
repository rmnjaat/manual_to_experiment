"""Google TTS (gTTS) — free, simple TTS provider."""
from .base import TTSProvider
from stage5_audio.tts_google import generate_audio as _generate


class GoogleTTSProvider(TTSProvider):
    """Free TTS using Google Translate's TTS engine (no API key needed)."""

    def __init__(self, language: str = "en", speed: float = 1.0):
        self.language = language
        self.speed = speed

    def generate(self, text: str, output_path: str, **kwargs) -> tuple[str, float]:
        lang = kwargs.get("language", self.language)
        speed = kwargs.get("speed", self.speed)
        return _generate(text, output_path, language=lang, speed=speed)
