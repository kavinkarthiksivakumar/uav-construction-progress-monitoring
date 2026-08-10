"""
Module 1: EXIF & Image Metadata Extractor
IEEE M.Tech Project — UAV Image Acquisition

Extracts:
  - EXIF metadata (camera model, GPS, datetime, focal length, etc.)
  - Basic image properties (dimensions, mode, format)
  - File system metadata (size, creation/modification times)
  - GPS coordinates with decimal conversion
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("module1.metadata")


# ─────────────────────────────────────────────────────────────────
# GPS Conversion Utility
# ─────────────────────────────────────────────────────────────────

def _rational_to_float(rational) -> float:
    """Convert an EXIF IFDRational or tuple (num, denom) to float."""
    try:
        if hasattr(rational, "numerator"):
            return rational.numerator / rational.denominator
        if isinstance(rational, tuple) and len(rational) == 2:
            return rational[0] / rational[1] if rational[1] != 0 else 0.0
        return float(rational)
    except Exception:
        return 0.0


def _gps_to_decimal(degrees, minutes, seconds, direction: str) -> float:
    """
    Convert GPS coordinates from DMS (degrees/minutes/seconds) to decimal.

    Args:
        degrees:   Degrees as rational.
        minutes:   Minutes as rational.
        seconds:   Seconds as rational.
        direction: Hemisphere indicator ('N', 'S', 'E', 'W').

    Returns:
        Decimal degrees (negative for S/W).
    """
    deg = _rational_to_float(degrees)
    mnt = _rational_to_float(minutes)
    sec = _rational_to_float(seconds)
    decimal = deg + mnt / 60.0 + sec / 3600.0
    if direction in ("S", "W"):
        decimal = -decimal
    return round(decimal, 8)


# ─────────────────────────────────────────────────────────────────
# EXIF Extraction via Pillow
# ─────────────────────────────────────────────────────────────────

def _extract_exif_pillow(file_path: Path) -> Dict[str, Any]:
    """
    Extract EXIF data using Pillow's getexif() interface.

    Args:
        file_path: Path to the image file.

    Returns:
        Flat dictionary of readable EXIF tag names to values.
    """
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS

        exif_data: Dict[str, Any] = {}

        with Image.open(file_path) as img:
            raw_exif = img._getexif()
            if not raw_exif:
                return exif_data

            for tag_id, value in raw_exif.items():
                tag = TAGS.get(tag_id, str(tag_id))

                # ── Handle GPS sub-IFD ──────────────────────────
                if tag == "GPSInfo" and isinstance(value, dict):
                    gps: Dict[str, Any] = {}
                    for gps_id, gps_val in value.items():
                        gps_tag = GPSTAGS.get(gps_id, str(gps_id))
                        gps[gps_tag] = str(gps_val)

                    # Attempt decimal conversion
                    try:
                        lat_dms  = value.get(2)
                        lat_ref  = value.get(1, "N")
                        lon_dms  = value.get(4)
                        lon_ref  = value.get(3, "E")
                        alt_r    = value.get(6)

                        if lat_dms and lon_dms:
                            gps["latitude_decimal"]  = _gps_to_decimal(*lat_dms, lat_ref)
                            gps["longitude_decimal"] = _gps_to_decimal(*lon_dms, lon_ref)
                        if alt_r is not None:
                            gps["altitude_m"] = round(_rational_to_float(alt_r), 2)
                    except Exception:
                        pass

                    exif_data["GPS"] = gps
                else:
                    # Convert bytes to string
                    if isinstance(value, bytes):
                        try:
                            value = value.decode("utf-8", errors="replace")
                        except Exception:
                            value = str(value)
                    exif_data[tag] = str(value) if not isinstance(value, (int, float, str)) else value

        return exif_data

    except Exception as exc:
        logger.debug("Pillow EXIF extraction error for %s: %s", file_path.name, exc)
        return {}


# ─────────────────────────────────────────────────────────────────
# Image Properties
# ─────────────────────────────────────────────────────────────────

def _extract_image_properties(file_path: Path) -> Dict[str, Any]:
    """
    Extract basic image properties (dimensions, mode, format).

    Args:
        file_path: Path to the image file.

    Returns:
        Dictionary of image properties.
    """
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            return {
                "width":         img.width,
                "height":        img.height,
                "mode":          img.mode,
                "format":        img.format or file_path.suffix.upper().lstrip("."),
                "megapixels":    round((img.width * img.height) / 1_000_000, 2),
                "aspect_ratio":  round(img.width / img.height, 3) if img.height else 0,
            }
    except Exception as exc:
        logger.warning("Could not read image properties for %s: %s", file_path.name, exc)
        return {}


# ─────────────────────────────────────────────────────────────────
# File System Metadata
# ─────────────────────────────────────────────────────────────────

def _extract_file_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract file-system level metadata.

    Args:
        file_path: Path to the file.

    Returns:
        Dictionary with size and timestamps.
    """
    stat = file_path.stat()
    return {
        "filename":          file_path.name,
        "file_path":         str(file_path),
        "file_size_bytes":   stat.st_size,
        "file_size_mb":      round(stat.st_size / (1024 * 1024), 3),
        "file_modified_at":  datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "file_created_at":   datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "extension":         file_path.suffix.lower(),
    }


# ─────────────────────────────────────────────────────────────────
# Main Extraction Function
# ─────────────────────────────────────────────────────────────────

def extract_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract complete metadata from a UAV image.

    Combines:
        - File-system metadata
        - Image properties (dimensions, format, mode)
        - EXIF data (camera, datetime, GPS, etc.)

    Args:
        file_path: Path to the image file.

    Returns:
        Unified metadata dictionary.
    """
    file_path = Path(file_path)
    logger.info("Extracting metadata from: %s", file_path.name)

    meta: Dict[str, Any] = {}

    # Layer 1: File system
    meta.update(_extract_file_metadata(file_path))

    # Layer 2: Image properties
    meta["image_properties"] = _extract_image_properties(file_path)
    # Also expose at top level for convenience
    props = meta["image_properties"]
    meta["width"]      = props.get("width", 0)
    meta["height"]     = props.get("height", 0)
    meta["mode"]       = props.get("mode", "")
    meta["megapixels"] = props.get("megapixels", 0)

    # Layer 3: EXIF
    exif = _extract_exif_pillow(file_path)
    meta["exif"] = exif

    # Convenient top-level EXIF fields
    meta["camera_make"]   = exif.get("Make",   "Unknown")
    meta["camera_model"]  = exif.get("Model",  "Unknown")
    meta["capture_date"]  = exif.get("DateTimeOriginal") or exif.get("DateTime", "")
    meta["focal_length"]  = exif.get("FocalLength", "")
    meta["exposure_time"] = exif.get("ExposureTime", "")
    meta["f_number"]      = exif.get("FNumber", "")
    meta["iso"]           = exif.get("ISOSpeedRatings", "")

    gps = exif.get("GPS", {})
    if gps:
        meta["gps_latitude"]  = gps.get("latitude_decimal",  None)
        meta["gps_longitude"] = gps.get("longitude_decimal", None)
        meta["gps_altitude"]  = gps.get("altitude_m",        None)
    else:
        meta["gps_latitude"]  = None
        meta["gps_longitude"] = None
        meta["gps_altitude"]  = None

    meta["extracted_at"] = datetime.utcnow().isoformat() + "Z"

    logger.info(
        "Metadata extracted: %s | %dx%d | %s | GPS: %s",
        file_path.name,
        meta.get("width", 0),
        meta.get("height", 0),
        meta.get("camera_model", "Unknown"),
        "Yes" if gps else "No",
    )

    return meta
