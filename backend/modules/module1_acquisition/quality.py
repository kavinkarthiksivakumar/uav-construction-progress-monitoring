"""
Module 1: Image Quality Assessment
IEEE M.Tech Project — UAV Image Acquisition

Computes per-image quality metrics:
  - Blur Score    (Laplacian variance)
  - Brightness    (mean pixel intensity)
  - Contrast      (RMS contrast)
  - Resolution    (megapixel normalized score)

Produces an overall weighted quality score and Accept/Reject decision.
"""

import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple

logger = logging.getLogger("module1.quality")

# ─────────────────────────────────────────────────────────────────
# Default Thresholds (can be overridden via config)
# ─────────────────────────────────────────────────────────────────
BLUR_THRESHOLD      = 100.0     # Laplacian variance below → blurry
BRIGHTNESS_MIN      = 30        # Below → too dark
BRIGHTNESS_MAX      = 225       # Above → overexposed
CONTRAST_MIN        = 20        # Below → low contrast
ACCEPT_THRESHOLD    = 60.0      # Overall score to accept

WEIGHTS = {
    "blur":       0.35,
    "brightness": 0.25,
    "contrast":   0.25,
    "resolution": 0.15,
}


# ─────────────────────────────────────────────────────────────────
# Individual Metric Functions
# ─────────────────────────────────────────────────────────────────

def compute_blur_score(gray: np.ndarray) -> Tuple[float, str]:
    """
    Compute blur score using Laplacian variance.

    Higher variance = sharper image. Score is clipped and normalized 0-100.

    Args:
        gray: Grayscale image as numpy array.

    Returns:
        (score_0_100, status_string)
    """
    import cv2
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Normalize: 0 → 0, 500+ → 100
    score = min(100.0, (lap_var / 500.0) * 100.0)
    status = "sharp" if lap_var >= BLUR_THRESHOLD else "blurry"
    return round(score, 2), status


def compute_brightness_score(gray: np.ndarray) -> Tuple[float, str]:
    """
    Compute brightness score from mean pixel intensity.

    Args:
        gray: Grayscale image as numpy array.

    Returns:
        (score_0_100, status_string)
    """
    mean_val = float(gray.mean())
    # Ideal range: 80-180
    if mean_val < BRIGHTNESS_MIN:
        score = (mean_val / BRIGHTNESS_MIN) * 30
        status = "too_dark"
    elif mean_val > BRIGHTNESS_MAX:
        score = max(0.0, 100.0 - ((mean_val - BRIGHTNESS_MAX) / (255 - BRIGHTNESS_MAX)) * 50)
        status = "overexposed"
    else:
        # Map 30-225 → 0-100 with peak at ~128
        deviation = abs(mean_val - 128) / 100.0
        score = max(50.0, 100.0 - deviation * 50)
        status = "good"
    return round(score, 2), status


def compute_contrast_score(gray: np.ndarray) -> Tuple[float, str]:
    """
    Compute contrast score using RMS contrast (std deviation of pixel values).

    Args:
        gray: Grayscale image as numpy array.

    Returns:
        (score_0_100, status_string)
    """
    rms = float(gray.std())
    # Normalize: 0 → 0, 80+ → 100
    score = min(100.0, (rms / 80.0) * 100.0)
    status = "good" if rms >= CONTRAST_MIN else "low_contrast"
    return round(score, 2), status


def compute_resolution_score(width: int, height: int) -> Tuple[float, str]:
    """
    Compute resolution score based on megapixel count.

    Scale:
        < 0.5 MP → 20
        0.5 MP   → 40
        1   MP   → 60
        2   MP   → 75
        4+  MP   → 100

    Args:
        width:  Image width in pixels.
        height: Image height in pixels.

    Returns:
        (score_0_100, status_string)
    """
    mp = (width * height) / 1_000_000
    if mp >= 4.0:
        score, status = 100.0, "high_res"
    elif mp >= 2.0:
        score, status = 75.0 + (mp - 2.0) / 2.0 * 25.0, "good_res"
    elif mp >= 1.0:
        score, status = 60.0 + (mp - 1.0) * 15.0, "moderate_res"
    elif mp >= 0.5:
        score, status = 40.0 + (mp - 0.5) * 40.0, "low_res"
    else:
        score, status = mp * 80.0, "very_low_res"
    return round(min(score, 100.0), 2), status


# ─────────────────────────────────────────────────────────────────
# Overall Score
# ─────────────────────────────────────────────────────────────────

def compute_overall_score(metrics: Dict[str, float], weights: Dict = None) -> float:
    """
    Compute weighted overall quality score from individual metric scores.

    Args:
        metrics: Dict with keys 'blur', 'brightness', 'contrast', 'resolution'.
        weights: Optional custom weight dict (must sum to 1.0).

    Returns:
        Overall score 0–100.
    """
    w = weights or WEIGHTS
    score = (
        metrics.get("blur", 0)       * w["blur"]       +
        metrics.get("brightness", 0) * w["brightness"] +
        metrics.get("contrast", 0)   * w["contrast"]   +
        metrics.get("resolution", 0) * w["resolution"]
    )
    return round(score, 2)


# ─────────────────────────────────────────────────────────────────
# Main Quality Assessment
# ─────────────────────────────────────────────────────────────────

def assess_quality(
    file_path: Path,
    width:     int = 0,
    height:    int = 0,
) -> Dict[str, Any]:
    """
    Perform complete quality assessment on a single UAV image.

    Args:
        file_path: Path to the image file.
        width:     Known image width (optional, will be read if 0).
        height:    Known image height (optional, will be read if 0).

    Returns:
        Quality report dictionary with per-metric scores and Accept/Reject.
    """
    import cv2
    from PIL import Image

    file_path = Path(file_path)
    report: Dict[str, Any] = {
        "filename":      file_path.name,
        "blur_score":    0.0,
        "blur_status":   "unknown",
        "brightness_score":  0.0,
        "brightness_status": "unknown",
        "contrast_score":    0.0,
        "contrast_status":   "unknown",
        "resolution_score":  0.0,
        "resolution_status": "unknown",
        "overall_score": 0.0,
        "accepted":      False,
        "issues":        [],
    }

    try:
        # Load image as numpy array
        img_bgr = cv2.imread(str(file_path))
        if img_bgr is None:
            # Fallback to PIL → numpy
            with Image.open(file_path) as pil_img:
                pil_img = pil_img.convert("RGB")
                img_bgr = np.array(pil_img)[:, :, ::-1].copy()

        if img_bgr is None:
            report["issues"].append("Could not load image for quality assessment")
            return report

        h, w = img_bgr.shape[:2]
        if width  == 0: width  = w
        if height == 0: height = h

        # Convert to grayscale for metric computation
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)

        # ── Compute metrics ─────────────────────────────────────
        blur_s,  blur_st  = compute_blur_score(gray)
        bri_s,   bri_st   = compute_brightness_score(gray)
        con_s,   con_st   = compute_contrast_score(gray)
        res_s,   res_st   = compute_resolution_score(width, height)

        report["blur_score"]         = blur_s
        report["blur_status"]        = blur_st
        report["brightness_score"]   = bri_s
        report["brightness_status"]  = bri_st
        report["contrast_score"]     = con_s
        report["contrast_status"]    = con_st
        report["resolution_score"]   = res_s
        report["resolution_status"]  = res_st

        # ── Overall Score ───────────────────────────────────────
        metrics = {
            "blur":       blur_s,
            "brightness": bri_s,
            "contrast":   con_s,
            "resolution": res_s,
        }
        overall = compute_overall_score(metrics)
        report["overall_score"] = overall
        report["accepted"]      = overall >= ACCEPT_THRESHOLD

        # ── Issues Summary ──────────────────────────────────────
        if blur_st  == "blurry":       report["issues"].append("Image appears blurry")
        if bri_st   == "too_dark":     report["issues"].append("Image is underexposed / too dark")
        if bri_st   == "overexposed":  report["issues"].append("Image is overexposed")
        if con_st   == "low_contrast": report["issues"].append("Low contrast detected")
        if res_st   == "very_low_res": report["issues"].append("Very low resolution")

        logger.info(
            "Quality [%s]: blur=%.1f | bright=%.1f | contrast=%.1f | res=%.1f | overall=%.1f → %s",
            file_path.name, blur_s, bri_s, con_s, res_s, overall,
            "ACCEPTED" if report["accepted"] else "REJECTED"
        )

    except Exception as exc:
        report["issues"].append(f"Quality assessment error: {exc}")
        logger.error("Quality assessment failed for %s: %s", file_path.name, exc, exc_info=True)

    return report


# ─────────────────────────────────────────────────────────────────
# Batch Quality Report
# ─────────────────────────────────────────────────────────────────

def generate_quality_report(quality_results: list) -> Dict[str, Any]:
    """
    Summarize quality metrics across a batch of images.

    Args:
        quality_results: List of per-image quality report dicts.

    Returns:
        Aggregated quality report with statistics and histogram data.
    """
    if not quality_results:
        return {"total": 0, "accepted": 0, "rejected": 0}

    scores = [r["overall_score"] for r in quality_results]
    accepted = [r for r in quality_results if r["accepted"]]
    rejected = [r for r in quality_results if not r["accepted"]]

    return {
        "total":           len(quality_results),
        "accepted":        len(accepted),
        "rejected":        len(rejected),
        "acceptance_rate": round(len(accepted) / len(quality_results) * 100, 1),
        "score_stats": {
            "mean":   round(float(np.mean(scores)),   2),
            "median": round(float(np.median(scores)), 2),
            "min":    round(float(np.min(scores)),    2),
            "max":    round(float(np.max(scores)),    2),
            "std":    round(float(np.std(scores)),    2),
        },
        "metric_averages": {
            "blur":       round(float(np.mean([r["blur_score"]       for r in quality_results])), 2),
            "brightness": round(float(np.mean([r["brightness_score"] for r in quality_results])), 2),
            "contrast":   round(float(np.mean([r["contrast_score"]   for r in quality_results])), 2),
            "resolution": round(float(np.mean([r["resolution_score"] for r in quality_results])), 2),
        },
        "per_image": quality_results,
    }
