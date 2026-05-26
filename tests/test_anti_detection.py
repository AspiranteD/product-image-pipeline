"""Tests for anti-detection transforms."""

from PIL import Image

from src.transforms.anti_detection import apply_anti_detection, get_transform_fingerprint
from src.utils.image_hash import perceptual_hash, are_similar


class TestApplyAntiDetection:
    def test_returns_valid_image(self, sample_image):
        result = apply_anti_detection(sample_image, seed=42)
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"

    def test_preserves_dimensions(self, sample_image):
        result = apply_anti_detection(sample_image, seed=42)
        assert result.size == sample_image.size

    def test_changes_pixel_data(self, sample_image):
        result = apply_anti_detection(sample_image, seed=42)
        orig_pixels = list(sample_image.getdata())
        new_pixels = list(result.getdata())
        changed = sum(1 for a, b in zip(orig_pixels, new_pixels) if a != b)
        assert changed > 0, "anti-detection should alter pixel data"

    def test_deterministic_with_seed(self, sample_image):
        r1 = apply_anti_detection(sample_image, seed=123)
        r2 = apply_anti_detection(sample_image, seed=123)
        assert list(r1.getdata()) == list(r2.getdata())

    def test_different_seeds_differ(self, sample_image):
        r1 = apply_anti_detection(sample_image, seed=1)
        r2 = apply_anti_detection(sample_image, seed=2)
        assert list(r1.getdata()) != list(r2.getdata())

    def test_visual_similarity_preserved(self, sample_image):
        result = apply_anti_detection(sample_image, seed=42)
        h1 = perceptual_hash(sample_image)
        h2 = perceptual_hash(result)
        assert are_similar(h1, h2, threshold=10)

    def test_handles_rgba_input(self):
        rgba = Image.new("RGBA", (64, 64), (100, 100, 100, 255))
        result = apply_anti_detection(rgba, seed=1)
        assert result.mode == "RGB"


class TestTransformFingerprint:
    def test_returns_hex_string(self, sample_image):
        fp = get_transform_fingerprint(sample_image)
        assert isinstance(fp, str)
        int(fp, 16)  # must be valid hex

    def test_same_image_same_fingerprint(self, sample_image):
        assert get_transform_fingerprint(sample_image) == get_transform_fingerprint(sample_image)

    def test_different_image_different_fingerprint(self, sample_image, small_image):
        assert get_transform_fingerprint(sample_image) != get_transform_fingerprint(small_image)
