"""Text-to-speech using ElevenLabs API — high quality, multi-voice, multilingual."""
import os
import subprocess
import wave

from elevenlabs.client import ElevenLabs


def _get_wav_duration(path: str) -> float:
    """Read the duration of a .wav file in seconds."""
    with wave.open(path, "r") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def list_voices(api_key: str) -> list[dict]:
    """List available ElevenLabs voices."""
    try:
        client = ElevenLabs(api_key=api_key)
        response = client.voices.get_all()
        return [
            {"voice_id": v.voice_id, "name": v.name, "category": getattr(v, "category", "")}
            for v in response.voices
        ]
    except Exception:
        # Fallback: ElevenLabs default library voices (always available)
        return [
            {"voice_id": "JBFqnCBsd6RMkjVDRZzb", "name": "George (British male)", "category": "premade"},
            {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah (American female)", "category": "premade"},
            {"voice_id": "TX3LPaxmHKxFdv7VOQHJ", "name": "Liam (American male)", "category": "premade"},
            {"voice_id": "XB0fDUnXU5powFXDhCwa", "name": "Charlotte (Swedish female)", "category": "premade"},
            {"voice_id": "pFZP5JQG7iQjIQuC4Bku", "name": "Lily (British female)", "category": "premade"},
            {"voice_id": "bIHbv24MWmeRgasZH58o", "name": "Will (American male)", "category": "premade"},
            {"voice_id": "nPczCjzI2devNBz1zQrb", "name": "Brian (American male)", "category": "premade"},
            {"voice_id": "XrExE9yKIg1WjnnlVkGX", "name": "Matilda (American female)", "category": "premade"},
            {"voice_id": "onwK4e9ZLuTAKqWW03F9", "name": "Daniel (British male)", "category": "premade"},
            {"voice_id": "N2lVS1w4EtoT3dr4eOWO", "name": "Callum (Transatlantic male)", "category": "premade"},
            {"voice_id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie (Australian male)", "category": "premade"},
            {"voice_id": "cjVigY5qzO86Huf0OWal", "name": "Eric (American male)", "category": "premade"},
            {"voice_id": "iP95p4xoKVk53GoZ742B", "name": "Chris (American male)", "category": "premade"},
            {"voice_id": "9BWtsMINqrJLrRacOk9x", "name": "Aria (American female)", "category": "premade"},
            {"voice_id": "FGY2WhTYpPnrIDTdsKH5", "name": "Laura (American female)", "category": "premade"},
        ]


def list_models(api_key: str) -> list[dict]:
    """List available ElevenLabs models."""
    client = ElevenLabs(api_key=api_key)
    models = client.models.list()
    return [
        {"model_id": m.model_id, "name": m.name}
        for m in models
    ]


def generate_audio(
    narration: str,
    output_path: str,
    api_key: str,
    voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
    model_id: str = "eleven_multilingual_v2",
    language: str = "en",
    speed: float = 1.0,
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    **kwargs,
) -> tuple[str, float]:
    """Generate speech audio using ElevenLabs.

    Args:
        narration: Text to speak.
        output_path: Where to save the .wav file.
        api_key: ElevenLabs API key.
        voice_id: Voice to use.
        model_id: Model to use.
        language: Language code (e.g. "en", "hi", "fr").
        speed: Speech speed (0.7 - 1.3).
        stability: Voice stability (0.0 - 1.0).
        similarity_boost: Voice similarity boost (0.0 - 1.0).

    Returns:
        Tuple of (output_path, duration_seconds).
    """
    from elevenlabs import VoiceSettings

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Clamp speed to ElevenLabs allowed range
    speed = max(0.7, min(1.2, speed))

    client = ElevenLabs(api_key=api_key)

    # Generate as MP3 first (more reliable), then convert to WAV
    mp3_path = output_path.replace(".wav", ".mp3")

    audio = client.text_to_speech.convert(
        text=narration,
        voice_id=voice_id,
        model_id=model_id,
        language_code=language,
        output_format="mp3_44100_128",
        voice_settings=VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost,
            speed=speed,
        ),
    )

    with open(mp3_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    # Convert MP3 to WAV
    subprocess.run(
        ["ffmpeg", "-y", "-i", mp3_path, output_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    if os.path.exists(mp3_path):
        os.unlink(mp3_path)

    duration = _get_wav_duration(output_path)
    return output_path, duration
