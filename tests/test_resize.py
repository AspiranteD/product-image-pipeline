"""Tests for platform-specific resizing."""

import pytest
from PIL import Image

from src.transforms.resize import PlatformResizer, resize_for_platform, PlatformConfig


class TestPlatformResizer:
    def setup_method(self):
        self.resizer = PlatformResizer()

    def test_wallapop_square(self, sample_image):
        result = self.resizer.resize(sample_image, "wallapop")
        assert result.size == (1080, 1080)

    def test_ebay_dimensions(self, sample_image):
        result = self.resizer.resize(sample_image, "ebay")
        w, h = result.size
        assert w == 1600
        assert h == 1600

    def test_landscape_preserves_content(self, wide_image):
        result = self.resizer.resize(wide_image, "generic")
        assert result.size == (1200, 1200)

    def test_portrait_preserves_content(self, tall_image):
        result = self.resizer.resize(tall_image, "generic")
        assert result.size == (1200, 1200)

    def test_output_is_rgb(self, sample_image):
        result = self.resizer.resize(sample_image, "wallapop")
        assert result.mode == "RGB"

    def test_unknown_platform_raises(self, sample_image):
        with pytest.raises(ValueError, match="Unknown platform"):
            self.resizer.resize(sample_image, "nonexistent")

    def test_custom_config(self, sample_image):
        custom = {"custom": PlatformConfig(max_width=500, max_height=500)}
        resizer = PlatformResizer(extra_configs=custom)
        result = resizer.resize(sample_image, "custom")
        assert result.size == (500, 500)

    def test_supported_platforms(self):
        platforms = self.resizer.supported_platforms
        assert "wallapop" in platforms
        assert "ebay" in platforms


class TestResizeForPlatform:
    def test_convenience_wrapper(self, sample_image):
        result = resize_for_platform(sample_image, "wallapop")
        assert result.size == (1080, 1080)
