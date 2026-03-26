"""Text-to-speech using Google TTS (gTTS) — free, simple, no API key."""
import os
import subprocess
import wave

from gtts import gTTS


def _get_wav_duration(path: str) -> float:
    """Read the duration of a .wav file in seconds."""
    with wave.open(path, "r") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def generate_audio(
    narration: str,
    output_path: str,
    language: str = "en",
    **kwargs,
) -> tuple[str, float]:
    """Generate speech audio from narration text using Google TTS.

    Args:
        narration: The text to speak.
        output_path: Where to save the .wav file.
        language: Language code (default "en").

    Returns:
        Tuple of (output_path, duration_seconds).
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # gTTS generates MP3 — convert to WAV via ffmpeg
    mp3_path = output_path.replace(".wav", ".mp3")
    tts = gTTS(text=narration, lang=language)
    tts.save(mp3_path)

    # Convert MP3 to WAV using ffmpeg (no pydub needed)
    subprocess.run(
        ["ffmpeg", "-y", "-i", mp3_path, output_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # Cleanup temp MP3
    if os.path.exists(mp3_path):
        os.unlink(mp3_path)

    duration = _get_wav_duration(output_path)
    return output_path, duration
