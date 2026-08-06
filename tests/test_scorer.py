"""
Tests for question generation, topic extraction, noise filtering, and visibility scoring in brand_visibility.scorer.
"""

from brand_visibility.scorer import (
    NOISE_WORDS,
    _extract_page_topics,
    generate_questions,
    score_visibility,
)


def test_extract_page_topics_returns_yake_phrases():
    """Verify YAKE returns plausible topic phrases instead of broken suffix-filtered output."""
    text = "We provide consulting services for small businesses. We also offer transportation and investment planning. Call us for automotive solutions."
    topics = _extract_page_topics(text)
    assert len(topics) >= 1
    joined = " ".join(topics).lower()
    assert "consulting" in joined
    assert any(word in joined for word in ["investment", "transportation", "automotive", "businesses"])


def test_generate_questions_count():
    """Verify that generate_questions respects the requested count parameter."""
    text = "Offering Pizza, Burgers, Tacos, Sushi, Salads, Pasta for food delivery."
    q1 = generate_questions("food delivery", text, count=1)
    q2 = generate_questions("food delivery", text, count=2)
    assert len(q1) == 1
    assert len(q2) == 2


def test_generate_questions_templates_no_topics():
    """Verify template fallback when YAKE returns no page topics."""
    questions = generate_questions("food & restaurant services", text="a an the and or but", count=2)
    assert len(questions) == 2
    assert "What are the top options in food & restaurant services?" in questions[0]
    assert "Which brands lead in food & restaurant services?" in questions[1]


def test_generate_questions_templates_with_topics():
    """Verify template output formatting when high-signal topics are present."""
    text = "Delivering Gourmet Pizza and Artisanal Pasta."
    questions = generate_questions("restaurant services", text, count=2)
    assert len(questions) == 2
    assert any("Pizza" in q or "Gourmet" in q or "Pasta" in q for q in questions)


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


def test_extract_page_topics_filters_web_structural_noise():
    """Verify YAKE extraction filters out pure structural noise phrases like Notice, Cookie, or JavaScript."""
    noisy_text = "Notice: Please enable Javascript and accept Cookie Policy to view this website notice."
    topics = _extract_page_topics(noisy_text)
    # Pure web noise should be filtered out
    for t in topics:
        assert t.lower() not in ("notice", "cookie policy", "javascript enabled", "cookie")


def test_extract_page_topics_handles_unicode_and_html():
    """Verify topic extraction handles raw HTML tags and unicode text cleanly without exceptions."""
    raw_html = "<script>var x=10;</script><p>We specialize in <b>Automotive Logistics</b> and Freight Management.</p>"
    topics = _extract_page_topics(raw_html)
    assert len(topics) >= 1
    joined = " ".join(topics).lower()
    assert "logistics" in joined or "freight" in joined or "automotive" in joined

    unicode_text = "Our café chain offers artisanal coffee in München and Zürich."
    topics_uni = _extract_page_topics(unicode_text)
    assert len(topics_uni) >= 1


def test_generate_questions_handles_large_and_malformed_inputs():
    """Verify generate_questions handles very large text (>100k chars) and None input safely."""
    huge_text = "Sustainable Organic Farming Practices. " * 5000
    questions = generate_questions("agriculture", text=huge_text, count=2)
    assert len(questions) == 2
    assert isinstance(questions[0], str)

    questions_none = generate_questions(None, text=None, count=2)
    assert len(questions_none) == 2
    assert "What are the top options in products and services?" in questions_none[0]


def test_score_visibility_handles_malformed_dicts():
    """Verify score_visibility handles None, empty, or malformed input dicts gracefully."""
    score_none = score_visibility(None)
    assert score_none["overall_score"] == 0
    assert score_none["visibility_grade"] == "Low"

    score_empty = score_visibility({}, diagnosis=None)
    assert score_empty["overall_score"] == 0

    score_malformed = score_visibility({"questions": "invalid_type"}, diagnosis="invalid_type")
    assert score_malformed["overall_score"] == 0

