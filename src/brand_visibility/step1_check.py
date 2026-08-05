"""
Step 1: CHECK (Sense) pipeline execution script for Brand Visibility Agent.

Fetches live brand website HTML, detects business type, generates buyer questions,
evaluates AI engine mention statuses, and persists check result JSON payload per schema.md.

Completely business-type agnostic.
"""

import json
import os
import sys
from pathlib import Path

# Ensure project root and src directory are in sys.path for direct execution
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from brand_visibility.ai_client import ask_ai
from brand_visibility.exceptions import (
    BrandNotFoundError,
    ConsentRequiredError,
    get_brand_dir,
    make_check_id,
)
from brand_visibility.persona import detect_business_type
from brand_visibility.probe import (
    count_words,
    detect_thin_content,
    extract_text,
    run_probe,
)
from brand_visibility.reader import fetch_url, save_cached_html
from brand_visibility.reporter import write_check_result
from brand_visibility.scorer import generate_questions


def run_check(brand_id: str, brand_type: str = None) -> tuple[dict, str]:
    """
    Execute Step 1 (CHECK) for a given brand_id.

    Returns tuple: (check_result_dict, raw_html_content_string)
    """
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    brand_json_path = brand_dir / "brand.json"

    if not brand_json_path.exists():
        raise BrandNotFoundError(f"Brand record not found at {brand_json_path}. Cannot execute CHECK.")

    brand_record = json.loads(brand_json_path.read_text(encoding="utf-8"))

    # Consent check for real brands per rules.md / app-flow.md
    if brand_record.get("brand_type") == "real" and not brand_record.get("consent_given"):
        raise ConsentRequiredError(
            f"Brand '{brand_id}' is marked brand_type: 'real' and consent_given is not True."
        )

    website_url = brand_record.get("website_url", "")
    display_name = brand_record.get("display_name", brand_id)
    check_id = make_check_id()

    print(f"\n[1/4] CHECK — reading {website_url} ...")

    # 1. Fetch website HTML
    status, raw_html, error_detail = fetch_url(website_url, timeout=10, retries=1)

    if status == "error" or not raw_html:
        check_result = {
            "check_id": check_id,
            "brand_id": brand_id,
            "status": "error",
            "error_detail": error_detail or "site_unreachable",
            "business_type_detected": "unknown",
            "questions": [],
        }
        write_check_result(check_result, brand_id, brand_type=brand_type)
        return check_result, ""

    # Save cache for replay mode
    save_cached_html(brand_id, raw_html, brand_type=brand_type)

    # 2. Extract text & detect thin content
    extracted_text = extract_text(raw_html)
    word_cnt = count_words(extracted_text)
    is_thin = detect_thin_content(extracted_text, threshold=100)

    # 3. Detect business type
    biz_type = detect_business_type(extracted_text, website_url=website_url)
    print(f"Detected business type: {biz_type}")

    # 4. Generate buyer questions
    question_texts = generate_questions(biz_type, extracted_text, count=2)
    print("\nGenerated buyer questions:")
    for idx, q_text in enumerate(question_texts, start=1):
        print(f'  Q{idx}: "{q_text}"')

    # 5. Evaluate AI engine mentions
    questions_payload = []
    print("\nQuerying engine_a...")
    print("Querying engine_b...")
    for idx, q_text in enumerate(question_texts, start=1):
        q_id = f"q{idx}"
        ans_a = ask_ai(q_text, brand_context=None, engine="engine_a")
        ans_b = ask_ai(q_text, brand_context=None, engine="engine_b")

        mention_a = "mentioned_accurate" if display_name.lower() in ans_a.lower() else "not_mentioned"
        mention_b = "mentioned_accurate" if display_name.lower() in ans_b.lower() else "not_mentioned"

        questions_payload.append({
            "question_id": q_id,
            "question_text": q_text,
            "engine_results": [
                {
                    "engine": "engine_a",
                    "mention_status": mention_a,
                    "response_excerpt": ans_a[:150] + "..." if len(ans_a) > 150 else ans_a,
                },
                {
                    "engine": "engine_b",
                    "mention_status": mention_b,
                    "response_excerpt": ans_b[:150] + "..." if len(ans_b) > 150 else ans_b,
                },
            ],
        })

    print("\nResults:")
    for q_data in questions_payload:
        q_id = q_data["question_id"]
        for eng in q_data["engine_results"]:
            eng_name = eng["engine"]
            m_status = eng["mention_status"].replace("_", " ").upper()
            print(f"  {q_id} x {eng_name:<10} [{m_status}]")

    check_result = {
        "check_id": check_id,
        "brand_id": brand_id,
        "status": "completed",
        "error_detail": None,
        "business_type_detected": biz_type,
        "questions": questions_payload,
    }

    output_path = write_check_result(check_result, brand_id, brand_type=brand_type)
    print(f"\nCheck result saved to: {output_path}")

    return check_result, raw_html


if __name__ == "__main__":
    import os as _os
    brand_id = _os.environ.get("BRAND_ID")
    brand_type = _os.environ.get("BRAND_TYPE")
    if not brand_id:
        print("Set BRAND_ID to run directly.", file=sys.stderr)
        raise SystemExit(2)
    res, html = run_check(brand_id, brand_type=brand_type)
    print(f"Step 1 CHECK completed successfully. Check ID: {res['check_id']}")
