"""Tests for photo store."""
import pytest
from src.photo.photo_store import PhotoStore, PhotoMetadata, UploadResult
from src.validation.image_validator import ValidationConfig


def _store(**kwargs):
    """Create a PhotoStore with test callbacks."""
    defaults = {
        "item_exists_fn": lambda _: True,
        "save_photo_fn": lambda item_id, data, ct: 1,
        "list_photos_fn": lambda item_id: [],
        "get_photo_fn": lambda pid: b"fake",
        "update_urls_fn": lambda item_id, csv: True,
    }
    defaults.update(kwargs)
    return PhotoStore(**defaults)


class TestUpload:
    def test_successful_upload(self):
        store = _store()
        result = store.upload("LPN-001", b"imagedata", "image/jpeg")
        assert result.success is True
        assert result.photo_id == 1
        assert result.errors == []

    def test_empty_item_id(self):
        store = _store()
        result = store.upload("", b"data", "image/jpeg")
        assert result.success is False
        assert "required" in result.errors[0].lower()

    def test_item_not_found(self):
        store = _store(item_exists_fn=lambda _: False)
        result = store.upload("LPN-999", b"data", "image/jpeg")
        assert result.success is False
        assert "not found" in result.errors[0].lower()

    def test_invalid_content_type(self):
        store = _store()
        result = store.upload("LPN-001", b"data", "text/plain")
        assert result.success is False
        assert len(result.errors) == 1

    def test_empty_file(self):
        store = _store()
        result = store.upload("LPN-001", b"", "image/jpeg")
        assert result.success is False

    def test_file_too_large(self):
        config = ValidationConfig(max_file_mb=1)
        store = _store(config=config)
        big_data = b"x" * (1024 * 1024 + 1)
        result = store.upload("LPN-001", big_data, "image/jpeg")
        assert result.success is False

    def test_no_storage_backend(self):
        store = PhotoStore(
            item_exists_fn=lambda _: True,
            save_photo_fn=None,
        )
        result = store.upload("LPN-001", b"data", "image/jpeg")
        assert result.success is False
        assert "backend" in result.errors[0].lower()

    def test_storage_error(self):
        def fail(*args):
            raise RuntimeError("db down")

        store = _store(save_photo_fn=fail)
        result = store.upload("LPN-001", b"data", "image/jpeg")
        assert result.success is False

    def test_no_item_check(self):
        store = PhotoStore(
            save_photo_fn=lambda item_id, data, ct: 42,
            item_exists_fn=None,
        )
        result = store.upload("ANY", b"data", "image/jpeg")
        assert result.success is True
        assert result.photo_id == 42


class TestListPhotos:
    def test_returns_list(self):
        photos = [PhotoMetadata(id=1, item_id="A"), PhotoMetadata(id=2, item_id="A")]
        store = _store(list_photos_fn=lambda _: photos)
        result = store.list_photos("A")
        assert len(result) == 2

    def test_empty_list(self):
        store = _store()
        assert store.list_photos("X") == []

    def test_no_callback(self):
        store = PhotoStore()
        assert store.list_photos("X") == []

    def test_error_returns_empty(self):
        def fail(_):
            raise RuntimeError("error")

        store = _store(list_photos_fn=fail)
        assert store.list_photos("X") == []


class TestGetPhoto:
    def test_returns_data(self):
        store = _store(get_photo_fn=lambda _: b"imagedata")
        assert store.get_photo(1) == b"imagedata"

    def test_not_found(self):
        store = _store(get_photo_fn=lambda _: None)
        assert store.get_photo(999) is None

    def test_no_callback(self):
        store = PhotoStore()
        assert store.get_photo(1) is None

    def test_error_returns_none(self):
        def fail(_):
            raise RuntimeError("error")

        store = _store(get_photo_fn=fail)
        assert store.get_photo(1) is None


class TestUpdateImageUrls:
    def test_successful_update(self):
        store = _store()
        result = store.update_image_urls(
            "LPN-001", ["https://a.com/1.jpg", "https://b.com/2.png"]
        )
        assert result["success"] is True
        assert result["url_count"] == 2

    def test_empty_item_id(self):
        store = _store()
        result = store.update_image_urls("", ["https://a.com/1.jpg"])
        assert result["success"] is False

    def test_item_not_found(self):
        store = _store(item_exists_fn=lambda _: False)
        result = store.update_image_urls("X", ["https://a.com/1.jpg"])
        assert result["success"] is False

    def test_filters_invalid_urls(self):
        store = _store()
        result = store.update_image_urls(
            "LPN-001", ["https://a.com/1.jpg", "bad-url", "https://b.com/2.png"]
        )
        assert result["success"] is True
        assert result["url_count"] == 2

    def test_empty_urls(self):
        store = _store()
        result = store.update_image_urls("LPN-001", [])
        assert result["success"] is True
        assert result["url_count"] == 0
        assert result["urls_csv"] is None

    def test_update_error(self):
        def fail(*args):
            raise RuntimeError("db error")

        store = _store(update_urls_fn=fail)
        result = store.update_image_urls("LPN-001", ["https://a.com/1.jpg"])
        assert result["success"] is False


class TestPhotoMetadata:
    def test_defaults(self):
        pm = PhotoMetadata()
        assert pm.id is None
        assert pm.content_type == "image/jpeg"
        assert pm.size_bytes == 0


class TestUploadResult:
    def test_success(self):
        r = UploadResult(success=True, photo_id=1)
        assert r.success is True

    def test_failure(self):
        r = UploadResult(success=False, errors=["bad"])
        assert r.errors == ["bad"]
