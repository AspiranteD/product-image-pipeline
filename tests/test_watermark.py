"""Tests for watermark overlay and removal."""

import pytest
from PIL import Image

from src.transforms.watermark import add_watermark, remove_watermark_region


class TestAddWatermark:
    def test_returns_valid_image(self, sample_image):
        result = add_watermark(sample_image, "Test")
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"

    def test_preserves_size(self, sample_image):
        result = add_watermark(sample_image, "Test")
        assert result.size == sample_image.size

    def test_modifies_pixels(self, sample_image):
        result = add_watermark(sample_image, "WATERMARK", position="center", opacity=0.8)
        orig = list(sample_image.convert("RGB").getdata())
        wm = list(result.getdata())
        changed = sum(1 for a, b in zip(orig, wm) if a != b)
        assert changed > 0

    def test_all_positions(self, sample_image):
        for pos in ("bottom-right", "bottom-left", "center", "tiled"):
            result = add_watermark(sample_image, "X", position=pos)
            assert result.size == sample_image.size

    def test_invalid_position_raises(self, sample_image):
        with pytest.raises(ValueError):
            add_watermark(sample_image, "X", position="top-middle")

    def test_custom_opacity(self, sample_image):
        low = add_watermark(sample_image, "Test", opacity=0.1)
        high = add_watermark(sample_image, "Test", opacity=0.9)
        assert low.size == high.size


class TestRemoveWatermarkRegion:
    def test_returns_valid_image(self, sample_image):
        region = (50, 50, 100, 100)
        result = remove_watermark_region(sample_image, region)
        assert isinstance(result, Image.Image)

    def test_modifies_region(self):
        img = Image.new("RGB", (200, 200), (128, 128, 128))
        pixels = list(img.getdata())
        for i in range(60 * 200 + 60, 60 * 200 + 140):
            pixels[i] = (255, 0, 0)
        img.putdata(pixels)

        region = (60, 60, 140, 61)
        result = remove_watermark_region(img, region)
        orig_crop = img.crop(region)
        result_crop = result.crop(region)
        assert list(orig_crop.getdata()) != list(result_crop.getdata())
