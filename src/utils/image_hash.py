"""
Perceptual hashing for duplicate / near-duplicate detection.

Uses the *average hash* algorithm — fast, no OpenCV dependency, pure PIL:
1. Resize to 8×8
2. Convert to grayscale
3. Compute the mean pixel value
4. Each pixel above the mean → 1, else → 0  →  64-bit hash
"""

from __future__ import annotations

from PIL import Image


def perceptual_hash(image: Image.Image) -> str:
    """Return a 16-character hex string (64-bit average hash)."""
    img = image.copy().convert("L").resize((8, 8), Image.LANCZOS)
    pixels = list(img.getdata())
    mean_val = sum(pixels) / len(pixels)
    bits = "".join("1" if p >= mean_val else "0" for p in pixels)
    return f"{int(bits, 2):016x}"


def hash_distance(hash1: str, hash2: str) -> int:
    """Hamming distance between two hex-encoded perceptual hashes."""
    val1 = int(hash1, 16)
    val2 = int(hash2, 16)
    return bin(val1 ^ val2).count("1")


def are_similar(hash1: str, hash2: str, threshold: int = 5) -> bool:
    """Two images are considered *similar* when their hash distance ≤ *threshold*."""
    return hash_distance(hash1, hash2) <= threshold
