"""
Tests for category detection and fallback logic in brand_visibility.llm.
"""

from brand_visibility.llm import analyze_persona


def test_analyze_persona_domain_signals():
    """Verify category detection using domain/URL signals."""
    assert analyze_persona(website_url="https://paytm.com/") == "financial services & payments"
    assert analyze_persona(website_url="https://github.com/") == "software & technology solutions"
    assert analyze_persona(website_url="https://food-delivery.com/") == "food & restaurant services"
    assert analyze_persona(website_url="https://trail-running.com/") == "athletic footwear & apparel"


def test_analyze_persona_head_signals():
    """Verify category detection from HTML title and meta description tags."""
    html_tech = "<html><head><title>Developer Portal & API Cloud Platform</title></head><body></body></html>"
    assert analyze_persona(raw_html=html_tech) == "software & technology solutions"

    html_food = '<html><head><meta name="description" content="Order food delivery from top restaurants"></head><body></body></html>'
    assert analyze_persona(raw_html=html_food) == "food & restaurant services"


def test_analyze_persona_body_signals():
    """Verify category detection from extracted body text sample."""
    text_health = "Welcome to our clinic offering health & wellness, hospital services, and ayurveda treatments."
    assert analyze_persona(extracted_text=text_health) == "health & wellness"

    text_travel = "Book flight tickets, resort stay, and travel holiday packages easily."
    assert analyze_persona(extracted_text=text_travel) == "travel & hospitality"


def test_analyze_persona_fallback():
    """Verify generic fallback category when no domain, head, or body keywords match."""
    assert analyze_persona(extracted_text="xqzqw123 random text without domain or head signals") == "products and services provider"
    assert analyze_persona(website_url="", extracted_text="", raw_html="") == "products and services provider"
