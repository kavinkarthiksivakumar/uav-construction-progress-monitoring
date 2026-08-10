"""
Module 2: Roboflow Construction Dataset Loader
IEEE M.Tech Project — Image Processing

Scans the Roboflow construction safety dataset.
Dataset root is configured via the ROBOFLOW_PATH environment variable
(see .env.example).

Classes: helmet, no-helmet, no-vest, person, vest (5 classes, YOLO format)
Splits:  train / valid / test — each with images/ + labels/ subdirs
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger("module2.roboflow_loader")

CLASSES = ["helmet", "no-helmet", "no-vest", "person", "vest"]


# ─────────────────────────────────────────────────────────────────
# Dataset Scanner
# ─────────────────────────────────────────────────────────────────

def scan_roboflow_dataset(root_path: str) -> Dict[str, Any]:
    """
    Scan the Roboflow construction dataset and return a full inventory.

    Args:
        root_path: Path to dataset root (configured via ROBOFLOW_PATH in .env)

    Returns:
        Inventory dict with split stats and sampled image records.
    """
    root = Path(root_path)

    if not root.exists():
        logger.error("Roboflow root not found: %s", root)
        return {"error": f"Dataset path not found: {root}", "available": False}

    splits  = ["train", "valid", "test"]
    result: Dict[str, Any] = {
        "root":       str(root),
        "available":  True,
        "scanned_at": datetime.utcnow().isoformat() + "Z",
        "classes":    CLASSES,
        "num_classes": len(CLASSES),
        "splits":     {},
        "total_images": 0,
        "summary":    {},
    }

    # Read data.yaml if present
    yaml_file = root / "data.yaml"
    if yaml_file.exists():
        result["data_yaml"] = yaml_file.read_text(encoding="utf-8")

    for split in splits:
        img_dir = root / split / "images"
        lbl_dir = root / split / "labels"

        if not img_dir.exists():
            logger.warning("Split '%s' images not found", split)
            continue

        img_files = sorted(
            list(img_dir.glob("*.jpg")) +
            list(img_dir.glob("*.jpeg")) +
            list(img_dir.glob("*.png"))
        )
        lbl_files = sorted(lbl_dir.glob("*.txt")) if lbl_dir.exists() else []

        # Build lightweight record per image
        records = []
        lbl_stems = {f.stem: f for f in lbl_files}

        for img in img_files:
            rec = {
                "image_id":   f"{split}_{img.stem}",
                "filename":   img.name,
                "stem":       img.stem,
                "split":      split,
                "image_path": str(img),
                "label_path": str(lbl_stems[img.stem]) if img.stem in lbl_stems else None,
                "has_label":  img.stem in lbl_stems,
            }

            # Parse YOLO label file to count class instances
            if rec["has_label"]:
                try:
                    labels_txt = Path(rec["label_path"]).read_text().strip()
                    class_counts = {c: 0 for c in CLASSES}
                    for line in labels_txt.splitlines():
                        parts = line.strip().split()
                        if parts:
                            cls_idx = int(parts[0])
                            if 0 <= cls_idx < len(CLASSES):
                                class_counts[CLASSES[cls_idx]] += 1
                    rec["class_counts"] = class_counts
                    rec["total_objects"] = sum(class_counts.values())
                except Exception:
                    rec["class_counts"]  = {}
                    rec["total_objects"] = 0

            records.append(rec)

        result["splits"][split] = {
            "path":        str(root / split),
            "image_count": len(img_files),
            "label_count": len(lbl_files),
            "images":      records,
        }
        result["total_images"] += len(img_files)

    result["summary"] = {
        "train_images": result["splits"].get("train", {}).get("image_count", 0),
        "valid_images": result["splits"].get("valid", {}).get("image_count", 0),
        "test_images":  result["splits"].get("test",  {}).get("image_count", 0),
        "total_images": result["total_images"],
        "classes":      CLASSES,
        "num_classes":  len(CLASSES),
    }

    logger.info(
        "Roboflow dataset scanned: %d total images (train=%d, valid=%d, test=%d)",
        result["total_images"],
        result["summary"]["train_images"],
        result["summary"]["valid_images"],
        result["summary"]["test_images"],
    )
    return result


# ─────────────────────────────────────────────────────────────────
# Class Distribution Analysis
# ─────────────────────────────────────────────────────────────────

def compute_class_distribution(scan_result: Dict) -> Dict[str, Any]:
    """
    Compute per-class annotation counts across all splits.

    Args:
        scan_result: Result from scan_roboflow_dataset().

    Returns:
        Distribution dict with per-class counts and percentages.
    """
    total_per_class = {c: 0 for c in CLASSES}
    total_objects   = 0

    for split_data in scan_result.get("splits", {}).values():
        for img in split_data.get("images", []):
            counts = img.get("class_counts", {})
            for c in CLASSES:
                n = counts.get(c, 0)
                total_per_class[c] += n
                total_objects       += n

    distribution = {}
    for c in CLASSES:
        n = total_per_class[c]
        distribution[c] = {
            "count":      n,
            "percentage": round(n / total_objects * 100, 2) if total_objects else 0,
        }

    return {
        "total_objects":   total_objects,
        "per_class":       distribution,
        "dominant_class":  max(total_per_class, key=total_per_class.get) if total_objects else None,
    }


# ─────────────────────────────────────────────────────────────────
# Paginated Image Listing
# ─────────────────────────────────────────────────────────────────

def get_images_paginated(
    scan_result: Dict,
    split: str = "train",
    page:  int = 1,
    limit: int = 24,
) -> Dict[str, Any]:
    """
    Return a paginated image listing for the UI dataset browser.

    Args:
        scan_result: Result from scan_roboflow_dataset().
        split:       Split name ('train', 'valid', 'test').
        page:        1-indexed page number.
        limit:       Items per page.

    Returns:
        Paginated response.
    """
    images = scan_result.get("splits", {}).get(split, {}).get("images", [])
    total  = len(images)
    start  = (page - 1) * limit
    end    = min(start + limit, total)

    return {
        "split":  split,
        "page":   page,
        "limit":  limit,
        "total":  total,
        "pages":  max(1, (total + limit - 1) // limit),
        "images": images[start:end],
    }
