"""
Content probe and engine query simulation module for Brand Visibility Agent.

Extracts page text, counts words, detects thin content, builds buyer intent queries,
and simulates probe result evaluation in mock mode.

Completely industry-agnostic and business-type neutral. Zero hardcoded vertical terms.
"""

import re
from bs4 import BeautifulSoup


def extract_text(html: str) -> str:
    """Extract clean text content from raw HTML, stripping non-content DOM elements."""
    if not html or not isinstance(html, str):
        return ""

    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        element.decompose()

    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_words(text: str) -> int:
    """Return total word count for a given text string."""
    if not text or not isinstance(text, str):
        return 0
    return len(text.split())


def detect_thin_content(text: str, threshold: int = 100) -> bool:
    """Return True if word count of text is below the specified threshold (default: 100)."""
    return count_words(text) < threshold


def build_engine_queries(brand_text: str, questions: list = None, max_queries: int = 5) -> list[str]:
    """
    Build search-engine-style buyer intent queries from extracted page text and questions.

    - brand_text: extracted text from the page
    - questions: list of question strings or dicts
    - max_queries: maximum number of queries to generate (default: 5)
    """
    queries = []

    if questions:
        for q in questions:
            q_text = q.get("question_text", q) if isinstance(q, dict) else str(q)
            if q_text and q_text.strip():
                queries.append(q_text.strip())

    if not queries and brand_text:
        # Fallback to topic extraction from brand_text (bounded to first 10,000 chars)
        sample_text = brand_text[:10000] if isinstance(brand_text, str) else ""
        words = [w for w in re.findall(r"\b[A-Za-z]{4,}\b", sample_text) if w.lower() not in ("with", "that", "this", "from", "have", "more")]
        if words:
            topic = " ".join(words[:3])
            queries.append(f"best options for {topic}")
            queries.append(f"top recommended brands for {topic}")

    if not queries:
        queries = [
            "best recommended products for this category",
            "top verified brands for this industry",
        ]

    return queries[:max_queries]


def run_probe(queries: list) -> list[dict]:
    """
    Simulate probe execution across AI engine endpoints (Mock Mode).

    Returns array of question/query result objects with simulated engine mention statuses:
    'not_mentioned', 'mentioned_accurate', or 'mentioned_inaccurate'.
    """
    if not queries:
        return []

    probe_results = []
    for idx, q in enumerate(queries):
        q_text = q.get("question_text", q) if isinstance(q, dict) else str(q)
        q_id = f"q{idx + 1}"

        # Generic, engine-agnostic mock query results
        engine_results = [
            {
                "engine": "engine_a",
                "mention_status": "not_mentioned",
                "response_excerpt": f"I recommend established market leaders for {q_text}.",
            },
            {
                "engine": "engine_b",
                "mention_status": "mentioned_inaccurate" if idx == 0 else "not_mentioned",
                "response_excerpt": f"Some options exist for {q_text}, but specific brand facts were unavailable.",
            },
        ]

        probe_results.append({
            "question_id": q_id,
            "question_text": q_text,
            "engine_results": engine_results,
        })

    return probe_results
