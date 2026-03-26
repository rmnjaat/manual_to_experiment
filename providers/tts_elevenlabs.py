"""ElevenLabs TTS provider — high quality, multi-voice, multilingual."""
from .base import TTSProvider
from stage5_audio.tts_elevenlabs import generate_audio as _generate


class ElevenLabsProvider(TTSProvider):
    """High quality TTS using ElevenLabs API."""

    def __init__(
        self,
        api_key: str,
        voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
        model_id: str = "eleven_multilingual_v2",
        language: str = "en",
        speed: float = 1.0,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.language = language
        self.speed = speed
        self.stability = stability
        self.similarity_boost = similarity_boost

    def generate(self, text: str, output_path: str, **kwargs) -> tuple[str, float]:
        return _generate(
            text,
            output_path,
            api_key=self.api_key,
            voice_id=kwargs.get("voice_id", self.voice_id),
            model_id=kwargs.get("model_id", self.model_id),
            language=kwargs.get("language", self.language),
            speed=kwargs.get("speed", self.speed),
            stability=kwargs.get("stability", self.stability),
            similarity_boost=kwargs.get("similarity_boost", self.similarity_boost),
        )
