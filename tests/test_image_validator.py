"""Tests for image validation."""
import pytest
from src.validation.image_validator import (
    is_valid_url,
    validate_content_type,
    validate_file_size,
    validate_upload,
    normalize_url_list,
    validate_url_list,
    urls_to_csv,
    csv_to_urls,
    ValidationConfig,
)


class TestIsValidUrl:
    def test_valid_http(self):
        assert is_valid_url("http://example.com/image.jpg") is True

    def test_valid_https(self):
        assert is_valid_url("https://cdn.example.com/img/1.png") is True

    def test_no_scheme(self):
        assert is_valid_url("example.com/image.jpg") is False

    def test_ftp(self):
        assert is_valid_url("ftp://files.com/img.jpg") is False

    def test_empty(self):
        assert is_valid_url("") is False

    def test_none(self):
        assert is_valid_url(None) is False

    def test_whitespace_only(self):
        assert is_valid_url("   ") is False

    def test_with_spaces(self):
        assert is_valid_url("http://example.com/my image.jpg") is False

    def test_with_query_params(self):
        assert is_valid_url("https://cdn.com/img.jpg?w=100&h=100") is True

    def test_strips_whitespace(self):
        assert is_valid_url("  https://example.com/img.jpg  ") is True


class TestValidateContentType:
    def test_jpeg(self):
        assert validate_content_type("image/jpeg") is None

    def test_png(self):
        assert validate_content_type("image/png") is None

    def test_gif(self):
        assert validate_content_type("image/gif") is None

    def test_webp(self):
        assert validate_content_type("image/webp") is None

    def test_not_image(self):
        error = validate_content_type("application/pdf")
        assert error is not None
        assert "image/" in error

    def test_empty(self):
        error = validate_content_type("")
        assert error is not None

    def test_none(self):
        error = validate_content_type(None)
        assert error is not None
        assert "unknown" in error

    def test_case_insensitive(self):
        assert validate_content_type("IMAGE/JPEG") is None


class TestValidateFileSize:
    def test_valid_size(self):
        data = b"x" * 1024
        assert validate_file_size(data) is None

    def test_empty(self):
        error = validate_file_size(b"")
        assert error is not None
        assert "Empty" in error

    def test_too_large(self):
        config = ValidationConfig(max_file_mb=1)
        data = b"x" * (1024 * 1024 + 1)
        error = validate_file_size(data, config)
        assert error is not None
        assert "Maximum" in error

    def test_exact_limit(self):
        config = ValidationConfig(max_file_mb=1)
        data = b"x" * (1024 * 1024)
        assert validate_file_size(data, config) is None


class TestValidateUpload:
    def test_valid(self):
        errors = validate_upload(b"imagedata", "image/jpeg")
        assert errors == []

    def test_invalid_type(self):
        errors = validate_upload(b"data", "text/plain")
        assert len(errors) == 1

    def test_empty_file(self):
        errors = validate_upload(b"", "image/jpeg")
        assert len(errors) == 1

    def test_multiple_errors(self):
        errors = validate_upload(b"", "text/plain")
        assert len(errors) == 2


class TestNormalizeUrlList:
    def test_valid_urls(self):
        urls = ["https://a.com/1.jpg", "https://b.com/2.png"]
        assert normalize_url_list(urls) == urls

    def test_strips_whitespace(self):
        urls = ["  https://a.com/1.jpg  ", "https://b.com/2.png"]
        result = normalize_url_list(urls)
        assert result == ["https://a.com/1.jpg", "https://b.com/2.png"]

    def test_filters_invalid(self):
        urls = ["https://a.com/1.jpg", "not-a-url", "https://b.com/2.png"]
        result = normalize_url_list(urls)
        assert len(result) == 2

    def test_filters_empty(self):
        urls = ["https://a.com/1.jpg", "", "  ", None]
        result = normalize_url_list(urls)
        assert len(result) == 1

    def test_empty_list(self):
        assert normalize_url_list([]) == []


class TestValidateUrlList:
    def test_all_valid(self):
        urls = ["https://a.com/1.jpg", "https://b.com/2.png"]
        valid, errors = validate_url_list(urls)
        assert len(valid) == 2
        assert errors == []

    def test_some_invalid(self):
        urls = ["https://a.com/1.jpg", "bad-url"]
        valid, errors = validate_url_list(urls)
        assert len(valid) == 1
        assert len(errors) == 1

    def test_skips_empty(self):
        urls = ["https://a.com/1.jpg", "", "  "]
        valid, errors = validate_url_list(urls)
        assert len(valid) == 1
        assert errors == []


class TestUrlCsvConversion:
    def test_to_csv(self):
        urls = ["https://a.com/1.jpg", "https://b.com/2.png"]
        assert urls_to_csv(urls) == "https://a.com/1.jpg,https://b.com/2.png"

    def test_to_csv_empty(self):
        assert urls_to_csv([]) is None

    def test_from_csv(self):
        csv = "https://a.com/1.jpg,https://b.com/2.png"
        result = csv_to_urls(csv)
        assert len(result) == 2

    def test_from_csv_none(self):
        assert csv_to_urls(None) == []

    def test_from_csv_empty(self):
        assert csv_to_urls("") == []

    def test_roundtrip(self):
        urls = ["https://a.com/1.jpg", "https://b.com/2.png"]
        assert csv_to_urls(urls_to_csv(urls)) == urls


class TestValidationConfig:
    def test_defaults(self):
        cfg = ValidationConfig()
        assert cfg.max_file_mb == 10
        assert cfg.max_bytes == 10 * 1024 * 1024

    def test_custom(self):
        cfg = ValidationConfig(max_file_mb=5)
        assert cfg.max_bytes == 5 * 1024 * 1024
