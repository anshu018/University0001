"""
Tests for Phase 1 Security Hardening:
- Path traversal defense in brand_visibility.exceptions.get_brand_dir
- SSRF prevention & URL scheme validation in brand_visibility.reader.fetch_url
- Stdio protocol isolation in brand_visibility.step4_prove.run_prove
"""

import io
import sys
import pytest
from brand_visibility.exceptions import get_brand_dir
from brand_visibility.reader import _is_safe_url, fetch_url
from brand_visibility.step4_prove import run_prove


def test_get_brand_dir_path_traversal_prevention():
    """Verify that path traversal attempts or invalid brand_ids raise ValueError."""
    with pytest.raises(ValueError, match="Invalid brand_id format"):
        get_brand_dir("../test")

    with pytest.raises(ValueError, match="Invalid brand_id format"):
        get_brand_dir("../../etc/passwd")

    with pytest.raises(ValueError, match="Invalid brand_id format"):
        get_brand_dir("brand/dir")

    with pytest.raises(ValueError, match="brand_id must be a non-empty string"):
        get_brand_dir("")


def test_get_brand_dir_valid_resolutions():
    """Verify that valid brand_id names resolve cleanly without error."""
    path = get_brand_dir("zomato", brand_type="test")
    assert "brands" in str(path)
    assert path.name == "zomato"


def test_ssrf_url_validation_blocks_internal_ips():
    """Verify that _is_safe_url rejects loopback, private IPs, metadata endpoints, and invalid schemes."""
    assert not _is_safe_url("http://127.0.0.1")[0]
    assert not _is_safe_url("http://localhost")[0]
    assert not _is_safe_url("http://169.254.169.254")[0]
    assert not _is_safe_url("file:///etc/passwd")[0]
    assert not _is_safe_url("ftp://example.com/file")[0]


def test_fetch_url_ssrf_returns_site_unreachable():
    """Verify that fetch_url returns site_unreachable on restricted SSRF URLs."""
    status, content, error = fetch_url("http://127.0.0.1")
    assert status == "error"
    assert content == ""
    assert error == "site_unreachable"

    status, content, error = fetch_url("http://169.254.169.254")
    assert status == "error"
    assert content == ""
    assert error == "site_unreachable"


def test_step4_prove_stdio_discipline():
    """Verify that run_prove writes 0 bytes to sys.stdout, redirecting all logs to stderr."""
    stdout_buf = io.StringIO()
    orig_stdout = sys.stdout
    sys.stdout = stdout_buf

    try:
        res = run_prove("zomato", brand_type="test")
        assert res["brand_id"] == "zomato"
        assert res["before"] != ""
        assert res["after"] != ""
        # Assert stdout remains completely empty (stdio protocol isolation)
        assert stdout_buf.getvalue() == ""
    finally:
        sys.stdout = orig_stdout
