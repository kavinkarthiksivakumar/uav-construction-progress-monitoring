"""
Module 1: Image Validator
IEEE M.Tech Project — UAV Image Acquisition

Validates uploaded UAV images for:
  - Supported file extension
  - File readability / non-corruption
  - Minimum resolution
  - Maximum file size
  - Duplicate detection (MD5 hash)
"""

import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Set

logger = logging.getLogger("module1.validator")

# Supported extensions (lowercase)
ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
MIN_RESOLUTION_PX: int = 100          # Minimum width AND height
MAX_FILE_SIZE_MB:  float = 100.0      # Maximum file size in MB


# ─────────────────────────────────────────────────────────────────
# Hash Utility
# ─────────────────────────────────────────────────────────────────

def compute_md5(file_path: Path) -> str:
    """
    Compute the MD5 hash of a file for duplicate detection.

    Args:
        file_path: Path to the file.

    Returns:
        Hex-string MD5 digest.
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# ─────────────────────────────────────────────────────────────────
# Single File Validation
# ─────────────────────────────────────────────────────────────────

def validate_image(
    file_path: Path,
    seen_hashes: Dict[str, str],
    max_file_size_mb: float = MAX_FILE_SIZE_MB,
    min_resolution:   int   = MIN_RESOLUTION_PX,
) -> Dict[str, Any]:
    """
    Run all validation checks on a single image file.

    Checks performed (in order):
        1. Extension check
        2. File size check
        3. Readability / corruption check (via PIL)
        4. Resolution check
        5. Duplicate detection (MD5)

    Args:
        file_path:        Absolute path to the image file.
        seen_hashes:      Mutable dict {md5_hash: filename} updated in place.
        max_file_size_mb: Maximum allowed file size in MB.
        min_resolution:   Minimum allowed width and height in pixels.

    Returns:
        Validation result dictionary with keys:
          - valid (bool)
          - errors (list[str])
          - warnings (list[str])
          - width, height (int)
          - file_size_mb (float)
          - md5 (str)
          - duplicate_of (str | None)
    """
    from PIL import Image, UnidentifiedImageError

    result: Dict[str, Any] = {
        "valid":       True,
        "errors":      [],
        "warnings":    [],
        "width":       0,
        "height":      0,
        "file_size_mb": 0.0,
        "md5":         "",
        "duplicate_of": None,
    }

    # ── 1. Extension Check ──────────────────────────────────────
    suffix = file_path.suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        result["valid"] = False
        result["errors"].append(
            f"Unsupported extension '{suffix}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
        logger.warning("Validation FAILED (extension): %s", file_path.name)
        return result  # Cannot continue — not an image

    # ── 2. File Size Check ──────────────────────────────────────
    size_bytes = file_path.stat().st_size
    size_mb    = size_bytes / (1024 * 1024)
    result["file_size_mb"] = round(size_mb, 3)

    if size_mb > max_file_size_mb:
        result["valid"] = False
        result["errors"].append(
            f"File too large: {size_mb:.1f} MB (max {max_file_size_mb} MB)"
        )

    if size_bytes == 0:
        result["valid"] = False
        result["errors"].append("File is empty (0 bytes)")
        return result

    # ── 3. Readability / Corruption Check ──────────────────────
    try:
        with Image.open(file_path) as img:
            img.verify()  # Detects most corruptions
    except UnidentifiedImageError:
        result["valid"] = False
        result["errors"].append("File cannot be identified as an image (possibly corrupted)")
        logger.warning("Validation FAILED (unreadable): %s", file_path.name)
        return result
    except Exception as exc:
        result["valid"] = False
        result["errors"].append(f"Image verification failed: {exc}")
        return result

    # Reopen for property checks (verify() closes the file)
    try:
        with Image.open(file_path) as img:
            img.load()  # Force full decode
            width, height = img.size
            result["width"]  = width
            result["height"] = height
    except Exception as exc:
        result["valid"] = False
        result["errors"].append(f"Cannot read image data: {exc}")
        return result

    # ── 4. Resolution Check ─────────────────────────────────────
    if width < min_resolution or height < min_resolution:
        result["valid"] = False
        result["errors"].append(
            f"Resolution too low: {width}×{height}px (min {min_resolution}×{min_resolution}px)"
        )

    # ── 5. Duplicate Detection ──────────────────────────────────
    md5 = compute_md5(file_path)
    result["md5"] = md5

    if md5 in seen_hashes:
        result["valid"] = False
        result["duplicate_of"] = seen_hashes[md5]
        result["errors"].append(
            f"Duplicate image — identical to '{seen_hashes[md5]}'"
        )
        logger.warning(
            "Validation FAILED (duplicate): %s is a duplicate of %s",
            file_path.name, seen_hashes[md5]
        )
    else:
        seen_hashes[md5] = file_path.name

    if result["valid"]:
        logger.info("Validation PASSED: %s (%dx%d, %.2f MB)", file_path.name, width, height, size_mb)
    else:
        logger.warning("Validation FAILED: %s — %s", file_path.name, "; ".join(result["errors"]))

    return result


# ─────────────────────────────────────────────────────────────────
# Batch Validation
# ─────────────────────────────────────────────────────────────────

def validate_batch(
    file_paths: list,
    max_file_size_mb: float = MAX_FILE_SIZE_MB,
    min_resolution:   int   = MIN_RESOLUTION_PX,
) -> Dict[str, Any]:
    """
    Validate a batch of image files.

    Args:
        file_paths:       List of Path objects to validate.
        max_file_size_mb: Maximum allowed file size in MB.
        min_resolution:   Minimum allowed resolution in pixels.

    Returns:
        Batch validation summary with per-file results.
    """
    seen_hashes: Dict[str, str] = {}
    results     = []
    passed      = 0
    failed      = 0

    for fp in file_paths:
        fp = Path(fp)
        res = validate_image(
            file_path=fp,
            seen_hashes=seen_hashes,
            max_file_size_mb=max_file_size_mb,
            min_resolution=min_resolution,
        )
        res["filename"] = fp.name
        results.append(res)
        if res["valid"]:
            passed += 1
        else:
            failed += 1

    logger.info("Batch validation: %d passed, %d failed out of %d", passed, failed, len(file_paths))

    return {
        "total":   len(file_paths),
        "passed":  passed,
        "failed":  failed,
        "results": results,
    }
