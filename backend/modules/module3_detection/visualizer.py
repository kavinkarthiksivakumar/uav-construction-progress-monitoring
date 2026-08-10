"""
Module 3: Detection Visualizer
IEEE M.Tech Project — Construction Activity Detection

Renders bounding boxes and class labels on images for visual inspection.
Produces annotated PNG files saved alongside the detection JSON results.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

logger = logging.getLogger("module3.visualizer")

# Color palette per class (BGR for OpenCV)
CLASS_COLORS = {
    "helmet":    (0, 200, 80),     # Green — compliant
    "vest":      (0, 180, 120),    # Teal  — compliant
    "person":    (0, 165, 255),    # Orange
    "no-helmet": (0, 0, 220),      # Red   — violation
    "no-vest":   (0, 80, 200),     # Dark red — violation
}
DEFAULT_COLOR = (200, 200, 200)


def draw_detections(
    image_path:  Path,
    detections:  List[Dict[str, Any]],
    output_path: Path,
    font_scale:  float = 0.45,
    thickness:   int   = 2,
) -> bool:
    """
    Draw bounding boxes and class labels on an image and save to output_path.

    Args:
        image_path:  Path to the original image.
        detections:  List of detection dicts (from detector.py).
        output_path: Path to save the annotated PNG.
        font_scale:  OpenCV font scale for labels.
        thickness:   Bounding box line thickness.

    Returns:
        True if saved successfully, False otherwise.
    """
    try:
        import cv2
        import numpy as np

        img = cv2.imread(str(image_path))
        if img is None:
            logger.warning("Could not read image for visualization: %s", image_path)
            return False

        for det in detections:
            x1, y1, x2, y2 = det.get("bbox", [0, 0, 0, 0])
            cls_name   = det.get("class_name", "unknown")
            confidence = det.get("confidence", 0.0)
            color      = CLASS_COLORS.get(cls_name, DEFAULT_COLOR)

            # Draw bounding box
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

            # Build label string
            label = f"{cls_name} {confidence:.2f}"
            (text_w, text_h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1
            )

            # Label background
            label_y1 = max(y1 - text_h - baseline - 4, 0)
            cv2.rectangle(
                img,
                (x1, label_y1),
                (x1 + text_w + 4, y1),
                color, -1
            )

            # Label text
            cv2.putText(
                img, label,
                (x1 + 2, y1 - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                (255, 255, 255), 1, cv2.LINE_AA,
            )

        # Add summary overlay (top-left corner)
        if detections:
            overlay_text = f"Detections: {len(detections)}"
            cv2.putText(
                img, overlay_text,
                (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                (0, 212, 255), 2, cv2.LINE_AA,
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), img)
        logger.debug("Visualization saved: %s", output_path)
        return True

    except Exception as exc:
        logger.error("Visualization failed for %s: %s", image_path, exc, exc_info=True)
        return False


def create_class_summary_image(
    class_counts: Dict[str, int],
    output_path:  Path,
    width:        int = 600,
    height:       int = 300,
) -> bool:
    """
    Create a simple bar-chart image of class detection counts.

    Args:
        class_counts: Dict of class_name → count.
        output_path:  Path to save the PNG.
        width, height: Output image dimensions.

    Returns:
        True if saved successfully.
    """
    try:
        import cv2
        import numpy as np

        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:] = (18, 18, 30)  # Dark background

        if not class_counts:
            cv2.imwrite(str(output_path), img)
            return True

        max_count = max(class_counts.values()) or 1
        classes   = list(class_counts.keys())
        n         = len(classes)

        bar_w = (width - 60) // n
        pad   = (width - bar_w * n) // 2

        for i, cls_name in enumerate(classes):
            count = class_counts[cls_name]
            color = CLASS_COLORS.get(cls_name, DEFAULT_COLOR)
            bar_h = int((count / max_count) * (height - 80))

            x1 = pad + i * bar_w + 4
            x2 = x1 + bar_w - 8
            y1 = height - 40 - bar_h
            y2 = height - 40

            cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)

            # Count label above bar
            cv2.putText(
                img, str(count),
                (x1 + 2, max(y1 - 6, 10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                (255, 255, 255), 1, cv2.LINE_AA,
            )

            # Class name below bar
            short_name = cls_name[:7]
            cv2.putText(
                img, short_name,
                (x1, height - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                (180, 180, 180), 1, cv2.LINE_AA,
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), img)
        return True

    except Exception as exc:
        logger.error("Class summary image failed: %s", exc, exc_info=True)
        return False
