"""
Schema validation and record normalization module for Brand Visibility Agent.

Validates and normalizes JSON data records against schema specifications defined in schema.md.
Completely industry-agnostic and business-type neutral.
"""

from brand_visibility.exceptions import (
    BRAND_FIELDS,
    CHECK_RESULT_FIELDS,
    DIAGNOSIS_FIELDS,
    BRAND_INFO_FIELDS,
    SchemaValidationError,
)

# Common field key aliases for normalization
FIELD_ALIASES = {
    "name": "display_name",
    "url": "website_url",
    "type": "brand_type",
    "id": "brand_id",
    "created_at": "added_on",
    "detected_business_type": "business_type_detected",
}

SCHEMA_FIELD_MAP = {
    "brand": BRAND_FIELDS,
    "check_result": CHECK_RESULT_FIELDS,
    "diagnosis": DIAGNOSIS_FIELDS,
    "brand_info": BRAND_INFO_FIELDS,
}


def _validate_record(record: dict, required_fields: list[str]) -> bool:
    """Check if all required schema fields are present in the record dict."""
    if not isinstance(record, dict):
        return False
    return all(field in record for field in required_fields)


def validate_brand_record(record: dict) -> bool:
    """Validate a brand input record dict against BRAND_FIELDS."""
    return _validate_record(record, BRAND_FIELDS)


def validate_check_result(record: dict) -> bool:
    """Validate a check result dict against CHECK_RESULT_FIELDS."""
    return _validate_record(record, CHECK_RESULT_FIELDS)


def validate_diagnosis(record: dict) -> bool:
    """Validate a diagnosis dict against DIAGNOSIS_FIELDS."""
    return _validate_record(record, DIAGNOSIS_FIELDS)


def validate_brand_info(record: dict) -> bool:
    """Validate a generated brand info dict against BRAND_INFO_FIELDS."""
    return _validate_record(record, BRAND_INFO_FIELDS)


def normalize_record(record: dict, schema_type: str) -> dict:
    """
    Normalize record keys using standard aliases and supply default null/empty values
    for missing schema fields.
    
    schema_type: 'brand', 'check_result', 'diagnosis', or 'brand_info'
    """
    if not isinstance(record, dict):
        raise SchemaValidationError(f"Expected dict for normalization, got {type(record)}")

    schema_type_clean = schema_type.lower().strip()
    if schema_type_clean not in SCHEMA_FIELD_MAP:
        raise SchemaValidationError(f"Unknown schema_type: '{schema_type}'")

    target_fields = SCHEMA_FIELD_MAP[schema_type_clean]
    normalized = {}

    # Map existing keys, replacing known legacy aliases
    for key, value in record.items():
        canonical_key = FIELD_ALIASES.get(key, key)
        normalized[canonical_key] = value

    # Ensure all required target fields exist
    for field in target_fields:
        if field not in normalized:
            if field in ("questions", "reasons", "facts"):
                normalized[field] = []
            else:
                normalized[field] = None

    return normalized
