"""
Tests for question generation, topic extraction, noise filtering, and visibility scoring in brand_visibility.scorer.
"""

from brand_visibility.scorer import (
    NOISE_WORDS,
    _extract_page_topics,
    generate_questions,
    score_visibility,
)


def test_extract_page_topics_noise_filtering():
    """Verify that noise words like 'welcome', 'login', 'copyright' are excluded from topics."""
    text = "Welcome to our page. Login to access menu and cart. Copyright 2026. Delivering Pizza and Burgers."
    topics = _extract_page_topics(text)
    # 'Welcome', 'Login', 'menu', 'cart', 'Copyright' should all be filtered out as noise words
    assert not any(t.lower() in NOISE_WORDS for t in topics)
    assert "Pizza" in topics or "Burgers" in topics or "Delivering" in topics


def test_generate_questions_count():
    """Verify that generate_questions respects the requested count parameter."""
    text = "Offering Pizza, Burgers, Tacos, Sushi, Salads, Pasta for food delivery."
    q1 = generate_questions("food delivery", text, count=1)
    q2 = generate_questions("food delivery", text, count=2)
    assert len(q1) == 1
    assert len(q2) == 2


def test_generate_questions_templates_no_topics():
    """Verify template fallback when no page topics are extracted."""
    text = "Welcome login copyright menu cart"  # All noise words
    questions = generate_questions("food & restaurant services", text, count=2)
    assert len(questions) == 2
    assert "What are the top options in food & restaurant services?" in questions[0]
    assert "Which brands lead in food & restaurant services?" in questions[1]


def test_generate_questions_templates_with_topics():
    """Verify template output formatting when high-signal topics are present."""
    text = "Delivering Gourmet Pizza and Artisanal Pasta."
    questions = generate_questions("restaurant services", text, count=2)
    assert len(questions) == 2
    assert any("Pizza" in q or "Gourmet" in q for q in questions)


def test_score_visibility_calculation():
    """Verify calculation of overall_score, mention_rate, accuracy_rate, and grade."""
    check_result_high = {
        "questions": [
            {
                "engine_results": [
                    {"mention_status": "mentioned_accurate"},
                    {"mention_status": "mentioned_accurate"},
                ]
            }
        ]
    }
    score_high = score_visibility(check_result_high)
    assert score_high["overall_score"] == 100
    assert score_high["visibility_grade"] == "High"
    assert score_high["mention_rate"] == 1.0
    assert score_high["accuracy_rate"] == 1.0

    check_result_low = {
        "questions": [
            {
                "engine_results": [
                    {"mention_status": "not_mentioned"},
                    {"mention_status": "not_mentioned"},
                ]
            }
        ]
    }
    score_low = score_visibility(check_result_low)
    assert score_low["overall_score"] == 0
    assert score_low["visibility_grade"] == "Low"
    assert score_low["mention_rate"] == 0.0


def test_score_visibility_thin_content_penalty():
    """Verify that thin_content or site_unreachable diagnosis reasons cap the score at 15."""
    check_result = {
        "questions": [
            {
                "engine_results": [
                    {"mention_status": "mentioned_accurate"},
                ]
            }
        ]
    }
    diagnosis_thin = {
        "reasons": [{"reason_code": "thin_content", "detail": "Less than 100 words"}]
    }
    score = score_visibility(check_result, diagnosis=diagnosis_thin)
    assert score["overall_score"] <= 15
    assert score["visibility_grade"] == "Low"
