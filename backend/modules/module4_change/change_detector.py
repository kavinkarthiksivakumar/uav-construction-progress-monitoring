"""
Module 4: Change Detector
Final Year Project — Construction Change Detection

Detects changed regions between two temporal (before/after) UAV images
using the LEVIR-CD dataset bi-temporal pairs.

Techniques Used:
  1. Absolute difference map between image pair (A=before, B=after)
  2. CLAHE contrast enhancement before differencing
  3. Gaussian smoothing to reduce noise
  4. Otsu / adaptive thresholding to produce binary change mask
  5. Connected component analysis to locate individual change regions
  6. Morphological operations (closing) to fill small gaps

Output per pair:
  - Binary change mask PNG
  - Overlay PNG (change regions highlighted on image B)
  - JSON result with change_percent, num_regions, region_bboxes, stats

Interface is compatible with real deep-learning models (e.g., FC-EF, BIT)
that can be plugged in via config["model_path"] without touching anything else.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("module4.change_detector")

# Default change detection config (overridable via MODULE4 in settings.py)
DEFAULT_CONFIG = {
    "target_size":      (512, 512),
    "threshold_method": "otsu",     # 'otsu' | 'adaptive' | 'fixed'
    "fixed_threshold":  30,         # used only when threshold_method == 'fixed'
    "min_change_area":  100,        # minimum pixel area to count as a region
    "morph_kernel":     5,          # morphological closing kernel size
    "blur_sigma":       1.5,        # Gaussian blur sigma before differencing
    "save_overlay":     True,
    "save_mask":        True,
    "model_path":       None,       # set to .pth/.onnx path to use deep model
}

# Overlay highlight colour (BGR for OpenCV) — bright yellow-green
CHANGE_OVERLAY_COLOR = (0, 230, 200)


# ─────────────────────────────────────────────────────────────────────────────
# Core: Detect Changes in a Single Pair
# ─────────────────────────────────────────────────────────────────────────────

def detect_change_pair(
    image_a:    Path,
    image_b:    Path,
    output_dir: Path,
    config:     Dict = None,
) -> Dict[str, Any]:
    """
    Run Module 4 change detection on one before/after image pair.

    Args:
        image_a:    Path to the "before" image (Time-1).
        image_b:    Path to the "after"  image (Time-2).
        output_dir: Where to save outputs (mask, overlay, JSON).
        config:     Optional config overrides.

    Returns:
        Result dict with change_percent, num_regions, region_bboxes, paths.
    """
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    image_a = Path(image_a)
    image_b = Path(image_b)

    result: Dict[str, Any] = {
        "pair_id":       f"{image_a.stem}__{image_b.stem}",
        "image_a":       str(image_a),
        "image_b":       str(image_b),
        "success":       False,
        "mode":          "classical",
        "change_percent": 0.0,
        "changed_pixels": 0,
        "total_pixels":   0,
        "num_regions":    0,
        "region_bboxes":  [],
        "region_areas":   [],
        "mask_path":      None,
        "overlay_path":   None,
        "json_path":      None,
        "stats":          {},
        "detected_at":    datetime.now(timezone.utc).isoformat(),
        "error":          None,
    }

    try:
        import cv2
        import numpy as np

        # ── Load and resize both images ───────────────────────────────────
        target_w, target_h = cfg["target_size"]

        img_a_raw = cv2.imread(str(image_a))
        img_b_raw = cv2.imread(str(image_b))

        if img_a_raw is None or img_b_raw is None:
            missing = str(image_a) if img_a_raw is None else str(image_b)
            raise ValueError(f"Could not read image: {missing}")

        img_a = cv2.resize(img_a_raw, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        img_b = cv2.resize(img_b_raw, (target_w, target_h), interpolation=cv2.INTER_LINEAR)

        # ── Deep model mode ───────────────────────────────────────────────
        model_path = cfg.get("model_path")
        if model_path and Path(model_path).exists():
            change_mask = _run_deep_model(img_a, img_b, model_path, cfg)
            result["mode"] = "deep_model"
        else:
            # ── Classical differencing pipeline ───────────────────────────
            change_mask = _classical_change_detection(img_a, img_b, cfg)
            result["mode"] = "classical"

        # ── Statistics ────────────────────────────────────────────────────
        total_px   = target_w * target_h
        changed_px = int(np.sum(change_mask > 0))
        change_pct = round(changed_px / total_px * 100, 2)

        # Connected components → individual change regions
        num_labels, labels, stats_cc, centroids = cv2.connectedComponentsWithStats(
            change_mask, connectivity=8
        )

        regions = []
        region_areas = []
        min_area = cfg["min_change_area"]

        for i in range(1, num_labels):  # skip background (label 0)
            area = int(stats_cc[i, cv2.CC_STAT_AREA])
            if area < min_area:
                continue
            x = int(stats_cc[i, cv2.CC_STAT_LEFT])
            y = int(stats_cc[i, cv2.CC_STAT_TOP])
            w = int(stats_cc[i, cv2.CC_STAT_WIDTH])
            h = int(stats_cc[i, cv2.CC_STAT_HEIGHT])
            regions.append([x, y, x + w, y + h])
            region_areas.append(area)

        # Intensity stats of diff map
        gray_a  = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)
        gray_b  = cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY)
        diff    = cv2.absdiff(gray_a.astype(np.float32), gray_b.astype(np.float32))
        mean_d  = round(float(np.mean(diff)), 2)
        max_d   = round(float(np.max(diff)),  2)
        std_d   = round(float(np.std(diff)),  2)

        # ── Save outputs ─────────────────────────────────────────────────
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        stem = f"{image_a.stem}__{image_b.stem}"
        mask_path    = output_dir / f"{stem}_mask.png"
        overlay_path = output_dir / f"{stem}_overlay.png"
        json_path    = output_dir / f"{stem}_change.json"

        if cfg["save_mask"]:
            cv2.imwrite(str(mask_path), change_mask)
            result["mask_path"] = str(mask_path)

        if cfg["save_overlay"]:
            overlay = _draw_change_overlay(img_b.copy(), change_mask, regions)
            cv2.imwrite(str(overlay_path), overlay)
            result["overlay_path"] = str(overlay_path)

        # Save JSON
        json_data = {
            "pair_id":        result["pair_id"],
            "mode":           result["mode"],
            "change_percent": change_pct,
            "changed_pixels": changed_px,
            "total_pixels":   total_px,
            "num_regions":    len(regions),
            "region_bboxes":  regions,
            "region_areas":   region_areas,
            "diff_stats":     {"mean": mean_d, "max": max_d, "std": std_d},
            "detected_at":    result["detected_at"],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)
        result["json_path"] = str(json_path)

        # ── Populate result ───────────────────────────────────────────────
        result["change_percent"] = change_pct
        result["changed_pixels"] = changed_px
        result["total_pixels"]   = total_px
        result["num_regions"]    = len(regions)
        result["region_bboxes"]  = regions
        result["region_areas"]   = region_areas
        result["stats"]          = {"mean_diff": mean_d, "max_diff": max_d, "std_diff": std_d}
        result["success"]        = True

        logger.info(
            "Module 4 (%s): %s -> %.2f%% changed, %d regions",
            result["mode"], stem, change_pct, len(regions)
        )

    except Exception as exc:
        result["error"] = str(exc)
        logger.error("Module 4 failed for pair (%s, %s): %s",
                     image_a.name, image_b.name, exc, exc_info=True)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Classical Change Detection Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def _classical_change_detection(img_a, img_b, cfg: Dict):
    """
    Produce a binary change mask using classical image differencing.
    Steps: grayscale → CLAHE → Gaussian blur → absdiff → threshold → morph close
    """
    import cv2
    import numpy as np

    # Grayscale
    gray_a = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY)

    # CLAHE contrast enhancement (helps reveal subtle changes)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_a = clahe.apply(gray_a)
    gray_b = clahe.apply(gray_b)

    # Gaussian blur
    sigma = cfg.get("blur_sigma", 1.5)
    ksize = max(3, int(sigma * 6) | 1)  # odd kernel size
    gray_a = cv2.GaussianBlur(gray_a, (ksize, ksize), sigma)
    gray_b = cv2.GaussianBlur(gray_b, (ksize, ksize), sigma)

    # Absolute difference
    diff = cv2.absdiff(gray_a, gray_b)

    # Threshold
    method = cfg.get("threshold_method", "otsu")
    if method == "otsu":
        _, mask = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == "adaptive":
        mask = cv2.adaptiveThreshold(
            diff, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    else:  # fixed
        tval = int(cfg.get("fixed_threshold", 30))
        _, mask = cv2.threshold(diff, tval, 255, cv2.THRESH_BINARY)

    # Morphological closing (fill holes)
    k = int(cfg.get("morph_kernel", 5))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)

    return mask


# ─────────────────────────────────────────────────────────────────────────────
# Draw Overlay
# ─────────────────────────────────────────────────────────────────────────────

def _draw_change_overlay(img_b, change_mask, regions: List):
    """
    Highlight changed pixels in green on image B and draw region bounding boxes.
    """
    import cv2
    import numpy as np

    overlay = img_b.copy()

    # Colour changed pixels
    overlay[change_mask > 0] = (0, 220, 120)  # green tint

    # Alpha blend
    result = cv2.addWeighted(img_b, 0.5, overlay, 0.5, 0)

    # Draw bounding boxes of regions
    for (x1, y1, x2, y2) in regions:
        cv2.rectangle(result, (x1, y1), (x2, y2), (0, 240, 180), 2)

    # Summary text
    cv2.putText(
        result, f"Changed Regions: {len(regions)}",
        (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
        (0, 230, 200), 2, cv2.LINE_AA
    )

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Deep Model Stub (activated when model_path is set)
# ─────────────────────────────────────────────────────────────────────────────

def _run_deep_model(img_a, img_b, model_path: str, cfg: Dict):
    """
    Placeholder for deep-learning change detection (FC-EF, BIT, ChangeFormer).
    Replace this body with actual model inference when the .pth file is ready.
    Falls back to classical if model loading fails.
    """
    try:
        # Example skeleton — replace with actual model inference
        import onnxruntime as ort
        import numpy as np

        sess = ort.InferenceSession(str(model_path))
        inp_name = sess.get_inputs()[0].name

        def preprocess(img):
            t = img[:, :, ::-1].astype(np.float32) / 255.0
            t = (t - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
            return t.transpose(2, 0, 1)[None].astype(np.float32)

        out = sess.run(None, {inp_name: np.concatenate([preprocess(img_a), preprocess(img_b)], axis=1)})[0]
        mask = (out[0, 0] > 0.5).astype(np.uint8) * 255
        return mask

    except Exception as exc:
        logger.warning("Deep model failed (%s), falling back to classical: %s", model_path, exc)
        return _classical_change_detection(img_a, img_b, cfg)


# ─────────────────────────────────────────────────────────────────────────────
# Batch Detection over LEVIR-CD Pairs
# ─────────────────────────────────────────────────────────────────────────────

def detect_levir_batch(
    pairs:      List[Dict],
    output_dir: Path,
    config:     Dict = None,
    max_pairs:  int  = 20,
) -> Dict[str, Any]:
    """
    Run Module 4 change detection on a batch of LEVIR-CD image pairs.

    Args:
        pairs:      List of dicts, each with 'image_a' and 'image_b' keys.
        output_dir: Root directory for all outputs.
        config:     Optional config overrides.
        max_pairs:  Cap on pairs processed per call.

    Returns:
        Batch result dict with per-pair results and aggregate stats.
    """
    pairs      = pairs[:max_pairs]
    results    = []
    ok         = 0
    fail       = 0
    total_pct  = []

    for pair in pairs:
        a = pair.get("image_a") or pair.get("A") or pair.get("before", "")
        b = pair.get("image_b") or pair.get("B") or pair.get("after",  "")
        if not a or not b:
            results.append({"success": False, "error": "Missing image paths"})
            fail += 1
            continue

        pair_out = Path(output_dir) / Path(a).stem
        res      = detect_change_pair(
            image_a    = Path(a),
            image_b    = Path(b),
            output_dir = pair_out,
            config     = config,
        )
        results.append(res)

        if res["success"]:
            ok += 1
            total_pct.append(res["change_percent"])
        else:
            fail += 1

    avg_change = round(sum(total_pct) / len(total_pct), 2) if total_pct else 0.0
    max_change = round(max(total_pct), 2) if total_pct else 0.0
    min_change = round(min(total_pct), 2) if total_pct else 0.0

    logger.info(
        "Module 4 batch: %d/%d succeeded, avg change %.2f%%",
        ok, len(pairs), avg_change
    )

    return {
        "total":       len(pairs),
        "succeeded":   ok,
        "failed":      fail,
        "avg_change":  avg_change,
        "max_change":  max_change,
        "min_change":  min_change,
        "results":     results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LEVIR-CD Split Scanner + Detector
# ─────────────────────────────────────────────────────────────────────────────

def detect_levir_split(
    levir_root: Path,
    split:      str,
    output_dir: Path,
    config:     Dict = None,
    max_pairs:  int  = 20,
) -> Dict[str, Any]:
    """
    Auto-scan a LEVIR-CD split folder and run change detection on found pairs.

    Expected LEVIR-CD structure:
      <split>/A/  — Time-1 images
      <split>/B/  — Time-2 images
      <split>/label/ — Ground-truth masks (optional)

    Args:
        levir_root: Root of the LEVIR-CD dataset.
        split:      'train' | 'val' | 'test'
        output_dir: Where to save outputs.
        config:     Optional config overrides.
        max_pairs:  Max pairs to process.

    Returns:
        Batch result dict.
    """
    levir_root = Path(levir_root)
    dir_a      = levir_root / split / "A"
    dir_b      = levir_root / split / "B"

    if not dir_a.exists() or not dir_b.exists():
        return {
            "total": 0, "succeeded": 0, "failed": 0,
            "error": f"Directories not found: {dir_a} or {dir_b}",
        }

    exts   = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    files_a = sorted(f for f in dir_a.iterdir() if f.suffix.lower() in exts)
    files_b = sorted(f for f in dir_b.iterdir() if f.suffix.lower() in exts)

    # Pair by matching stem name
    stems_b = {f.stem: f for f in files_b}
    pairs   = [
        {"image_a": str(fa), "image_b": str(stems_b[fa.stem])}
        for fa in files_a
        if fa.stem in stems_b
    ]

    if not pairs:
        return {
            "total": 0, "succeeded": 0, "failed": 0,
            "error": "No matching A/B pairs found (check filenames match)",
        }

    return detect_levir_batch(
        pairs      = pairs[:max_pairs],
        output_dir = Path(output_dir),
        config     = config,
        max_pairs  = max_pairs,
    )
