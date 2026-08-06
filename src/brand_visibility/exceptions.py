"""
Exceptions, ID generators, path resolution, and schema constants for Brand Visibility Agent.

Completely industry-agnostic and business-type neutral.
"""

import datetime
import random
import string
from pathlib import Path


# -----------------------------------------------------------------------------
# Custom Error Classes
# -----------------------------------------------------------------------------

class BrandVisibilityError(Exception):
    """Base exception class for Brand Visibility Agent errors."""
    pass


class SiteUnreachableError(BrandVisibilityError):
    """Raised when a brand's website cannot be reached or times out."""
    pass


class ThinContentError(BrandVisibilityError):
    """Raised when extracted website content falls below word count threshold."""
    pass


class BrandNotFoundError(BrandVisibilityError):
    """Raised when a specified brand record or folder cannot be found."""
    pass


class ConsentRequiredError(BrandVisibilityError):
    """Raised when a real brand record lacks explicit consent_given = True."""
    pass


class SchemaValidationError(BrandVisibilityError):
    """Raised when a data record fails schema structure validation."""
    pass


# -----------------------------------------------------------------------------
# ID Generators
# -----------------------------------------------------------------------------

def generate_run_id(prefix: str = "") -> str:
    """
    Generate a timestamped ID matching YYYY-MM-DD-xxxx format per schema.md.
    
    Optional prefix can prepend to the ID if needed.
    """
    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    run_id = f"{date_str}-{suffix}"
    return f"{prefix}{run_id}" if prefix else run_id


def make_check_id() -> str:
    """Generate a check ID matching YYYY-MM-DD-xxxx."""
    return generate_run_id()


def make_diagnosis_id() -> str:
    """Generate a diagnosis ID matching YYYY-MM-DD-xxxx."""
    return generate_run_id()


# -----------------------------------------------------------------------------
# Path Utilities
# -----------------------------------------------------------------------------

import re


def get_base_dir() -> Path:
    """Return the absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def get_brand_dir(brand_id: str, brand_type: str = None) -> Path:
    """
    Resolve the directory path for a given brand_id with path traversal defense.
    
    If brand_type is provided ('test' or 'real'), resolves directly under that folder.
    Otherwise, checks brands/test/<brand_id> first, then brands/real/<brand_id>.
    """
    if not brand_id or not isinstance(brand_id, str):
        raise ValueError("brand_id must be a non-empty string")
    
    if not re.match(r"^[a-zA-Z0-9_-]+$", brand_id):
        raise ValueError(f"Invalid brand_id format: '{brand_id}'")
        
    base_dir = get_base_dir()
    brands_root = (base_dir / "brands").resolve()

    if brand_type:
        if brand_type not in ("test", "real"):
            raise ValueError(f"Invalid brand_type: '{brand_type}'")
        target_path = (base_dir / "brands" / brand_type / brand_id).resolve()
        if not str(target_path).startswith(str(brands_root)):
            raise ValueError(f"Path traversal detected for brand_id '{brand_id}'")
        return target_path

    test_path = (base_dir / "brands" / "test" / brand_id).resolve()
    if not str(test_path).startswith(str(brands_root)):
        raise ValueError(f"Path traversal detected for brand_id '{brand_id}'")
    if test_path.exists():
        return test_path

    real_path = (base_dir / "brands" / "real" / brand_id).resolve()
    if not str(real_path).startswith(str(brands_root)):
        raise ValueError(f"Path traversal detected for brand_id '{brand_id}'")
    if real_path.exists():
        return real_path

    # Default fallback to test if neither exists yet
    return test_path


def brand_output_path(brand_id: str, category: str, filename: str, brand_type: str = None) -> Path:
    """
    Construct path for a specific brand output file (e.g. checks, diagnoses, generated).
    """
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    return brand_dir / category / filename


# -----------------------------------------------------------------------------
# Schema Field Validation Constants (Strictly matching schema.md)
# -----------------------------------------------------------------------------

BRAND_FIELDS = [
    "brand_id",
    "display_name",
    "website_url",
    "brand_type",
    "added_on",
    "consent_given",
    "consent_given_by",
    "consent_given_on",
]

CHECK_RESULT_FIELDS = [
    "check_id",
    "brand_id",
    "run_at",
    "status",
    "error_detail",
    "business_type_detected",
    "questions",
]

DIAGNOSIS_FIELDS = [
    "diagnosis_id",
    "check_id",
    "brand_id",
    "run_at",
    "plain_summary",
    "reasons",
]

BRAND_INFO_FIELDS = [
    "brand_id",
    "generated_at",
    "approved",
    "approved_by",
    "approved_at",
    "content_file",
    "facts",
]
