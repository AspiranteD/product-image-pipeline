"""
Platform-specific image resizing with aspect-ratio preservation and
configurable background fill.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from PIL import Image


@dataclass(frozen=True)
class PlatformConfig:
    max_width: int
    max_height: int
    square_crop: bool = False
    fill_color: Tuple[int, int, int] = (255, 255, 255)
    output_format: str = "JPEG"


PLATFORM_CONFIGS: Dict[str, PlatformConfig] = {
    "wallapop": PlatformConfig(
        max_width=1080, max_height=1080, square_crop=True, output_format="JPEG",
    ),
    "ebay": PlatformConfig(
        max_width=1600, max_height=1600, square_crop=False, output_format="JPEG",
    ),
    "amazon": PlatformConfig(
        max_width=2000, max_height=2000, square_crop=False, output_format="JPEG",
    ),
    "generic": PlatformConfig(
        max_width=1200, max_height=1200, square_crop=False, output_format="JPEG",
    ),
}


class PlatformResizer:
    """Resize images according to marketplace-specific constraints."""

    def __init__(self, extra_configs: Optional[Dict[str, PlatformConfig]] = None):
        self.configs = {**PLATFORM_CONFIGS}
        if extra_configs:
            self.configs.update(extra_configs)

    def _square_crop(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        return img.crop((left, top, left + side, top + side))

    def _fit_with_fill(
        self, img: Image.Image, max_w: int, max_h: int, fill: Tuple[int, int, int],
    ) -> Image.Image:
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        canvas = Image.new("RGB", (max_w, max_h), fill)
        offset_x = (max_w - img.size[0]) // 2
        offset_y = (max_h - img.size[1]) // 2
        canvas.paste(img, (offset_x, offset_y))
        return canvas

    def resize(self, image: Image.Image, platform: str) -> Image.Image:
        cfg = self.configs.get(platform)
        if cfg is None:
            raise ValueError(f"Unknown platform: {platform}")

        img = image.copy()
        if img.mode != "RGB":
            img = img.convert("RGB")

        if cfg.square_crop:
            img = self._square_crop(img)

        return self._fit_with_fill(img, cfg.max_width, cfg.max_height, cfg.fill_color)

    @property
    def supported_platforms(self) -> list[str]:
        return list(self.configs.keys())


def resize_for_platform(image: Image.Image, platform: str) -> Image.Image:
    """Convenience wrapper around PlatformResizer."""
    return PlatformResizer().resize(image, platform)
