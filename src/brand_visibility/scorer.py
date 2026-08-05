"""
Visibility scoring and question generation module for Brand Visibility Agent.

Calculates structured AI engine visibility metrics (0-100 score, mention rate, accuracy rate)
and generates dynamic buyer intent questions parameterized by business type and extracted text.

Completely industry-agnostic and business-type neutral. Zero vertical-specific assumptions.
"""

import re
from collections import Counter

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
    # Additional noise words (verbs, adverbs, web controls, promotional action words)
    "earn", "online", "click", "make", "find", "show", "give", "take", "need", "want",
    "more", "less", "just", "very", "also", "with", "from", "into", "onto", "your", "our",
    "my", "us", "we", "you", "they", "them", "signup", "register", "join", "money",
    "apply", "drive", "ride", "deliver", "downloading", "starting", "earning", "ordering",
    "food", "restaurant", "delivery", "services", "solutions", "options", "platforms",
    "products", "providers", "brands", "software", "technology", "business", "company",
}

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "at", "to", "for", "with",
    "by", "about", "against", "between", "into", "through", "during", "before", "after",
    "above", "below", "up", "down", "out", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will",
    "just", "don", "should", "now",
}


def _is_valid_word(word: str) -> bool:
    wl = word.lower()
    if len(wl) < 4 or len(wl) > 40:
        return False
    if wl in NOISE_WORDS or wl in STOP_WORDS:
        return False
    if wl.isdigit():
        return False
    if wl.endswith("ly") and len(wl) > 5:
        return False
    return True


def _extract_page_topics(text: str) -> list[str]:
    """Extract high-signal topic phrases from text using n-grams and frequency ranking."""
    if not text or not isinstance(text, str):
        return []

    clean_text = re.sub(r"[^\w\s]", " ", text)
    words = clean_text.split()

    candidates = []

    # 1. Bigrams (2 consecutive valid words or proper title phrases)
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        if _is_valid_word(w1) and _is_valid_word(w2):
            phrase = f"{w1} {w2}".title()
            candidates.append(phrase)

    # 2. Capitalized / Title Case Phrases in raw text (e.g. "Gourmet Pizza", "Ride Sharing")
    raw_phrases = re.findall(r"\b[A-Z][a-z]{3,}(?:\s+[A-Z][a-z]{3,}){1,2}\b", text)
    for phrase in raw_phrases:
        parts = phrase.split()
        if all(_is_valid_word(p) for p in parts):
            candidates.append(phrase.title())

    # 3. High-signal Single Nouns (valid words)
    for w in words:
        if _is_valid_word(w):
            candidates.append(w.capitalize())

    if not candidates:
        return []

    counts = Counter(candidates)
    most_common = counts.most_common()

    topics = []
    seen_lower = set()
    for phrase, count in most_common:
        pl = phrase.lower()
        if pl not in seen_lower:
            parts = pl.split()
            if not any(p in NOISE_WORDS for p in parts):
                seen_lower.add(pl)
                topics.append(phrase)
                if len(topics) >= 3:
                    break

    return topics


def generate_questions(business_type: str, text: str = "", count: int = 2) -> list[str]:
    """
    Generate realistic buyer intent questions parameterized by detected business_type
    and dynamic context words extracted from the website text.

    Three-tier fallback:
    a. Strong topics from page extraction
    b. Business-type intent questions when page topics are minimal
    c. Fully generic fallback questions
    """
    biz = (business_type or "products and services").strip()
    topics = _extract_page_topics(text)

    questions = []

    # Tier A: Strong topics extracted from page
    if len(topics) >= 2:
        t1, t2 = topics[0], topics[1]
        questions.append(f"What are the top {t1} options in {biz}?")
        questions.append(f"Which {t2} solutions are most recommended in {biz}?")
    elif len(topics) == 1:
        t1 = topics[0]
        questions.append(f"What are the top {t1} options in {biz}?")
        questions.append(f"Which providers lead in {biz}?")
    else:
        # Tier B / C: Generic on-topic fallback when page topics are weak/absent
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
