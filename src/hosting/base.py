"""Abstract base class for image hosting backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from PIL import Image


class ImageHost(ABC):
    """Minimal contract every hosting backend must implement."""

    @abstractmethod
    def upload(self, image: Image.Image, filename: str) -> str:
        """Persist *image* and return its public URL / path."""

    @abstractmethod
    def get_url(self, filename: str) -> str:
        """Return the public URL / path for an already-uploaded file."""

    @abstractmethod
    def delete(self, filename: str) -> bool:
        """Remove a previously uploaded file. Return True on success."""
