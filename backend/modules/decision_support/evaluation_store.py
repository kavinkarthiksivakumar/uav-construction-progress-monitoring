"""
Dataset / Model Evaluation Store
================================

Loads REAL, reproducible evaluation results that were generated offline by:
    evaluate_change_detection.py  ->  reports/evaluation/change_detection_eval.json
    evaluate_detection.py         ->  reports/evaluation/detection_eval.json

These results are clearly separated into two categories and must never be
presented as live project inspection metrics:

  A. CHANGE DETECTION BASELINE EVALUATION
     Classical CV baseline (CLAHE + differencing + Otsu + morphology) scored
     against LEVIR-CD+ and SYSU-CD ground-truth masks.
     Metrics: IoU, Precision, Recall, F1-score, Pixel Accuracy.

  B. DETECTION DATASET ANNOTATION ANALYSIS
     Roboflow Construction Site Safety dataset statistics derived from the
     actual YOLO label files (annotation counts, class distribution,
     per-image compliance) — explicitly NOT trained-model mAP metrics.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("decision.eval_store")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EVAL_DIR = PROJECT_ROOT / "reports" / "evaluation"
CHANGE_EVAL_FILE = EVAL_DIR / "change_detection_eval.json"
DETECTION_EVAL_FILE = EVAL_DIR / "detection_eval.json"


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Could not load evaluation file %s: %s", path, exc)
        return None


def _summarise_change_dataset(name: str, block: Dict[str, Any]) -> Dict[str, Any]:
    agg = block.get("aggregate_metrics", {})
    return {
        "dataset":           block.get("dataset", name),
        "split":             block.get("split"),
        "evaluated_pairs":   block.get("evaluated_pairs"),
        "gt_evaluated":      block.get("gt_evaluated"),
        "errors":            block.get("errors"),
        "iou":               round(agg.get("iou_mean", 0.0), 4),
        "iou_std":           round(agg.get("iou_std", 0.0), 4),
        "precision":         round(agg.get("precision_mean", 0.0), 4),
        "recall":            round(agg.get("recall_mean", 0.0), 4),
        "f1_score":          round(agg.get("f1_mean", 0.0), 4),
        "pixel_accuracy":    round(agg.get("pixel_accuracy_mean", 0.0), 4),
    }


def load_change_detection_eval(include_per_pair: bool = False) -> Dict[str, Any]:
    """
    Return the classical change-detection baseline evaluation
    computed against real ground-truth masks (LEVIR-CD+ & SYSU-CD).
    """
    raw = _load_json(CHANGE_EVAL_FILE)
    if not raw:
        return {
            "available": False,
            "unavailable_reason": (
                f"Evaluation file not found at {CHANGE_EVAL_FILE}. "
                "Run 'py evaluate_change_detection.py' to (re)generate it."
            ),
        }

    results_raw = raw.get("results", {})
    datasets = {k: _summarise_change_dataset(k, v) for k, v in results_raw.items()}

    response = {
        "available": True,
        "category_title": "A — Change Detection Baseline Evaluation",
        "methodology_label": (
            f"Classical Change Detection Baseline — {raw.get('algorithm', '')}"
        ),
        "integrity_note": raw.get("note",
            "Metrics are real values computed from actual dataset ground-truth masks."),
        "important_disclosure": (
            "These are CLASSICAL COMPUTER-VISION BASELINE results evaluated against "
            "ground-truth masks. They are NOT trained deep-learning model performance "
            "and must not be presented as such."
        ),
        "generated_at": raw.get("generated_at"),
        "elapsed_seconds": raw.get("elapsed_seconds"),
        "datasets": datasets,
    }

    if include_per_pair:
        response["per_pair_results"] = {
            k: v.get("per_pair_results", []) for k, v in results_raw.items()
        }

    return response


def _summarise_detection_split(split_key: str, block: Dict[str, Any]) -> Dict[str, Any]:
    counts = block.get("class_counts", {})
    safe = sum(int(counts.get(k, 0)) for k in ("Hardhat", "Mask", "Safety Vest"))
    risk = sum(int(counts.get(k, 0)) for k in ("NO-Hardhat", "NO-Mask", "NO-Safety Vest"))
    activity = sum(
        int(counts.get(k, 0)) for k in ("Person", "machinery", "vehicle", "Safety Cone")
    )
    return {
        "split":                    split_key,
        "images_processed":         block.get("images_processed"),
        "images_with_labels":       block.get("images_with_labels"),
        "total_detections":         block.get("total_detections"),
        "avg_detections_per_image": block.get("avg_detections_per_image"),
        "class_counts":             counts,
        "compliance_groups": {
            "safety_equipment": safe,
            "violations":       risk,
            "site_activity":    activity,
        },
        "compliance_rate_pct":      round(block.get("compliance_rate", 0) * 100, 2),
    }


def load_detection_eval() -> Dict[str, Any]:
    """
    Return Roboflow dataset annotation statistics — real label-file analysis,
    explicitly labelled as dataset annotation analysis (not model performance).
    """
    raw = _load_json(DETECTION_EVAL_FILE)
    if not raw:
        return {
            "available": False,
            "unavailable_reason": (
                f"Detection evaluation file not found at {DETECTION_EVAL_FILE}. "
                "Run 'py evaluate_detection.py' to (re)generate it."
            ),
        }

    results_raw = raw.get("results", {})
    splits = {k: _summarise_detection_split(k, v) for k, v in results_raw.items()}

    total_images = sum(v.get("images_processed") or 0 for v in results_raw.values())
    total_dets = sum(v.get("total_detections") or 0 for v in results_raw.values())

    merged_counts: Dict[str, int] = {}
    for v in results_raw.values():
        for cls, cnt in (v.get("class_counts") or {}).items():
            merged_counts[cls] = merged_counts.get(cls, 0) + int(cnt)

    return {
        "available": True,
        "category_title": "B — Detection Dataset Annotation Analysis",
        "dataset_name": "Roboflow Construction Site Safety",
        "mode": raw.get("mode"),
        "important_disclosure": (
            "These statistics are computed from actual dataset ANNOTATION FILES "
            "(YOLO label reads). They describe the DATASET composition only and are "
            "NOT trained-YOLO model performance metrics. No mAP/precision/recall for "
            "a trained detector is claimed."
        ),
        "classes": raw.get("classes", []),
        "safe_classes": raw.get("safe_classes", []),
        "risk_classes": raw.get("risk_classes", []),
        "totals": {
            "images": total_images,
            "annotations": total_dets,
        },
        "class_distribution_total": dict(sorted(merged_counts.items(), key=lambda kv: -kv[1])),
        "splits": splits,
        "generated_at": raw.get("generated_at"),
    }
