"""Google Imagen 4 — cloud image generation provider."""
from google import genai
from .base import ImageProvider
from stage4_images.imagen import generate_image as _generate


class ImagenProvider(ImageProvider):
    """Image generation using Google Imagen 4 (uses Gemini credits)."""

    def __init__(self, client: genai.Client, model: str = "imagen-4.0-fast-generate-001", product_context: str = ""):
        self.client = client
        self.model = model
        self.product_context = product_context

    def generate(self, prompt: str, output_path: str, **kwargs) -> str:
        context = kwargs.get("product_context", self.product_context)
        return _generate(self.client, prompt, output_path, model=self.model, product_context=context)
