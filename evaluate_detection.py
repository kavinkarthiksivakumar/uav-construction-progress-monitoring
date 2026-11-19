"""
Evaluate Construction Safety Detection on Roboflow Dataset.
Final Year Project — Explainable Vision-Based Construction Progress Assessment

This script validates Module 3 simulation mode against the actual Roboflow
Construction Site Safety dataset. It reads real YOLO annotations and computes:
  - Class distribution statistics per split
  - Per-class annotation counts
  - Detection simulation accuracy (reading GT labels as detections)
  - Site compliance statistics per image

Dataset: datasets/roboflow/ (10 classes, 2603 train / 114 val / 82 test images)

Usage:
    py -3 evaluate_detection.py [--split test|valid|train] [--limit N]

Results are saved to:
    reports/evaluation/detection_eval.json
    reports/evaluation/detection_eval_summary.txt

IMPORTANT: These are REAL counts from the actual dataset annotations.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

# ─── Project root setup ────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import ROBOFLOW_ROOT, ROBOFLOW_CLASSES, REPORTS_DIR, MODULE3
from backend.modules.module3_detection.annotation_parser import parse_yolo_label, get_image_size

EVAL_DIR = REPORTS_DIR / "evaluation"
EVAL_DIR.mkdir(parents=True, exist_ok=True)

SAFE_CLASSES     = set(MODULE3["safe_classes"])
RISK_CLASSES     = set(MODULE3["risk_classes"])
ACTIVITY_CLASSES = set(MODULE3["activity_classes"])


def evaluate_split(
    roboflow_root: Path,
    split: str = "test",
    limit: int = -1,
) -> dict:
    """
    Parse all YOLO label files in a split and compute annotation statistics.

    Args:
        roboflow_root: Root of the Roboflow dataset.
        split:         'train', 'valid', or 'test'.
        limit:         Max images to process (-1 = all).

    Returns:
        Evaluation dict with class counts, compliance stats, etc.
    """
    images_dir = roboflow_root / split / "images"
    labels_dir = roboflow_root / split / "labels"

    if not images_dir.exists():
        return {"error": f"images dir not found: {images_dir}", "split": split}

    image_files = sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.png"))
    if limit > 0:
        image_files = image_files[:limit]

    print(f"\n[Roboflow {split}] Processing {len(image_files)} images …")

    # Counters
    class_counts: dict = defaultdict(int)
    total_detections   = 0
    images_processed   = 0
    images_with_labels = 0
    compliant_images   = 0
    per_image_stats    = []

    for img_path in image_files:
        stem     = img_path.stem
        lbl_path = labels_dir / (stem + ".txt")

        try:
            img_w, img_h = get_image_size(img_path)
        except Exception:
            img_w, img_h = 640, 640  # fallback

        detections = []
        if lbl_path.exists():
            detections = parse_yolo_label(
                txt_path=lbl_path,
                img_w=img_w,
                img_h=img_h,
                class_names=ROBOFLOW_CLASSES,
            )
            images_with_labels += 1

        # Per-image class counts
        img_classes = [d["class_name"] for d in detections]
        img_safe    = sum(1 for c in img_classes if c in SAFE_CLASSES)
        img_risk    = sum(1 for c in img_classes if c in RISK_CLASSES)
        img_person  = sum(1 for c in img_classes if c == "Person")

        compliance = (img_risk == 0 and img_safe > 0) or img_person == 0

        for c in img_classes:
            class_counts[c] += 1

        total_detections  += len(detections)
        images_processed  += 1
        if compliance:
            compliant_images += 1

        per_image_stats.append({
            "image":      img_path.name,
            "detections": len(detections),
            "safe_count": img_safe,
            "risk_count": img_risk,
            "compliant":  compliance,
        })

    compliance_rate = round(compliant_images / max(images_processed, 1), 4)
    avg_detections  = round(total_detections  / max(images_processed, 1), 2)

    # Sort class counts descending
    sorted_class_counts = dict(
        sorted(class_counts.items(), key=lambda x: -x[1])
    )

    result = {
        "dataset":           "Roboflow Construction Site Safety",
        "split":             split,
        "images_processed":  images_processed,
        "images_with_labels": images_with_labels,
        "total_detections":  total_detections,
        "avg_detections_per_image": avg_detections,
        "class_counts":      sorted_class_counts,
        "classes":           ROBOFLOW_CLASSES,
        "compliance_rate":   compliance_rate,
        "compliant_images":  compliant_images,
        "per_image_stats":   per_image_stats,
    }

    print(f"  Images: {images_processed}  |  With labels: {images_with_labels}")
    print(f"  Total detections: {total_detections}  |  Avg/image: {avg_detections}")
    print(f"  Site compliance rate: {compliance_rate:.1%}")
    print(f"  Class counts: {dict(list(sorted_class_counts.items())[:5])} …")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Module 3 detection simulation on Roboflow dataset."
    )
    parser.add_argument(
        "--split", choices=["train", "valid", "test", "all"],
        default="all", help="Which split(s) to evaluate (default: all)"
    )
    parser.add_argument(
        "--limit", type=int, default=-1,
        help="Max images per split (-1 = all)"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Module 3: Construction Safety Detection Evaluation")
    print("Explainable Vision-Based Construction Progress Assessment")
    print("=" * 70)
    print(f"Roboflow root : {ROBOFLOW_ROOT}")
    print(f"Classes       : {ROBOFLOW_CLASSES}")
    print()

    splits = ["train", "valid", "test"] if args.split == "all" else [args.split]

    report = {
        "title":        "Module 3 Detection Evaluation Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode":         "Simulation (reading YOLO ground-truth labels as detections)",
        "note":         "Counts are REAL values from actual dataset annotations.",
        "classes":      ROBOFLOW_CLASSES,
        "safe_classes": list(SAFE_CLASSES),
        "risk_classes": list(RISK_CLASSES),
        "results":      {},
    }

    overall_class_counts: dict = defaultdict(int)

    for split in splits:
        result = evaluate_split(ROBOFLOW_ROOT, split=split, limit=args.limit)
        report["results"][split] = result
        # Accumulate class counts
        for cls, cnt in result.get("class_counts", {}).items():
            overall_class_counts[cls] += cnt

    report["overall_class_counts"] = dict(
        sorted(overall_class_counts.items(), key=lambda x: -x[1])
    )

    # Save JSON
    json_path = EVAL_DIR / "detection_eval.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n[Saved] JSON report : {json_path}")

    # Save summary text
    summary_path = EVAL_DIR / "detection_eval_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("Module 3: Detection Evaluation Summary\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated : {report['generated_at']}\n")
        f.write(f"Mode      : {report['mode']}\n\n")
        for split, result in report["results"].items():
            f.write(f"Split: {split}\n")
            f.write(f"  Images processed    : {result.get('images_processed', 0)}\n")
            f.write(f"  Images with labels  : {result.get('images_with_labels', 0)}\n")
            f.write(f"  Total detections    : {result.get('total_detections', 0)}\n")
            f.write(f"  Avg det/image       : {result.get('avg_detections_per_image', 0)}\n")
            f.write(f"  Compliance rate     : {result.get('compliance_rate', 0):.1%}\n")
            f.write("  Class counts:\n")
            for cls, cnt in result.get("class_counts", {}).items():
                f.write(f"    {cls:<20}: {cnt}\n")
            f.write("\n")
        f.write("Overall Class Counts (all splits combined):\n")
        for cls, cnt in report["overall_class_counts"].items():
            f.write(f"  {cls:<20}: {cnt}\n")
    print(f"[Saved] Summary     : {summary_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("DETECTION EVALUATION SUMMARY")
    print("=" * 70)
    for split, result in report["results"].items():
        print(f"\n  {split.upper()} split:")
        print(f"    Images  : {result.get('images_processed')} | "
              f"With labels: {result.get('images_with_labels')}")
        print(f"    Dets    : {result.get('total_detections')} | "
              f"Avg/img: {result.get('avg_detections_per_image')}")
        print(f"    Compliance: {result.get('compliance_rate', 0):.1%}")
    print("\n  Overall class distribution (all splits):")
    for cls, cnt in list(report["overall_class_counts"].items())[:10]:
        print(f"    {cls:<20}: {cnt}")


if __name__ == "__main__":
    main()
