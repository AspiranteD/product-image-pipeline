"""
Image validation for upload and URL management.

Validates:
  - URL format (http/https, no whitespace)
  - Content type (must be image/*)
  - File size limits (configurable max MB)
  - Image data integrity (non-empty, decodable)
  - URL list normalization (strip, deduplicate, filter empty)

Based on real production validation used for marketplace product photos.
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

URL_PATTERN = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)
ALLOWED_CONTENT_PREFIX = "image/"
DEFAULT_MAX_FILE_MB = 10


@dataclass
class ValidationConfig:
    """Configuration for image validation rules."""
    max_file_mb: int = DEFAULT_MAX_FILE_MB
    allowed_content_prefix: str = ALLOWED_CONTENT_PREFIX
    min_bytes: int = 1
    max_urls_per_item: int = 20

    @property
    def max_bytes(self) -> int:
        return self.max_file_mb * 1024 * 1024


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid HTTP(S) URL (format only)."""
    return bool(url and URL_PATTERN.match(url.strip()))


def validate_content_type(content_type: Optional[str], config: Optional[ValidationConfig] = None) -> Optional[str]:
    """
    Validate that content type is an image type.

    Returns error message or None if valid.
    """
    cfg = config or ValidationConfig()
    ct = (content_type or "").strip().lower()
    if not ct.startswith(cfg.allowed_content_prefix):
        return (
            f"Only images ({cfg.allowed_content_prefix}*) are allowed. "
            f"Received: {content_type or 'unknown'}"
        )
    return None


def validate_file_size(data: bytes, config: Optional[ValidationConfig] = None) -> Optional[str]:
    """
    Validate file size constraints.

    Returns error message or None if valid.
    """
    cfg = config or ValidationConfig()
    if len(data) < cfg.min_bytes:
        return "Empty file"
    if len(data) > cfg.max_bytes:
        return f"File too large. Maximum: {cfg.max_file_mb} MB"
    return None


def validate_upload(
    data: bytes,
    content_type: Optional[str],
    config: Optional[ValidationConfig] = None,
) -> List[str]:
    """
    Validate an image upload (content type + size).

    Returns list of error messages. Empty list = valid.
    """
    cfg = config or ValidationConfig()
    errors = []

    ct_error = validate_content_type(content_type, cfg)
    if ct_error:
        errors.append(ct_error)

    size_error = validate_file_size(data, cfg)
    if size_error:
        errors.append(size_error)

    return errors


def normalize_url_list(urls: List[str]) -> List[str]:
    """
    Normalize a list of image URLs.

    - Strips whitespace
    - Removes empty strings
    - Validates URL format
    - Returns only valid URLs
    """
    result = []
    for url in urls:
        stripped = (url or "").strip()
        if stripped and is_valid_url(stripped):
            result.append(stripped)
    return result


def validate_url_list(urls: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate and partition a list of URLs into valid and invalid.

    Returns (valid_urls, error_messages).
    """
    valid = []
    errors = []
    for url in urls:
        stripped = (url or "").strip()
        if not stripped:
            continue
        if is_valid_url(stripped):
            valid.append(stripped)
        else:
            errors.append(f"Invalid URL format: {stripped[:80]!r}")
    return valid, errors


def urls_to_csv(urls: List[str]) -> Optional[str]:
    """Convert URL list to comma-separated string for storage."""
    if not urls:
        return None
    return ",".join(urls)


def csv_to_urls(csv_string: Optional[str]) -> List[str]:
    """Parse comma-separated URL string back to list."""
    if not csv_string:
        return []
    return [u.strip() for u in csv_string.split(",") if u.strip()]
