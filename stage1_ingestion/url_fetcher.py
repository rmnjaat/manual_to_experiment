"""Fetch and clean HTML content from a URL."""
import re
import httpx


def _strip_html(html: str) -> str:
    """Strip scripts, styles, nav, footer, and HTML tags — keep only text."""
    # Remove script and style blocks entirely
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove nav, footer, header, aside
    html = re.sub(r'<(nav|footer|header|aside)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # Remove all HTML tags
    html = re.sub(r'<[^>]+>', ' ', html)
    # Decode common HTML entities
    html = html.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    html = html.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&#39;', "'")
    # Collapse whitespace
    html = re.sub(r'\s+', ' ', html).strip()
    return html


def fetch_url_html(url: str, timeout: int = 30, max_chars: int = 50000) -> str:
    """GET request, strip HTML junk, return clean text.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.
        max_chars: Maximum characters to return (avoids token limits).

    Returns:
        Cleaned text content from the page.
    """
    response = httpx.get(url, timeout=timeout, follow_redirects=True)
    response.raise_for_status()

    clean = _strip_html(response.text)

    # Truncate if still too long
    if len(clean) > max_chars:
        clean = clean[:max_chars] + "\n\n[Content truncated — original page was too long]"

    return clean
