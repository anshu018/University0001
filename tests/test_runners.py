"""
Tests for direct runner scripts and BRAND_AUTO_APPROVE=1 non-interactive publishing.
Uses 'zomato' test brand and mocked network I/O for 100% offline execution.
"""

import os
import sys
from unittest.mock import patch
from brand_visibility.step1_check import run_check
from brand_visibility.step2_diagnose import run_diagnose
from brand_visibility.step3_fix import approval_gate, generate_brand_files
from brand_visibility.step4_prove import run_prove
import run_demo


def test_step1_check_runner_offline(monkeypatch):
    """Verify step1_check run_check completes offline when website fetch is mocked."""
    mock_html = "<html><head><title>Zomato Food Delivery</title></head><body>Zomato restaurant food ordering.</body></html>"
    monkeypatch.setattr("brand_visibility.step1_check.fetch_url", lambda url, **kw: ("completed", mock_html, None))

    check_res, raw_html = run_check("zomato", brand_type="test")
    assert check_res["brand_id"] == "zomato"
    assert check_res["status"] == "completed"
    assert len(raw_html) > 0


def test_step2_diagnose_runner():
    """Verify step2_diagnose run_diagnose completes successfully for zomato."""
    sample_check = {
        "check_id": "chk-zomato-001",
        "brand_id": "zomato",
        "status": "completed",
        "questions": [],
    }
    sample_html = "<html><body>Zomato online food ordering and restaurant delivery services.</body></html>"
    diag = run_diagnose("zomato", check_result=sample_check, raw_html=sample_html, brand_type="test")
    assert diag["brand_id"] == "zomato"
    assert "plain_summary" in diag


def test_step3_fix_brand_auto_approve(monkeypatch):
    """Verify BRAND_AUTO_APPROVE=1 enables non-interactive publishing without waiting for stdin."""
    monkeypatch.setenv("BRAND_AUTO_APPROVE", "1")
    res = approval_gate("zomato", brand_type="test")
    assert res["approved"] is True
    assert res["approved_by"] is not None
    assert res["approved_at"] is not None


def test_step4_prove_runner():
    """Verify step4_prove run_prove executes without network calls."""
    proof = run_prove("zomato", brand_type="test")
    assert proof["brand_id"] == "zomato"
    assert "before" in proof
    assert "after" in proof


def test_run_demo_replay_runner():
    """Verify run_demo orchestrator --replay mode loads cached run from disk cleanly."""
    result = run_demo.run_pipeline("zomato", brand_type="test", replay=True)
    assert result["brand_id"] == "zomato"
    assert "step1" in result
    assert "step2" in result
