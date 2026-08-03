"""
Tests for diagnosis reason codes and step2_diagnose logic in brand_visibility.
"""

from brand_visibility.llm import get_diagnosis
from brand_visibility.step2_diagnose import run_diagnose


def test_get_diagnosis_site_unreachable():
    """Verify site_unreachable reason_code when check result status is error."""
    check_error = {
        "check_id": "chk-123",
        "brand_id": "zomato",
        "status": "error",
        "error_detail": "site_unreachable",
        "questions": [],
    }
    diag = get_diagnosis(check_error, raw_text="")
    assert len(diag["reasons"]) == 1
    assert diag["reasons"][0]["reason_code"] == "site_unreachable"
    assert "unreachable" in diag["plain_summary"].lower()


def test_get_diagnosis_thin_content():
    """Verify thin_content reason_code when raw_text contains less than 100 words."""
    check_ok = {
        "check_id": "chk-123",
        "brand_id": "zomato",
        "status": "completed",
        "questions": [],
    }
    thin_text = "Short page with only ten words here."
    diag = get_diagnosis(check_ok, raw_text=thin_text)
    assert len(diag["reasons"]) == 1
    assert diag["reasons"][0]["reason_code"] == "thin_content"
    assert "little indexable text" in diag["plain_summary"].lower()


def test_get_diagnosis_low_visibility():
    """Verify low_visibility reason_code when site has content but brand is not mentioned."""
    check_not_mentioned = {
        "check_id": "chk-123",
        "brand_id": "zomato",
        "status": "completed",
        "questions": [
            {
                "question_id": "q1",
                "engine_results": [
                    {"engine": "engine_a", "mention_status": "not_mentioned"},
                    {"engine": "engine_b", "mention_status": "not_mentioned"},
                ],
            }
        ],
    }
    rich_text = "Word " * 150  # 150 words
    diag = get_diagnosis(check_not_mentioned, raw_text=rich_text)
    assert any(r["reason_code"] == "low_visibility" for r in diag["reasons"])


def test_get_diagnosis_no_structured_data():
    """Verify no_structured_data reason_code when not mentioned and no raw text provided."""
    check_not_mentioned = {
        "check_id": "chk-123",
        "brand_id": "zomato",
        "status": "completed",
        "questions": [
            {
                "question_id": "q1",
                "engine_results": [
                    {"engine": "engine_a", "mention_status": "not_mentioned"},
                ],
            }
        ],
    }
    diag = get_diagnosis(check_not_mentioned, raw_text="")
    assert any(r["reason_code"] == "no_structured_data" for r in diag["reasons"])


def test_get_diagnosis_outdated_or_incorrect():
    """Verify outdated_or_incorrect_info reason_code when mention status is mentioned_inaccurate."""
    check_inaccurate = {
        "check_id": "chk-123",
        "brand_id": "zomato",
        "status": "completed",
        "questions": [
            {
                "question_id": "q1",
                "engine_results": [
                    {"engine": "engine_a", "mention_status": "mentioned_inaccurate"},
                ],
            }
        ],
    }
    diag = get_diagnosis(check_inaccurate, raw_text="Word " * 150)
    assert any(r["reason_code"] == "outdated_or_incorrect_info" for r in diag["reasons"])


def test_run_diagnose_integration():
    """Verify run_diagnose executes end-to-end with in-memory check_result and html for brand 'zomato'."""
    sample_check = {
        "check_id": "test-chk-001",
        "brand_id": "zomato",
        "status": "completed",
        "business_type_detected": "food & restaurant services",
        "questions": [],
    }
    sample_html = "<html><body>" + "Zomato food delivery restaurant services. " * 30 + "</body></html>"
    result = run_diagnose("zomato", check_result=sample_check, raw_html=sample_html, brand_type="test")
    assert result["brand_id"] == "zomato"
    assert result["check_id"] == "test-chk-001"
    assert "plain_summary" in result
    assert "reasons" in result
