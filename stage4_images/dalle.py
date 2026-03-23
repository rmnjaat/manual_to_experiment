"""Generate images using OpenAI DALL-E 3 API.

DALL-E 3 excels at understanding complex prompts with human hands,
object interactions, and specific compositions — making it ideal for
instructional video frames.
"""
import os
import io
import httpx
from PIL import Image


STYLE_PREFIX = (
    "Photorealistic first-person POV instructional photograph. "
    "Show ONLY ONE person's hands (maximum two hands) from the viewer's perspective. "
    "NEVER show more than two hands. NEVER show mirrored or duplicate hands. "
    "Warm studio lighting, soft shadows, shallow depth of field. "
    "Clean modern workspace background. "
    "No text, no watermarks, no logos, no overlays. "
)

STYLE_SUFFIX = (
    " 4K, professional product photography, cinematic color grading. "
    "Single person's hands only. Natural hand anatomy. No extra limbs."
)


def generate_image(
    api_key: str,
    visual_hint: str,
    output_path: str,
    product_context: str = "",
    quality: str = "hd",
    size: str = "1792x1024",
) -> str:
    """Generate a scene image using DALL-E 3.

    Args:
        api_key: OpenAI API key.
        visual_hint: Description of what the image should show.
        output_path: Where to save the PNG file.
        product_context: Product name/brand for consistency.
        quality: "standard" or "hd".
        size: Image size ("1792x1024" for landscape).

    Returns:
        The output_path on success.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "OpenAI package not installed. Run: pip install openai"
        )

    client = OpenAI(api_key=api_key)

    context = f"Product: {product_context}. " if product_context else ""
    full_prompt = STYLE_PREFIX + context + visual_hint + STYLE_SUFFIX

    response = client.images.generate(
        model="dall-e-3",
        prompt=full_prompt,
        size=size,
        quality=quality,
        n=1,
    )

    image_url = response.data[0].url

    # Download the image
    img_response = httpx.get(image_url, timeout=60)
    img_response.raise_for_status()

    img = Image.open(io.BytesIO(img_response.content))
    img = img.resize((1920, 1080), Image.LANCZOS)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG")
    return output_path
