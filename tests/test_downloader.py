"""Tests for carrier label downloader."""
import pytest

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from src.label.downloader import (
    download_label,
    _is_pdf,
    _resize_to_width,
)
from src.label.layout import LABEL_WIDTH_PX
import io

pytestmark = pytest.mark.skipif(not HAS_PIL, reason="Pillow not installed")


class TestIsPdf:
    def test_pdf_content_type(self):
        assert _is_pdf("application/pdf", "label.bin") is True

    def test_pdf_url_extension(self):
        assert _is_pdf("application/octet-stream", "label.pdf") is True

    def test_image_content_type(self):
        assert _is_pdf("image/png", "label.png") is False

    def test_pdf_in_content_type(self):
        assert _is_pdf("application/x-pdf", "label") is True

    def test_case_insensitive_url(self):
        assert _is_pdf("", "LABEL.PDF") is True


class TestResizeToWidth:
    def test_resize_larger(self):
        img = Image.new("RGB", (200, 400), "red")
        result = _resize_to_width(img, 400)
        assert result.width == 400
        assert result.height == 800

    def test_resize_smaller(self):
        img = Image.new("RGB", (800, 600), "blue")
        result = _resize_to_width(img, 400)
        assert result.width == 400
        assert result.height == 300

    def test_no_resize_needed(self):
        img = Image.new("RGB", (720, 500), "green")
        result = _resize_to_width(img, 720)
        assert result is img

    def test_maintains_aspect_ratio(self):
        img = Image.new("RGB", (300, 600), "white")
        result = _resize_to_width(img, 600)
        assert result.width == 600
        assert result.height == 1200


class TestDownloadLabel:
    def test_download_image(self):
        test_img = Image.new("RGB", (400, 300), "red")
        buf = io.BytesIO()
        test_img.save(buf, "PNG")
        raw = buf.getvalue()

        def mock_get(url, timeout):
            return raw, "image/png"

        result = download_label("https://example.com/label.png", http_get=mock_get)
        assert isinstance(result, Image.Image)
        assert result.width == LABEL_WIDTH_PX

    def test_download_jpeg(self):
        test_img = Image.new("RGB", (500, 400), "blue")
        buf = io.BytesIO()
        test_img.save(buf, "JPEG")
        raw = buf.getvalue()

        def mock_get(url, timeout):
            return raw, "image/jpeg"

        result = download_label("https://example.com/label.jpg", http_get=mock_get)
        assert isinstance(result, Image.Image)
        assert result.width == LABEL_WIDTH_PX

    def test_custom_target_width(self):
        test_img = Image.new("RGB", (400, 300), "green")
        buf = io.BytesIO()
        test_img.save(buf, "PNG")
        raw = buf.getvalue()

        def mock_get(url, timeout):
            return raw, "image/png"

        result = download_label(
            "https://example.com/label.png",
            target_width=500,
            http_get=mock_get,
        )
        assert result.width == 500

    def test_aspect_ratio_preserved(self):
        test_img = Image.new("RGB", (400, 800), "white")
        buf = io.BytesIO()
        test_img.save(buf, "PNG")
        raw = buf.getvalue()

        def mock_get(url, timeout):
            return raw, "image/png"

        result = download_label("https://example.com/label.png", http_get=mock_get)
        expected_height = int(800 * (LABEL_WIDTH_PX / 400))
        assert abs(result.height - expected_height) <= 1
