"""
Orchestrator: download → transform → upload.

Coordinates anti-detection transforms, platform-specific resizing,
quality optimization, and hosting upload in a single pass.
"""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass, field
from io import BytesIO
from typing import Callable, Dict, List, Optional, Sequence

from PIL import Image

from ..hosting.base import ImageHost
from ..transforms.anti_detection import apply_anti_detection
from ..transforms.quality import optimize_quality
from ..transforms.resize import PlatformResizer
from ..utils.image_hash import perceptual_hash


@dataclass
class PipelineStats:
    processed: int = 0
    skipped: int = 0
    failed: int = 0


class ImagePipeline:
    """End-to-end image processing pipeline.

    Parameters
    ----------
    host : ImageHost
        Backend used to persist processed images.
    resizer : PlatformResizer | None
        Custom resizer; a default one is created when ``None``.
    anti_detection_seed : int | None
        Fixed seed for reproducible anti-detection transforms.
    target_size_kb : int
        JPEG file-size budget forwarded to the quality optimizer.
    extra_transforms : list[Callable]
        Additional ``(Image) -> Image`` callables appended after the
        built-in transform chain.
    """

    def __init__(
        self,
        host: ImageHost,
        resizer: Optional[PlatformResizer] = None,
        anti_detection_seed: Optional[int] = None,
        target_size_kb: int = 300,
        extra_transforms: Optional[List[Callable]] = None,
    ):
        self.host = host
        self.resizer = resizer or PlatformResizer()
        self.seed = anti_detection_seed
        self.target_size_kb = target_size_kb
        self.extra_transforms = extra_transforms or []
        self._hash_cache: set[str] = set()
        self.stats = PipelineStats()

    def _download(self, url_or_path: str) -> Image.Image:
        if url_or_path.startswith(("http://", "https://")):
            data = urllib.request.urlopen(url_or_path).read()
            return Image.open(BytesIO(data))
        return Image.open(url_or_path)

    def _is_duplicate(self, image: Image.Image) -> bool:
        h = perceptual_hash(image)
        if h in self._hash_cache:
            return True
        self._hash_cache.add(h)
        return False

    def process_image(
        self,
        image_or_url: str | Image.Image,
        platforms: Sequence[str] = ("generic",),
        apply_transforms: bool = True,
    ) -> Dict[str, str]:
        """Process a single image for each *platform* and return ``{platform: url}``."""
        if isinstance(image_or_url, str):
            img = self._download(image_or_url)
        else:
            img = image_or_url.copy()

        if self._is_duplicate(img):
            self.stats.skipped += 1
            return {}

        if apply_transforms:
            img = apply_anti_detection(img, seed=self.seed)
            for fn in self.extra_transforms:
                img = fn(img)

        results: Dict[str, str] = {}
        for platform in platforms:
            try:
                resized = self.resizer.resize(img, platform)
                optimized = optimize_quality(resized, target_size_kb=self.target_size_kb)
                filename = f"{platform}_{perceptual_hash(optimized)}.jpg"
                url = self.host.upload(optimized, filename)
                results[platform] = url
                self.stats.processed += 1
            except Exception:
                self.stats.failed += 1

        return results

    def process_batch(
        self,
        images: Sequence[str | Image.Image],
        platforms: Sequence[str] = ("generic",),
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict[str, str]]:
        """Process multiple images, calling *on_progress(current, total)* after each."""
        total = len(images)
        results = []
        for idx, item in enumerate(images):
            results.append(self.process_image(item, platforms=platforms))
            if on_progress:
                on_progress(idx + 1, total)
        return results
