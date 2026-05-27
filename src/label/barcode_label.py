"""
Barcode label generator for item identification.

Generates landscape-oriented labels with:
  - Large centered identifier text
  - Code128 barcode for scanner readability
  - Automatic rotation for thermal printer paper orientation

The image is built in landscape (1180x720) for visual readability,
then rotated 90 CW to fit the 62mm-wide thermal paper physically.
"""
import logging

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from src.label.layout import LABEL_WIDTH_PX, LABEL_HEIGHT_PX, _get_font

logger = logging.getLogger(__name__)


def build_barcode_label(
    identifier: str,
    font_size: int = 56,
    barcode_module_width: float = 0.5,
    barcode_module_height: int = 25,
) -> Image.Image:
    """
    Generate a landscape barcode label for an item identifier.

    The label contains:
    1. Large centered text with the identifier
    2. Code128 barcode below

    Built in landscape (1180x720), then rotated to portrait (720x1180)
    for the thermal printer.
    """
    if not HAS_PIL:
        raise ImportError("Pillow is required for label generation")

    W = LABEL_HEIGHT_PX  # 1180 px (100 mm) used as visual width
    H = LABEL_WIDTH_PX   # 720 px (62 mm) used as visual height
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    font_id = _get_font(font_size, bold=True)
    margin = 30

    id_bbox = draw.textbbox((0, 0), identifier, font=font_id)
    id_tw = id_bbox[2] - id_bbox[0]
    id_th = id_bbox[3] - id_bbox[1]
    id_y = margin
    draw.text(((W - id_tw) // 2, id_y), identifier, fill="black", font=font_id)

    barcode_top = id_y + id_th + 20

    try:
        import barcode as python_barcode
        from barcode.writer import ImageWriter

        code128 = python_barcode.get("code128", identifier, writer=ImageWriter())
        barcode_img = code128.render({
            "module_width": barcode_module_width,
            "module_height": barcode_module_height,
            "font_size": 14,
            "text_distance": 6,
            "quiet_zone": 4,
        })
        barcode_img = barcode_img.convert("RGB")

        available_w = W - 2 * margin
        available_h = H - barcode_top - margin
        bw, bh = barcode_img.size
        scale = min(available_w / bw, available_h / bh)
        new_w = int(bw * scale)
        new_h = int(bh * scale)
        barcode_img = barcode_img.resize((new_w, new_h), Image.LANCZOS)

        x_pos = (W - new_w) // 2
        img.paste(barcode_img, (x_pos, barcode_top))
    except ImportError:
        logger.warning("python-barcode not installed, skipping barcode for %s", identifier)
    except Exception as e:
        logger.warning("Could not generate barcode for %s: %s", identifier, e)

    img = img.transpose(Image.ROTATE_270)
    return img
