"""Create scene images using scraped product photos with text overlay."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """Try to load a good font, fall back to default."""
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSText.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _load_and_fit(image_path: str, target_size: tuple[int, int] = (1920, 1080)) -> Image.Image:
    """Load an image and resize/crop it to fill 1920x1080."""
    img = Image.open(image_path).convert("RGB")
    tw, th = target_size
    iw, ih = img.size

    # Scale to cover the target
    scale = max(tw / iw, th / ih)
    new_w = int(iw * scale)
    new_h = int(ih * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Center crop
    left = (new_w - tw) // 2
    top = (new_h - th) // 2
    img = img.crop((left, top, left + tw, top + th))
    return img


def create_scene_image(
    product_image_path: str,
    output_path: str,
    scene_type: str = "",
    step_text: str = "",
    section_name: str = "",
) -> str:
    """Create a scene image with product photo background and text overlay.

    Args:
        product_image_path: Path to the product photo.
        output_path: Where to save the final image.
        scene_type: Type of scene (intro, step, outro, etc.)
        step_text: Short text to overlay (step description).
        section_name: Section name for context.

    Returns:
        The output_path.
    """
    # Load and fit product image to 1920x1080
    bg = _load_and_fit(product_image_path)

    # Add a semi-transparent dark gradient at the bottom for text readability
    overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    # Bottom gradient overlay (darker at bottom)
    for y in range(540, 1080):
        alpha = int(180 * ((y - 540) / 540))
        draw_overlay.line([(0, y), (1920, y)], fill=(0, 0, 0, alpha))

    # Top bar for scene type
    draw_overlay.rectangle([0, 0, 1920, 80], fill=(0, 0, 0, 140))

    bg = bg.convert("RGBA")
    bg = Image.alpha_composite(bg, overlay).convert("RGB")

    draw = ImageDraw.Draw(bg)
    font_large = _get_font(52)
    font_medium = _get_font(32)
    font_small = _get_font(24)

    # Scene type badge at top
    badge_text = scene_type.upper() if scene_type else ""
    if badge_text:
        # Badge colors by type
        badge_colors = {
            "INTRO": (79, 142, 255),
            "STEP": (76, 175, 80),
            "PREREQUISITES": (255, 170, 79),
            "SECTION_TRANSITION": (176, 79, 255),
            "OUTRO": (79, 142, 255),
        }
        color = badge_colors.get(badge_text, (200, 200, 200))
        draw.text((40, 22), badge_text, fill=color, font=font_medium)

    # Section name at top right
    if section_name:
        bbox = draw.textbbox((0, 0), section_name, font=font_small)
        tw = bbox[2] - bbox[0]
        draw.text((1920 - tw - 40, 28), section_name, fill=(180, 180, 180), font=font_small)

    # Step text at bottom
    if step_text:
        # Word wrap
        words = step_text.split()
        lines = []
        current = []
        for word in words:
            current.append(word)
            test_line = " ".join(current)
            bbox = draw.textbbox((0, 0), test_line, font=font_large)
            if bbox[2] - bbox[0] > 1700:
                current.pop()
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))

        # Draw from bottom up
        y = 1080 - 60 - len(lines) * 65
        for line in lines:
            draw.text((60, y), line, fill=(255, 255, 255), font=font_large)
            y += 65

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    bg.save(output_path, "PNG")
    return output_path
