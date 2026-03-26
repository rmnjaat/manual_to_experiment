"""OpenAI DALL-E 3 — cloud image generation provider.

Requires OPENAI_API_KEY environment variable.
DALL-E 3 excels at complex prompts with hands, interactions, and compositions.
"""
import os
from .base import ImageProvider
from stage4_images.dalle import generate_image as _generate


class DalleProvider(ImageProvider):
    """Image generation using OpenAI DALL-E 3."""

    def __init__(self, api_key: str | None = None, quality: str = "hd"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.quality = quality
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required for DALL-E 3 provider")

    def generate(self, prompt: str, output_path: str, **kwargs) -> str:
        context = kwargs.get("product_context", "")
        return _generate(
            self.api_key,
            prompt,
            output_path,
            product_context=context,
            quality=self.quality,
        )

    def get_name(self) -> str:
        return "DALL-E 3"
