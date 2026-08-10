"""
Module 1: Temporal Image Ordering
IEEE M.Tech Project — UAV Image Acquisition

Handles chronological sorting of UAV images based on:
  1. EXIF DateTimeOriginal metadata
  2. Filename natural sort (fallback)
  3. Upload order (final fallback)
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger("module1.temporal")


# ─────────────────────────────────────────────────────────────────
# Natural Sort Key
# ─────────────────────────────────────────────────────────────────

def _natural_sort_key(text: str) -> List:
    """
    Generate a natural sort key so that 'day10' sorts after 'day5'.

    Args:
        text: Filename or string to sort.

    Returns:
        List of string/int tokens for comparison.
    """
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", text)
    ]


# ─────────────────────────────────────────────────────────────────
# Extract Capture Date from Image Record
# ─────────────────────────────────────────────────────────────────

def _get_sort_datetime(image_record: Dict[str, Any]) -> datetime:
    """
    Extract the best available datetime for sorting.

    Priority:
        1. EXIF DateTimeOriginal
        2. EXIF DateTime
        3. File modification time
        4. epoch (never None)

    Args:
        image_record: Dictionary with 'exif' and 'filename' keys.

    Returns:
        datetime object for comparison.
    """
    exif = image_record.get("exif", {})
    fmt = "%Y:%m:%d %H:%M:%S"

    # 1. EXIF DateTimeOriginal
    raw = exif.get("DateTimeOriginal") or exif.get("DateTime")
    if raw:
        try:
            return datetime.strptime(str(raw).strip(), fmt)
        except ValueError:
            pass

    # 2. File modification time
    mtime = image_record.get("file_modified_at")
    if mtime:
        try:
            return datetime.fromisoformat(mtime)
        except (ValueError, TypeError):
            pass

    # 3. Epoch fallback
    return datetime(1970, 1, 1)


# ─────────────────────────────────────────────────────────────────
# Main Sort Function
# ─────────────────────────────────────────────────────────────────

def sort_images_temporally(
    image_records: List[Dict[str, Any]],
    fallback: str = "filename",
) -> List[Dict[str, Any]]:
    """
    Sort a list of image records in chronological order.

    Strategy:
        - If ANY record has a valid EXIF date → sort ALL by EXIF date
          (records without dates are appended at the end by filename)
        - Otherwise → natural sort by filename
        - Otherwise → preserve upload order

    Args:
        image_records: List of image metadata dictionaries.
        fallback:      'filename' or 'upload_order'

    Returns:
        Sorted list with 'temporal_index' field added to each record.
    """
    if not image_records:
        return []

    # Determine if EXIF dates are available for at least one image
    has_exif_dates = any(
        (r.get("exif", {}).get("DateTimeOriginal") or r.get("exif", {}).get("DateTime"))
        for r in image_records
    )

    if has_exif_dates:
        logger.info("Temporal sort: using EXIF DateTimeOriginal")
        sorted_records = sorted(
            image_records,
            key=lambda r: (
                _get_sort_datetime(r),
                _natural_sort_key(r.get("filename", "")),
            )
        )
        sort_method = "exif_date"

    elif fallback == "filename":
        logger.info("Temporal sort: no EXIF dates found — using filename natural sort")
        sorted_records = sorted(
            image_records,
            key=lambda r: _natural_sort_key(r.get("filename", "")),
        )
        sort_method = "filename"

    else:
        logger.info("Temporal sort: preserving upload order")
        sorted_records = list(image_records)
        sort_method = "upload_order"

    # Assign temporal indices
    for idx, record in enumerate(sorted_records):
        record["temporal_index"] = idx
        record["sort_method"] = sort_method
        capture_dt = _get_sort_datetime(record)
        if capture_dt > datetime(1970, 1, 1):
            record["capture_datetime"] = capture_dt.isoformat()

    logger.info(
        "Temporal sort complete: %d images ordered by %s",
        len(sorted_records), sort_method
    )

    return sorted_records


# ─────────────────────────────────────────────────────────────────
# Generate Timeline Summary
# ─────────────────────────────────────────────────────────────────

def build_timeline(image_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a structured timeline from sorted image records.

    Produces day-level groupings with date labels for the UI.

    Args:
        image_records: Temporally sorted image metadata list.

    Returns:
        Timeline dictionary with entries, date range, and statistics.
    """
    if not image_records:
        return {"entries": [], "total_images": 0, "date_range": None}

    entries = []
    seen_dates: set = set()

    for record in image_records:
        date_label = record.get("capture_datetime", "")
        if date_label:
            try:
                dt = datetime.fromisoformat(date_label)
                day_key = dt.strftime("%Y-%m-%d")
                is_new_day = day_key not in seen_dates
                seen_dates.add(day_key)
            except ValueError:
                day_key = f"Day {record['temporal_index'] + 1}"
                is_new_day = True
        else:
            day_key = f"Day {record['temporal_index'] + 1}"
            is_new_day = record["temporal_index"] == 0

        entries.append({
            "temporal_index": record["temporal_index"],
            "image_id":       record.get("image_id", ""),
            "filename":       record.get("filename", ""),
            "day_label":      day_key,
            "is_new_day":     is_new_day,
            "capture_datetime": record.get("capture_datetime", ""),
            "quality_score":  record.get("quality_score", None),
            "status":         record.get("status", "unknown"),
        })

    first_date = entries[0]["day_label"]  if entries else None
    last_date  = entries[-1]["day_label"] if entries else None

    return {
        "entries":     entries,
        "total_images": len(entries),
        "unique_days": len(seen_dates) if seen_dates else len(entries),
        "date_range":  {"start": first_date, "end": last_date},
        "sort_method": image_records[0].get("sort_method", "unknown") if image_records else None,
    }
