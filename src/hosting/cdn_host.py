"""CDN image host — interface for uploading to a remote CDN.

The actual HTTP calls are stubbed so the project stays dependency-light;
a real implementation would use ``httpx`` or ``requests``.
"""

from __future__ import annotations

from io import BytesIO
from typing import Optional

from PIL import Image

from .base import ImageHost


class CDNImageHost(ImageHost):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._uploaded: dict[str, bytes] = {}

    def _build_url(self, filename: str) -> str:
        return f"{self.base_url}/{filename}"

    def upload(self, image: Image.Image, filename: str) -> str:
        buf = BytesIO()
        fmt = "JPEG" if filename.lower().endswith((".jpg", ".jpeg")) else "PNG"
        img = image.copy()
        if img.mode != "RGB" and fmt == "JPEG":
            img = img.convert("RGB")
        img.save(buf, format=fmt)
        self._uploaded[filename] = buf.getvalue()
        return self._build_url(filename)

    def get_url(self, filename: str) -> str:
        if filename not in self._uploaded:
            raise FileNotFoundError(f"{filename} not uploaded")
        return self._build_url(filename)

    def delete(self, filename: str) -> bool:
        if filename in self._uploaded:
            del self._uploaded[filename]
            return True
        return False
