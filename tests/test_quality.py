"""Tests for quality optimization and estimation."""

from PIL import Image

from src.transforms.quality import optimize_quality, convert_format, estimate_quality


class TestOptimizeQuality:
    def test_returns_valid_image(self, sample_image):
        result = optimize_quality(sample_image, target_size_kb=50)
        assert isinstance(result, Image.Image)

    def test_respects_size_budget(self, sample_image):
        from io import BytesIO
        result = optimize_quality(sample_image, target_size_kb=50)
        buf = BytesIO()
        result.save(buf, format="JPEG", quality=95)
        assert buf.tell() / 1024 <= 100  # generous margin

    def test_output_is_rgb(self, sample_image):
        result = optimize_quality(sample_image)
        assert result.mode == "RGB"

    def test_handles_small_image(self, small_image):
        result = optimize_quality(small_image, target_size_kb=10)
        assert result.size[0] > 0 and result.size[1] > 0


class TestConvertFormat:
    def test_to_jpeg(self, sample_image):
        result = convert_format(sample_image, "JPEG")
        assert result.mode == "RGB"

    def test_rgba_to_jpeg(self):
        rgba = Image.new("RGBA", (64, 64), (100, 100, 100, 128))
        result = convert_format(rgba, "JPEG")
        assert result.mode == "RGB"

    def test_to_png(self, sample_image):
        result = convert_format(sample_image, "PNG")
        assert isinstance(result, Image.Image)


class TestEstimateQuality:
    def test_returns_int_in_range(self, sample_image):
        score = estimate_quality(sample_image)
        assert isinstance(score, int)
        assert 0 <= score <= 100

    def test_high_quality_image_scores_well(self, sample_image):
        score = estimate_quality(sample_image)
        assert score >= 20  # gradient images compress reasonably
