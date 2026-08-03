"""
Disk persistence and schema reporting module for Brand Visibility Agent.

Validates and writes check results and diagnosis payloads to disk per schema.md.
Writes to:
- brands/<test|real>/<brand_id>/checks/<check_id>.json
- brands/<test|real>/<brand_id>/diagnoses/<diagnosis_id>.json

Completely industry-agnostic and business-type neutral.
"""

import datetime
import json
from pathlib import Path

from brand_visibility.exceptions import (
    get_brand_dir,
    make_check_id,
    make_diagnosis_id,
    SchemaValidationError,
)
from brand_visibility.schema_generator import (
    normalize_record,
    validate_check_result,
    validate_diagnosis,
)


def _get_iso_timestamp() -> str:
    """Return current UTC timestamp formatted as ISO string."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_check_result(check_result: dict, brand_id: str, brand_type: str = None) -> Path:
    """
    Validate and persist a check result payload to disk.

    Target path: brands/<test|real>/<brand_id>/checks/<check_id>.json
    Returns Path object of the written JSON file.
    """
    if not isinstance(check_result, dict):
        raise SchemaValidationError("check_result must be a dictionary")

    record = normalize_record(check_result, "check_result")
    
    # Ensure mandatory identifiers are populated
    record["brand_id"] = brand_id
    if not record.get("check_id"):
        record["check_id"] = make_check_id()
    if not record.get("run_at"):
        record["run_at"] = _get_iso_timestamp()
    if not record.get("status"):
        record["status"] = "completed"

    if not validate_check_result(record):
        raise SchemaValidationError(f"check_result record failed schema validation: {record}")

    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    checks_dir = brand_dir / "checks"
    checks_dir.mkdir(parents=True, exist_ok=True)

    output_path = checks_dir / f"{record['check_id']}.json"
    output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return output_path


def write_diagnosis(diagnosis: dict, brand_id: str, brand_type: str = None) -> Path:
    """
    Validate and persist a diagnosis payload to disk.

    Target path: brands/<test|real>/<brand_id>/diagnoses/<diagnosis_id>.json
    Returns Path object of the written JSON file.
    """
    if not isinstance(diagnosis, dict):
        raise SchemaValidationError("diagnosis must be a dictionary")

    record = normalize_record(diagnosis, "diagnosis")
    
    # Ensure mandatory identifiers are populated
    record["brand_id"] = brand_id
    if not record.get("diagnosis_id"):
        record["diagnosis_id"] = make_diagnosis_id()
    if not record.get("run_at"):
        record["run_at"] = _get_iso_timestamp()

    if not validate_diagnosis(record):
        raise SchemaValidationError(f"diagnosis record failed schema validation: {record}")

    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    diagnoses_dir = brand_dir / "diagnoses"
    diagnoses_dir.mkdir(parents=True, exist_ok=True)

    output_path = diagnoses_dir / f"{record['diagnosis_id']}.json"
    output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return output_path
