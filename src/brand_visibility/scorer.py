"""
Visibility scoring and question generation module for Brand Visibility Agent.

Calculates structured AI engine visibility metrics (0-100 score, mention rate, accuracy rate)
and generates dynamic buyer intent questions parameterized by business type and extracted text.

Completely industry-agnostic and business-type neutral. Zero vertical-specific assumptions.
"""

import re

NOISE_WORDS = {
    "welcome", "notice", "started", "download", "downloads", "success", "stories",
    "events", "community", "foundation", "donate", "sponsors", "jobs", "news", "blog",
    "careers", "press", "official", "learn", "getting", "this", "that", "these", "those",
    "here", "there", "possible", "causes", "include", "because", "script", "scripts",
    "stylesheet", "stylesheets", "enabled", "failure", "interactive", "page", "display",
    "displays", "fallback", "disabled", "site", "sites", "menu", "cart", "cookie",
    "cookies", "privacy", "copyright", "javascript", "rights", "reserved", "select", "sign",
    "login", "search", "home", "items", "view", "link", "text", "main", "body", "title",
    "about", "contact", "free", "shipping", "returns", "order", "account", "checkout",
    "help", "support", "policy", "company", "whether", "easy", "would", "could", "should",
    "their", "where", "which", "other", "first", "experienced", "user",
}


def _extract_page_topics(text: str) -> list[str]:
    """Extract high-signal topic phrases from text while aggressively filtering noise words."""
    if not text or not isinstance(text, str):
        return []

    words = re.findall(r"\b[A-Za-z]{4,}\b", text)
    topics = []
    for w in words:
        wl = w.lower()
        if wl not in NOISE_WORDS and len(wl) > 3 and not wl.isdigit():
            if wl not in [t.lower() for t in topics]:
                topics.append(w)
                if len(topics) >= 5:
                    break

    return topics


def generate_questions(business_type: str, text: str = "", count: int = 2) -> list[str]:
    """
    Generate realistic buyer intent questions parameterized by detected business_type
    and dynamic context words extracted from the website text.

    Natural phrase formatting without artificial slot fillers or web layout noise.
    """
    biz = (business_type or "products and services").strip()
    topics = _extract_page_topics(text)

    questions = []
    if len(topics) >= 2:
        t1, t2 = topics[0], topics[1]
        q1 = f"What is the best {t1} in {biz}?" if t1[0].isupper() else f"What are the best {t1} in {biz}?"
        q2 = f"What is the best {t2} in {biz}?" if t2[0].isupper() or not t2.endswith("s") else f"Which {t2} are most recommended for {biz}?"
        questions.append(q1)
        questions.append(q2)
    elif len(topics) == 1:
        t1 = topics[0]
        q = f"What is the best {t1} in {biz}?" if t1[0].isupper() else f"What are the best {t1} options for {biz}?"
        questions.append(q)
        questions.append(f"Which providers are most trusted in {biz}?")
    else:
        questions.append(f"What are the top options in {biz}?")
        questions.append(f"Which brands lead in {biz}?")

    return questions[:count]


def score_visibility(check_result: dict, diagnosis: dict = None, persona: dict = None) -> dict:
    """
    Compute a structured visibility score metrics record from Stage 1 check artifacts.
    """
    if not isinstance(check_result, dict):
        check_result = {}

    questions = check_result.get("questions", [])
    total_evaluations = 0
    mentions_count = 0
    accurate_count = 0

    for q in questions:
        for res in q.get("engine_results", []):
            total_evaluations += 1
            status = res.get("mention_status")
            if status == "mentioned_accurate":
                mentions_count += 1
                accurate_count += 1
            elif status == "mentioned_inaccurate":
                mentions_count += 1

    if total_evaluations > 0:
        mention_rate = round(mentions_count / total_evaluations, 2)
        accuracy_rate = round(accurate_count / max(1, mentions_count), 2)
    else:
        mention_rate = 0.0
        accuracy_rate = 0.0

    raw_score = (mention_rate * 60.0) + (accuracy_rate * 40.0)

    if diagnosis and isinstance(diagnosis, dict):
        reasons = [r.get("reason_code") for r in diagnosis.get("reasons", []) if isinstance(r, dict)]
        if "site_unreachable" in reasons or "thin_content" in reasons:
            raw_score = min(raw_score, 15.0)

    overall_score = int(round(raw_score))

    if overall_score >= 70:
        grade = "High"
        summary_text = "The brand has strong, accurate visibility across evaluated AI engines."
    elif overall_score >= 35:
        grade = "Medium"
        summary_text = "The brand is partially visible to AI engines, but lacks consistent accurate brand facts."
    else:
        grade = "Low"
        summary_text = "The brand is largely invisible or misrepresented across AI search engines."

    return {
        "overall_score": overall_score,
        "visibility_grade": grade,
        "mention_rate": mention_rate,
        "accuracy_rate": accuracy_rate,
        "total_queries_evaluated": total_evaluations,
        "summary": summary_text,
    }
