"""
Website HTML reader module for Brand Visibility Agent.

Fetches live HTML content using requests with retry/timeout logic or reads cached raw HTML.
Completely industry-agnostic and business-type neutral.
"""

import time
from pathlib import Path
import requests
from brand_visibility.exceptions import SiteUnreachableError, get_brand_dir

# Standard browser headers to ensure web servers return HTML content cleanly
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_url(url: str, timeout: int = 10, retries: int = 1) -> tuple[str, str, str | None]:
    """
    Fetch raw HTML from a website URL.

    - timeout: max time in seconds per attempt (default: 10s)
    - retries: number of retry attempts on failure (default: 1)

    Returns tuple: (status, html_content, error_detail)
    - On success: ("completed", raw_html_string, None)
    - On failure: ("error", "", "site_unreachable")
    """
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    attempts = 1 + max(0, retries)
    last_exception = None

    for attempt in range(attempts):
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            response.raise_for_status()
            if response.text and len(response.text) > 100:
                return "completed", response.text, None
            return "completed", response.text, None
        except (requests.RequestException, Exception) as exc:
            last_exception = exc
            if attempt < attempts - 1:
                time.sleep(1)

    return "error", "", "site_unreachable"


def save_cached_html(brand_id: str, html_content: str, brand_type: str = None) -> Path:
    """Save raw HTML to disk cache for replay/offline inspection."""
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    cache_dir = brand_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "raw_page.html"
    cache_file.write_text(html_content, encoding="utf-8")
    return cache_file


def read_cached_html(brand_id: str, brand_type: str = None) -> str:
    """
    Read cached raw HTML for a given brand_id if available.
    
    Raises FileNotFoundError if cached file does not exist.
    """
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    cache_file = brand_dir / "cache" / "raw_page.html"
    
    if not cache_file.exists():
        raise FileNotFoundError(f"No cached HTML found for brand '{brand_id}' at {cache_file}")
        
    content = cache_file.read_text(encoding="utf-8")
    if not content:
        raise SiteUnreachableError(f"Cached HTML for brand '{brand_id}' is empty.")
        
    return content
