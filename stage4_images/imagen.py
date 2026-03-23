"""Generate images using Google Imagen 4.0 API."""
import os
from google import genai
from google.genai import types
from PIL import Image
import io


STYLE_PREFIX = (
    "Photorealistic first-person POV instructional photograph. "
    "Show ONLY ONE person's hands (maximum two hands) from the viewer's perspective, "
    "as if the viewer is performing the action themselves. "
    "NEVER show more than two hands. NEVER show mirrored or duplicate hands. "
    "Warm studio lighting, soft shadows, shallow depth of field. "
    "Clean modern workspace background. "
    "No text, no watermarks, no logos, no overlays. "
)
STYLE_SUFFIX = (
    " 4K, professional product photography, cinematic color grading. "
    "Single person's hands only. Natural hand anatomy. No extra limbs."
)

# Available Imagen models (best to fastest)
IMAGEN_MODELS = [
    "imagen-4.0-generate-001",
    "imagen-4.0-fast-generate-001",
]


def generate_image(
    client: genai.Client,
    visual_hint: str,
    output_path: str,
    model: str = "imagen-4.0-fast-generate-001",
    product_context: str = "",
) -> str:
    """Generate a 1920x1080 image from a visual hint using Imagen 4.

    Args:
        client: A google.genai.Client instance.
        visual_hint: Description of what the image should show.
        output_path: Where to save the PNG file.
        model: Imagen model to use.
        product_context: Product name/brand to include for consistency.

    Returns:
        The output_path on success.
    """
    # Build prompt with product context for coherent series
    context = f"Product: {product_context}. " if product_context else ""
    full_prompt = STYLE_PREFIX + context + visual_hint + STYLE_SUFFIX

    response = client.models.generate_images(
        model=model,
        prompt=full_prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
        ),
    )

    if not response.generated_images:
        raise RuntimeError(f"Imagen returned no images for: {visual_hint[:80]}")

    image_bytes = response.generated_images[0].image.image_bytes
    img = Image.open(io.BytesIO(image_bytes))
    img = img.resize((1920, 1080), Image.LANCZOS)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG")
    return output_path
