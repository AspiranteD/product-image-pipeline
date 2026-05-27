"""
Photo storage abstraction for product images.

Provides a framework-agnostic interface for:
  - Uploading photos with validation
  - Listing photos by item identifier
  - Retrieving photo data
  - Updating image URL lists on items

Uses callbacks for actual persistence (database, filesystem, etc.).
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Callable, Dict, Any

from src.validation.image_validator import (
    validate_upload,
    ValidationConfig,
    normalize_url_list,
    urls_to_csv,
    csv_to_urls,
)

logger = logging.getLogger(__name__)


@dataclass
class PhotoMetadata:
    """Metadata for a stored photo."""
    id: Optional[int] = None
    item_id: str = ""
    content_type: str = "image/jpeg"
    size_bytes: int = 0
    created_at: Optional[datetime] = None


@dataclass
class UploadResult:
    """Result of a photo upload attempt."""
    success: bool
    photo_id: Optional[int] = None
    errors: List[str] = field(default_factory=list)


class PhotoStore:
    """
    Manages photo upload, validation, and retrieval.

    Architecture: database-agnostic via callbacks:
      - save_photo_fn: (item_id, data, content_type) -> int (photo_id)
      - list_photos_fn: (item_id) -> List[PhotoMetadata]
      - get_photo_fn: (photo_id) -> Optional[bytes]
      - item_exists_fn: (item_id) -> bool
      - update_urls_fn: (item_id, csv_urls) -> bool
    """

    def __init__(
        self,
        config: Optional[ValidationConfig] = None,
        save_photo_fn: Optional[Callable] = None,
        list_photos_fn: Optional[Callable] = None,
        get_photo_fn: Optional[Callable] = None,
        item_exists_fn: Optional[Callable] = None,
        update_urls_fn: Optional[Callable] = None,
    ):
        self.config = config or ValidationConfig()
        self._save_photo = save_photo_fn
        self._list_photos = list_photos_fn
        self._get_photo = get_photo_fn
        self._item_exists = item_exists_fn
        self._update_urls = update_urls_fn

    def upload(
        self, item_id: str, data: bytes, content_type: str
    ) -> UploadResult:
        """
        Upload a photo for an item.

        Validates content type and size, checks item exists,
        then persists via callback.
        """
        item_id = (item_id or "").strip()
        if not item_id:
            return UploadResult(success=False, errors=["Item ID is required"])

        if self._item_exists and not self._item_exists(item_id):
            return UploadResult(
                success=False,
                errors=[f"Item not found: {item_id}"],
            )

        validation_errors = validate_upload(data, content_type, self.config)
        if validation_errors:
            return UploadResult(success=False, errors=validation_errors)

        if not self._save_photo:
            return UploadResult(
                success=False, errors=["No storage backend configured"]
            )

        try:
            photo_id = self._save_photo(item_id, data, content_type)
            return UploadResult(success=True, photo_id=photo_id)
        except Exception as e:
            logger.error("Error saving photo for %s: %s", item_id, e)
            return UploadResult(success=False, errors=[f"Storage error: {e}"])

    def list_photos(self, item_id: str) -> List[PhotoMetadata]:
        """List all photos for an item."""
        if not self._list_photos:
            return []
        try:
            return self._list_photos(item_id)
        except Exception as e:
            logger.error("Error listing photos for %s: %s", item_id, e)
            return []

    def get_photo(self, photo_id: int) -> Optional[bytes]:
        """Retrieve photo data by ID."""
        if not self._get_photo:
            return None
        try:
            return self._get_photo(photo_id)
        except Exception as e:
            logger.error("Error retrieving photo %d: %s", photo_id, e)
            return None

    def update_image_urls(
        self, item_id: str, urls: List[str]
    ) -> Dict[str, Any]:
        """
        Update the image URL list for an item.

        Validates URL formats, normalizes the list, and persists
        as comma-separated CSV.
        """
        item_id = (item_id or "").strip()
        if not item_id:
            return {"success": False, "error": "Item ID is required"}

        if self._item_exists and not self._item_exists(item_id):
            return {"success": False, "error": f"Item not found: {item_id}"}

        valid_urls = normalize_url_list(urls)
        csv_value = urls_to_csv(valid_urls)

        if self._update_urls:
            try:
                self._update_urls(item_id, csv_value)
            except Exception as e:
                return {"success": False, "error": f"Update error: {e}"}

        return {
            "success": True,
            "item_id": item_id,
            "url_count": len(valid_urls),
            "urls_csv": csv_value,
        }
