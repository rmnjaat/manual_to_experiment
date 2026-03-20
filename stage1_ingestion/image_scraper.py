"""Scrape product images from a URL."""
import os
import re
from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx


class _ImgParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.images: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "img":
            return
        d = dict(attrs)
        # Try src, then data-src (lazy loading)
        src = d.get("src") or d.get("data-src") or ""
        if not src or src.startswith("data:"):
            return
        src = urljoin(self.base_url, src)
        # Filter for actual product images (skip icons, logos, tiny assets)
        if any(ext in src.lower() for ext in (".jpg", ".jpeg", ".png", ".webp")):
            if not any(skip in src.lower() for skip in ("icon", "logo", "favicon", "badge", "sprite", "bolt")):
                self.images.append(src)


def _extract_og_image(html: str) -> str | None:
    """Extract Open Graph image from meta tags."""
    match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html)
    if match:
        return match.group(1)
    match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', html)
    if match:
        return match.group(1)
    return None


def scrape_product_images(url: str, save_dir: str, max_images: int = 5) -> list[str]:
    """Download product images from a URL.

    Args:
        url: The product page URL.
        save_dir: Directory to save downloaded images.
        max_images: Maximum number of images to download.

    Returns:
        List of saved image file paths.
    """
    os.makedirs(save_dir, exist_ok=True)

    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    html = resp.text

    # Collect image URLs
    image_urls: list[str] = []

    # Try OG image first (usually the hero/product image)
    og = _extract_og_image(html)
    if og:
        image_urls.append(og)

    # Parse all img tags
    parser = _ImgParser(url)
    parser.feed(html)
    for img_url in parser.images:
        if img_url not in image_urls:
            image_urls.append(img_url)

    # Download images
    saved: list[str] = []
    seen_urls: set[str] = set()
    for img_url in image_urls:
        if len(saved) >= max_images:
            break
        # Deduplicate by base URL (ignore query params)
        base = img_url.split("?")[0]
        if base in seen_urls:
            continue
        seen_urls.add(base)

        try:
            img_resp = httpx.get(img_url, timeout=15, follow_redirects=True)
            img_resp.raise_for_status()

            # Determine extension
            content_type = img_resp.headers.get("content-type", "")
            if "webp" in content_type:
                ext = ".webp"
            elif "png" in content_type:
                ext = ".png"
            else:
                ext = ".jpg"

            filename = f"product_{len(saved)}{ext}"
            filepath = os.path.join(save_dir, filename)
            with open(filepath, "wb") as f:
                f.write(img_resp.content)
            saved.append(filepath)
        except Exception:
            continue

    return saved
