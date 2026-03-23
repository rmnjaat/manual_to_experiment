"""Generate images using Flux Pro 1.1 API (Black Forest Labs).

Flux Pro produces exceptionally photorealistic images with
fine-grained prompt following — great for consistent product shots.
"""
import os
import io
import time
import httpx
from PIL import Image


BFL_API_BASE = "https://api.bfl.ml/v1"

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
    model: str = "flux-pro-1.1",
    width: int = 1920,
    height: int = 1080,
    poll_interval: int = 3,
    max_wait: int = 120,
) -> str:
    """Generate a scene image using Flux Pro.

    Args:
        api_key: Black Forest Labs API key.
        visual_hint: Description of what the image should show.
        output_path: Where to save the PNG file.
        product_context: Product name/brand for consistency.
        model: Flux model variant.
        width: Image width.
        height: Image height.
        poll_interval: Seconds between status checks.
        max_wait: Maximum seconds to wait.

    Returns:
        The output_path on success.
    """
    context = f"Product: {product_context}. " if product_context else ""
    full_prompt = STYLE_PREFIX + context + visual_hint + STYLE_SUFFIX

    headers = {
        "x-key": api_key,
        "Content-Type": "application/json",
    }

    # Step 1: Submit generation request
    submit_resp = httpx.post(
        f"{BFL_API_BASE}/{model}",
        headers=headers,
        json={
            "prompt": full_prompt,
            "width": width,
            "height": height,
        },
        timeout=30,
    )
    submit_resp.raise_for_status()
    request_id = submit_resp.json()["id"]

    # Step 2: Poll for result
    elapsed = 0
    while elapsed < max_wait:
        result_resp = httpx.get(
            f"{BFL_API_BASE}/get_result",
            params={"id": request_id},
            headers=headers,
            timeout=30,
        )
        result_resp.raise_for_status()
        result = result_resp.json()

        if result["status"] == "Ready":
            image_url = result["result"]["sample"]
            break
        elif result["status"] in ("Error", "Failed"):
            raise RuntimeError(f"Flux generation failed: {result.get('error', 'unknown')}")

        time.sleep(poll_interval)
        elapsed += poll_interval
    else:
        raise TimeoutError(f"Flux generation timed out after {max_wait}s")

    # Step 3: Download and save image
    img_response = httpx.get(image_url, timeout=60)
    img_response.raise_for_status()

    img = Image.open(io.BytesIO(img_response.content))
    img = img.resize((1920, 1080), Image.LANCZOS)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG")
    return output_path
