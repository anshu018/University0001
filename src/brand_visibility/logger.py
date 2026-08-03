"""
Structured pipeline logger module for Brand Visibility Agent.

Writes timestamped execution and extraction metrics to brands/<test|real>/<brand_id>/logs/<run_id>.log.
Completely industry-agnostic and business-type neutral.
"""

import datetime
from pathlib import Path
from brand_visibility.exceptions import get_brand_dir


def _get_log_file(run_id: str, brand_id: str, brand_type: str = None) -> Path:
    """Resolve and ensure parent directory for execution log file."""
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    log_dir = brand_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{run_id}.log"


def _format_timestamp() -> str:
    """Return current UTC timestamp formatted ISO string."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_log(log_path: Path, level: str, message: str) -> None:
    """Append a formatted log line to log_path and stdout."""
    timestamp = _format_timestamp()
    log_line = f"[{timestamp}] [{level}] {message}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_line)


def log_run_start(run_id: str, brand_id: str, step: str, brand_type: str = None) -> Path:
    """Log pipeline step execution start."""
    log_path = _get_log_file(run_id, brand_id, brand_type=brand_type)
    msg = f"STEP START | Step: {step} | BrandID: {brand_id} | RunID: {run_id}"
    _append_log(log_path, "INFO", msg)
    return log_path


def log_run_end(
    run_id: str,
    brand_id: str,
    step: str,
    status: str,
    error: str = None,
    brand_type: str = None,
) -> Path:
    """Log pipeline step execution completion or error."""
    log_path = _get_log_file(run_id, brand_id, brand_type=brand_type)
    level = "INFO" if status.lower() in ("completed", "success", "ok") else "ERROR"
    msg = f"STEP END | Step: {step} | BrandID: {brand_id} | Status: {status}"
    if error:
        msg += f" | Error: {error}"
    _append_log(log_path, level, msg)
    return log_path


def log_extraction_stats(
    run_id: str,
    brand_id: str,
    url: str,
    word_count: int,
    link_count: int,
    brand_type: str = None,
) -> Path:
    """Log webpage extraction word count and link count metrics."""
    log_path = _get_log_file(run_id, brand_id, brand_type=brand_type)
    msg = f"EXTRACTION STATS | URL: {url} | Words: {word_count} | Links: {link_count}"
    _append_log(log_path, "METRICS", msg)
    return log_path
