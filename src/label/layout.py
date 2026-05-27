"""
Dynamic label layout engine for thermal printers.

Generates shipping labels with dynamic content:
  - Title section (carrier name, centered)
  - Data fields (LPN, item name, weight)
  - Multi-item lists for bundle orders
  - QR codes for postal carriers
  - Carrier label embedding (downloaded PDF/image)
  - Barcode text fallback

Layout adapts to content: starts with maximum height and crops
to actual content at the end.

Designed for Brother QL-700 (62mm x 100mm @ 300 DPI).
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

LABEL_WIDTH_PX = 720
LABEL_HEIGHT_PX = 1180
DPI = 300
MAX_WORK_HEIGHT = 2400

POSTAL_CARRIERS = frozenset({"CORREOS", "CORREOS_EXPRESS"})


@dataclass
class LabelData:
    """Data needed to generate a shipping label."""
    lpn: Optional[str] = None
    item_name: Optional[str] = None
    weight_kg: float = 0.0
    carrier_name: str = "SHIPPING"
    carrier_code: str = ""
    shipping_code: Optional[str] = None
    order_id: Optional[str] = None
    items: List[Dict[str, Any]] = field(default_factory=list)
    max_item_name_len: int = 26

    @property
    def is_postal(self) -> bool:
        return self.carrier_code.upper() in POSTAL_CARRIERS

    @property
    def display_name(self) -> str:
        name = self.item_name or self.order_id or ""
        if len(name) > self.max_item_name_len:
            return name[: self.max_item_name_len - 3] + "..."
        return name

    @property
    def is_multi_item(self) -> bool:
        return len(self.items) > 1


@dataclass
class LayoutConfig:
    """Configuration for label layout."""
    width: int = LABEL_WIDTH_PX
    max_height: int = LABEL_HEIGHT_PX
    margin: int = 24
    title_font_size: int = 52
    field_label_font_size: int = 18
    field_value_font_size: int = 32
    name_font_size: int = 24
    small_font_size: int = 20
    code_font_size: int = 24
    max_items_shown: int = 4
    separator_width: int = 3
    qr_box_size: int = 12
    qr_border: int = 2


def _get_font(size: int, bold: bool = False):
    """Load a TrueType font with fallback to default."""
    if not HAS_PIL:
        return None
    for name in (
        ("arialbd.ttf" if bold else "arial.ttf"),
        ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


class LabelLayoutEngine:
    """
    Generates label images with dynamic content layout.

    Content is drawn top-to-bottom, tracking the Y cursor position.
    The final image is cropped to actual content height.
    """

    def __init__(self, config: Optional[LayoutConfig] = None):
        if not HAS_PIL:
            raise ImportError("Pillow is required for label generation")
        self.config = config or LayoutConfig()
        self._load_fonts()

    def _load_fonts(self):
        c = self.config
        self.font_title = _get_font(c.title_font_size, bold=True)
        self.font_label = _get_font(c.field_label_font_size)
        self.font_value = _get_font(c.field_value_font_size, bold=True)
        self.font_name = _get_font(c.name_font_size)
        self.font_small = _get_font(c.small_font_size)
        self.font_code = _get_font(c.code_font_size, bold=True)

    def build(
        self,
        data: LabelData,
        carrier_label: Optional[Any] = None,
    ) -> Image.Image:
        """
        Build a complete shipping label image.

        Args:
            data: Label content data
            carrier_label: Optional pre-downloaded carrier label (PIL Image)
        """
        c = self.config
        img = Image.new("RGB", (c.width, MAX_WORK_HEIGHT), "white")
        draw = ImageDraw.Draw(img)

        y = 20

        y = self._draw_title(draw, data, y)
        y = self._draw_separator(draw, y)
        y = self._draw_data_fields(draw, data, y)

        if data.is_multi_item:
            y = self._draw_item_list(draw, data, y)

        y += 8
        y = self._draw_separator(draw, y)

        y = self._draw_code_section(draw, img, data, carrier_label, y)

        final_h = min(y + 30, c.max_height)
        return img.crop((0, 0, c.width, final_h))

    def _draw_title(self, draw: ImageDraw.Draw, data: LabelData, y: int) -> int:
        c = self.config
        title = "CORREOS" if data.is_postal else data.carrier_name
        title = title.upper()
        bbox = draw.textbbox((0, 0), title, font=self.font_title)
        tw = bbox[2] - bbox[0]
        draw.text(((c.width - tw) // 2, y), title, fill="black", font=self.font_title)
        return y + 70

    def _draw_separator(self, draw: ImageDraw.Draw, y: int) -> int:
        c = self.config
        draw.line(
            [(c.margin, y), (c.width - c.margin, y)],
            fill="black",
            width=c.separator_width,
        )
        return y + 16

    def _draw_field(
        self, draw: ImageDraw.Draw, label: str, value: str, y: int,
        value_font=None,
    ) -> int:
        c = self.config
        vf = value_font or self.font_value

        lbox = draw.textbbox((0, 0), label, font=self.font_label)
        draw.text(
            ((c.width - (lbox[2] - lbox[0])) // 2, y),
            label, fill="#555555", font=self.font_label,
        )

        vbox = draw.textbbox((0, 0), str(value), font=vf)
        draw.text(
            ((c.width - (vbox[2] - vbox[0])) // 2, y + 22),
            str(value), fill="black", font=vf,
        )
        return y + 62

    def _draw_data_fields(self, draw: ImageDraw.Draw, data: LabelData, y: int) -> int:
        lpn_text = data.lpn or "(multi)"
        y = self._draw_field(draw, "LPN", lpn_text, y)
        y = self._draw_field(draw, "ITEM", data.display_name, y, value_font=self.font_name)
        y = self._draw_field(draw, "WEIGHT", f"{data.weight_kg:.2f} kg", y)
        return y

    def _draw_item_list(self, draw: ImageDraw.Draw, data: LabelData, y: int) -> int:
        c = self.config
        y += 4
        draw.text(
            (c.margin, y),
            f"Items ({len(data.items)}):",
            fill="black", font=self.font_small,
        )
        y += 28
        for item in data.items[: c.max_items_shown]:
            lpn = item.get("lpn", "?")
            draw.text((c.margin + 10, y), str(lpn), fill="black", font=self.font_small)
            y += 26
        return y

    def _draw_code_section(
        self, draw: ImageDraw.Draw, img: Image.Image,
        data: LabelData, carrier_label: Optional[Any], y: int,
    ) -> int:
        c = self.config

        if carrier_label is not None:
            return self._embed_carrier_label(img, carrier_label, y)

        if data.is_postal and data.shipping_code:
            return self._draw_qr_code(draw, img, data.shipping_code, y)

        if data.shipping_code:
            return self._draw_text_code(draw, data.shipping_code, y)

        return y

    def _embed_carrier_label(self, img: Image.Image, carrier_label: Any, y: int) -> int:
        c = self.config
        cl_w, cl_h = carrier_label.size
        available_w = c.width - 2 * c.margin
        scale = available_w / cl_w
        new_w = int(cl_w * scale)
        new_h = int(cl_h * scale)
        resized = carrier_label.resize((new_w, new_h), Image.LANCZOS)
        x_pos = (c.width - new_w) // 2
        img.paste(resized, (x_pos, y))
        return y + new_h + 10

    def _draw_qr_code(self, draw: ImageDraw.Draw, img: Image.Image, code: str, y: int) -> int:
        c = self.config
        try:
            import qrcode
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=c.qr_box_size,
                border=c.qr_border,
            )
            qr.add_data(code)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

            available_w = c.width - 2 * c.margin
            qr_w, qr_h = qr_img.size
            scale = available_w / qr_w
            qr_img = qr_img.resize(
                (int(qr_w * scale), int(qr_h * scale)), Image.LANCZOS
            )
            x_pos = (c.width - qr_img.width) // 2
            img.paste(qr_img, (x_pos, y))
            y += qr_img.height + 12
        except ImportError:
            pass

        bbox = draw.textbbox((0, 0), code, font=self.font_code)
        tw = bbox[2] - bbox[0]
        draw.text(((c.width - tw) // 2, y), code, fill="black", font=self.font_code)
        return y + (bbox[3] - bbox[1]) + 10

    def _draw_text_code(self, draw: ImageDraw.Draw, code: str, y: int) -> int:
        c = self.config
        font = _get_font(28, bold=True)
        bbox = draw.textbbox((0, 0), code, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((c.width - tw) // 2, y), code, fill="black", font=font)
        return y + (bbox[3] - bbox[1]) + 10
