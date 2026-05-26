"""
Subtle image transforms to defeat reverse image search while preserving
visual quality.  Every operation is individually imperceptible; combined
they alter enough pixel data to break perceptual matching algorithms.
"""

from __future__ import annotations

import hashlib
import random
from io import BytesIO
from typing import Optional

from PIL import Image, ImageEnhance, ImageFilter


def _seeded_rng(seed: Optional[int]) -> random.Random:
    return random.Random(seed)


def _strip_exif(img: Image.Image) -> Image.Image:
    """Return a clean copy with all EXIF / metadata removed."""
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))
    return clean


def _slight_rotation(img: Image.Image, rng: random.Random) -> Image.Image:
    angle = rng.uniform(0.1, 0.5) * rng.choice([-1, 1])
    return img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))


def _subtle_crop(img: Image.Image, rng: random.Random) -> Image.Image:
    w, h = img.size
    pct = rng.uniform(0.01, 0.03)
    left = int(w * pct)
    top = int(h * pct)
    right = w - int(w * pct)
    bottom = h - int(h * pct)
    cropped = img.crop((left, top, right, bottom))
    return cropped.resize((w, h), Image.LANCZOS)


def _brightness_contrast(img: Image.Image, rng: random.Random) -> Image.Image:
    brightness_factor = 1.0 + rng.uniform(-0.05, 0.05)
    contrast_factor = 1.0 + rng.uniform(-0.05, 0.05)
    img = ImageEnhance.Brightness(img).enhance(brightness_factor)
    img = ImageEnhance.Contrast(img).enhance(contrast_factor)
    return img


def _pixel_noise(img: Image.Image, rng: random.Random) -> Image.Image:
    """Add subtle per-pixel noise (±3 intensity levels)."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    pixels = list(img.getdata())
    noisy = []
    for r, g, b in pixels:
        nr = max(0, min(255, r + rng.randint(-3, 3)))
        ng = max(0, min(255, g + rng.randint(-3, 3)))
        nb = max(0, min(255, b + rng.randint(-3, 3)))
        noisy.append((nr, ng, nb))
    out = Image.new("RGB", img.size)
    out.putdata(noisy)
    return out


def _color_channel_shift(img: Image.Image, rng: random.Random) -> Image.Image:
    """Micro-shift individual color channels by 1-2 levels."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    r, g, b = img.split()
    r_shift = rng.randint(-2, 2)
    g_shift = rng.randint(-2, 2)
    b_shift = rng.randint(-2, 2)
    r = r.point(lambda p: max(0, min(255, p + r_shift)))
    g = g.point(lambda p: max(0, min(255, p + g_shift)))
    b = b.point(lambda p: max(0, min(255, p + b_shift)))
    return Image.merge("RGB", (r, g, b))


def apply_anti_detection(
    image: Image.Image,
    seed: Optional[int] = None,
) -> Image.Image:
    """Apply a deterministic chain of subtle transforms.

    With the same *seed* the output is identical, making the pipeline
    reproducible while still defeating reverse-image-search engines.
    """
    rng = _seeded_rng(seed)
    img = image.copy()
    if img.mode != "RGB":
        img = img.convert("RGB")

    img = _strip_exif(img)
    img = _slight_rotation(img, rng)
    img = _subtle_crop(img, rng)
    img = _brightness_contrast(img, rng)
    img = _pixel_noise(img, rng)
    img = _color_channel_shift(img, rng)

    return img


def get_transform_fingerprint(image: Image.Image) -> str:
    """Compute a SHA-256 fingerprint of raw pixel data."""
    buf = BytesIO()
    image.save(buf, format="PNG")
    return hashlib.sha256(buf.getvalue()).hexdigest()
