"""Generate multiple frames per scene for enhanced visual progression.

Instead of one static image per scene, generates 3 frames showing
the action progressing — then crossfaded in Remotion for smooth motion.

Example:
  visual_hint: "Hand turning the temperature dial to 180C on the air fryer"
  Frame 1: Hand approaching the dial
  Frame 2: Hand gripping and turning the dial
  Frame 3: Dial at 180C, hand releasing
"""
import json
import os
from google import genai
from google.genai import types


FRAME_DECOMPOSITION_PROMPT = """You are a cinematographer planning a 3-shot sequence for an instructional video.

Given a scene description, break it into exactly 3 frames that show the ACTION PROGRESSING:
- Frame 1: The BEGINNING of the action (one hand approaching, reaching, preparing)
- Frame 2: The MID-POINT of the action (one hand gripping, pressing, turning)
- Frame 3: The COMPLETION of the action (result visible, hand releasing, final state)

CRITICAL RULES:
- ONLY ONE person's hands in every frame. Maximum TWO hands. NEVER more than two hands.
- First-person POV — the viewer IS the person doing the action
- Use "a single hand", "one hand", "the right hand" — NEVER "hands" without specifying count
- Each frame must be a complete, standalone image description for an AI image generator
- Include the EXACT product name in every frame
- Keep the same camera angle, lighting, and background across all 3 frames
- Be very specific about hand position and product state in each frame
- If the scene has no physical action (e.g. intro/outro), use different camera angles instead with NO hands:
  Frame 1: Wide shot, Frame 2: Medium shot, Frame 3: Close-up detail

INPUT SCENE DESCRIPTION:
{visual_hint}

PRODUCT: {product_context}

Return ONLY a JSON array of exactly 3 strings (no markdown, no explanation):
["frame 1 description", "frame 2 description", "frame 3 description"]"""


def decompose_visual_hint(
    client: genai.Client,
    visual_hint: str,
    product_context: str = "",
    model_name: str = "gemini-2.5-flash",
) -> list[str]:
    """Use Gemini to decompose a visual_hint into 3 progressive frame descriptions.

    Args:
        client: Google genai client.
        visual_hint: The scene's visual description.
        product_context: Product name/brand for consistency.
        model_name: Gemini model to use.

    Returns:
        List of 3 frame description strings.
    """
    prompt = FRAME_DECOMPOSITION_PROMPT.format(
        visual_hint=visual_hint,
        product_context=product_context,
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=1024,
        ),
    )

    text = response.text.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        frames = json.loads(text)
        if isinstance(frames, list) and len(frames) == 3:
            return frames
    except json.JSONDecodeError:
        pass

    # Fallback: generate 3 frames manually from the hint
    return [
        f"Beginning of action: {visual_hint} — hands approaching, preparing to interact with {product_context}",
        f"Mid-action: {visual_hint} — hands actively interacting with {product_context}",
        f"Action complete: {visual_hint} — result visible, {product_context} in final state",
    ]


def generate_multi_frame(
    client: genai.Client,
    image_provider,
    visual_hint: str,
    output_dir: str,
    scene_id: int,
    product_context: str = "",
    model_name: str = "gemini-2.5-flash",
    num_frames: int = 3,
) -> list[str]:
    """Generate multiple frames for a single scene.

    Args:
        client: Google genai client (for frame decomposition).
        image_provider: The image generation provider to use.
        visual_hint: Scene's visual description.
        output_dir: Directory to save frame images.
        scene_id: Scene ID for file naming.
        product_context: Product name for consistency.
        model_name: Gemini model for decomposition.
        num_frames: Number of frames (default 3).

    Returns:
        List of paths to generated frame images.
    """
    # Step 1: Decompose visual_hint into frame descriptions
    frame_descriptions = decompose_visual_hint(
        client, visual_hint, product_context, model_name
    )

    # Step 2: Generate an image for each frame
    frame_paths = []
    os.makedirs(output_dir, exist_ok=True)

    for i, frame_desc in enumerate(frame_descriptions[:num_frames]):
        frame_path = os.path.join(output_dir, f"scene_{scene_id}_frame_{i}.png")
        try:
            image_provider.generate(
                frame_desc,
                frame_path,
                product_context=product_context,
            )
            frame_paths.append(frame_path)
        except Exception as e:
            print(f"[multi_frame] Frame {i} failed for scene {scene_id}: {e}")
            # If a frame fails, duplicate the previous one or skip
            if frame_paths:
                import shutil
                shutil.copy2(frame_paths[-1], frame_path)
                frame_paths.append(frame_path)

    return frame_paths
