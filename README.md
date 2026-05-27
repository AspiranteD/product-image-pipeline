# Product Image Pipeline
> **Portfolio context:** Extracted from founder-led production systems — multi-marketplace inventory, orders, and warehouse execution. **[Full portfolio](https://github.com/AspiranteD)** · [aspiranted.github.io](https://aspiranted.github.io)

Image management and label generation library for e-commerce operations. Handles the full lifecycle: photo upload validation, URL management, shipping label generation with dynamic layouts, barcode labels, and carrier label processing.

Extracted from a production system processing 500+ labels/day across multiple carriers.

## Architecture

```
src/
├── validation/
│   └── image_validator.py      # URL validation, content type, size limits
├── label/
│   ├── layout.py               # Dynamic label layout engine (PIL)
│   ├── barcode_label.py        # Code128 barcode labels with rotation
│   └── downloader.py           # Carrier label download (PDF/image)
└── photo/
    └── photo_store.py          # Photo upload/retrieval abstraction
```

## Key Features

### Image Validation (`image_validator.py`)
- URL format validation (HTTP/HTTPS)
- Content type enforcement (`image/*`)
- Configurable file size limits
- URL list normalization (strip, filter, deduplicate)
- CSV conversion for comma-separated URL storage

### Label Layout Engine (`layout.py`)
- **Dynamic vertical layout** — content drawn top-to-bottom with cursor tracking
- **Multi-carrier support** — postal carriers (Correos) get QR codes, others get text codes
- **Carrier label embedding** — downloads and embeds carrier-provided labels (PDF/image)
- **Multi-item orders** — shows item list for bundle shipments
- **Configurable** — font sizes, margins, dimensions via `LayoutConfig`
- **Auto-crop** — starts with max height, crops to actual content

### Barcode Labels (`barcode_label.py`)
- **Landscape-to-portrait rotation** — built in 1180x720 (readable), rotated 90° for 62mm paper
- **Code128 barcodes** — scanner-friendly with configurable module dimensions
- **Large centered text** — identifier visible from distance

### Carrier Label Downloader (`downloader.py`)
- **PDF support** — converts first page to image via PyMuPDF at print DPI
- **Image support** — PNG, JPG, etc.
- **Auto-resize** — scales to target width maintaining aspect ratio
- **Injectable HTTP** — `http_get` parameter for testing without network

### Photo Store (`photo_store.py`)
- **Callback-driven** — database-agnostic via `save_photo_fn`, `list_photos_fn`, etc.
- **Upload validation** — content type + size checks before persistence
- **URL management** — normalize, validate, and persist image URL lists

## Design Decisions

| Decision | Rationale |
|---|---|
| PIL for label generation | Production-proven, handles fonts/QR/barcodes natively |
| Landscape build + 90° rotate | Content readable on label, fits 62mm paper physically |
| Postal QR vs carrier label | Correos machines scan QR reliably; GLS/InPost have their own labels |
| Dynamic height with crop | Different content amounts produce different label heights |
| Injectable HTTP/storage | Testing without network or database dependencies |

## Installation

```bash
pip install -r requirements.txt
```

## Running Tests

```bash
pytest tests/ -v
```

108 tests covering validation, layout generation, barcode labels, downloading, and photo storage.

## License

MIT
