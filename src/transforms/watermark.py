"""
Watermark overlay for brand protection and basic inpainting-based removal.
"""

from __future__ import annotations

from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont


_POSITIONS = {"bottom-right", "bottom-left", "center", "tiled"}


def _auto_font_size(image: Image.Image) -> int:
    return max(12, min(image.size) // 20)


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except OSError:
            return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def add_watermark(
    image: Image.Image,
    text: str,
    position: str = "bottom-right",
    opacity: float = 0.3,
    font_size: Optional[int] = None,
) -> Image.Image:
    """Overlay a semi-transparent text watermark on *image*."""
    if position not in _POSITIONS:
        raise ValueError(f"position must be one of {_POSITIONS}")

    base = image.copy().convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    fs = font_size or _auto_font_size(image)
    font = _get_font(fs)
    tw, th = _text_size(draw, text, font)
    alpha = int(255 * opacity)
    fill = (255, 255, 255, alpha)
    w, h = base.size
    margin = int(min(w, h) * 0.03)

    if position == "bottom-right":
        coords = [(w - tw - margin, h - th - margin)]
    elif position == "bottom-left":
        coords = [(margin, h - th - margin)]
    elif position == "center":
        coords = [((w - tw) // 2, (h - th) // 2)]
    elif position == "tiled":
        coords = []
        step_x = tw + margin * 4
        step_y = th + margin * 4
        for y in range(0, h, step_y):
            for x in range(0, w, step_x):
                coords.append((x, y))

    for x, y in coords:
        draw.text((x, y), text, font=font, fill=fill)

    composite = Image.alpha_composite(base, overlay)
    return composite.convert("RGB")


def remove_watermark_region(
    image: Image.Image,
    region: Tuple[int, int, int, int],
) -> Image.Image:
    """Basic watermark removal by inpainting a rectangular region.

    Uses a simple median-filter approach: the region is replaced by
    a blurred version of its neighbourhood.  Not production-grade but
    demonstrates the concept.
    """
    img = image.copy()
    left, top, right, bottom = region
    w, h = img.size
    pad = 10
    sample_left = max(0, left - pad)
    sample_top = max(0, top - pad)
    sample_right = min(w, right + pad)
    sample_bottom = min(h, bottom + pad)

    neighbourhood = img.crop((sample_left, sample_top, sample_right, sample_bottom))
    from PIL import ImageFilter
    blurred = neighbourhood.filter(ImageFilter.GaussianBlur(radius=5))

    paste_x = left - sample_left
    paste_y = top - sample_top
    patch = blurred.crop((paste_x, paste_y, paste_x + (right - left), paste_y + (bottom - top)))
    img.paste(patch, (left, top))
    return img
