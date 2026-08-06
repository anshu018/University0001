"""
Step 2: SHOW WHY (Sense -> Generate diagnostic bridge) pipeline execution script.

Receives Step 1 check result and in-memory raw webpage content, evaluates reason codes,
builds a specific plain-language summary for brand owners/judges, and persists diagnosis JSON.

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

from brand_visibility.exceptions import (
    BrandNotFoundError,
    get_brand_dir,
    make_diagnosis_id,
)
from brand_visibility.llm import get_diagnosis
from brand_visibility.probe import extract_text
from brand_visibility.reader import read_cached_html
from brand_visibility.reporter import write_diagnosis


def get_latest_check_result(brand_id: str, brand_type: str = None) -> tuple[dict, str]:
    """Load latest check-result JSON and cached raw HTML for a brand from disk."""
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    checks_dir = brand_dir / "checks"

    if not checks_dir.exists():
        raise FileNotFoundError(f"No checks directory found for brand '{brand_id}' at {checks_dir}")

    check_files = sorted(checks_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not check_files:
        raise FileNotFoundError(f"No check result JSON files found in {checks_dir}")

    latest_check_path = check_files[0]
    check_data = json.loads(latest_check_path.read_text(encoding="utf-8"))

    # Try to read cached HTML
    raw_html = ""
    try:
        raw_html = read_cached_html(brand_id, brand_type=brand_type)
    except Exception:
        pass

    return check_data, raw_html


def run_diagnose(
    brand_id: str,
    check_result: dict = None,
    raw_html: str = "",
    brand_type: str = None,
) -> dict:
    """
    Execute Step 2 (SHOW WHY) diagnosis.

    Returns diagnosis dict matching schema.md.
    """
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    brand_json_path = brand_dir / "brand.json"

    if not brand_json_path.exists():
        raise BrandNotFoundError(f"Brand record not found at {brand_json_path}. Cannot execute SHOW WHY.")

    brand_record = json.loads(brand_json_path.read_text(encoding="utf-8"))
    display_name = brand_record.get("display_name", brand_id)

    # If check_result or raw_html is not passed in memory from Step 1, load latest from disk
    if check_result is None or not raw_html:
        disk_check, cached_html = get_latest_check_result(brand_id, brand_type=brand_type)
        if check_result is None:
            check_result = disk_check
        if not raw_html:
            raw_html = cached_html

    print("\n------------------------------------------", file=sys.stderr)
    print("[2/4] SHOW WHY", file=sys.stderr)
    print("------------------------------------------", file=sys.stderr)

    extracted_text = extract_text(raw_html) if raw_html else ""
    diagnosis_payload = get_diagnosis(check_result, raw_text=extracted_text)

    diagnosis_id = make_diagnosis_id()
    check_id = check_result.get("check_id", "")

    full_diagnosis = {
        "diagnosis_id": diagnosis_id,
        "check_id": check_id,
        "brand_id": brand_id,
        "plain_summary": diagnosis_payload.get("plain_summary", ""),
        "reasons": diagnosis_payload.get("reasons", []),
    }

    print(f"{full_diagnosis['plain_summary']}\n", file=sys.stderr)
    for r in full_diagnosis["reasons"]:
        rcode = r.get("reason_code", "")
        rdetail = r.get("detail", "")
        print(f"Reason: {rcode}", file=sys.stderr)
        print(f"  -> {rdetail}", file=sys.stderr)

    output_path = write_diagnosis(full_diagnosis, brand_id, brand_type=brand_type)
    print(f"\nDiagnosis saved to: {output_path}", file=sys.stderr)

    return full_diagnosis


if __name__ == "__main__":
    import os as _os
    brand_id = _os.environ.get("BRAND_ID")
    brand_type = _os.environ.get("BRAND_TYPE")
    if not brand_id:
        print("Set BRAND_ID to run directly.", file=sys.stderr)
        raise SystemExit(2)
    res = run_diagnose(brand_id, brand_type=brand_type)
    print(f"Step 2 SHOW WHY completed successfully. Diagnosis ID: {res['diagnosis_id']}", file=sys.stderr)
