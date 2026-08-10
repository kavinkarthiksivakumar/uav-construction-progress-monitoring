"""
Module 3: Construction Activity Detector
IEEE M.Tech Project — Construction Activity Detection

Detects construction site activities and safety compliance in images using the
Roboflow 5-class dataset (helmet, no-helmet, vest, no-vest, person).

Operating Modes:
  1. Simulation Mode (default) — reads YOLO ground-truth label .txt files from
     the Roboflow dataset as "detections". This lets the full pipeline run
     without a GPU or trained model, producing realistic results.

  2. YOLOv8 Mode — when ultralytics + a model weight file are available,
     runs real inference. Drop a .pt file path into config["model_path"] to
     activate this mode automatically.

Interface is identical in both modes so the frontend and API never change.

Pipeline:
  1. Load image → get size
  2. Find matching label file (simulation) OR run YOLOv8 (real)
  3. Parse / collect detections
  4. Compute per-image statistics (class counts, avg confidence, compliance)
  5. Draw annotated visualization
  6. Save results JSON
  7. Return structured result dict
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("module3.detector")

# ─── Class definitions ─────────────────────────────────────────────────────────
CLASSES      = ["helmet", "no-helmet", "no-vest", "person", "vest"]
SAFE_CLASSES = {"helmet", "vest"}
RISK_CLASSES = {"no-helmet", "no-vest"}

# ─── Compliance thresholds ─────────────────────────────────────────────────────
COMPLIANCE_THRESHOLD = 0.5   # fraction of workers with full PPE = compliant site


# ─────────────────────────────────────────────────────────────────────────────
# Core: Detect Single Image
# ─────────────────────────────────────────────────────────────────────────────

def detect_image(
    image_path:    Path,
    output_dir:    Path,
    config:        Dict = None,
    roboflow_root: Path = None,
) -> Dict[str, Any]:
    """
    Run Module 3 detection on a single image.

    Args:
        image_path:    Path to input image.
        output_dir:    Directory for outputs (viz PNG + JSON).
        config:        Optional config overrides (see settings.MODULE3).
        roboflow_root: Root of Roboflow dataset (for simulation label lookup).

    Returns:
        Detection result dict.
    """
    from backend.modules.module3_detection.annotation_parser import (
        parse_yolo_label, find_label_for_image, get_image_size,
    )
    from backend.modules.module3_detection.visualizer import draw_detections

    cfg          = config or {}
    class_names  = cfg.get("classes",        CLASSES)
    model_path   = cfg.get("model_path",     None)
    conf_thresh  = cfg.get("conf_threshold", 0.40)
    iou_thresh   = cfg.get("iou_threshold",  0.45)
    save_viz     = cfg.get("save_viz",       True)

    image_path = Path(image_path)
    result: Dict[str, Any] = {
        "image_path":    str(image_path),
        "filename":      image_path.name,
        "success":       False,
        "mode":          "simulation",
        "detections":    [],
        "class_counts":  {c: 0 for c in class_names},
        "total_objects": 0,
        "avg_confidence": 0.0,
        "compliance":    {},
        "viz_path":      None,
        "json_path":     None,
        "detected_at":   datetime.utcnow().isoformat() + "Z",
        "error":         None,
    }

    try:
        img_w, img_h = get_image_size(image_path)

        # ── Mode selection ──────────────────────────────────────────────────
        detections = []

        if model_path and Path(model_path).exists():
            # Real YOLOv8 inference
            detections = _run_yolov8(
                image_path, model_path, conf_thresh, iou_thresh, class_names
            )
            result["mode"] = "yolov8"
        else:
            # Simulation: parse Roboflow YOLO label files
            label_path = find_label_for_image(image_path, roboflow_root or Path("."), class_names)
            detections = parse_yolo_label(label_path, img_w, img_h, class_names)
            result["mode"] = "simulation"

        # ── Statistics ─────────────────────────────────────────────────────
        class_counts = {c: 0 for c in class_names}
        confidences  = []

        for det in detections:
            cn = det.get("class_name", "")
            if cn in class_counts:
                class_counts[cn] += 1
            confidences.append(det.get("confidence", 0.0))

        avg_conf = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

        # Compliance analysis
        persons    = class_counts.get("person",    0)
        helmets    = class_counts.get("helmet",    0)
        vests      = class_counts.get("vest",      0)
        no_helmet  = class_counts.get("no-helmet", 0)
        no_vest    = class_counts.get("no-vest",   0)

        # Worker count is number of persons, or inferred from PPE/violations if person is not detected
        worker_count = persons if persons > 0 else max(helmets + no_helmet, vests + no_vest)

        if worker_count == 0:
            compliance_rate = 100.0
            site_compliant = True
            compliant_workers = 0
        else:
            # A worker is compliant if they do not have a no-helmet or no-vest detection
            compliant_workers = max(0, worker_count - no_helmet - no_vest)
            compliance_rate = round(compliant_workers / worker_count * 100, 1)
            site_compliant = compliance_rate >= (COMPLIANCE_THRESHOLD * 100)

        compliance = {
            "compliance_rate":  compliance_rate,
            "site_compliant":   site_compliant,
            "worker_count":     worker_count,
            "helmet_count":     helmets,
            "vest_count":       vests,
            "total_workers":    worker_count,
            "safe_workers":     compliant_workers,
            "unsafe_workers":   worker_count - compliant_workers,
            "violations":       no_helmet + no_vest,
        }

        # ── Visualization ───────────────────────────────────────────────────
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        viz_path  = output_dir / f"{image_path.stem}_viz.png"
        json_path = output_dir / f"{image_path.stem}_detections.json"

        if save_viz and detections:
            draw_detections(image_path, detections, viz_path)
            result["viz_path"] = str(viz_path)

        # Save JSON
        json_data = {
            "filename":     image_path.name,
            "mode":         result["mode"],
            "detections":   detections,
            "class_counts": class_counts,
            "compliance":   compliance,
            "avg_confidence": avg_conf,
            "detected_at":  result["detected_at"],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)
        result["json_path"] = str(json_path)

        # ── Final result ────────────────────────────────────────────────────
        result["detections"]     = detections
        result["class_counts"]   = class_counts
        result["total_objects"]  = len(detections)
        result["avg_confidence"] = avg_conf
        result["compliance"]     = compliance
        result["success"]        = True

        logger.info(
            "Module 3 (%s): %s → %d detections, %.1f%% compliance",
            result["mode"], image_path.name, len(detections), compliance_rate
        )

    except Exception as exc:
        result["error"] = str(exc)
        logger.error("Module 3 detection failed for %s: %s", image_path.name, exc, exc_info=True)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Real YOLOv8 Inference (activated when model_path + ultralytics are present)
# ─────────────────────────────────────────────────────────────────────────────

def _run_yolov8(
    image_path:  Path,
    model_path:  str,
    conf_thresh: float,
    iou_thresh:  float,
    class_names: List[str],
) -> List[Dict[str, Any]]:
    """
    Run YOLOv8 inference and return detections in standard format.

    This function is only called when ultralytics is installed and a model
    weight file (.pt) is present at model_path.
    """
    from ultralytics import YOLO

    model   = YOLO(model_path)
    results = model(str(image_path), conf=conf_thresh, iou=iou_thresh, verbose=False)
    detections = []

    for r in results:
        boxes = r.boxes
        if boxes is None:
            continue
        for box in boxes:
            class_id  = int(box.cls[0].item())
            if class_id >= len(class_names):
                continue
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            confidence = round(float(box.conf[0].item()), 3)
            class_name = class_names[class_id]
            area_px    = max(0, (x2 - x1) * (y2 - y1))
            bw = (x2 - x1) / max(r.orig_shape[1], 1)
            bh = (y2 - y1) / max(r.orig_shape[0], 1)
            xc = (x1 + x2) / 2 / max(r.orig_shape[1], 1)
            yc = (y1 + y2) / 2 / max(r.orig_shape[0], 1)

            detections.append({
                "class_id":   class_id,
                "class_name": class_name,
                "confidence": confidence,
                "bbox":       [x1, y1, x2, y2],
                "bbox_norm":  [round(xc, 4), round(yc, 4), round(bw, 4), round(bh, 4)],
                "area_px":    area_px,
            })

    return detections


# ─────────────────────────────────────────────────────────────────────────────
# Batch Detector
# ─────────────────────────────────────────────────────────────────────────────

def detect_batch(
    items:         Optional[List[Dict]] = None,
    output_dir:    Path = None,
    config:        Dict = None,
    max_items:     int  = 50,
    roboflow_root: Path = None,
    images:        Optional[List[Path]] = None,
) -> Dict[str, Any]:
    """
    Run Module 3 detection on a batch of images.

    Args:
        items:         List of dicts, each with an 'image_path' key.
        output_dir:    Root output directory.
        config:        Optional config overrides.
        max_items:     Cap on items processed per call.
        roboflow_root: Roboflow dataset root (for label lookup in simulation).
        images:        Optional list of image paths (for tests).

    Returns:
        Batch result dict with per-item results and aggregate statistics.
    """
    if items is None:
        if images is not None:
            items = [{"image_path": str(img)} for img in images]
        else:
            raise ValueError("Either items or images must be provided")

    items   = items[:max_items]
    results = []
    ok      = 0
    fail    = 0

    aggregate_counts = {c: 0 for c in CLASSES}
    total_detections = 0
    total_compliance = []

    for item in items:
        path = item.get("image_path") or item.get("file_path") or item.get("output_path", "")
        if not path:
            results.append({"success": False, "error": "No image path"})
            fail += 1
            continue

        img_out = Path(output_dir) / Path(path).stem
        res     = detect_image(
            image_path    = Path(path),
            output_dir    = img_out,
            config        = config,
            roboflow_root = roboflow_root,
        )
        results.append(res)

        if res.get("success"):
            ok += 1
            total_detections += res.get("total_objects", 0)
            for cls, cnt in res.get("class_counts", {}).items():
                aggregate_counts[cls] = aggregate_counts.get(cls, 0) + cnt
            cr = res.get("compliance", {}).get("compliance_rate", 0)
            total_compliance.append(cr)
        else:
            fail += 1

    avg_compliance = round(sum(total_compliance) / len(total_compliance), 1) if total_compliance else 0.0

    logger.info("Module 3 batch: %d/%d succeeded, %d total detections", ok, len(items), total_detections)

    return {
        "total":             len(items),
        "succeeded":         ok,
        "failed":            fail,
        "total_detections":  total_detections,
        "aggregate_counts":  aggregate_counts,
        "avg_compliance":    avg_compliance,
        "results":           results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Roboflow Dataset Detection (scans images from the Roboflow split)
# ─────────────────────────────────────────────────────────────────────────────

def detect_roboflow_split(
    roboflow_root: Path,
    split:         str,
    output_dir:    Path,
    config:        Dict = None,
    max_items:     int  = 30,
) -> Dict[str, Any]:
    """
    Run detection on a split of the Roboflow Construction dataset.

    Automatically pairs each image with its YOLO label file (simulation mode)
    or runs YOLOv8 inference.

    Args:
        roboflow_root: Root path of the Roboflow dataset.
        split:         'train' | 'valid' | 'test'
        output_dir:    Directory for output files.
        config:        Optional config.
        max_items:     Max images to process.

    Returns:
        Batch result dict.
    """
    roboflow_root = Path(roboflow_root)
    images_dir    = roboflow_root / split / "images"

    if not images_dir.exists():
        return {
            "total": 0, "succeeded": 0, "failed": 0,
            "error": f"Images directory not found: {images_dir}",
        }

    image_files = sorted(images_dir.glob("*.jpg")) + \
                  sorted(images_dir.glob("*.jpeg")) + \
                  sorted(images_dir.glob("*.png"))
    image_files = image_files[:max_items]

    items = [{"image_path": str(f)} for f in image_files]

    return detect_batch(
        items         = items,
        output_dir    = output_dir,
        config        = config,
        max_items     = max_items,
        roboflow_root = roboflow_root,
    )
