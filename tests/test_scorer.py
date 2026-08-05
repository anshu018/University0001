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
    assert not any(t.lower() in NOISE_WORDS for t in topics)
    assert any("Pizza" in t or "Burgers" in t for t in topics)


def test_noisy_page_text_filters_out_earn_online_money():
    """Verify that noisy words like 'Earn', 'Online', 'Money', 'Downloading' are filtered out."""
    noisy_text = (
        "Earn money online! Click here to start downloading and earning today. "
        "Get started now with easy online registration."
    )
    topics = _extract_page_topics(noisy_text)
    topic_words = [t.lower() for t in topics]
    for bad in ["earn", "online", "money", "downloading", "earning", "started", "register"]:
        assert bad not in topic_words
        assert not any(bad in t.lower().split() for t in topics)


def test_generate_questions_quality_uber_zomato_noisy_text():
    """Verify that generated questions for noisy text do not contain broken 'best Earn' / 'best Online' phrasing."""
    uber_noisy_text = "Earn money driving. Download app and start earning online. Flexible hours for drivers."
    questions_uber = generate_questions("transport & mobility", uber_noisy_text, count=2)
    for q in questions_uber:
        assert "best Earn" not in q
        assert "best Online" not in q
        assert "best Money" not in q
        assert "top" in q.lower() or "which" in q.lower() or "best" in q.lower()

    zomato_noisy_text = "Order food online. Easy checkout and online payment for restaurant delivery."
    questions_zomato = generate_questions("food & restaurant services", zomato_noisy_text, count=2)
    for q in questions_zomato:
        assert "best Online" not in q
        assert "best Order" not in q
        assert "top" in q.lower() or "which" in q.lower() or "best" in q.lower()


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
