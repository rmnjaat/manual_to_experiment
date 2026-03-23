"""Generate video clips from images using Google Veo 2.

Takes a generated scene image and a motion description, then uses
Google's Veo model to create a short video clip with actual motion.

This is the "Cinematic" quality mode — produces real motion instead of
static images with Ken Burns effect.
"""
import os
import time
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image


# Available Veo models
VEO_MODELS = [
    "veo-2.0-generate-001",
]


def generate_video_clip(
    client: genai.Client,
    image_path: str,
    motion_hint: str,
    output_path: str,
    model: str = "veo-2.0-generate-001",
    duration_seconds: int = 5,
    poll_interval: int = 10,
    max_wait: int = 300,
) -> str:
    """Generate a video clip from a static image using Veo.

    Args:
        client: Google genai client.
        image_path: Path to the source image (PNG/JPG).
        motion_hint: Description of the motion/action to animate.
        output_path: Where to save the output video (MP4).
        model: Veo model to use.
        duration_seconds: Target clip duration (5 or 8 seconds).
        poll_interval: Seconds between status checks.
        max_wait: Maximum seconds to wait for generation.

    Returns:
        Path to the generated video clip.
    """
    # Load the source image
    image = Image.open(image_path)

    # Submit video generation request
    operation = client.models.generate_videos(
        model=model,
        image=image,
        config=types.GenerateVideoConfig(
            prompt=motion_hint,
            person_generation="allow_all",
            aspect_ratio="16:9",
            number_of_videos=1,
        ),
    )

    # Poll until complete
    elapsed = 0
    while not operation.done:
        if elapsed >= max_wait:
            raise TimeoutError(
                f"Veo video generation timed out after {max_wait}s for: {motion_hint[:60]}"
            )
        time.sleep(poll_interval)
        elapsed += poll_interval
        operation = client.operations.get(operation)

    # Download the generated video
    if not operation.result or not operation.result.generated_videos:
        raise RuntimeError(f"Veo returned no video for: {motion_hint[:60]}")

    video = operation.result.generated_videos[0]

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Download video file
    video_data = client.files.download(file=video.video)
    with open(output_path, "wb") as f:
        for chunk in video_data:
            f.write(chunk)

    return output_path


def generate_motion_hint(visual_hint: str, narration: str = "") -> str:
    """Generate a motion description from visual hint and narration.

    Creates a concise motion prompt for Veo based on what the scene
    is about. Focuses on the primary physical action.

    Args:
        visual_hint: The scene's visual description.
        narration: The scene's narration text.

    Returns:
        A motion description string for Veo.
    """
    # Extract the key action from the visual hint
    action_words = [
        "turn", "press", "push", "pull", "open", "close", "remove", "insert",
        "plug", "connect", "slide", "rotate", "flip", "lift", "place", "pour",
        "fill", "empty", "adjust", "set", "lock", "unlock", "attach", "detach",
    ]

    hint_lower = visual_hint.lower()
    has_action = any(word in hint_lower for word in action_words)

    if has_action:
        return f"Smooth, natural motion: {visual_hint}. Realistic hand movement, steady camera."
    else:
        # For scenes without explicit action, use a slow camera movement
        return f"Slow cinematic camera pan across the scene. {visual_hint}. Gentle zoom movement."
