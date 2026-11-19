"""
Evaluate Change Detection on LEVIR-CD+ and SYSU-CD test splits.
Final Year Project — Explainable Vision-Based Construction Progress Assessment

This script runs the Module 4 classical change detection pipeline against
the ground-truth binary masks from LEVIR-CD+ and SYSU-CD, and reports
real quantitative metrics: IoU, Precision, Recall, F1-score, Pixel Accuracy.

Usage:
    py -3 evaluate_change_detection.py [--levir-limit N] [--sysu-limit N]

Results are saved to:
    reports/evaluation/change_detection_eval.json
    reports/evaluation/change_detection_eval_summary.txt

IMPORTANT: These are REAL metrics computed from the actual datasets.
No values are fabricated or estimated.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# ─── Project root setup ────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import LEVIR_CD_ROOT, SYSU_CD_ROOT, REPORTS_DIR
from backend.modules.module4_change.change_detector import detect_change_pair

EVAL_DIR = REPORTS_DIR / "evaluation"
EVAL_DIR.mkdir(parents=True, exist_ok=True)


# ─── Ground-truth mask evaluation ─────────────────────────────────────────────

def evaluate_mask(pred_mask: np.ndarray, gt_mask: np.ndarray) -> dict:
    """
    Compute binary change detection metrics against a ground-truth mask.

    Args:
        pred_mask: Predicted binary mask (uint8, 0/255 or 0/1).
        gt_mask:   Ground-truth binary mask (uint8, 0/255 or 0/1).

    Returns:
        Dict with iou, precision, recall, f1, pixel_accuracy.
    """
    import cv2

    # Resize GT to match pred if needed
    if pred_mask.shape != gt_mask.shape:
        gt_mask = cv2.resize(
            gt_mask, (pred_mask.shape[1], pred_mask.shape[0]),
            interpolation=cv2.INTER_NEAREST,
        )

    pred_bin = (pred_mask > 127).astype(np.uint8)
    gt_bin   = (gt_mask   > 127).astype(np.uint8)

    tp = int(np.sum((pred_bin == 1) & (gt_bin == 1)))
    fp = int(np.sum((pred_bin == 1) & (gt_bin == 0)))
    fn = int(np.sum((pred_bin == 0) & (gt_bin == 1)))
    tn = int(np.sum((pred_bin == 0) & (gt_bin == 0)))

    iou           = round(tp / max(tp + fp + fn, 1), 4)
    precision     = round(tp / max(tp + fp, 1), 4)
    recall        = round(tp / max(tp + fn, 1), 4)
    f1            = round(2 * precision * recall / max(precision + recall, 1e-9), 4)
    pixel_accuracy = round((tp + tn) / max(tp + fp + fn + tn, 1), 4)

    return {
        "iou":            iou,
        "precision":      precision,
        "recall":         recall,
        "f1":             f1,
        "pixel_accuracy": pixel_accuracy,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }


def aggregate_metrics(metrics_list: list) -> dict:
    """Compute mean and std of each metric across all pairs."""
    if not metrics_list:
        return {}
    keys = ["iou", "precision", "recall", "f1", "pixel_accuracy"]
    agg = {}
    for k in keys:
        vals = [m[k] for m in metrics_list if k in m]
        if vals:
            agg[f"{k}_mean"] = round(float(np.mean(vals)), 4)
            agg[f"{k}_std"]  = round(float(np.std(vals)),  4)
            agg[f"{k}_min"]  = round(float(np.min(vals)),  4)
            agg[f"{k}_max"]  = round(float(np.max(vals)),  4)
    return agg


# ─── LEVIR-CD+ evaluation ─────────────────────────────────────────────────────

def evaluate_levir(levir_root: Path, limit: int = 50, output_dir: Path = None) -> dict:
    """
    Evaluate change detection on LEVIR-CD+ test split.

    Args:
        levir_root: Root of LEVIR-CD+ dataset (contains train/ and test/).
        limit:      Max pairs to evaluate (default 50 for speed; use -1 for all).
        output_dir: Directory for per-pair mask outputs.

    Returns:
        Evaluation result dict.
    """
    import cv2

    test_dir = levir_root / "test"
    a_dir    = test_dir / "A"
    b_dir    = test_dir / "B"
    lbl_dir  = test_dir / "label"

    if not a_dir.exists():
        return {"error": f"LEVIR test/A not found at {a_dir}", "evaluated": 0}

    image_files = sorted(a_dir.glob("*.png"))
    if limit > 0:
        image_files = image_files[:limit]

    print(f"\n[LEVIR-CD+] Evaluating {len(image_files)} pairs from {test_dir}")

    out_dir = (output_dir or EVAL_DIR) / "levir_predictions"
    out_dir.mkdir(parents=True, exist_ok=True)

    per_pair = []
    errors   = []

    for i, a_path in enumerate(image_files):
        stem   = a_path.stem
        b_path = b_dir   / a_path.name
        l_path = lbl_dir / a_path.name

        if not b_path.exists():
            errors.append({"stem": stem, "error": "B image missing"})
            continue

        try:
            result = detect_change_pair(
                image_a=a_path,
                image_b=b_path,
                output_dir=out_dir,
            )

            if not result.get("success"):
                errors.append({"stem": stem, "error": result.get("error", "unknown")})
                continue

            # Load predicted mask
            pred_mask_path = result.get("mask_path")
            gt_metrics = None
            if pred_mask_path and l_path.exists():
                pred_mask = cv2.imread(str(pred_mask_path), cv2.IMREAD_GRAYSCALE)
                gt_mask   = cv2.imread(str(l_path),          cv2.IMREAD_GRAYSCALE)
                if pred_mask is not None and gt_mask is not None:
                    gt_metrics = evaluate_mask(pred_mask, gt_mask)

            pair_result = {
                "pair_id":        f"levir_test_{stem}",
                "change_percent": result.get("change_percent", 0.0),
                "num_regions":    result.get("num_regions", 0),
                "has_gt":         l_path.exists(),
                "gt_metrics":     gt_metrics,
            }
            per_pair.append(pair_result)

            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(image_files)}] processed …")

        except Exception as exc:
            errors.append({"stem": stem, "error": str(exc)})

    # Aggregate GT metrics only for pairs where GT was available
    gt_metric_list = [p["gt_metrics"] for p in per_pair if p.get("gt_metrics")]
    agg = aggregate_metrics(gt_metric_list)

    print(f"  Completed: {len(per_pair)} pairs | GT metrics: {len(gt_metric_list)} pairs")
    if agg:
        print(f"  IoU={agg.get('iou_mean', 'N/A')}  F1={agg.get('f1_mean', 'N/A')}  "
              f"Prec={agg.get('precision_mean', 'N/A')}  Rec={agg.get('recall_mean', 'N/A')}  "
              f"Acc={agg.get('pixel_accuracy_mean', 'N/A')}")

    return {
        "dataset":          "LEVIR-CD+",
        "split":            "test",
        "evaluated_pairs":  len(per_pair),
        "gt_evaluated":     len(gt_metric_list),
        "errors":           len(errors),
        "aggregate_metrics": agg,
        "per_pair_results":  per_pair,
        "error_list":        errors,
    }


# ─── SYSU-CD evaluation ────────────────────────────────────────────────────────

def evaluate_sysu(sysu_root: Path, limit: int = 50, output_dir: Path = None) -> dict:
    """
    Evaluate change detection on SYSU-CD test split.

    SYSU-CD structure: test/test/{time1,time2,label}/
    """
    import cv2

    # Handle nested vs flat structure:
    # train → train/train/{time1,time2,label}
    # val   → val/val/{time1,time2,label}
    # test  → test/{time1,time2,label}  (flat, no double nest)
    test_root = sysu_root / "test"
    if not (test_root / "time1").exists():
        # Try nested: test/test/time1
        nested = test_root / "test"
        if (nested / "time1").exists():
            test_root = nested

    t1_dir  = test_root / "time1"
    t2_dir  = test_root / "time2"
    lbl_dir = test_root / "label"

    if not t1_dir.exists():
        return {"error": f"SYSU test/time1 not found at {t1_dir}", "evaluated": 0}

    image_files = sorted(t1_dir.glob("*.png"))
    if limit > 0:
        image_files = image_files[:limit]

    print(f"\n[SYSU-CD] Evaluating {len(image_files)} pairs from {test_root}")

    out_dir = (output_dir or EVAL_DIR) / "sysu_predictions"
    out_dir.mkdir(parents=True, exist_ok=True)

    per_pair = []
    errors   = []

    for i, t1_path in enumerate(image_files):
        stem   = t1_path.stem
        t2_path  = t2_dir  / t1_path.name
        lbl_path = lbl_dir / t1_path.name

        if not t2_path.exists():
            errors.append({"stem": stem, "error": "time2 image missing"})
            continue

        try:
            result = detect_change_pair(
                image_a=t1_path,
                image_b=t2_path,
                output_dir=out_dir,
            )

            if not result.get("success"):
                errors.append({"stem": stem, "error": result.get("error", "unknown")})
                continue

            pred_mask_path = result.get("mask_path")
            gt_metrics = None
            if pred_mask_path and lbl_path.exists():
                pred_mask = cv2.imread(str(pred_mask_path), cv2.IMREAD_GRAYSCALE)
                gt_mask   = cv2.imread(str(lbl_path),        cv2.IMREAD_GRAYSCALE)
                if pred_mask is not None and gt_mask is not None:
                    gt_metrics = evaluate_mask(pred_mask, gt_mask)

            per_pair.append({
                "pair_id":        f"sysu_test_{stem}",
                "change_percent": result.get("change_percent", 0.0),
                "num_regions":    result.get("num_regions", 0),
                "has_gt":         lbl_path.exists(),
                "gt_metrics":     gt_metrics,
            })

            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(image_files)}] processed …")

        except Exception as exc:
            errors.append({"stem": stem, "error": str(exc)})

    gt_metric_list = [p["gt_metrics"] for p in per_pair if p.get("gt_metrics")]
    agg = aggregate_metrics(gt_metric_list)

    print(f"  Completed: {len(per_pair)} pairs | GT metrics: {len(gt_metric_list)} pairs")
    if agg:
        print(f"  IoU={agg.get('iou_mean', 'N/A')}  F1={agg.get('f1_mean', 'N/A')}  "
              f"Prec={agg.get('precision_mean', 'N/A')}  Rec={agg.get('recall_mean', 'N/A')}  "
              f"Acc={agg.get('pixel_accuracy_mean', 'N/A')}")

    return {
        "dataset":          "SYSU-CD",
        "split":            "test",
        "evaluated_pairs":  len(per_pair),
        "gt_evaluated":     len(gt_metric_list),
        "errors":           len(errors),
        "aggregate_metrics": agg,
        "per_pair_results":  per_pair,
        "error_list":        errors,
    }


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Module 4 change detection against LEVIR-CD+ and SYSU-CD."
    )
    parser.add_argument("--levir-limit", type=int, default=50,
                        help="Max LEVIR pairs to evaluate (default: 50, -1 for all 348)")
    parser.add_argument("--sysu-limit",  type=int, default=50,
                        help="Max SYSU pairs to evaluate (default: 50, -1 for all 720)")
    parser.add_argument("--skip-levir",  action="store_true")
    parser.add_argument("--skip-sysu",   action="store_true")
    args = parser.parse_args()

    print("=" * 70)
    print("Module 4: Change Detection Evaluation")
    print("Explainable Vision-Based Construction Progress Assessment")
    print("=" * 70)
    print(f"LEVIR-CD+ root : {LEVIR_CD_ROOT}")
    print(f"SYSU-CD root   : {SYSU_CD_ROOT}")
    print(f"Reports dir    : {EVAL_DIR}")
    print()

    report = {
        "title":        "Module 4 Change Detection Evaluation Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "algorithm":    "Classical: CLAHE → Gaussian Blur → Otsu Threshold → Morphological Close",
        "note":         "Metrics are REAL values computed from actual dataset ground-truth masks.",
        "results":      {},
    }

    t0 = time.time()

    if not args.skip_levir:
        levir_result = evaluate_levir(
            LEVIR_CD_ROOT, limit=args.levir_limit
        )
        report["results"]["levir_cd_plus"] = levir_result
    else:
        print("[LEVIR-CD+] Skipped.")

    if not args.skip_sysu:
        sysu_result = evaluate_sysu(
            SYSU_CD_ROOT, limit=args.sysu_limit
        )
        report["results"]["sysu_cd"] = sysu_result
    else:
        print("[SYSU-CD] Skipped.")

    report["elapsed_seconds"] = round(time.time() - t0, 1)

    # Save JSON report
    json_path = EVAL_DIR / "change_detection_eval.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n[Saved] JSON report: {json_path}")

    # Save human-readable summary
    summary_path = EVAL_DIR / "change_detection_eval_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("Module 4: Change Detection Evaluation Summary\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated : {report['generated_at']}\n")
        f.write(f"Algorithm : {report['algorithm']}\n")
        f.write(f"Elapsed   : {report['elapsed_seconds']}s\n\n")
        for ds_key, ds_result in report["results"].items():
            f.write(f"Dataset: {ds_result.get('dataset', ds_key)}\n")
            f.write(f"  Split              : {ds_result.get('split')}\n")
            f.write(f"  Pairs evaluated    : {ds_result.get('evaluated_pairs', 0)}\n")
            f.write(f"  GT pairs           : {ds_result.get('gt_evaluated', 0)}\n")
            agg = ds_result.get("aggregate_metrics", {})
            if agg:
                f.write(f"  IoU (mean±std)     : {agg.get('iou_mean','—')} ± {agg.get('iou_std','—')}\n")
                f.write(f"  F1  (mean±std)     : {agg.get('f1_mean','—')} ± {agg.get('f1_std','—')}\n")
                f.write(f"  Precision (mean)   : {agg.get('precision_mean','—')}\n")
                f.write(f"  Recall    (mean)   : {agg.get('recall_mean','—')}\n")
                f.write(f"  Pixel Acc (mean)   : {agg.get('pixel_accuracy_mean','—')}\n")
            else:
                f.write("  No GT metrics available\n")
            f.write("\n")
    print(f"[Saved] Summary  : {summary_path}")

    # Print compact summary to stdout
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    for ds_key, ds_result in report["results"].items():
        agg = ds_result.get("aggregate_metrics", {})
        print(f"\n{ds_result.get('dataset', ds_key)} — {ds_result.get('split')} split")
        print(f"  Pairs: {ds_result.get('evaluated_pairs')}  |  GT: {ds_result.get('gt_evaluated')}")
        if agg:
            print(f"  IoU  : {agg.get('iou_mean','—')}  |  F1: {agg.get('f1_mean','—')}")
            print(f"  Prec : {agg.get('precision_mean','—')}  |  Rec: {agg.get('recall_mean','—')}")
            print(f"  Acc  : {agg.get('pixel_accuracy_mean','—')}")


if __name__ == "__main__":
    main()
