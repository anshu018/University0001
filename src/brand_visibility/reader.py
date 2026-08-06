"""
Website HTML reader module for Brand Visibility Agent.

Fetches live HTML content using requests with retry/timeout logic or reads cached raw HTML.
Completely industry-agnostic and business-type neutral.
"""

import ipaddress
import socket
import time
from pathlib import Path
from urllib.parse import urlparse
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

# Maximum allowed HTML response body size (5 MB)
MAX_RESPONSE_BYTES = 5 * 1024 * 1024


def _is_safe_url(url: str) -> tuple[bool, str, str]:
    """
    Validate URL scheme and target IP address against SSRF attack vectors.

    Blocks private, loopback, link-local, reserved IP ranges, and cloud metadata endpoints.
    Returns tuple: (is_safe: bool, resolved_ip: str, hostname: str)
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, "", ""

        hostname = parsed.hostname
        if not hostname:
            return False, "", ""

        # Resolve IP addresses for the hostname
        addr_info = socket.getaddrinfo(hostname, None)
        if not addr_info:
            return False, "", hostname

        resolved_ips = []
        for family, socktype, proto, canonname, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)

            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_reserved
                or str(ip_obj) == "169.254.169.254"
                or str(ip_obj).endswith("169.254.169.254")
            ):
                return False, "", hostname

            resolved_ips.append(ip_str)

        if not resolved_ips:
            return False, "", hostname

        primary_ip = resolved_ips[0]
        return True, primary_ip, hostname
    except (ValueError, socket.gaierror, Exception):
        return False, "", ""


def fetch_url(url: str, timeout: int = 10, retries: int = 1) -> tuple[str, str, str | None]:
    """
    Fetch raw HTML from a website URL with SSRF defense, DNS rebinding IP pinning, and payload capping.

    - timeout: max time in seconds per attempt (default: 10s)
    - retries: number of retry attempts on failure (default: 1)

    Returns tuple: (status, html_content, error_detail)
    - On success: ("completed", raw_html_string, None)
    - On failure: ("error", "", "site_unreachable")
    """
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    is_safe, resolved_ip, hostname = _is_safe_url(url)
    if not is_safe or not resolved_ip:
        return "error", "", "site_unreachable"

    attempts = 1 + max(0, retries)
    last_exception = None

    orig_getaddrinfo = socket.getaddrinfo

    def _pinned_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if host == hostname:
            af = socket.AF_INET6 if ":" in resolved_ip else socket.AF_INET
            p = port if isinstance(port, int) else (443 if url.startswith("https") else 80)
            return [(af, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (resolved_ip, p))]
        return orig_getaddrinfo(host, port, family, type, proto, flags)

    headers = dict(DEFAULT_HEADERS)
    headers["Host"] = hostname

    for attempt in range(attempts):
        try:
            socket.getaddrinfo = _pinned_getaddrinfo
            try:
                response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            finally:
                socket.getaddrinfo = orig_getaddrinfo

            response.raise_for_status()

            chunks = []
            total_bytes = 0
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    total_bytes += len(chunk)
                    if total_bytes > MAX_RESPONSE_BYTES:
                        response.close()
                        return "error", "", "site_unreachable"
                    chunks.append(chunk)

            raw_bytes = b"".join(chunks)
            encoding = response.encoding or "utf-8"
            try:
                html_text = raw_bytes.decode(encoding, errors="replace")
            except Exception:
                html_text = raw_bytes.decode("utf-8", errors="replace")

            return "completed", html_text, None
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
