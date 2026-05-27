"""Tests for label layout engine."""
import pytest
from unittest.mock import patch, MagicMock

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from src.label.layout import (
    LabelData,
    LayoutConfig,
    LabelLayoutEngine,
    LABEL_WIDTH_PX,
    LABEL_HEIGHT_PX,
    POSTAL_CARRIERS,
    _get_font,
)

pytestmark = pytest.mark.skipif(not HAS_PIL, reason="Pillow not installed")


class TestLabelData:
    def test_defaults(self):
        data = LabelData()
        assert data.lpn is None
        assert data.carrier_name == "SHIPPING"
        assert data.is_postal is False
        assert data.is_multi_item is False

    def test_postal_detection_correos(self):
        data = LabelData(carrier_code="CORREOS")
        assert data.is_postal is True

    def test_postal_detection_correos_express(self):
        data = LabelData(carrier_code="correos_express")
        assert data.is_postal is True

    def test_postal_detection_gls(self):
        data = LabelData(carrier_code="GLS")
        assert data.is_postal is False

    def test_display_name_truncation(self):
        data = LabelData(item_name="A" * 50, max_item_name_len=26)
        assert len(data.display_name) == 26
        assert data.display_name.endswith("...")

    def test_display_name_short(self):
        data = LabelData(item_name="Short name")
        assert data.display_name == "Short name"

    def test_display_name_fallback_to_order(self):
        data = LabelData(item_name=None, order_id="ORD-123")
        assert data.display_name == "ORD-123"

    def test_multi_item(self):
        data = LabelData(items=[{"lpn": "A"}, {"lpn": "B"}])
        assert data.is_multi_item is True

    def test_single_item(self):
        data = LabelData(items=[{"lpn": "A"}])
        assert data.is_multi_item is False


class TestLayoutConfig:
    def test_defaults(self):
        cfg = LayoutConfig()
        assert cfg.width == LABEL_WIDTH_PX
        assert cfg.max_height == LABEL_HEIGHT_PX
        assert cfg.margin == 24

    def test_custom(self):
        cfg = LayoutConfig(width=500, margin=10)
        assert cfg.width == 500
        assert cfg.margin == 10


class TestGetFont:
    def test_returns_font(self):
        font = _get_font(24)
        assert font is not None

    def test_bold_font(self):
        font = _get_font(24, bold=True)
        assert font is not None


class TestLabelLayoutEngine:
    def test_basic_label(self):
        engine = LabelLayoutEngine()
        data = LabelData(
            lpn="LPN-001",
            item_name="Test Item",
            weight_kg=1.5,
            carrier_name="GLS",
        )
        img = engine.build(data)
        assert isinstance(img, Image.Image)
        assert img.width == LABEL_WIDTH_PX
        assert img.height <= LABEL_HEIGHT_PX

    def test_postal_label_with_code(self):
        engine = LabelLayoutEngine()
        data = LabelData(
            lpn="LPN-002",
            item_name="Postal Item",
            weight_kg=0.5,
            carrier_name="Correos",
            carrier_code="CORREOS",
            shipping_code="PK123456789ES",
        )
        img = engine.build(data)
        assert isinstance(img, Image.Image)

    def test_multi_item_label(self):
        engine = LabelLayoutEngine()
        data = LabelData(
            lpn=None,
            item_name="Bundle",
            weight_kg=3.0,
            carrier_name="SEUR",
            items=[
                {"lpn": "LPN-A"},
                {"lpn": "LPN-B"},
                {"lpn": "LPN-C"},
            ],
        )
        img = engine.build(data)
        assert isinstance(img, Image.Image)

    def test_with_carrier_label(self):
        engine = LabelLayoutEngine()
        carrier = Image.new("RGB", (400, 300), "gray")
        data = LabelData(
            lpn="LPN-003",
            item_name="With Carrier",
            weight_kg=2.0,
            carrier_name="InPost",
        )
        img = engine.build(data, carrier_label=carrier)
        assert isinstance(img, Image.Image)

    def test_text_code_fallback(self):
        engine = LabelLayoutEngine()
        data = LabelData(
            lpn="LPN-004",
            carrier_name="GLS",
            carrier_code="GLS",
            shipping_code="GLS-12345",
        )
        img = engine.build(data)
        assert isinstance(img, Image.Image)

    def test_no_code_no_label(self):
        engine = LabelLayoutEngine()
        data = LabelData(lpn="LPN-005", carrier_name="Unknown")
        img = engine.build(data)
        assert isinstance(img, Image.Image)

    def test_custom_config(self):
        cfg = LayoutConfig(width=500, max_height=800, margin=10)
        engine = LabelLayoutEngine(config=cfg)
        data = LabelData(lpn="LPN-006", weight_kg=1.0)
        img = engine.build(data)
        assert img.width == 500
        assert img.height <= 800
