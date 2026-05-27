"""
Carrier label downloader and converter.

Downloads shipping labels from carrier URLs and converts them
to PIL images suitable for thermal printing. Supports:
  - Direct images (PNG, JPG, etc.)
  - PDF documents (via PyMuPDF, first page only)
  - Automatic resizing to target width

Content type detection uses both HTTP headers and URL extension
as fallback.
"""
import io
import logging
from typing import Optional, Callable, Tuple

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from src.label.layout import LABEL_WIDTH_PX, DPI

logger = logging.getLogger(__name__)


def download_label(
    url: str,
    target_width: int = LABEL_WIDTH_PX,
    timeout: int = 30,
    http_get: Optional[Callable] = None,
) -> Image.Image:
    """
    Download a carrier label and return as a PIL Image.

    Supports PDF and image formats. The result is resized
    to target_width while maintaining aspect ratio.

    Args:
        url: URL of the carrier label
        target_width: Desired width in pixels
        timeout: HTTP timeout in seconds
        http_get: Optional injectable HTTP function for testing.
                  Signature: (url, timeout) -> (content_bytes, content_type)
    """
    if not HAS_PIL:
        raise ImportError("Pillow is required")

    raw, content_type = _fetch(url, timeout, http_get)
    is_pdf = _is_pdf(content_type, url)

    if is_pdf:
        img = _pdf_to_image(raw)
    else:
        img = Image.open(io.BytesIO(raw)).convert("RGB")

    img = _resize_to_width(img, target_width)
    return img


def _fetch(
    url: str, timeout: int, http_get: Optional[Callable]
) -> Tuple[bytes, str]:
    """Fetch raw bytes and content type from URL."""
    if http_get:
        return http_get(url, timeout)

    import requests
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    return response.content, content_type


def _is_pdf(content_type: str, url: str) -> bool:
    """Detect if the content is PDF by header or URL extension."""
    return "pdf" in content_type or url.lower().endswith(".pdf")


def _pdf_to_image(raw: bytes) -> Image.Image:
    """Convert first page of a PDF to an RGB PIL image at print DPI."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PyMuPDF (fitz) is required for PDF conversion. "
            "Install with: pip install PyMuPDF"
        )

    doc = fitz.open(stream=raw, filetype="pdf")
    page = doc[0]
    zoom = DPI / 72  # PDF uses 72 DPI base
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return img


def _resize_to_width(img: Image.Image, target_width: int) -> Image.Image:
    """Resize image to target width maintaining aspect ratio."""
    w, h = img.size
    if w == target_width:
        return img
    scale = target_width / w
    target_h = int(h * scale)
    return img.resize((target_width, target_h), Image.LANCZOS)
