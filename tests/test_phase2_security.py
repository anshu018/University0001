"""
Tests for Phase 2 Security Hardening:
- SDK timeout forwarding to Gemini and Groq calls
- Thread-safe state locking for _real_call_count and _circuit_state
- Sanitization of raw exception messages
- Dependency hygiene validation for requirements.txt
"""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest
from brand_visibility.ai_client import ask_ai, reset_client_state
from config import settings


def test_sdk_timeouts_passed_to_gemini_and_groq(monkeypatch):
    """Verify that configured AI_REQUEST_TIMEOUT setting is passed to underlying SDKs."""
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "fake-key")
    monkeypatch.setattr(settings, "AI_REQUEST_TIMEOUT", 25)

    with patch("brand_visibility.ai_client._call_gemini") as mock_gemini:
        mock_gemini.return_value = "gemini-response"
        ask_ai("test question", engine="engine_a")
        mock_gemini.assert_called_once_with("test question", "fake-key", brand_context=None, timeout=25)

    reset_client_state()

    with patch("brand_visibility.ai_client._call_groq") as mock_groq:
        mock_groq.return_value = "groq-response"
        ask_ai("test question", engine="engine_b")
        mock_groq.assert_called_once_with("test question", "fake-key", brand_context=None, timeout=25)


def test_multithreaded_concurrency_safety(monkeypatch):
    """Verify that concurrent calls in multi-threaded environment execute cleanly without race conditions."""
    reset_client_state()
    monkeypatch.setattr(settings, "REAL_MODE", False)

    def _worker(idx):
        return ask_ai(f"question {idx}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(isinstance(r, str) and len(r) > 0 for r in results)


def test_exception_sanitization_masks_raw_details(monkeypatch):
    """Verify that generic exceptions return sanitized error strings without leaking internal tracebacks."""
    reset_client_state()
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-key")

    class SensitiveInternalException(Exception):
        pass

    with patch("brand_visibility.ai_client._call_gemini", side_effect=SensitiveInternalException("secret_internal_ip_10.0.0.1")):
        answer = ask_ai("test", engine="engine_a")

    assert "[engine_a error: request failed]" in answer
    assert "secret_internal_ip" not in answer


def test_requirements_txt_contains_mcp_and_bounded_versions():
    """Verify requirements.txt contains mcp>=1.27,<2 and bounded version specs."""
    from pathlib import Path

    req_file = Path(__file__).resolve().parent.parent / "requirements.txt"
    assert req_file.exists()
    content = req_file.read_text(encoding="utf-8")

    assert "mcp>=1.27.0,<2" in content or "mcp>=1.27,<2" in content
    assert "requests>=" in content
    assert "google-generativeai>=" in content
    assert "groq>=" in content
    assert "yake>=" in content
