"""
Module 4: Change Metrics & Report Generator
IEEE M.Tech Project — Construction Change Detection

Computes construction-domain metrics from change detection results:
  - Progress rate (change / total over time)
  - Change severity classification (low / moderate / high / critical)
  - Comparison vs ground-truth mask (if available) → IoU, precision, recall
  - Site-level aggregated change report
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("module4.metrics")

# Severity thresholds (% changed pixels)
SEVERITY_THRESHOLDS = {
    "low":      (0,    5),
    "moderate": (5,   20),
    "high":     (20,  50),
    "critical": (50, 100),
}

SEVERITY_COLORS = {
    "low":      "#22c55e",
    "moderate": "#f59e0b",
    "high":     "#ef4444",
    "critical": "#dc2626",
}


def classify_severity(change_percent: float) -> str:
    """Return severity label for a given change percentage."""
    for label, (lo, hi) in SEVERITY_THRESHOLDS.items():
        if lo <= change_percent < hi:
            return label
    return "critical"


def compute_iou(pred_mask_path: Path, gt_mask_path: Path) -> Optional[Dict]:
    """
    Compute IoU, precision and recall between predicted change mask and ground truth.

    Args:
        pred_mask_path: Path to predicted binary mask PNG.
        gt_mask_path:   Path to ground-truth binary mask PNG.

    Returns:
        Dict with iou, precision, recall, f1 — or None if masks can't be loaded.
    """
    try:
        import cv2

        pred = cv2.imread(str(pred_mask_path), cv2.IMREAD_GRAYSCALE)
        gt   = cv2.imread(str(gt_mask_path),   cv2.IMREAD_GRAYSCALE)

        if pred is None or gt is None:
            return None

        # Resize gt to match pred if needed
        if pred.shape != gt.shape:
            gt = cv2.resize(gt, (pred.shape[1], pred.shape[0]), interpolation=cv2.INTER_NEAREST)

        pred_bin = (pred > 127).astype(np.uint8)
        gt_bin   = (gt   > 127).astype(np.uint8)

        tp = int(np.sum((pred_bin == 1) & (gt_bin == 1)))
        fp = int(np.sum((pred_bin == 1) & (gt_bin == 0)))
        fn = int(np.sum((pred_bin == 0) & (gt_bin == 1)))

        iou       = round(tp / max(tp + fp + fn, 1), 4)
        precision = round(tp / max(tp + fp, 1), 4)
        recall    = round(tp / max(tp + fn, 1), 4)
        f1        = round(2 * precision * recall / max(precision + recall, 1e-6), 4)

        return {"iou": iou, "precision": precision, "recall": recall, "f1": f1}

    except Exception as exc:
        logger.warning("IoU computation failed: %s", exc)
        return None


def aggregate_batch_metrics(results: List[Dict]) -> Dict[str, Any]:
    """
    Compute site-level aggregate metrics from a batch of pair results.

    Args:
        results: List of per-pair result dicts from detect_levir_batch.

    Returns:
        Aggregate stats dict.
    """
    successful = [r for r in results if r.get("success")]
    if not successful:
        return {"total": len(results), "succeeded": 0, "avg_change": 0.0}

    pcts      = [r["change_percent"] for r in successful]
    regions   = [r["num_regions"]    for r in successful]
    severities = [classify_severity(p) for p in pcts]

    severity_counts = {k: severities.count(k) for k in SEVERITY_THRESHOLDS}

    return {
        "total":          len(results),
        "succeeded":      len(successful),
        "avg_change":     round(float(np.mean(pcts)),  2),
        "max_change":     round(float(np.max(pcts)),   2),
        "min_change":     round(float(np.min(pcts)),   2),
        "std_change":     round(float(np.std(pcts)),   2),
        "avg_regions":    round(float(np.mean(regions)), 2),
        "total_regions":  int(np.sum(regions)),
        "severity_counts": severity_counts,
        "dominant_severity": max(severity_counts, key=severity_counts.get),
    }


def generate_change_report(
    batch_result: Dict,
    output_path:  Path,
) -> Path:
    """
    Write a JSON change detection report for a processed batch.

    Args:
        batch_result: Result dict from detect_levir_batch.
        output_path:  Where to save the report JSON.

    Returns:
        Path to the saved report.
    """
    from datetime import datetime

    metrics   = aggregate_batch_metrics(batch_result.get("results", []))
    report    = {
        "module":          "Module 4: Construction Change Detection",
        "generated_at":    datetime.utcnow().isoformat() + "Z",
        "summary":         metrics,
        "pair_results":    [
            {
                "pair_id":        r.get("pair_id"),
                "change_percent": r.get("change_percent"),
                "num_regions":    r.get("num_regions"),
                "severity":       classify_severity(r.get("change_percent", 0)),
                "mode":           r.get("mode"),
                "success":        r.get("success"),
                "error":          r.get("error"),
            }
            for r in batch_result.get("results", [])
        ],
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Change report saved: %s", output_path)
    return output_path
