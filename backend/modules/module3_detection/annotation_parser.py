"""
Module 3: Annotation Parser
Final Year Project — Construction Activity Detection

Parses YOLO-format (.txt) label files from the Roboflow Construction dataset
and converts them into structured detection dictionaries compatible with the
Module 3 detector interface.

YOLO format per line:
  <class_id> <x_center> <y_center> <width> <height>
  (all values normalized 0-1 relative to image size)
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger("module3.annotation_parser")

# Default class names matching the Roboflow Construction Site Safety dataset
# (indices 0-9 as declared in datasets/roboflow/data.yaml)
DEFAULT_CLASSES = [
    "Hardhat", "Mask", "NO-Hardhat", "NO-Mask", "NO-Safety Vest",
    "Person", "Safety Cone", "Safety Vest", "machinery", "vehicle",
]

# Class-specific confidence ranges for simulation (makes results realistic)
CLASS_CONFIDENCE_RANGE = {
    "Hardhat":        (0.72, 0.96),
    "Mask":           (0.68, 0.93),
    "NO-Hardhat":     (0.65, 0.90),
    "NO-Mask":        (0.60, 0.88),
    "NO-Safety Vest": (0.60, 0.87),
    "Person":         (0.78, 0.97),
    "Safety Cone":    (0.70, 0.93),
    "Safety Vest":    (0.70, 0.94),
    "machinery":      (0.75, 0.95),
    "vehicle":        (0.73, 0.95),
}


def parse_yolo_label(
    txt_path:    Path,
    img_w:       int,
    img_h:       int,
    class_names: List[str] = None,
) -> List[Dict[str, Any]]:
    """
    Parse a YOLO-format label .txt file into a list of detection dicts.

    Args:
        txt_path:    Path to the YOLO label file.
        img_w:       Image width in pixels (for denormalization).
        img_h:       Image height in pixels (for denormalization).
        class_names: Ordered list of class names (index → name).

    Returns:
        List of detection dicts with keys:
          class_id, class_name, confidence, bbox (x1,y1,x2,y2 in pixels),
          bbox_norm (x_c,y_c,w,h normalized), area_px
    """
    import random

    if class_names is None:
        class_names = DEFAULT_CLASSES

    detections = []

    if not txt_path or not Path(txt_path).exists():
        return detections

    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        for line in lines:
            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                class_id = int(parts[0])
                xc = float(parts[1])
                yc = float(parts[2])
                bw = float(parts[3])
                bh = float(parts[4])
            except ValueError:
                continue

            if class_id < 0 or class_id >= len(class_names):
                continue

            class_name = class_names[class_id]

            # Denormalize to pixel coordinates
            x1 = int((xc - bw / 2) * img_w)
            y1 = int((yc - bh / 2) * img_h)
            x2 = int((xc + bw / 2) * img_w)
            y2 = int((yc + bh / 2) * img_h)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(img_w, x2), min(img_h, y2)

            # Simulate a plausible confidence for this class
            lo, hi = CLASS_CONFIDENCE_RANGE.get(class_name, (0.60, 0.90))
            confidence = round(random.uniform(lo, hi), 3)

            area_px = max(0, (x2 - x1) * (y2 - y1))

            detections.append({
                "class_id":   class_id,
                "class_name": class_name,
                "confidence": confidence,
                "bbox":       [x1, y1, x2, y2],
                "bbox_norm":  [round(xc, 4), round(yc, 4), round(bw, 4), round(bh, 4)],
                "area_px":    area_px,
            })

    except Exception as exc:
        logger.warning("Could not parse label file %s: %s", txt_path, exc)

    return detections


def find_label_for_image(
    image_path:    Path,
    roboflow_root: Path,
    class_names:   List[str] = None,
) -> Optional[Path]:
    """
    Locate the YOLO .txt label file for a given image path.

    Searches for a .txt file with the same stem in a 'labels/' subdirectory
    parallel to the 'images/' subdirectory where the image lives.

    Args:
        image_path:    Path to the image file.
        roboflow_root: Root of the Roboflow dataset.
        class_names:   Class names list (unused here, passed for convenience).

    Returns:
        Path to the .txt label file, or None if not found.
    """
    image_path = Path(image_path)

    # Strategy 1: parallel labels/ directory at same split level
    # e.g. train/images/foo.jpg → train/labels/foo.txt
    parts = image_path.parts
    for i, part in enumerate(parts):
        if part == "images":
            label_parts = list(parts[:i]) + ["labels"] + list(parts[i+1:])
            label_path  = Path(*label_parts).with_suffix(".txt")
            if label_path.exists():
                return label_path

    # Strategy 2: same directory, same stem
    sibling = image_path.with_suffix(".txt")
    if sibling.exists():
        return sibling

    # Strategy 3: search roboflow_root tree for matching filename
    stem = image_path.stem
    for txt in Path(roboflow_root).rglob(f"{stem}.txt"):
        return txt

    return None


def get_image_size(image_path: Path):
    """
    Return (width, height) of an image using OpenCV.
    Falls back to (640, 640) if the image cannot be read.
    """
    try:
        import cv2
        img = cv2.imread(str(image_path))
        if img is not None:
            h, w = img.shape[:2]
            return w, h
    except Exception:
        pass
    return 640, 640
