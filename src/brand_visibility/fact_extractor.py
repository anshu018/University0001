"""
Rule-based fact extractor and question generator module for Brand Visibility Agent.

Extracts verified facts from HTML elements (<title>, <meta>, <h1>-<h3>, <p>, <li>)
with mandatory source URLs, and generates topic-aware buyer questions.

Completely industry-agnostic and business-type neutral. Zero hardcoded vertical terms.
"""

import re
from bs4 import BeautifulSoup


def _clean_text(text: str) -> str:
    """Clean whitespace, newlines, and non-printable characters from string."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_facts(raw_html: str, website_url: str = "", max_facts: int = 8) -> list[dict]:
    """
    Extract factual claims directly from raw HTML content.

    - raw_html: HTML string of the webpage
    - website_url: source URL associated with extracted facts
    - max_facts: maximum number of facts to return (default: 8)

    Returns a list of dicts: [{"fact": "...", "source": website_url}, ...]
    Rule 3 enforced: Every fact carries a verified source URL. Never invents facts.
    """
    if not raw_html or not isinstance(raw_html, str):
        return []

    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove script, style, header, footer, nav tags to focus on core body content
    for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        element.decompose()

    facts = []
    seen_facts = set()

    def add_fact(fact_text: str, source_url: str):
        cleaned = _clean_text(fact_text)
        if 15 <= len(cleaned) <= 250 and cleaned.lower() not in seen_facts:
            seen_facts.add(cleaned.lower())
            facts.append({"fact": cleaned, "source": source_url or website_url})

    # 1. Page Title
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        add_fact(f"Official Website Title: {title_tag.string}", website_url)

    # 2. Meta Description
    meta_desc = (
        soup.find("meta", attrs={"name": "description"})
        or soup.find("meta", attrs={"property": "og:description"})
    )
    if meta_desc and meta_desc.get("content"):
        add_fact(meta_desc["content"], website_url)

    # 3. Headings (h1, h2, h3)
    for h in soup.find_all(["h1", "h2", "h3"]):
        heading_text = h.get_text(strip=True)
        if len(heading_text) >= 10:
            add_fact(f"Featured Topic: {heading_text}", website_url)
            if len(facts) >= max_facts:
                break

    # 4. Content Paragraphs (p)
    if len(facts) < max_facts:
        main_content = soup.find(["main", "article"]) or soup.body or soup
        for p in main_content.find_all("p"):
            p_text = p.get_text(strip=True)
            if len(p_text) >= 20:
                add_fact(p_text, website_url)
                if len(facts) >= max_facts:
                    break

    # 5. List Items (li)
    if len(facts) < max_facts:
        for li in soup.find_all("li"):
            li_text = li.get_text(strip=True)
            if len(li_text) >= 15:
                add_fact(li_text, website_url)
                if len(facts) >= max_facts:
                    break

    return facts[:max_facts]


def extract_questions(raw_html: str, max_questions: int = 5) -> list[str]:
    """
    Generate topic-aware buyer intent questions based on extracted page headings and text.

    - raw_html: raw HTML string
    - max_questions: maximum questions to return (default: 5)

    Returns a list of question strings.
    """
    if not raw_html or not isinstance(raw_html, str):
        return [
            "What products or services does this brand offer?",
            "Where can I find verified information about this brand?",
        ]

    soup = BeautifulSoup(raw_html, "html.parser")
    topics = []

    # Extract topics from title, h1, h2
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        clean_title = _clean_text(title_tag.string)
        # Split on common separators like |, -, :
        parts = re.split(r"[|\-:]", clean_title)
        if parts:
            topics.append(parts[0].strip())

    for h in soup.find_all(["h1", "h2"]):
        h_text = _clean_text(h.get_text())
        if 5 <= len(h_text) <= 50:
            topics.append(h_text)

    # Clean and deduplicate topics
    unique_topics = []
    seen = set()
    for t in topics:
        if t.lower() not in seen and len(t) > 3:
            seen.add(t.lower())
            unique_topics.append(t)

    questions = []
    if unique_topics:
        primary = unique_topics[0]
        questions.append(f"best options for {primary}")
        questions.append(f"top recommendations for {primary}")
        if len(unique_topics) > 1:
            questions.append(f"what is {unique_topics[1]}")
        questions.append(f"reliable brands offering {primary}")
        questions.append(f"where to buy or find {primary}")
    else:
        questions = [
            "best available products and services for this brand",
            "top features and offerings of this business",
            "reliable options offered by this company",
            "key details and background about this brand",
            "customer recommendations for this brand's offerings",
        ]

    return questions[:max_questions]
