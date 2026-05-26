"""Local-filesystem image host — useful for development and testing."""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

from .base import ImageHost


class LocalImageHost(ImageHost):
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def upload(self, image: Image.Image, filename: str) -> str:
        path = self.directory / filename
        fmt = "JPEG" if filename.lower().endswith((".jpg", ".jpeg")) else "PNG"
        img = image.copy()
        if img.mode != "RGB" and fmt == "JPEG":
            img = img.convert("RGB")
        img.save(path, format=fmt)
        return str(path.resolve())

    def get_url(self, filename: str) -> str:
        path = self.directory / filename
        if not path.exists():
            raise FileNotFoundError(f"{filename} not found in {self.directory}")
        return str(path.resolve())

    def delete(self, filename: str) -> bool:
        path = self.directory / filename
        if path.exists():
            path.unlink()
            return True
        return False
