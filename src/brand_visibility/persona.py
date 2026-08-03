"""
Audience analysis and persona profiling module for Brand Visibility Agent.

Infers audience segments, structures buyer personas, and calculates persona fit scores.

Completely industry-agnostic and business-type neutral. Zero vertical-specific assumptions.
"""

from brand_visibility.llm import analyze_persona as _llm_analyze_persona


def detect_business_type(raw_text: str, website_url: str = "") -> str:
    """Detect business type category string (business-agnostic wrapper)."""
    return _llm_analyze_persona(raw_text, website_url=website_url)


def analyze_audience(raw_text: str, questions: list = None) -> dict:
    """
    Infer likely target audience segments from website text and buyer questions.

    - raw_text: extracted text from the brand website
    - questions: list of buyer intent questions (strings or dicts)

    Returns dict containing primary_segment, secondary_segment, and intent_signals.
    """
    text_lower = (raw_text or "").lower()
    intent_signals = []

    # Extract intent signals from questions if provided
    if questions:
        for q in questions:
            q_text = q.get("question_text", q) if isinstance(q, dict) else str(q)
            if q_text:
                intent_signals.append(q_text.strip())

    # Industry-neutral segment inference heuristics
    if "enterprise" in text_lower or "b2b" in text_lower or "organization" in text_lower:
        primary = "Enterprise & Business Organizations"
        secondary = "Professional Teams & Decision Makers"
    elif "pro" in text_lower or "professional" in text_lower or "expert" in text_lower:
        primary = "Professional & Specialist Users"
        secondary = "Performance Seekers"
    else:
        primary = "General Consumer & End Users"
        secondary = "Value & Quality Seekers"

    return {
        "primary_segment": primary,
        "secondary_segment": secondary,
        "intent_signals": intent_signals[:5],
    }


def audience_to_persona(audience: dict) -> dict:
    """
    Convert inferred audience analysis dict into a structured buyer persona record.

    Returns dict with persona_type, target_segment, key_needs, and buyer_intent_level.
    """
    if not isinstance(audience, dict):
        audience = {}

    primary = audience.get("primary_segment", "General Target Audience")

    # Generic needs mapping based on segment
    if "Enterprise" in primary:
        needs = ["Reliability & Scalability", "Verified Credentials", "Support & Governance"]
        intent_level = "High Intent (Evaluation / Decision)"
    elif "Professional" in primary:
        needs = ["High Quality & Performance", "Technical Accuracy", "Efficiency"]
        intent_level = "High Intent (Research / Selection)"
    else:
        needs = ["Clear Information", "Authenticity & Trust", "Ease of Purchase/Use"]
        intent_level = "Medium Intent (Discovery / Comparison)"

    return {
        "persona_type": f"Primary Buyer: {primary}",
        "target_segment": primary,
        "key_needs": needs,
        "buyer_intent_level": intent_level,
    }


def score_persona_fit(persona: dict, brand_text: str) -> float:
    """
    Calculate a persona fit score between 0.0 and 1.0 based on keyword overlap
    between persona needs/target segment and brand text.
    """
    if not brand_text or not isinstance(brand_text, str):
        return 0.0

    if not isinstance(persona, dict):
        return 0.5

    text_lower = brand_text.lower()
    needs = persona.get("key_needs", [])
    target = persona.get("target_segment", "").lower()

    if not needs and not target:
        return 0.5

    matches = 0
    total_checks = len(needs) + (1 if target else 0)

    if target and any(term in text_lower for term in target.split()):
        matches += 1

    for need in needs:
        # Check if individual words of need appear in brand_text
        need_words = [w.lower() for w in need.split() if len(w) > 3]
        if any(w in text_lower for w in need_words):
            matches += 1

    score = matches / max(1, total_checks)
    # Normalize score strictly between 0.0 and 1.0
    return round(min(1.0, max(0.0, score)), 2)
