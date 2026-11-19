"""
Module 5: Progress Report Generator
Final Year Project — Explainable Vision-Based Construction Progress Assessment

Generates a structured JSON progress report combining:
  - Module 5 prediction results (progress score, delay, risk)
  - Module 4 change detection summary
  - Module 3 activity detection summary
  - Module 1 image quality summary
  - S-curve data
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("module5.report")


def generate_progress_report(
    project_data:    Dict,
    prediction:      Dict,
    output_path:     Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Generate a comprehensive progress assessment report.

    Args:
        project_data: Project dict from the project store.
        prediction:   Full prediction dict from run_full_prediction().
        output_path:  If provided, saves the report as JSON to this path.

    Returns:
        Report dict.
    """
    project_id   = project_data.get("project_id", "unknown")
    project_name = project_data.get("name", "Unnamed Project")
    location     = project_data.get("location", "")
    created_at   = project_data.get("created_at", "")

    progress = prediction.get("progress", {})
    delay    = prediction.get("delay",    {})
    risk     = prediction.get("risk",     {})
    s_curve  = prediction.get("s_curve",  {})
    stats    = prediction.get("summary_stats", {})

    # ── Executive Summary ─────────────────────────────────────────────────────
    progress_score = progress.get("progress_score", 0.0)
    delay_days     = delay.get("delay_days", 0)
    risk_level     = risk.get("risk_level", "unknown")

    direction = "ahead of" if delay_days <= 0 else "behind"
    abs_delay = abs(delay_days)

    executive_summary = (
        f"Project '{project_name}' is currently at {progress_score:.1f}% completion. "
        f"The project is {abs_delay} days {direction} schedule ({risk.get('label', risk_level)}). "
        f"{risk.get('recommendation', '')}"
    )

    # ── Activity Log (recent detections summary) ──────────────────────────────
    images = project_data.get("images", [])
    activity_log = []
    for img in images[-10:]:  # last 10 images
        entry = {
            "image_id":   img.get("image_id"),
            "filename":   img.get("filename"),
            "timestamp":  img.get("timestamp") or img.get("upload_time"),
            "quality":    img.get("quality", {}).get("overall_score"),
            "accepted":   img.get("accepted", True),
        }
        activity_log.append(entry)

    # ── Change Timeline (from M4 results) ────────────────────────────────────
    change_timeline = []
    for r in prediction.get("delay", {}).get("__change_results_ref", []):
        pass  # placeholder

    # Pull from s_curve points
    change_events = [
        {
            "label":          pt["label"],
            "change_percent": pt["change_percent"],
            "planned":        pt["planned"],
            "actual":         pt["actual"],
        }
        for pt in s_curve.get("points", [])
        if pt.get("change_event")
    ]

    # ── Build Report ──────────────────────────────────────────────────────────
    report = {
        "module":             "Module 5: Delay Prediction & Progress Assessment",
        "report_type":        "Construction Progress Assessment Report",
        "generated_at":       datetime.now(timezone.utc).isoformat(),
        "project": {
            "project_id":    project_id,
            "name":          project_name,
            "location":      location,
            "created_at":    created_at,
            "total_images":  stats.get("total_images", len(images)),
        },
        "executive_summary": executive_summary,
        "progress_assessment": {
            "overall_score":      progress_score,
            "score_grade":        _letter_grade(progress_score),
            "sub_scores":         progress.get("sub_scores", {}),
            "weights_used":       progress.get("weights_used", {}),
            "component_breakdown": progress.get("breakdown", {}),
        },
        "schedule_analysis": {
            "elapsed_days":          delay.get("elapsed_days", 0),
            "planned_duration_days": delay.get("planned_duration_days", 365),
            "expected_progress":     delay.get("expected_progress", 0.0),
            "actual_progress":       delay.get("progress_score", progress_score),
            "delta_progress":        delay.get("delta_progress", 0.0),
            "delay_days":            delay_days,
            "ahead_of_schedule":     delay.get("ahead_of_schedule", False),
            "confidence":            delay.get("confidence", 0.0),
            "predicted_completion":  delay.get("predicted_completion"),
        },
        "risk_assessment": {
            "risk_level":     risk_level,
            "label":          risk.get("label", ""),
            "color":          risk.get("color", ""),
            "recommendation": risk.get("recommendation", ""),
        },
        "change_detection_summary": {
            "avg_change_percent": stats.get("avg_change_percent", 0.0),
            "max_change_percent": stats.get("max_change_percent", 0.0),
            "change_pairs":       stats.get("change_pairs", 0),
            "severity_counts":    stats.get("severity_counts", {}),
            "change_events":      change_events,
        },
        "activity_detection_summary": {
            "total_detections": stats.get("total_detections", 0),
            "total_images":     stats.get("total_images", 0),
        },
        "s_curve": {
            "label_mode":   s_curve.get("label_mode", "sequence"),
            "n_points":     s_curve.get("n_points", 0),
            "points":       s_curve.get("points", []),
        },
        "recent_activity": activity_log,
        "metadata": {
            "planned_start":    prediction.get("planned_start_date"),
            "planned_duration": prediction.get("planned_duration_days", 365),
            "predicted_at":     prediction.get("predicted_at"),
        },
    }

    # ── Save to file if requested ─────────────────────────────────────────────
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info("Module 5 progress report saved: %s", output_path)

    return report


def _letter_grade(score: float) -> str:
    """Convert a numeric score 0–100 to a letter grade."""
    if score >= 90:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 45:
        return "D"
    else:
        return "F"
