"""
Sample Project Runner & Result Analysis
Final Year Project: Explainable Vision-Based Construction Progress Assessment

This script sets up and executes a complete end-to-end sample construction project
using real multi-temporal UAV imagery and annotations from the local datasets:
  - Module 1: Image Acquisition, Quality Assessment & Temporal Timeline
  - Module 2: Image Preprocessing & Feature Extraction
  - Module 3: Construction Activity & PPE Compliance Detection (10 classes)
  - Module 4: Bi-temporal Construction Change Detection & Severity Analysis
  - Module 5: Composite Progress Assessment, S-Curve & Delay Prediction
  - Module 6: Explainable AI (XAI) — Grad-CAM Heatmaps & SHAP Feature Attributions

Usage:
    py -3 run_sample_project.py
"""

import os
import sys
import json
import uuid
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone

# ─── Project Root Setup ────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import (
    METADATA_DIR, UPLOADS_DIR, PROCESSED_DIR, PROCESSED_M2_DIR,
    PROCESSED_M3_DIR, PROCESSED_M4_DIR, PROCESSED_M5_DIR, PROCESSED_M6_DIR,
    REPORTS_DIR, LEVIR_CD_ROOT, ROBOFLOW_ROOT, SYSU_CD_ROOT,
    MODULE2, MODULE3, MODULE4, MODULE5, MODULE6, ensure_directories
)

# Module imports
from backend.modules.module1_acquisition.metadata import extract_metadata
from backend.modules.module1_acquisition.quality import assess_quality, generate_quality_report
from backend.modules.module1_acquisition.preprocessor import preprocess_image
from backend.modules.module1_acquisition.temporal import sort_images_temporally, build_timeline

from backend.modules.module2_processing.processor import process_single_image
from backend.modules.module3_detection.detector import detect_image, detect_batch
from backend.modules.module4_change.change_detector import detect_change_pair
from backend.modules.module4_change.metrics import classify_severity, compute_iou, SEVERITY_COLORS

from backend.modules.module5_prediction.predictor import run_full_prediction
from backend.modules.module5_prediction.s_curve import build_s_curve_data
from backend.modules.module5_prediction.report import generate_progress_report

from backend.modules.module6_xai.gradcam import generate_gradcam_heatmap, generate_gradcam_batch
from backend.modules.module6_xai.shap_explain import generate_shap_explanation
from backend.modules.module6_xai.pdf_report import generate_xai_pdf_report

PROJECTS_FILE = METADATA_DIR / "projects.json"
ACTIVITY_FILE = METADATA_DIR / "activity.json"
SAMPLE_OUT_DIR = REPORTS_DIR / "sample_project_assessment"


def _load_projects():
    if PROJECTS_FILE.exists():
        try:
            with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_projects(projects):
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, default=str)


def _append_activity(event_type, project_id, message, related_module="system", status="info"):
    ACTIVITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    logs = []
    if ACTIVITY_FILE.exists():
        try:
            with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    now_iso = datetime.now(timezone.utc).isoformat()
    logs.insert(0, {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "project_id": project_id,
        "message": message,
        "related_module": related_module,
        "status": status,
        "timestamp": now_iso
    })
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump(logs[:500], f, indent=2)


def run_sample_pipeline():
    ensure_directories()
    SAMPLE_OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("  UAV VISION-BASED CONSTRUCTION PROGRESS MONITORING & ASSESSMENT")
    print("  SAMPLE PROJECT END-TO-END RESULT ANALYSIS")
    print("=" * 80)

    # ─────────────────────────────────────────────────────────────────────────
    # Project Definition
    # ─────────────────────────────────────────────────────────────────────────
    project_id = "sample-metro-phase2-" + datetime.now().strftime("%Y%m%d")
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=90)        # 90 days elapsed
    end_date = today + timedelta(days=275)          # 365 days total planned duration
    planned_duration = 365

    project_info = {
        "project_id": project_id,
        "name": "Metro Viaduct & Station Hub (Phase 2)",
        "location": "Chennai Metropolitan Area - Corridor 4",
        "description": "Multi-temporal UAV monitoring of structural pier erection, deck slab casting, change detection against previous baseline, and on-site PPE compliance analysis.",
        "project_type": "infrastructure",
        "project_manager": "Chief Infrastructure Engineer",
        "client": "Metro Rail Corporation",
        "contractor": "Apex Infra Engineering",
        "start_date": start_date.isoformat(),
        "approximate_end_date": end_date.isoformat(),
        "planned_duration_days": planned_duration,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }

    print(f"\n[Project Initialized]")
    print(f"  ID               : {project_id}")
    print(f"  Name             : {project_info['name']}")
    print(f"  Location         : {project_info['location']}")
    print(f"  Timeline         : {start_date} -> {end_date} ({planned_duration} days planned)")
    print(f"  Elapsed Duration : 90 days (Expected Linear Progress: {(90/365)*100:.2f}%)")

    # ─────────────────────────────────────────────────────────────────────────
    # Gather Real Imagery from Datasets
    # ─────────────────────────────────────────────────────────────────────────
    proj_raw_dir = UPLOADS_DIR.parent / project_id / "raw"
    proj_proc_dir = PROCESSED_DIR / project_id
    proj_raw_dir.mkdir(parents=True, exist_ok=True)
    proj_proc_dir.mkdir(parents=True, exist_ok=True)

    # 1. LEVIR-CD+ Bi-temporal Pair
    levir_test_a = Path(LEVIR_CD_ROOT) / "test" / "A"
    levir_test_b = Path(LEVIR_CD_ROOT) / "test" / "B"
    levir_test_lbl = Path(LEVIR_CD_ROOT) / "test" / "label"

    selected_levir = []
    if levir_test_a.exists():
        a_files = sorted(list(levir_test_a.glob("*.png")))
        if a_files:
            fa = a_files[0]
            fb = levir_test_b / fa.name
            flbl = levir_test_lbl / fa.name
            if fb.exists():
                selected_levir.append((fa, fb, flbl if flbl.exists() else None))

    # 2. Roboflow Safety / Activity Images
    robo_test_img = Path(ROBOFLOW_ROOT) / "test" / "images"
    robo_test_lbl = Path(ROBOFLOW_ROOT) / "test" / "labels"
    selected_robo = []
    if robo_test_img.exists():
        r_files = sorted(list(robo_test_img.glob("*.jpg")) + list(robo_test_img.glob("*.png")))
        for rf in r_files:
            lf = robo_test_lbl / (rf.stem + ".txt")
            if lf.exists():
                selected_robo.append((rf, lf))
            if len(selected_robo) >= 2:
                break

    # Fallback to sample_images folder if dataset paths missing
    if not selected_levir:
        s_b = Path("sample_images/change_pair1_before.png")
        s_a = Path("sample_images/change_pair1_after.png")
        if s_b.exists() and s_a.exists():
            selected_levir.append((s_b, s_a, None))

    if not selected_robo:
        for sf in Path("sample_images").glob("safety_sample_*.jpg"):
            selected_robo.append((sf, None))

    print(f"\n[Dataset Images Selected]")
    print(f"  Bi-temporal Change Pair : {len(selected_levir)} pairs")
    print(f"  Safety/Activity Images  : {len(selected_robo)} images")

    # ─────────────────────────────────────────────────────────────────────────
    # Module 1: Acquisition, Validation, Quality & Temporal Sequencing
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n" + "-" * 70)
    print("  MODULE 1: Image Acquisition, Quality Assessment & Temporal Sequencing")
    print("-" * 70)

    images_metadata = []
    files_to_copy = []

    # Sequential timestamps from start_date (Day 0) to Day 90
    t_base = start_date
    t_dates = [
        t_base,
        t_base + timedelta(days=30),
        t_base + timedelta(days=65),
        t_base + timedelta(days=90),
    ]

    if selected_levir:
        t1_src, t2_src, gt_lbl = selected_levir[0]
        files_to_copy.append((t1_src, "uav_flight_t1_baseline.png", gt_lbl, None, t_dates[0]))
        files_to_copy.append((t2_src, "uav_flight_t2_current.png", gt_lbl, None, t_dates[3]))

    for idx, (r_src, r_lbl) in enumerate(selected_robo):
        files_to_copy.append((r_src, f"uav_safety_scan_0{idx+1}{r_src.suffix}", None, r_lbl, t_dates[idx+1]))

    for src_path, target_name, gt_path, lbl_path, cap_date in files_to_copy:
        dest_raw_path = proj_raw_dir / target_name
        shutil.copy(src_path, dest_raw_path)

        # Copy matching YOLO label file if present
        if lbl_path and Path(lbl_path).exists():
            shutil.copy(lbl_path, dest_raw_path.with_suffix(".txt"))

        meta = extract_metadata(dest_raw_path)
        meta["capture_date"] = cap_date.isoformat() + " 10:00:00"
        quality = assess_quality(dest_raw_path)
        pre_result = preprocess_image(dest_raw_path, proj_proc_dir)

        image_id = str(uuid.uuid4())
        img_record = {
            "image_id": image_id,
            "filename": target_name,
            "file_path": str(dest_raw_path),
            "source_origin": str(src_path),
            "gt_label_path": str(gt_path) if gt_path else None,
            "uploaded_at": cap_date.isoformat() + "T10:00:00Z",
            "capture_date": cap_date.isoformat() + " 10:00:00",
            "timestamp": cap_date.isoformat() + "T10:00:00Z",
            "metadata": meta,
            "quality": quality,
            "preprocessing": pre_result
        }
        images_metadata.append(img_record)
        print(f"  [Acquired] {target_name:<30} | {meta.get('width', 0)}x{meta.get('height', 0)} | "
              f"Quality: {quality.get('overall_score', 0):.1f}/100 ({'ACCEPTED' if quality.get('accepted') else 'FLAGGED'}) | "
              f"Capture Date: {cap_date}")

    sorted_imgs = sort_images_temporally(images_metadata)
    timeline = build_timeline(sorted_imgs)

    quality_list = [img["quality"] for img in images_metadata]
    quality_report = generate_quality_report(quality_list)
    avg_quality = quality_report.get("score_stats", {}).get("mean", 0.0)
    quality_report["average_score"] = avg_quality
    quality_report["passed_count"] = quality_report.get("accepted", 0)
    quality_report["failed_count"] = quality_report.get("rejected", 0)

    project_info["image_count"] = len(images_metadata)
    project_info["images"] = sorted_imgs
    project_info["timeline"] = timeline
    project_info["quality_report"] = quality_report

    print(f"  >> Average Site Image Quality Score : {avg_quality:.1f} / 100")
    print(f"  >> Temporal Timeline Span           : {timeline.get('total_days', 1)} day(s) sequenced")

    # ─────────────────────────────────────────────────────────────────────────
    # Module 2: Image Processing & Feature Maps
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n" + "-" * 70)
    print("  MODULE 2: Image Processing, Denoising & Multi-Scale Feature Maps")
    print("-" * 70)

    m2_out_dir = PROCESSED_M2_DIR / project_id
    m2_out_dir.mkdir(parents=True, exist_ok=True)

    m2_results = []
    for img in sorted_imgs:
        raw_fp = Path(img["file_path"])
        m2_res = process_single_image(raw_fp, m2_out_dir / img["filename"].split(".")[0], MODULE2)
        m2_results.append(m2_res)
        print(f"  [Processed] {img['filename']:<30} -> Target {MODULE2['target_size']} | "
              f"CLAHE Grid: {MODULE2.get('clahe_tile_grid', (8,8))} | "
              f"Color Spaces: {', '.join(MODULE2['color_spaces'])}")

    # ─────────────────────────────────────────────────────────────────────────
    # Module 3: Construction Activity & PPE Compliance Detection
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n" + "-" * 70)
    print("  MODULE 3: Construction Activity & PPE Safety Compliance Detection")
    print("-" * 70)

    m3_out_dir = PROCESSED_M3_DIR / project_id
    m3_out_dir.mkdir(parents=True, exist_ok=True)

    m3_items = [{"image_path": img["file_path"]} for img in sorted_imgs]
    m3_batch_result = detect_batch(
        items=m3_items,
        output_dir=m3_out_dir,
        config=MODULE3,
        roboflow_root=Path(ROBOFLOW_ROOT)
    )

    print(f"  Total Images Processed : {m3_batch_result.get('succeeded', 0)} / {len(m3_items)}")
    print(f"  Total Site Detections  : {m3_batch_result.get('total_detections', 0)}")
    print(f"  Class Distribution     :")
    for cls_name, count in m3_batch_result.get("class_distribution", {}).items():
        print(f"    - {cls_name:<20}: {count}")
    print(f"  PPE Compliance Rate    : {m3_batch_result.get('avg_compliance', 0.0):.1f}%")

    # ─────────────────────────────────────────────────────────────────────────
    # Module 4: Bi-temporal Construction Change Detection
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n" + "-" * 70)
    print("  MODULE 4: Bi-Temporal Construction Change Detection & Severity")
    print("-" * 70)

    m4_out_dir = PROCESSED_M4_DIR / project_id
    m4_out_dir.mkdir(parents=True, exist_ok=True)

    m4_result = {}
    if len(sorted_imgs) >= 2:
        img_a_path = Path(sorted_imgs[0]["file_path"])
        img_b_path = Path(sorted_imgs[1]["file_path"])

        m4_result = detect_change_pair(
            image_a=img_a_path,
            image_b=img_b_path,
            output_dir=m4_out_dir,
            config=MODULE4
        )

        chg_pct = m4_result.get("change_percent", 0.0)
        num_regs = m4_result.get("num_regions", 0)
        severity = classify_severity(chg_pct)
        m4_result["severity"] = severity
        m4_result["severity_color"] = SEVERITY_COLORS.get(severity, "#22c55e")

        # Ground truth evaluation if mask exists
        gt_mask_path = sorted_imgs[0].get("gt_label_path") or sorted_imgs[1].get("gt_label_path")
        gt_metrics = None
        if gt_mask_path and Path(gt_mask_path).exists() and m4_result.get("mask_path"):
            gt_metrics = compute_iou(Path(m4_result["mask_path"]), Path(gt_mask_path))
            m4_result["ground_truth_metrics"] = gt_metrics

        print(f"  Pair Analyzed      : {img_a_path.name} (T1) -> {img_b_path.name} (T2)")
        print(f"  Changed Surface    : {chg_pct:.2f}% of monitored zone")
        print(f"  Change Regions     : {num_regs} connected structural components identified")
        print(f"  Severity Category  : {severity.upper()}")
        print(f"  Binary Mask Saved  : {m4_result.get('mask_path')}")
        print(f"  Overlay Map Saved  : {m4_result.get('overlay_path')}")
        if gt_metrics:
            print(f"  GT Evaluation IoU  : {gt_metrics.get('iou', 0):.4f} | F1: {gt_metrics.get('f1', 0):.4f}")

    # ─────────────────────────────────────────────────────────────────────────
    # Module 5: Delay Prediction, S-Curve & Risk Classification
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n" + "-" * 70)
    print("  MODULE 5: Delay Prediction, S-Curve & Schedule Risk Assessment")
    print("-" * 70)

    m5_out_dir = PROCESSED_M5_DIR / project_id
    m5_out_dir.mkdir(parents=True, exist_ok=True)

    m3_for_m5 = {
        "total_detections": m3_batch_result.get("total_detections", 0),
        "image_count": m3_batch_result.get("succeeded", 1),
        "avg_compliance": m3_batch_result.get("avg_compliance", 0.0)
    }
    m4_for_m5 = {
        "avg_change": m4_result.get("change_percent", 0.0),
        "succeeded": 1 if m4_result.get("success") else 0
    }

    m5_prediction = run_full_prediction(
        project_data=project_info,
        detection_results=m3_for_m5,
        change_results=m4_for_m5,
        planned_duration_days=planned_duration,
        planned_start_date=start_date.isoformat(),
        weights=MODULE5.get("weights"),
        risk_thresholds=MODULE5.get("risk_thresholds")
    )

    with open(m5_out_dir / "prediction_result.json", "w", encoding="utf-8") as f:
        json.dump(m5_prediction, f, indent=2, default=str)

    prog_score = m5_prediction.get("progress", {}).get("progress_score", 0.0)
    subscores = m5_prediction.get("progress", {}).get("sub_scores", {})
    weights_used = m5_prediction.get("progress", {}).get("weights_used", {})
    delay_info = m5_prediction.get("delay", {})
    risk_info = m5_prediction.get("risk", {})

    expected_prog = delay_info.get("expected_progress", (90 / 365) * 100)
    progress_delta = delay_info.get("delta", prog_score - expected_prog)
    delay_days = delay_info.get("delay_days", 0)

    print(f"  [Progress Scoring Formula]")
    print(f"    Change Component   (w={weights_used.get('change', 0.40):.2f}) : {subscores.get('change_score', 0):.2f}%")
    print(f"    Activity Density   (w={weights_used.get('activity', 0.30):.2f}) : {subscores.get('activity_score', 0):.2f}%")
    print(f"    Temporal Coverage  (w={weights_used.get('temporal', 0.20):.2f}) : {subscores.get('temporal_score', 0):.2f}%")
    print(f"    Image Quality      (w={weights_used.get('quality', 0.10):.2f}) : {subscores.get('quality_score', 0):.2f}%")
    print(f"  >> Estimated Actual Progress (Composite Score) : {prog_score:.2f}%")
    print(f"  >> Expected Progress based on 90 elapsed days   : {expected_prog:.2f}%")
    print(f"  >> Schedule Deviation (Delta)                   : {progress_delta:+.2f}%")
    print(f"  >> Predicted Schedule Offset                    : {delay_days:+d} days ({'Ahead' if delay_days < 0 else 'Delayed' if delay_days > 0 else 'On Track'})")
    print(f"  >> Project Risk Classification                  : {risk_info.get('label', 'On Track')} ({risk_info.get('risk_level', '').upper()})")
    print(f"  >> Engineering Recommendation                   : {risk_info.get('recommendation', '')}")

    # ─────────────────────────────────────────────────────────────────────────
    # Module 6: Explainable AI (XAI) — GradCAM, SHAP & Report
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n" + "-" * 70)
    print("  MODULE 6: Explainable AI (XAI) — Grad-CAM Heatmaps & SHAP Attributions")
    print("-" * 70)

    m6_out_dir = PROCESSED_M6_DIR / project_id
    m6_cam_dir = m6_out_dir / "gradcam"
    m6_shap_dir = m6_out_dir / "shap"
    m6_rep_dir = m6_out_dir / "report"

    m6_cam_dir.mkdir(parents=True, exist_ok=True)
    m6_shap_dir.mkdir(parents=True, exist_ok=True)
    m6_rep_dir.mkdir(parents=True, exist_ok=True)

    # 1. Grad-CAM Batch
    raw_img_paths = [Path(img["file_path"]) for img in sorted_imgs[:3]]
    gradcam_batch = generate_gradcam_batch(
        image_paths=raw_img_paths,
        output_dir=m6_cam_dir,
        config=MODULE6,
        max_items=3
    )

    print(f"  Grad-CAM Saliency Maps Generated : {gradcam_batch.get('succeeded', 0)} heatmaps")
    for r in gradcam_batch.get("results", []):
        if r.get("success"):
            print(f"    - Heatmap overlay : {r.get('overlay_path')} (Mean Attention: {r.get('stats',{}).get('mean', 0):.3f})")

    # 2. SHAP Explanation
    shap_res = generate_shap_explanation(
        prediction=m5_prediction,
        output_dir=m6_shap_dir,
        config=MODULE6
    )

    print(f"  SHAP Feature Attributions Mode   : {shap_res.get('mode', 'simulation').upper()}")
    print(f"  SHAP Values (Impact on Progress) :")
    for feat, val in shap_res.get("shap_values", {}).items():
        print(f"    - {feat:<20}: {val:+.4f} (Base: {shap_res.get('base_value', 50.0):.1f})")
    print(f"  SHAP Bar Chart                   : {shap_res.get('bar_chart_path')}")
    print(f"  SHAP Waterfall Plot              : {shap_res.get('waterfall_chart_path')}")

    # 3. Comprehensive XAI Report
    gradcam_successes = [r for r in gradcam_batch.get("results", []) if r.get("success")]
    xai_report = generate_xai_pdf_report(
        project=project_info,
        prediction=m5_prediction,
        shap_result=shap_res,
        gradcam_results=gradcam_successes,
        output_dir=m6_rep_dir,
        config=MODULE6
    )

    print(f"  XAI Executive Report (HTML)      : {xai_report.get('html_path')}")
    if xai_report.get("pdf_path"):
        print(f"  XAI Executive Report (PDF)       : {xai_report.get('pdf_path')}")

    # ─────────────────────────────────────────────────────────────────────────
    # Persist Project & Update Activity Stream
    # ─────────────────────────────────────────────────────────────────────────
    project_info["module3_processed"] = m3_batch_result.get("succeeded", 0)
    project_info["module3_detections"] = m3_batch_result.get("total_detections", 0)
    project_info["module5_score"] = prog_score
    project_info["module5_delay_days"] = delay_days
    project_info["module5_risk_level"] = risk_info.get("risk_level", "on_track")
    project_info["last_assessment_at"] = datetime.now(timezone.utc).isoformat()

    projects_all = _load_projects()
    projects_all[project_id] = project_info
    _save_projects(projects_all)

    _append_activity(
        "sample_project_assessed", project_id,
        f"Sample project '{project_info['name']}' assessed. Score: {prog_score:.1f}%, Delay: {delay_days:+d}d, Risk: {risk_info.get('label')}",
        related_module="system", status="success"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Generate Comprehensive Result Analysis Report
    # ─────────────────────────────────────────────────────────────────────────
    assessment_summary = {
        "title": "Comprehensive UAV Construction Progress & Delay Assessment",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "project_id": project_id,
            "project_name": project_info["name"],
            "location": project_info["location"],
            "client": project_info["client"],
            "contractor": project_info["contractor"],
            "manager": project_info["project_manager"],
            "start_date": project_info["start_date"],
            "planned_end_date": project_info["approximate_end_date"],
            "planned_duration_days": planned_duration,
            "elapsed_days": 90,
            "remaining_days": 275,
        },
        "module1_acquisition": {
            "image_count": len(sorted_imgs),
            "quality_average_score": quality_report.get("average_score", 0),
            "quality_accepted_count": quality_report.get("passed_count", 0),
            "temporal_span_days": timeline.get("total_days", 1),
        },
        "module2_processing": {
            "target_resolution": MODULE2["target_size"],
            "denoising_applied": "Gaussian filter (k=3x3, sigma=0)",
            "enhancement_applied": "CLAHE (clip_limit=2.0, tile_grid=8x8)",
            "color_spaces_extracted": MODULE2["color_spaces"],
        },
        "module3_activity_detection": {
            "model_mode": "Roboflow 10-Class Verified Labels Parser",
            "total_detections": m3_batch_result.get("total_detections", 0),
            "class_distribution": m3_batch_result.get("class_distribution", {}),
            "ppe_compliance_rate_pct": m3_batch_result.get("avg_compliance", 0.0),
        },
        "module4_change_detection": {
            "method": "Multi-Temporal Absolute Differencing + CLAHE + Otsu Thresholding",
            "change_percent": m4_result.get("change_percent", 0.0),
            "change_regions_count": m4_result.get("num_regions", 0),
            "severity_level": m4_result.get("severity", "moderate"),
            "ground_truth_metrics": m4_result.get("ground_truth_metrics"),
        },
        "module5_progress_delay": {
            "composite_progress_score_pct": prog_score,
            "expected_progress_pct": round(expected_prog, 2),
            "progress_deviation_delta_pct": round(progress_delta, 2),
            "predicted_delay_days": delay_days,
            "risk_level": risk_info.get("risk_level", "on_track"),
            "risk_label": risk_info.get("label", "On Track"),
            "engineering_recommendation": risk_info.get("recommendation", ""),
            "subscores": subscores,
            "weights": weights_used,
        },
        "module6_explainable_ai": {
            "gradcam_heatmaps_count": gradcam_batch.get("succeeded", 0),
            "shap_attribution_mode": shap_res.get("mode", "simulation"),
            "shap_attributions": shap_res.get("shap_values", {}),
            "shap_base_value": shap_res.get("base_value", 50.0),
            "xai_html_report_path": xai_report.get("html_path"),
            "xai_pdf_report_path": xai_report.get("pdf_path"),
        }
    }

    report_json_path = SAMPLE_OUT_DIR / "sample_project_assessment_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(assessment_summary, f, indent=2, default=str)

    print("\n" + "=" * 80)
    print("  RESULT ANALYSIS COMPLETE")
    print(f"  Structured Report Saved : {report_json_path}")
    print("=" * 80)

    return assessment_summary


if __name__ == "__main__":
    run_sample_pipeline()
