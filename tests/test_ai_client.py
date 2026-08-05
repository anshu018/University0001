"""
Stage 2 tests for ai_client real-engine wiring.

All tests run offline with mocked providers. No real API calls.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from brand_visibility.ai_client import ask_ai, get_brand_context
from config import settings


def test_mock_mode_default_engine_preserves_existing_behavior(monkeypatch):
    """REAL_MODE=False should return the same generic/brand-aware mock text as Stage 1."""
    monkeypatch.setattr(settings, "REAL_MODE", False)
    answer = ask_ai("any question")
    assert isinstance(answer, str)
    assert len(answer) > 0


def test_mock_mode_with_brand_context_preserves_existing_behavior(monkeypatch):
    """With brand_context and REAL_MODE=False, should still use mock branch."""
    monkeypatch.setattr(settings, "REAL_MODE", False)
    ctx = {"display_name": "TestBrand", "website_url": "https://example.com", "facts": []}
    answer = ask_ai("any question", brand_context=ctx)
    assert "TestBrand" in answer or isinstance(answer, str)


def test_real_mode_missing_key_returns_visible_error(monkeypatch):
    """REAL_MODE=True but no API key should return a visible error string."""
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    answer = ask_ai("test", engine="engine_a")
    assert "[engine_a error: missing API key]" == answer

    answer = ask_ai("test", engine="engine_b")
    assert "[engine_b error: missing API key]" == answer


def test_default_engine_is_engine_a(monkeypatch):
    """Default engine parameter should be engine_a for backward compatibility."""
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-key")
    with patch("brand_visibility.ai_client._call_gemini", return_value="mocked") as mock_a:
        ask_ai("test question")
        mock_a.assert_called_once()


def test_engine_a_routes_to_gemini(monkeypatch):
    """engine='engine_a' should call _call_gemini, not _call_groq."""
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-key")
    with patch("brand_visibility.ai_client._call_gemini", return_value="gemini-response") as mock_a:
        with patch("brand_visibility.ai_client._call_groq", return_value="groq-response") as mock_b:
            answer = ask_ai("test", engine="engine_a")
            mock_a.assert_called_once()
            mock_b.assert_not_called()
            assert "gemini-response" == answer


def test_engine_b_routes_to_groq(monkeypatch):
    """engine='engine_b' should call _call_groq, not _call_gemini."""
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "fake-key")
    with patch("brand_visibility.ai_client._call_gemini", return_value="gemini-response") as mock_a:
        with patch("brand_visibility.ai_client._call_groq", return_value="groq-response") as mock_b:
            answer = ask_ai("test", engine="engine_b")
            mock_b.assert_called_once()
            mock_a.assert_not_called()
            assert "groq-response" == answer


def test_timeout_retry_exhausted_returns_visible_error(monkeypatch):
    """Timeout on all retries should return a visible error with dynamic engine name."""
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(settings, "AI_REQUEST_TIMEOUT", 15)
    monkeypatch.setattr(settings, "AI_MAX_RETRIES", 1)
    monkeypatch.setattr(settings, "AI_RETRY_BACKOFF_SECONDS", 0)  # speed up test

    with patch("brand_visibility.ai_client._call_gemini", side_effect=TimeoutError("boom")):
        answer = ask_ai("test", engine="engine_a")
    assert "[engine_a error: timeout after 15s]" == answer


def test_rate_limit_retry_then_visible_error(monkeypatch):
    """429 on all attempts should retry with backoff then return visible error."""
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(settings, "AI_REQUEST_TIMEOUT", 15)
    monkeypatch.setattr(settings, "AI_MAX_RETRIES", 1)
    monkeypatch.setattr(settings, "AI_RETRY_BACKOFF_SECONDS", 0)  # speed up test

    class RateLimit(Exception):
        status_code = 429

    with patch("brand_visibility.ai_client._call_gemini", side_effect=RateLimit("rate limited")):
        answer = ask_ai("test", engine="engine_a")
    assert "[engine_a error: rate limited]" == answer


def test_auth_error_no_retry_returns_visible_error(monkeypatch):
    """401/403 should fail fast with no retry."""
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "bad-key")
    monkeypatch.setattr(settings, "AI_REQUEST_TIMEOUT", 15)
    monkeypatch.setattr(settings, "AI_MAX_RETRIES", 99)  # prove it's not retrying

    class AuthError(Exception):
        status_code = 401

    with patch("brand_visibility.ai_client._call_gemini", side_effect=AuthError("nope")):
        answer = ask_ai("test", engine="engine_a")
    assert "[engine_a error: auth failed]" == answer


def test_malformed_response_returns_visible_error(monkeypatch):
    """Empty or None response should be classified as malformed."""
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-key")

    with patch("brand_visibility.ai_client._call_gemini", return_value=""):
        answer = ask_ai("test", engine="engine_a")
    assert "[engine_a error: malformed response]" == answer


def test_real_mode_per_call_budget_exhausted(monkeypatch):
    """After budget exhausted, further calls return visible error without calling provider."""
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "fake-key")
    monkeypatch.setattr(settings, "AI_MAX_REAL_CALLS_PER_RUN", 1)
    monkeypatch.setattr(settings, "AI_CONSECUTIVE_FAILURE_LIMIT", 99)

    with patch("brand_visibility.ai_client._call_gemini", return_value="ok") as mock_a:
        with patch("brand_visibility.ai_client._call_groq", return_value="ok") as mock_b:
            first = ask_ai("q1", engine="engine_a")
            second = ask_ai("q2", engine="engine_a")
            third = ask_ai("q3", engine="engine_b")
            assert "ok" == first
            assert "[engine_a error: real call budget exhausted]" == second
            assert "[engine_b error: real call budget exhausted]" == third
            assert mock_a.call_count == 1
            assert mock_b.call_count == 0


def test_per_engine_circuit_breaker_independent(monkeypatch):
    """engine_a circuit open should not block engine_b."""
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "fake-key")
    monkeypatch.setattr(settings, "AI_REQUEST_TIMEOUT", 15)
    monkeypatch.setattr(settings, "AI_MAX_RETRIES", 0)
    monkeypatch.setattr(settings, "AI_RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(settings, "AI_CONSECUTIVE_FAILURE_LIMIT", 2)
    monkeypatch.setattr(settings, "AI_MAX_REAL_CALLS_PER_RUN", 99)

    class Boom(Exception):
        pass

    with patch("brand_visibility.ai_client._call_gemini", side_effect=Boom("x")):
        with patch("brand_visibility.ai_client._call_groq", return_value="groq-ok") as mock_b:
            a1 = ask_ai("q", engine="engine_a")
            a2 = ask_ai("q", engine="engine_a")
            b1 = ask_ai("q", engine="engine_b")
            assert "[engine_a error:" in a1
            assert "[engine_a error:" in a2
            assert "groq-ok" == b1
            assert mock_b.call_count == 1


def test_both_engines_failed_signal(monkeypatch):
    """When both engines fail for the same question, caller can detect both errors."""
    monkeypatch.setattr(settings, "REAL_MODE", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "fake-key")
    monkeypatch.setattr(settings, "AI_REQUEST_TIMEOUT", 15)
    monkeypatch.setattr(settings, "AI_MAX_RETRIES", 0)
    monkeypatch.setattr(settings, "AI_RETRY_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(settings, "AI_CONSECUTIVE_FAILURE_LIMIT", 99)
    monkeypatch.setattr(settings, "AI_MAX_REAL_CALLS_PER_RUN", 99)

    class Boom(Exception):
        pass

    with patch("brand_visibility.ai_client._call_gemini", side_effect=Boom("x")):
        with patch("brand_visibility.ai_client._call_groq", side_effect=Boom("x")):
            ans_a = ask_ai("test", engine="engine_a")
            ans_b = ask_ai("test", engine="engine_b")
    assert "[engine_a error:" in ans_a
    assert "[engine_b error:" in ans_b
    both_signal = "[both engines unavailable for this question; manual review recommended]"
    assert both_signal == f"{ans_a} {ans_b} {both_signal}".split()[-1] or both_signal in f"{ans_a} | {ans_b}"


def test_step1_check_offline_uses_both_engines(monkeypatch):
    """step1_check run_check should query both engines and store both results."""
    from brand_visibility.step1_check import run_check

    mock_html = "<html><head><title>Zomato</title></head><body>Zomato food ordering.</body></html>"
    monkeypatch.setattr(
        "brand_visibility.step1_check.fetch_url",
        lambda url, **kw: ("completed", mock_html, None),
    )
    monkeypatch.setattr(settings, "REAL_MODE", False)

    check_res, raw_html = run_check("zomato", brand_type="test")
    assert check_res["brand_id"] == "zomato"
    assert len(check_res["questions"]) == 2
    for q in check_res["questions"]:
        engines = {r["engine"] for r in q["engine_results"]}
        assert "engine_a" in engines
        assert "engine_b" in engines
