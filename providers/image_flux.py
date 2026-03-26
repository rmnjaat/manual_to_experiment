"""Flux Pro 1.1 — cloud image generation provider (Black Forest Labs).

Requires FLUX_API_KEY environment variable.
Flux Pro produces exceptionally photorealistic images with fine-grained control.
"""
import os
from .base import ImageProvider
from stage4_images.flux import generate_image as _generate


class FluxProvider(ImageProvider):
    """Image generation using Flux Pro 1.1 (Black Forest Labs)."""

    def __init__(self, api_key: str | None = None, model: str = "flux-pro-1.1"):
        self.api_key = api_key or os.getenv("FLUX_API_KEY", "")
        self.model = model
        if not self.api_key:
            raise ValueError("FLUX_API_KEY required for Flux Pro provider")

    def generate(self, prompt: str, output_path: str, **kwargs) -> str:
        context = kwargs.get("product_context", "")
        return _generate(
            self.api_key,
            prompt,
            output_path,
            product_context=context,
            model=self.model,
        )

    def get_name(self) -> str:
        return "Flux Pro 1.1"
