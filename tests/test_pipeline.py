"""Tests for the image pipeline orchestrator."""

from unittest.mock import MagicMock

from PIL import Image

from src.hosting.local_host import LocalImageHost
from src.hosting.cdn_host import CDNImageHost
from src.pipeline.image_pipeline import ImagePipeline


def _make_image(color=(100, 150, 200)):
    return Image.new("RGB", (256, 256), color)


class TestImagePipeline:
    def test_process_single_image(self, tmp_path):
        host = LocalImageHost(tmp_path / "output")
        pipe = ImagePipeline(host, anti_detection_seed=42)
        result = pipe.process_image(_make_image(), platforms=["generic"])
        assert "generic" in result
        assert pipe.stats.processed == 1

    def test_process_batch(self, tmp_path):
        host = LocalImageHost(tmp_path / "output")
        pipe = ImagePipeline(host, anti_detection_seed=42)
        images = [_make_image((i * 30, i * 20, i * 10)) for i in range(3)]
        results = pipe.process_batch(images, platforms=["wallapop"])
        assert len(results) == 3

    def test_duplicate_skipping(self, tmp_path):
        host = LocalImageHost(tmp_path / "output")
        pipe = ImagePipeline(host, anti_detection_seed=42)
        img = _make_image()
        pipe.process_image(img, platforms=["generic"])
        pipe.process_image(img, platforms=["generic"])
        assert pipe.stats.skipped == 1

    def test_multi_platform(self, tmp_path):
        host = LocalImageHost(tmp_path / "output")
        pipe = ImagePipeline(host, anti_detection_seed=42)
        result = pipe.process_image(_make_image(), platforms=["wallapop", "ebay"])
        assert "wallapop" in result
        assert "ebay" in result

    def test_progress_callback(self, tmp_path):
        host = LocalImageHost(tmp_path / "output")
        pipe = ImagePipeline(host, anti_detection_seed=42)
        progress = []
        images = [_make_image((i * 50, 0, 0)) for i in range(3)]
        pipe.process_batch(images, platforms=["generic"], on_progress=lambda c, t: progress.append((c, t)))
        assert progress == [(1, 3), (2, 3), (3, 3)]

    def test_cdn_host_integration(self):
        host = CDNImageHost("https://cdn.example.com/images", "test-key")
        pipe = ImagePipeline(host, anti_detection_seed=42)
        result = pipe.process_image(_make_image(), platforms=["generic"])
        assert "generic" in result
        url = result["generic"]
        assert url.startswith("https://cdn.example.com/images/")

    def test_stats_tracking(self, tmp_path):
        host = LocalImageHost(tmp_path / "output")
        pipe = ImagePipeline(host, anti_detection_seed=42)

        img1 = Image.new("RGB", (256, 256))
        img1.putdata([(x, y, 0) for y in range(256) for x in range(256)])

        img2 = Image.new("RGB", (256, 256))
        img2.putdata([(0, x, y) for y in range(256) for x in range(256)])

        pipe.process_image(img1, platforms=["generic"])
        pipe.process_image(img2, platforms=["wallapop", "ebay"])
        assert pipe.stats.processed == 3
        assert pipe.stats.failed == 0

    def test_extra_transforms(self, tmp_path):
        def flip_horizontal(img):
            return img.transpose(Image.FLIP_LEFT_RIGHT)

        host = LocalImageHost(tmp_path / "output")
        pipe = ImagePipeline(host, anti_detection_seed=42, extra_transforms=[flip_horizontal])
        result = pipe.process_image(_make_image(), platforms=["generic"])
        assert "generic" in result
