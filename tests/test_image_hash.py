"""Tests for perceptual hashing utilities."""

from PIL import Image

from src.utils.image_hash import perceptual_hash, hash_distance, are_similar


class TestPerceptualHash:
    def test_returns_hex_string(self, sample_image):
        h = perceptual_hash(sample_image)
        assert isinstance(h, str)
        assert len(h) == 16
        int(h, 16)

    def test_deterministic(self, sample_image):
        assert perceptual_hash(sample_image) == perceptual_hash(sample_image)

    def test_identical_images_same_hash(self):
        img1 = Image.new("RGB", (100, 100), (128, 128, 128))
        img2 = Image.new("RGB", (100, 100), (128, 128, 128))
        assert perceptual_hash(img1) == perceptual_hash(img2)

    def test_very_different_images(self):
        img1 = Image.new("RGB", (100, 100))
        pixels1 = [(x * 2, y * 2, 0) for y in range(100) for x in range(100)]
        img1.putdata(pixels1)

        img2 = Image.new("RGB", (100, 100))
        pixels2 = [(255 - x * 2, 0, y * 2) for y in range(100) for x in range(100)]
        img2.putdata(pixels2)

        h1 = perceptual_hash(img1)
        h2 = perceptual_hash(img2)
        assert hash_distance(h1, h2) > 0


class TestHashDistance:
    def test_same_hash_zero_distance(self):
        assert hash_distance("abcdef0123456789", "abcdef0123456789") == 0

    def test_known_distance(self):
        assert hash_distance("0000000000000000", "0000000000000001") == 1

    def test_max_distance(self):
        assert hash_distance("0000000000000000", "ffffffffffffffff") == 64


class TestAreSimilar:
    def test_identical_is_similar(self, sample_image):
        h = perceptual_hash(sample_image)
        assert are_similar(h, h)

    def test_threshold_boundary(self):
        h1 = "0000000000000000"
        h2 = "000000000000001f"  # 5 bits differ
        assert are_similar(h1, h2, threshold=5)
        assert not are_similar(h1, h2, threshold=4)

    def test_very_different_not_similar(self):
        assert not are_similar("0000000000000000", "ffffffffffffffff")
