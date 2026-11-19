"""
Module 2: SYSU-CD Dataset Loader
Final Year Project — Explainable Vision-Based Construction Progress Assessment

Loads and manages the SYSU-CD (Seasonal Urban Change Detection) dataset.

Dataset structure (datasets/sysu/):
    train/
        train/
            time1/  ← 12,000 images (before)
            time2/  ← 12,000 images (after)
            label/  ← 12,000 binary change masks
    val/
        val/
            time1/  ← 4,000 images
            time2/  ← 4,000 images
            label/  ← 4,000 binary change masks
    test/
        test/
            time1/  ← (images named 00000.png …)
            time2/  ← matching images
            label/  ← 720 binary change masks

Images: 256×256 pixels, PNG format.
Labels: Binary masks — 0 = no change, 255 = changed.

Reference:
  Shi Q, Liu M, Li S, et al. "A Deeply Supervised Attention Metric-Based
  Network and an Open Aerial Image Dataset for Remote Sensing Change
  Detection." IEEE TGRS, 2022.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("module2.sysu_loader")

# Supported image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def _get_split_root(sysu_root: Path, split: str) -> Path:
    """
    Resolve the nested split directory.

    SYSU-CD has a quirky double-nesting: train/train/, val/val/, test/test/.
    This helper checks both the flat and nested path.
    """
    flat   = sysu_root / split
    nested = sysu_root / split / split
    if nested.exists():
        return nested
    if flat.exists():
        return flat
    return nested  # return nested even if missing (for cleaner error messages)


def scan_sysu_dataset(sysu_root: Path) -> Dict[str, Any]:
    """
    Scan the SYSU-CD dataset and return a summary of available splits.

    Args:
        sysu_root: Root directory of the SYSU-CD dataset.

    Returns:
        Dict with structure:
            {
              "dataset":  "SYSU-CD",
              "root":     str,
              "exists":   bool,
              "splits":   {
                  "train": {"time1": int, "time2": int, "label": int, "paired": int},
                  "val":   { ... },
                  "test":  { ... },
              },
              "total_pairs": int,
              "image_size":  "256x256 px",
              "annotation":  "Binary PNG masks (0=no-change, 255=changed)",
            }
    """
    sysu_root = Path(sysu_root)
    result: Dict[str, Any] = {
        "dataset":    "SYSU-CD",
        "root":       str(sysu_root),
        "exists":     sysu_root.exists(),
        "splits":     {},
        "total_pairs": 0,
        "image_size": "256×256 px",
        "annotation": "Binary PNG masks (0=no-change, 255=changed)",
    }

    if not sysu_root.exists():
        logger.warning("SYSU-CD root not found: %s", sysu_root)
        return result

    for split in ["train", "val", "test"]:
        split_root = _get_split_root(sysu_root, split)
        split_info: Dict[str, Any] = {
            "split_root": str(split_root),
            "exists":     split_root.exists(),
            "time1": 0, "time2": 0, "label": 0, "paired": 0,
        }

        if split_root.exists():
            for subdir in ["time1", "time2", "label"]:
                d = split_root / subdir
                if d.exists():
                    count = sum(
                        1 for f in d.iterdir()
                        if f.suffix.lower() in IMAGE_EXTENSIONS
                    )
                    split_info[subdir] = count
                    logger.debug("SYSU %s/%s: %d images", split, subdir, count)

            # Paired count = min of the three subdirs (they should match)
            split_info["paired"] = min(
                split_info["time1"],
                split_info["time2"],
                split_info["label"],
            )
            result["total_pairs"] += split_info["paired"]

        result["splits"][split] = split_info

    logger.info(
        "SYSU-CD scan complete: %d total pairs across %d splits",
        result["total_pairs"],
        len(result["splits"]),
    )
    return result


def get_sysu_pairs(
    sysu_root:    Path,
    split:        str = "test",
    limit:        int = 20,
    offset:       int = 0,
) -> Dict[str, Any]:
    """
    Return a paginated list of time1/time2/label triplets from a SYSU split.

    Args:
        sysu_root: Root directory of SYSU-CD.
        split:     One of 'train', 'val', 'test'.
        limit:     Max pairs to return per page.
        offset:    Start index (0-based).

    Returns:
        Dict with "pairs", "total", "limit", "offset" fields.
    """
    sysu_root  = Path(sysu_root)
    split_root = _get_split_root(sysu_root, split)

    t1_dir  = split_root / "time1"
    t2_dir  = split_root / "time2"
    lbl_dir = split_root / "label"

    if not t1_dir.exists():
        logger.warning("SYSU-CD %s/time1 not found: %s", split, t1_dir)
        return {"pairs": [], "total": 0, "limit": limit, "offset": offset, "split": split}

    # Collect all time1 image stems in sorted order
    t1_files = sorted(
        f for f in t1_dir.iterdir()
        if f.suffix.lower() in IMAGE_EXTENSIONS
    )
    total = len(t1_files)
    page  = t1_files[offset: offset + limit]

    pairs: List[Dict[str, Any]] = []
    for t1_path in page:
        stem   = t1_path.stem  # e.g. "00000"
        # time2 and label may differ in extension; try same, then .png
        t2_path  = t2_dir  / t1_path.name
        lbl_path = lbl_dir / t1_path.name
        if not t2_path.exists():
            t2_path  = t2_dir  / (stem + ".png")
        if not lbl_path.exists():
            lbl_path = lbl_dir / (stem + ".png")

        pairs.append({
            "pair_id": f"sysu_{split}_{stem}",
            "stem":    stem,
            "split":   split,
            "time1":   str(t1_path),
            "time2":   str(t2_path)  if t2_path.exists()  else None,
            "label":   str(lbl_path) if lbl_path.exists() else None,
            "has_t1":  t1_path.exists(),
            "has_t2":  t2_path.exists(),
            "has_gt":  lbl_path.exists(),
        })

    return {
        "pairs":  pairs,
        "total":  total,
        "limit":  limit,
        "offset": offset,
        "split":  split,
    }
