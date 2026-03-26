"""Product image provider — uses scraped product photos for scene images."""
from .base import ImageProvider
from stage4_images.product_image import create_scene_image


class ProductImageProvider(ImageProvider):
    """Uses real product photos scraped from the source URL."""

    def __init__(self, product_images: list[str]):
        """
        Args:
            product_images: List of downloaded product image file paths.
        """
        self.product_images = product_images

    def generate(self, prompt: str, output_path: str, **kwargs) -> str:
        scene_index = kwargs.get("scene_index", 0)
        scene_type = kwargs.get("scene_type", "")
        section_name = kwargs.get("section_name", "")
        step_text = kwargs.get("step_text", "")

        # Cycle through available product images
        if self.product_images:
            img_path = self.product_images[scene_index % len(self.product_images)]
        else:
            raise RuntimeError("No product images available")

        return create_scene_image(
            product_image_path=img_path,
            output_path=output_path,
            scene_type=scene_type,
            step_text=step_text,
            section_name=section_name,
        )
