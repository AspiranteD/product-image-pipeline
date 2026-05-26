"""Shared fixtures — programmatically generated test images."""

import pytest
from PIL import Image


@pytest.fixture
def sample_image() -> Image.Image:
    """256×256 RGB gradient image for deterministic testing."""
    img = Image.new("RGB", (256, 256))
    pixels = []
    for y in range(256):
        for x in range(256):
            pixels.append((x, y, (x + y) % 256))
    img.putdata(pixels)
    return img


@pytest.fixture
def small_image() -> Image.Image:
    """32×32 solid red image."""
    return Image.new("RGB", (32, 32), (200, 50, 50))


@pytest.fixture
def wide_image() -> Image.Image:
    """800×400 landscape image."""
    return Image.new("RGB", (800, 400), (100, 150, 200))


@pytest.fixture
def tall_image() -> Image.Image:
    """400×800 portrait image."""
    return Image.new("RGB", (400, 800), (200, 150, 100))
