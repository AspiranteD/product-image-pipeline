"""
Quality optimization: JPEG compression targeting a file-size budget,
format conversion, and quality estimation.
"""

from __future__ import annotations

from io import BytesIO

from PIL import Image


def optimize_quality(
    image: Image.Image,
    target_size_kb: int = 200,
    min_quality: int = 60,
) -> Image.Image:
    """Binary-search for the highest JPEG quality that stays under *target_size_kb*.

    Returns a re-opened PIL Image so callers get the exact bytes that
    would be written to disk.
    """
    img = image.copy()
    if img.mode != "RGB":
        img = img.convert("RGB")

    lo, hi = min_quality, 95
    best_buf = BytesIO()

    while lo <= hi:
        mid = (lo + hi) // 2
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=mid, progressive=(mid >= 70))
        size_kb = buf.tell() / 1024

        if size_kb <= target_size_kb:
            best_buf = buf
            lo = mid + 1
        else:
            hi = mid - 1

    if best_buf.tell() == 0:
        best_buf = BytesIO()
        img.save(best_buf, format="JPEG", quality=min_quality, progressive=False)

    best_buf.seek(0)
    return Image.open(best_buf).copy()


def convert_format(
    image: Image.Image,
    target_format: str = "JPEG",
) -> Image.Image:
    """Convert image to *target_format* and return a re-opened copy."""
    img = image.copy()
    if img.mode in ("RGBA", "P") and target_format.upper() == "JPEG":
        img = img.convert("RGB")

    buf = BytesIO()
    img.save(buf, format=target_format)
    buf.seek(0)
    return Image.open(buf).copy()


def estimate_quality(image: Image.Image) -> int:
    """Heuristic quality score (0-100) based on JPEG artefact analysis.

    Compares original size to a high-quality JPEG encode; large
    compression ratios imply lower original quality.
    """
    img = image.copy()
    if img.mode != "RGB":
        img = img.convert("RGB")

    high_buf = BytesIO()
    img.save(high_buf, format="JPEG", quality=95)
    high_size = high_buf.tell()

    low_buf = BytesIO()
    img.save(low_buf, format="JPEG", quality=20)
    low_size = low_buf.tell()

    if high_size == 0:
        return 0

    ratio = low_size / high_size
    score = int((1 - ratio) * 100)
    return max(0, min(100, score))
