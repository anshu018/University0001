"""
Step 3: FIX IT
Generate the structured brand-info files from live/extracted brand data.

Outputs:
- generated/brand-info.json   <- metadata + approval state + facts
- generated/brand-info.llms.txt <- human-readable AI-facing content

Approval:
- Terminal prompt: Type APPROVE to publish, or anything else to cancel
- On APPROVE: sets approved=true, approved_by=OPERATOR_NAME, approved_at=ISO timestamp
- Otherwise: leaves approved=false and prints "Cancelled."
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root and src directory are in sys.path for direct execution
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from config.settings import OPERATOR_NAME
from brand_visibility.exceptions import get_brand_dir, BrandNotFoundError
from brand_visibility.fact_extractor import extract_facts
from brand_visibility.reader import read_cached_html
from brand_visibility.schema_generator import validate_brand_record


APPROVAL_PROMPT = "Type APPROVE to publish, or anything else to cancel:\n> "


def _default_brand_info(brand_record: dict, facts: list[dict]) -> dict:
    return {
        "brand_id": brand_record.get("brand_id"),
        "display_name": brand_record.get("display_name", brand_record.get("brand_id")),
        "website_url": brand_record.get("website_url", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "approved": False,
        "approved_by": None,
        "approved_at": None,
        "content_file": "brand-info.llms.txt",
        "facts": facts,
    }


def _render_llms_txt(brand_info: dict) -> str:
    lines = [
        f"# {brand_info.get('display_name', brand_info.get('brand_id'))}",
        "",
        "## Summary",
        f"Official website: {brand_info.get('website_url', '')}",
        f"Generated at: {brand_info.get('generated_at', '')}",
        "",
        "## Facts",
    ]
    for idx, fact in enumerate(brand_info.get("facts", []), start=1):
        source = fact.get("source", brand_info.get("website_url", ""))
        lines.append(f"{idx}. {fact.get('fact', '')} (source: {source})")

    lines.append("")
    lines.append("## Approval")
    lines.append(f"Approved: {brand_info.get('approved')}")
    lines.append(f"Approved by: {brand_info.get('approved_by')}")
    lines.append(f"Approved at: {brand_info.get('approved_at')}")
    return "\n".join(lines)


def generate_brand_files(brand_id: str, brand_type: str = None) -> dict:
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    brand_json_path = brand_dir / "brand.json"

    if not brand_json_path.exists():
        raise BrandNotFoundError(f"Brand record not found at {brand_json_path}")

    brand_record = json.loads(brand_json_path.read_text(encoding="utf-8"))
    validate_brand_record(brand_record)

    raw_html = ""
    try:
        raw_html = read_cached_html(brand_id, brand_type=brand_type)
    except Exception:
        pass

    facts = extract_facts(raw_html, website_url=brand_record.get("website_url", "")) if raw_html else []
    brand_info = _default_brand_info(brand_record, facts)

    generated_dir = brand_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    json_path = generated_dir / "brand-info.json"
    llms_path = generated_dir / "brand-info.llms.txt"

    json_path.write_text(json.dumps(brand_info, indent=2) + "\n", encoding="utf-8")
    llms_path.write_text(_render_llms_txt(brand_info), encoding="utf-8")

    print(f"Generated: {json_path}")
    print(f"Generated: {llms_path}")
    return brand_info


def approval_gate(brand_id: str, brand_type: str = None) -> dict:
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    brand_json_path = brand_dir / "brand.json"
    brand_record = json.loads(brand_json_path.read_text(encoding="utf-8"))

    raw_html = ""
    try:
        raw_html = read_cached_html(brand_id, brand_type=brand_type)
    except Exception:
        pass

    facts = extract_facts(raw_html, website_url=brand_record.get("website_url", "")) if raw_html else []
    brand_info = _default_brand_info(brand_record, facts)

    print("\n=== APPROVAL REQUIRED ===")
    print("This will be published and made reachable by AI agents via MCP.")
    if os.environ.get("BRAND_AUTO_APPROVE") == "1":
        approved = True
        print("Auto-approved via BRAND_AUTO_APPROVE=1.")
    else:
        try:
            response = input(APPROVAL_PROMPT)
        except EOFError:
            response = ""
        approved = response.strip().upper() == "APPROVE"
        print("Published." if approved else "Cancelled.")

    if approved:
        brand_info["approved"] = True
        brand_info["approved_by"] = OPERATOR_NAME
        brand_info["approved_at"] = datetime.now(timezone.utc).isoformat()

    generated_dir = brand_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    json_path = generated_dir / "brand-info.json"
    llms_path = generated_dir / "brand-info.llms.txt"

    json_path.write_text(json.dumps(brand_info, indent=2) + "\n", encoding="utf-8")
    llms_path.write_text(_render_llms_txt(brand_info), encoding="utf-8")

    return brand_info


def unapprove_brand(brand_id: str, brand_type: str = None) -> dict:
    """Reset brand approval state to unapproved (False, None, None) without deleting files."""
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    generated_dir = brand_dir / "generated"
    json_path = generated_dir / "brand-info.json"
    llms_path = generated_dir / "brand-info.llms.txt"

    if not json_path.exists():
        raise BrandNotFoundError(f"Generated brand info file not found at {json_path}")

    brand_info = json.loads(json_path.read_text(encoding="utf-8"))
    brand_info["approved"] = False
    brand_info["approved_by"] = None
    brand_info["approved_at"] = None

    json_path.write_text(json.dumps(brand_info, indent=2) + "\n", encoding="utf-8")
    llms_path.write_text(_render_llms_txt(brand_info), encoding="utf-8")

    return brand_info


if __name__ == "__main__":
    import os as _os
    brand_id = _os.environ.get("BRAND_ID")
    brand_type = _os.environ.get("BRAND_TYPE")
    if not brand_id:
        print("Set BRAND_ID to run directly.", file=sys.stderr)
        raise SystemExit(2)
    result = approval_gate(brand_id, brand_type=brand_type)
    print(json.dumps(result, indent=2))
