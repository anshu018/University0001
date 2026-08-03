"""
Stage 1 orchestrator for the Brand Visibility Agent demo pipeline.

Usage:
    python run_demo.py --brand hoka
    python run_demo.py --brand hoka --replay
    python run_demo.py --brand hoka --approve
    python run_demo.py --list
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

root_dir = Path(__file__).resolve().parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from brand_visibility.exceptions import get_brand_dir, BrandNotFoundError
from brand_visibility.logger import log_run_start, log_run_end
from brand_visibility.probe import extract_text
from brand_visibility.reader import fetch_url, read_cached_html, save_cached_html
from brand_visibility.reporter import write_check_result
from brand_visibility.schema_generator import validate_check_result
from brand_visibility.step1_check import run_check
from brand_visibility.step2_diagnose import run_diagnose
from brand_visibility.step3_fix import generate_brand_files, approval_gate
from brand_visibility.step4_prove import run_prove


REPLAY_DIR_NAME = "replay"


def _list_brands() -> list[str]:
    base = Path("brands")
    if not base.exists():
        return []
    brands = []
    for brand_type in ("test", "real"):
        type_dir = base / brand_type
        if not type_dir.exists():
            continue
        for brand_dir in sorted(type_dir.iterdir()):
            if brand_dir.is_dir() and (brand_dir / "brand.json").exists():
                brands.append(f"{brand_type}/{brand_dir.name}")
    return brands


def _save_replay(brand_id: str, brand_type: str | None, data: dict) -> Path:
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    replay_dir = brand_dir / REPLAY_DIR_NAME
    replay_dir.mkdir(parents=True, exist_ok=True)
    path = replay_dir / "last_run.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def _load_replay(brand_id: str, brand_type: str | None) -> dict | None:
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    path = brand_dir / REPLAY_DIR_NAME / "last_run.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _terminal_approve_gate(brand_id: str, brand_type: str | None) -> bool:
    print("=== APPROVAL REQUIRED ===")
    print("This will be published and made reachable by AI agents via MCP.")
    try:
        response = input("Type APPROVE to publish, or anything else to cancel:\n> ")
    except EOFError:
        response = ""
    approved = response.strip().upper() == "APPROVE"
    print("Published." if approved else "Cancelled.")
    return approved


def run_pipeline(brand_id: str, brand_type: str | None = None, replay: bool = False, approve: bool = False) -> dict:
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    brand_json_path = brand_dir / "brand.json"
    if not brand_json_path.exists():
        raise BrandNotFoundError(f"Brand record not found at {brand_json_path}")

    brand_record = json.loads(brand_json_path.read_text(encoding="utf-8"))
    if brand_record.get("brand_type") == "real" and not brand_record.get("consent_given"):
        raise BrandNotFoundError(
            f"Brand '{brand_id}' is marked real and consent_given is not True."
        )

    run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    log_path = log_run_start(run_id, brand_id, "run_demo", brand_type=brand_type)
    result = {
        "brand_id": brand_id,
        "brand_type": brand_type,
        "replay": replay,
        "run_id": run_id,
        "log_path": str(log_path),
    }

    if replay:
        replay_data = _load_replay(brand_id, brand_type)
        if not replay_data:
            print("No replay data found. Running live pipeline instead.")
            replay = False
        else:
            result.update(replay_data)
            print(f"Replayed run {result.get('run_id')} for {brand_id}.")
            return result

    print(f"[1/4] CHECK — inspecting {brand_record.get('website_url')}")
    check_result, raw_html = run_check(brand_id, brand_type=brand_type)
    result["step1"] = check_result

    print(f"[2/4] SHOW WHY — diagnosing {brand_id}")
    diagnosis = run_diagnose(brand_id, check_result=check_result, raw_html=raw_html, brand_type=brand_type)
    result["step2"] = diagnosis

    print(f"[3/4] FIX IT — generating brand files for {brand_id}")
    brand_info = generate_brand_files(brand_id, brand_type=brand_type)

    approved = approve or _terminal_approve_gate(brand_id, brand_type=brand_type)
    if approved:
        brand_info["approved"] = True
        brand_info["approved_by"] = os.environ.get("OPERATOR_NAME", "Anshu")
        brand_info["approved_at"] = datetime.now(timezone.utc).isoformat()

    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    generated_dir = brand_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    (generated_dir / "brand-info.json").write_text(json.dumps(brand_info, indent=2) + "\n", encoding="utf-8")
    (generated_dir / "brand-info.llms.txt").write_text(
        "\n".join([
            f"# {brand_info.get('display_name', brand_info.get('brand_id'))}",
            "",
            "## Summary",
            f"Official website: {brand_info.get('website_url', '')}",
            f"Generated at: {brand_info.get('generated_at', '')}",
            "",
            "## Facts",
            *[f"{idx}. {fact.get('fact', '')} (source: {fact.get('source', brand_info.get('website_url', ''))})" for idx, fact in enumerate(brand_info.get("facts", []), start=1)],
            "",
            "## Approval",
            f"Approved: {brand_info.get('approved')}",
            f"Approved by: {brand_info.get('approved_by')}",
            f"Approved at: {brand_info.get('approved_at')}",
        ]),
        encoding="utf-8",
    )
    result["step3"] = brand_info

    print(f"[4/4] PROVE IT — proving visibility for {brand_id}")
    proof = run_prove(brand_id, brand_type=brand_type)
    result["step4"] = proof

    _save_replay(brand_id, brand_type, result)
    log_run_end(run_id, brand_id, "run_demo", "completed", brand_type=brand_type)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Brand Visibility Agent demo orchestrator")
    parser.add_argument("--brand", required=False, help="brand_id to run, e.g. hoka")
    parser.add_argument("--list", action="store_true", help="list available brands")
    parser.add_argument("--replay", action="store_true", help="replay last approved run from disk")
    parser.add_argument("--approve", action="store_true", help="auto-approve generated brand info without prompt")
    args = parser.parse_args()

    if args.list:
        print("Available brands:")
        for b in _list_brands():
            print(f"- {b}")
        return 0

    brand_id = args.brand or os.environ.get("BRAND_ID")
    if not brand_id:
        print("Provide --brand or set BRAND_ID.", file=sys.stderr)
        return 2

    brand_type = None
    if "/" in brand_id:
        brand_type, brand_id = brand_id.split("/", 1)

    try:
        data = run_pipeline(brand_id, brand_type=brand_type, replay=args.replay, approve=args.approve)
    except BrandNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1

    print("\n=========================================")
    print(" Done. Run again with --replay for instant cached re-run.")
    print("=========================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
