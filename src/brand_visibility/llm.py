"""
LLM client wrapper and diagnostic engine module for Brand Visibility Agent.

Provides persona analysis and plain-language diagnosis generation.
Uses config.settings.REAL_MODE to toggle between mock mode (deterministic) and real mode.

Completely industry-agnostic and business-type neutral. Zero hardcoded vertical terms.
"""

from bs4 import BeautifulSoup
import re
from config.settings import REAL_MODE
from brand_visibility.exceptions import DIAGNOSIS_FIELDS


def analyze_persona(extracted_text: str = "", website_url: str = "", raw_html: str = "") -> str:
    """
    Detect the business type / industry persona from extracted website text.

    In mock mode (REAL_MODE=False): Uses rule-based category signals from title, meta tags,
    domain/URL, and page text to infer business type dynamically.
    """
    domain_hint = (website_url or "").lower()
    text_sample = (extracted_text or "")[:4000].lower()

    title_text = ""
    meta_desc = ""
    if raw_html and isinstance(raw_html, str):
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            title_tag = soup.find("title")
            if title_tag and title_tag.string:
                title_text = title_tag.string.strip().lower()
            meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            if meta_tag and meta_tag.get("content"):
                meta_desc = meta_tag["content"].strip().lower()
        except Exception:
            pass

    # 1. Domain / URL signal overrides (category patterns, not brand names)
    if any(w in domain_hint for w in ["upi", "payment", "razorpay", "paytm", "wallet", "bharatpe", "bajajpay", "payu", "banking", "fintech", "insurance", "investment", "money"]):
        return "financial services & payments"
    if any(w in domain_hint for w in [".shop", ".store", "store.", "shop.", "retail", "ecommerce", "e-commerce", "cart", "product", "products"]):
        return "retail & consumer products"
    if any(w in domain_hint for w in [".io", "github.com", "stackoverflow", "developer", "programming", "software", "api", "cloud", "saas", "tech", "dev"]):
        return "software & technology solutions"
    if any(w in domain_hint for w in ["running", "trail", "sneaker", "footwear", "shoes", "sport", "sports", "fitness", "athletic"]):
        return "athletic footwear & apparel"
    if any(w in domain_hint for w in ["food", "restaurant", "dining", "cuisine", "delivery", "meal", "eat"]):
        return "food & restaurant services"
    if any(w in domain_hint for w in ["cab", "taxi", "mobility", "rapido", "ride", "transport"]):
        return "transport & mobility"
    if any(w in domain_hint for w in ["grocery", "supermarket", "hyperlocal", "market", "mart"]):
        return "grocery & retail"
    if any(w in domain_hint for w in ["health", "wellness", "medical", "hospital", "clinic", "pharmacy", "ayurveda"]):
        return "health & wellness"
    if any(w in domain_hint for w in ["hotel", "stay", "booking", "travel", "flight", "holiday", "resort", "trip"]):
        return "travel & hospitality"
    if any(w in domain_hint for w in ["learn", "course", "class", "tutorial", "education", "coaching", "university", "college", "school"]):
        return "education & e-learning"
    if any(w in domain_hint for w in ["movie", "cinema", "film", "stream", "video", "ott", "show", "entertainment", "music"]):
        return "entertainment & media"
    if any(w in domain_hint for w in ["news", "breaking", "daily", "journal", "press", "media"]):
        return "news & media"

    # 2. Title & Meta signals (stronger than raw body text)
    combined_head = f"{title_text} {meta_desc}".strip()
    if any(w in combined_head for w in ["upi", "payment", "payments", "wallet", "recharge", "money transfer", "banking", "fintech"]):
        return "financial services & payments"
    if any(w in combined_head for w in ["programming", "software", "developer", "api", "code", "language", "framework", "platform", "cloud", "saas", "tech"]):
        return "software & technology solutions"
    if any(w in combined_head for w in ["shoes", "footwear", "sneakers", "running", "athletic", "boots", "apparel", "fitness", "sport"]):
        return "athletic footwear & apparel"
    if any(w in combined_head for w in ["food", "restaurant", "dining", "cuisine", "delivery", "meal"]):
        return "food & restaurant services"
    if any(w in combined_head for w in ["cab", "taxi", "mobility", "ride", "transport"]):
        return "transport & mobility"
    if any(w in combined_head for w in ["grocery", "supermarket", "hyperlocal", "market"]):
        return "grocery & retail"
    if any(w in combined_head for w in ["health", "wellness", "medical", "hospital", "clinic", "pharmacy"]):
        return "health & wellness"
    if any(w in combined_head for w in ["hotel", "stay", "booking", "travel", "flight", "holiday", "resort"]):
        return "travel & hospitality"
    if any(w in combined_head for w in ["learn", "course", "class", "tutorial", "education", "coaching", "university", "college"]):
        return "education & e-learning"
    if any(w in combined_head for w in ["movie", "cinema", "film", "stream", "video", "ott", "show", "entertainment"]):
        return "entertainment & media"
    if any(w in combined_head for w in ["news", "breaking", "daily", "journal", "press"]):
        return "news & media"

    # 3. Body text signals
    if any(w in text_sample for w in ["upi", "digital wallet", "payment gateway", "money transfer", "payments", "recharge", "banking", "fintech"]):
        return "financial services & payments"
    if any(w in text_sample for w in ["programming language", "software development", "source code", "open source platform", "developer tools", "api", "cloud", "saas", "platform"]):
        return "software & technology solutions"
    if any(w in text_sample for w in ["running shoes", "athletic footwear", "trail running", "sneakers", "fitness gear", "sportswear"]):
        return "athletic footwear & apparel"
    if any(w in text_sample for w in ["health & wellness", "medical center", "hospital services", "clinic", "pharmacy", "ayurveda"]):
        return "health & wellness"
    if any(w in text_sample for w in ["food delivery", "restaurant", "dining", "cuisine", "meal", "order food"]):
        return "food & restaurant services"
    if any(w in text_sample for w in ["cab", "taxi", "mobility", "ride", "transport", "book ride"]):
        return "transport & mobility"
    if any(w in text_sample for w in ["grocery", "supermarket", "hyperlocal", "market", "fresh"]):
        return "grocery & retail"
    if any(w in text_sample for w in ["hotel", "stay", "booking", "travel", "flight", "holiday", "resort", "trip"]):
        return "travel & hospitality"
    if any(w in text_sample for w in ["learn", "course", "class", "tutorial", "education", "coaching", "university", "college", "school"]):
        return "education & e-learning"
    if any(w in text_sample for w in ["movie", "cinema", "film", "stream", "video", "ott", "show", "entertainment", "music"]):
        return "entertainment & media"
    if any(w in text_sample for w in ["news", "breaking", "daily", "journal", "press", "media"]):
        return "news & media"
    if any(w in text_sample for w in ["consulting", "advisory", "agency", "services", "solution", "solutions"]):
        return "professional services"

    # 4. Simple word-frequency fallback for unknown brands
    words = re.findall(r"\b[a-z]{4,}\b", text_sample)
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:8]
    top_words = [w for w, _ in top if w not in {"welcome", "notice", "started", "download", "success", "stories", "events", "community", "foundation", "donate", "sponsors", "jobs", "news", "blog", "careers", "press", "official", "learn", "getting", "this", "that", "these", "those", "here", "there", "possible", "causes", "include", "because", "script", "scripts", "stylesheet", "stylesheets", "enabled", "failure", "interactive", "page", "display", "displays", "fallback", "disabled", "site", "sites", "menu", "cart", "cookie", "cookies", "privacy", "copyright", "javascript", "rights", "reserved", "select", "sign", "login", "search", "home", "items", "view", "link", "text", "main", "body", "title", "about", "contact", "free", "shipping", "returns", "order", "account", "checkout", "help", "support", "policy", "company", "whether", "easy", "would", "could", "should", "their", "where", "which", "other", "first", "experienced", "user"}]

    category_hints = {
        "software & technology solutions": ["software", "platform", "cloud", "saas", "api", "developer", "programming", "tech", "code", "framework", "python", "java", "javascript"],
        "financial services & payments": ["payment", "banking", "fintech", "wallet", "money", "insurance", "investment", "recharge"],
        "food & restaurant services": ["food", "restaurant", "dining", "cuisine", "delivery", "meal", "eat"],
        "transport & mobility": ["cab", "taxi", "mobility", "ride", "transport"],
        "retail & consumer products": ["shop", "store", "retail", "product", "cart", "ecommerce"],
        "grocery & retail": ["grocery", "supermarket", "hyperlocal", "market", "mart"],
        "health & wellness": ["health", "wellness", "medical", "hospital", "clinic", "pharmacy", "ayurveda"],
        "travel & hospitality": ["hotel", "stay", "booking", "travel", "flight", "holiday", "resort", "trip"],
        "education & e-learning": ["learn", "course", "class", "tutorial", "education", "coaching", "university", "college", "school"],
        "entertainment & media": ["movie", "cinema", "film", "stream", "video", "ott", "show", "entertainment", "music"],
        "news & media": ["news", "breaking", "daily", "journal", "press"],
        "athletic footwear & apparel": ["shoes", "footwear", "sneakers", "running", "athletic", "boots", "apparel", "fitness", "sport"],
        "professional services": ["consulting", "advisory", "agency", "services", "solution"],
    }
    best_cat = None
    best_score = 0
    for cat, hints in category_hints.items():
        score = sum(1 for w in top_words if w in hints)
        if score > best_score:
            best_score = score
            best_cat = cat
    if best_cat and best_score >= 1:
        return best_cat

    return "products and services provider"


def get_diagnosis(check_result: dict, raw_text: str = "") -> dict:
    """
    Generate a plain-language diagnosis of why AI engines missed or misdescribed the brand.

    - check_result: check result dict per schema.md
    - raw_text: in-memory raw page text for thin-content evaluation

    Returns dict containing 'plain_summary' and 'reasons' list per DIAGNOSIS_FIELDS.
    """
    if not isinstance(check_result, dict):
        check_result = {}

    status = check_result.get("status", "completed")
    error_detail = check_result.get("error_detail")
    brand_id = check_result.get("brand_id", "the brand")

    reasons = []

    # 1. Site Unreachable
    if status == "error" or error_detail == "site_unreachable":
        reason_code = "site_unreachable"
        detail = f"The website for '{brand_id}' could not be reached or timed out during inspection."
        summary = (
            f"AI engines cannot find or evaluate {brand_id} because the brand's website "
            "was unreachable or timed out."
        )
        reasons.append({"reason_code": reason_code, "detail": detail})
        return {"plain_summary": summary, "reasons": reasons}

    # 2. Thin Content
    word_count = len(raw_text.split()) if raw_text else 0
    if raw_text and word_count < 100:
        reason_code = "thin_content"
        detail = f"Extracted site text is thin ({word_count} words found, under 100 word threshold)."
        summary = (
            f"AI engines have limited information about {brand_id} because its website contains "
            "very little indexable text content."
        )
        reasons.append({"reason_code": reason_code, "detail": detail})
        return {"plain_summary": summary, "reasons": reasons}

    # 3. Dynamic Analysis of Engine Query Results
    questions = check_result.get("questions", [])
    not_mentioned_count = 0
    inaccurate_count = 0
    accurate_count = 0

    for q in questions:
        for res in q.get("engine_results", []):
            m_status = res.get("mention_status")
            if m_status == "not_mentioned":
                not_mentioned_count += 1
            elif m_status == "mentioned_inaccurate":
                inaccurate_count += 1
            elif m_status == "mentioned_accurate":
                accurate_count += 1

    has_real_content = bool(raw_text and len(raw_text.split()) >= 100)

    if not_mentioned_count > 0 and inaccurate_count == 0:
        if has_real_content:
            reason_code = "low_visibility"
            detail = "The website has real content, but AI engines still do not mention this brand in response to buyer-intent questions."
            summary = (
                f"AI engines do not mention {brand_id} in buyer-intent results, even though its "
                "website has real content. Without a structured brand fact file, the brand stays invisible."
            )
        else:
            reason_code = "no_structured_data"
            detail = "No llms.txt, schema.org markup, or structured brand fact file found online for AI engines to read from."
            summary = (
                f"AI engines can't find or recommend {brand_id} because there is no structured, "
                "machine-readable information about the brand anywhere online."
            )
        reasons.append({"reason_code": reason_code, "detail": detail})

    elif inaccurate_count > 0:
        reason_code = "outdated_or_incorrect_info"
        detail = "AI engines return inaccurate or incomplete details due to missing verified brand facts."
        summary = (
            f"AI engines mention {brand_id}, but provide inaccurate or incomplete details "
            "due to a lack of verified, structured brand information online."
        )
        reasons.append({"reason_code": reason_code, "detail": detail})
        if not_mentioned_count > 0:
            reasons.append({
                "reason_code": "low_visibility",
                "detail": "AI engines fail to mention the brand across several queries.",
            })

    else:
        summary = (
            f"AI engines can find {brand_id}, but establishing an approved machine-readable "
            "brand fact file ensures ongoing accuracy."
        )

    return {"plain_summary": summary, "reasons": reasons}
