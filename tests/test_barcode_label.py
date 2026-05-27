"""Tests for barcode label generator."""
import pytest

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from src.label.barcode_label import build_barcode_label
from src.label.layout import LABEL_WIDTH_PX, LABEL_HEIGHT_PX

pytestmark = pytest.mark.skipif(not HAS_PIL, reason="Pillow not installed")


class TestBuildBarcodeLabel:
    def test_basic_generation(self):
        img = build_barcode_label("LPN-001")
        assert isinstance(img, Image.Image)
        assert img.width == LABEL_WIDTH_PX
        assert img.height == LABEL_HEIGHT_PX

    def test_portrait_orientation(self):
        img = build_barcode_label("TEST-123")
        assert img.width < img.height

    def test_custom_font_size(self):
        img = build_barcode_label("LPN-002", font_size=40)
        assert isinstance(img, Image.Image)

    def test_long_identifier(self):
        img = build_barcode_label("VERY-LONG-IDENTIFIER-12345678")
        assert isinstance(img, Image.Image)

    def test_short_identifier(self):
        img = build_barcode_label("A")
        assert isinstance(img, Image.Image)

    def test_numeric_identifier(self):
        img = build_barcode_label("123456789")
        assert isinstance(img, Image.Image)

    def test_white_background(self):
        img = build_barcode_label("LPN-003")
        corner_pixel = img.getpixel((0, 0))
        assert corner_pixel == (255, 255, 255)
