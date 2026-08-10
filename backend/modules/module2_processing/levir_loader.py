"""
Module 2: LEVIR-CD Dataset Loader
IEEE M.Tech Project — Image Processing

Scans and loads image pairs (A/B) and change masks (label) from the
LEVIR-CD dataset. The dataset root path is configured via the
LEVIR_CD_PATH environment variable (see .env.example).

LEVIR-CD Structure:
  levir_cd/
    train/
      A/      ← Before images (train_1.png … train_445.png)
      B/      ← After images  (same filenames)
      label/  ← Binary change masks (same filenames)
    val/
      A/ B/ label/
    test/
      A/ B/ label/
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("module2.levir_loader")


# ─────────────────────────────────────────────────────────────────
# Dataset Scanner
# ─────────────────────────────────────────────────────────────────

def scan_levir_dataset(root_path: str) -> Dict[str, Any]:
    """
    Scan the LEVIR-CD dataset directory and return a full inventory.

    Args:
        root_path: Absolute path to the LEVIR-CD root (configured via LEVIR_CD_PATH in .env)

    Returns:
        Dictionary with split statistics, pair counts, and file lists.
    """
    root = Path(root_path)

    if not root.exists():
        logger.error("LEVIR-CD root not found: %s", root)
        return {"error": f"Dataset path not found: {root}", "available": False}

    splits = ["train", "val", "test"]
    result: Dict[str, Any] = {
        "root":      str(root),
        "available": True,
        "scanned_at": datetime.utcnow().isoformat() + "Z",
        "splits":    {},
        "total_pairs": 0,
        "summary":   {},
    }

    for split in splits:
        split_dir = root / split
        if not split_dir.exists():
            logger.warning("Split '%s' not found in LEVIR-CD", split)
            continue

        a_dir     = split_dir / "A"
        b_dir     = split_dir / "B"
        label_dir = split_dir / "label"

        a_files = sorted(a_dir.glob("*.png"))     if a_dir.exists()     else []
        b_files = sorted(b_dir.glob("*.png"))     if b_dir.exists()     else []
        lbl_files = sorted(label_dir.glob("*.png")) if label_dir.exists() else []

        # Match by filename stem
        a_stems = {f.stem: f for f in a_files}
        b_stems = {f.stem: f for f in b_files}
        l_stems = {f.stem: f for f in lbl_files}
        common  = sorted(set(a_stems) & set(b_stems))

        pairs = []
        for stem in common:
            pairs.append({
                "pair_id":    f"{split}_{stem}",
                "stem":       stem,
                "split":      split,
                "before":     str(a_stems[stem]),
                "after":      str(b_stems[stem]),
                "label":      str(l_stems[stem]) if stem in l_stems else None,
                "has_label":  stem in l_stems,
            })

        result["splits"][split] = {
            "path":        str(split_dir),
            "pair_count":  len(pairs),
            "a_images":    len(a_files),
            "b_images":    len(b_files),
            "labels":      len(lbl_files),
            "pairs":       pairs,
        }
        result["total_pairs"] += len(pairs)

    result["summary"] = {
        "train_pairs": result["splits"].get("train", {}).get("pair_count", 0),
        "val_pairs":   result["splits"].get("val",   {}).get("pair_count", 0),
        "test_pairs":  result["splits"].get("test",  {}).get("pair_count", 0),
        "total_pairs": result["total_pairs"],
    }

    logger.info(
        "LEVIR-CD scanned: %d total pairs (train=%d, val=%d, test=%d)",
        result["total_pairs"],
        result["summary"]["train_pairs"],
        result["summary"]["val_pairs"],
        result["summary"]["test_pairs"],
    )
    return result


# ─────────────────────────────────────────────────────────────────
# Load a Single Pair
# ─────────────────────────────────────────────────────────────────

def load_pair(
    before_path: str,
    after_path:  str,
    label_path:  Optional[str] = None,
    target_size: tuple = (512, 512),
) -> Dict[str, Any]:
    """
    Load a single LEVIR-CD image pair into numpy arrays.

    Args:
        before_path: Path to the 'before' image (A).
        after_path:  Path to the 'after' image (B).
        label_path:  Path to the binary change mask (label), optional.
        target_size: (width, height) to resize images to.

    Returns:
        Dictionary with arrays and metadata.
    """
    import cv2
    import numpy as np

    result: Dict[str, Any] = {
        "before_path": before_path,
        "after_path":  after_path,
        "label_path":  label_path,
        "success":     False,
        "error":       None,
    }

    try:
        before_img = cv2.imread(before_path)
        after_img  = cv2.imread(after_path)

        if before_img is None or after_img is None:
            raise ValueError("Could not load one or both images")

        # Resize to target
        w, h = target_size
        before_img = cv2.resize(before_img, (w, h), interpolation=cv2.INTER_LANCZOS4)
        after_img  = cv2.resize(after_img,  (w, h), interpolation=cv2.INTER_LANCZOS4)

        result["before"]     = before_img
        result["after"]      = after_img
        result["shape"]      = before_img.shape
        result["success"]    = True

        if label_path and Path(label_path).exists():
            label_img = cv2.imread(label_path, cv2.IMREAD_GRAYSCALE)
            if label_img is not None:
                label_img = cv2.resize(label_img, (w, h), interpolation=cv2.INTER_NEAREST)
                result["label"]           = label_img
                result["change_pixels"]   = int(np.sum(label_img > 127))
                result["change_percent"]  = round(
                    float(np.sum(label_img > 127)) / label_img.size * 100, 2
                )

    except Exception as exc:
        result["error"] = str(exc)
        logger.error("Failed to load pair (%s, %s): %s", before_path, after_path, exc)

    return result


# ─────────────────────────────────────────────────────────────────
# Get Paginated Preview Pairs
# ─────────────────────────────────────────────────────────────────

def get_preview_pairs(
    scan_result: Dict,
    split:       str = "train",
    page:        int = 1,
    limit:       int = 20,
) -> Dict[str, Any]:
    """
    Return a paginated slice of pairs for the UI dataset browser.

    Args:
        scan_result: Result from scan_levir_dataset().
        split:       Which split to use ('train', 'val', 'test').
        page:        Page number (1-indexed).
        limit:       Items per page.

    Returns:
        Paginated response with pairs metadata.
    """
    split_data = scan_result.get("splits", {}).get(split, {})
    pairs      = split_data.get("pairs", [])

    total  = len(pairs)
    start  = (page - 1) * limit
    end    = min(start + limit, total)
    sliced = pairs[start:end]

    return {
        "split":  split,
        "page":   page,
        "limit":  limit,
        "total":  total,
        "pages":  max(1, (total + limit - 1) // limit),
        "pairs":  sliced,
    }
