"""
Module 5: Delay Prediction & Progress Assessment — Core Predictor
IEEE M.Tech Project — Explainable Vision-Based Construction Progress Assessment

Consumes outputs from Modules 1–4 to compute:
  1. Weighted composite progress score  (0–100 %)
  2. Schedule delay prediction          (days ahead / behind)
  3. Risk level classification          (on_track / at_risk / delayed / critical)

Scoring formula
───────────────
  progress_score =
      w_change    × change_score    (40 %)  ← Module 4 change %
    + w_activity  × activity_score  (30 %)  ← Module 3 detection density
    + w_temporal  × temporal_score  (20 %)  ← Module 1 temporal span
    + w_quality   × quality_score   (10 %)  ← Module 1 avg quality

Delay prediction
────────────────
  expected_progress = elapsed_days / planned_duration_days × 100
  delta             = actual_progress − expected_progress
  delay_days        = −delta / 100 × planned_duration_days
  (negative delay_days → ahead of schedule)
"""

import logging
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("module5.predictor")

# ─────────────────────────────────────────────────────────────────────────────
# Default weights (overridable via MODULE5 settings)
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_WEIGHTS = {
    "change":   0.40,   # Module 4 change %
    "activity": 0.30,   # Module 3 activity density
    "temporal": 0.20,   # Module 1 temporal coverage
    "quality":  0.10,   # Module 1 avg quality score
}

RISK_THRESHOLDS = {
    "at_risk":  10,   # delay ≥ 10 days
    "delayed":  20,   # delay ≥ 20 days
    "critical": 35,   # delay ≥ 35 days
}

RISK_COLORS = {
    "on_track": "#22c55e",
    "at_risk":  "#f59e0b",
    "delayed":  "#ef4444",
    "critical": "#dc2626",
}


# ─────────────────────────────────────────────────────────────────────────────
# Sub-score helpers
# ─────────────────────────────────────────────────────────────────────────────

def _change_score(change_results: Dict) -> float:
    """
    Score [0–100] derived from Module 4 average change percentage.
    Sigmoid-like normalisation: 0 % change → score 0, ≥60 % change → score 100.
    """
    if not change_results:
        return 0.0

    avg_change = change_results.get("avg_change", 0.0)
    if avg_change <= 0:
        return 0.0

    # Sigmoid-like mapping: half-score at 20% change, saturation near 60%
    k = 0.12          # steepness
    mid = 20.0        # inflection point (% change)
    score = 100.0 / (1.0 + math.exp(-k * (avg_change - mid)))
    return round(min(max(score, 0.0), 100.0), 2)


def _activity_score(detection_results: Dict) -> float:
    """
    Score [0–100] derived from Module 3 detection density and compliance rate.
    detection_density = total_detections / max(image_count, 1)
    score = 0.6 × normalised_density + 0.4 × compliance_rate × 100
    """
    if not detection_results:
        return 0.0

    total_dets   = detection_results.get("total_detections", 0)
    image_count  = max(detection_results.get("image_count", 1), 1)
    avg_comp     = detection_results.get("avg_compliance", 0.0)

    density      = total_dets / image_count
    # Cap density normalisation at 20 detections/image → score 100
    density_norm = min(density / 20.0, 1.0) * 100.0

    score = 0.6 * density_norm + 0.4 * avg_comp
    return round(min(max(score, 0.0), 100.0), 2)


def _temporal_score(project_data: Dict) -> float:
    """
    Score [0–100] based on how many distinct temporal points are covered.
    More images spread across time → higher temporal score.
    10+ images → full temporal coverage score.
    """
    images = project_data.get("images", [])
    count  = len(images)

    if count == 0:
        return 0.0
    if count == 1:
        return 10.0

    # Try to measure date span
    dates = []
    for img in images:
        ts = img.get("timestamp") or img.get("capture_date") or img.get("upload_time")
        if ts:
            try:
                if isinstance(ts, str):
                    # Strip trailing Z and microseconds if needed
                    ts_clean = ts.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(ts_clean)
                else:
                    dt = ts
                dates.append(dt)
            except Exception:
                pass

    if len(dates) >= 2:
        dates.sort()
        span_days = (dates[-1] - dates[0]).days
        # A span of 90+ days with 10+ images → full score
        date_score = min(span_days / 90.0, 1.0) * 60.0
        count_score = min(count / 10.0, 1.0) * 40.0
        return round(date_score + count_score, 2)
    else:
        # No date info — purely by count
        return round(min(count / 10.0, 1.0) * 100.0, 2)


def _quality_score(project_data: Dict) -> float:
    """
    Score [0–100] based on average image quality from Module 1.
    Uses the quality_report overall_score or computes from individual images.
    """
    qr = project_data.get("quality_report", {})
    if qr:
        avg_q = qr.get("avg_quality_score") or qr.get("average_score") or qr.get("overall_score")
        if avg_q is not None:
            return round(min(max(float(avg_q), 0.0), 100.0), 2)

    # Fallback: compute from individual image quality scores
    images = project_data.get("images", [])
    scores = []
    for img in images:
        qs = img.get("quality", {}).get("overall_score") or img.get("quality_score")
        if qs is not None:
            scores.append(float(qs))

    if scores:
        return round(min(max(sum(scores) / len(scores), 0.0), 100.0), 2)

    return 50.0  # default neutral when no quality data


# ─────────────────────────────────────────────────────────────────────────────
# Composite Progress Score
# ─────────────────────────────────────────────────────────────────────────────

def compute_progress_score(
    project_data:      Dict,
    detection_results: Dict,
    change_results:    Dict,
    weights:           Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Compute a weighted composite construction progress score.

    Args:
        project_data:      Full project dict (images, quality_report, …).
        detection_results: Module 3 detection result dict.
        change_results:    Module 4 batch result dict (avg_change, num_regions, …).
        weights:           Optional weight overrides.

    Returns:
        Dict with:
          progress_score   — overall progress percentage [0–100]
          sub_scores       — individual component scores
          weights_used     — weights applied
          breakdown        — human-readable explanation
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}

    # Normalise weights to sum to 1.0
    total_w = sum(w.values())
    if total_w > 0:
        w = {k: v / total_w for k, v in w.items()}

    cs  = _change_score(change_results)
    acs = _activity_score(detection_results)
    ts  = _temporal_score(project_data)
    qs  = _quality_score(project_data)

    score = (
        w["change"]   * cs  +
        w["activity"] * acs +
        w["temporal"] * ts  +
        w["quality"]  * qs
    )
    score = round(min(max(score, 0.0), 100.0), 2)

    breakdown = {
        "change_component":   f"{cs:.1f}% × {w['change']:.0%} = {w['change']*cs:.1f}pts (Module 4 change detection)",
        "activity_component": f"{acs:.1f}% × {w['activity']:.0%} = {w['activity']*acs:.1f}pts (Module 3 activity detections)",
        "temporal_component": f"{ts:.1f}% × {w['temporal']:.0%} = {w['temporal']*ts:.1f}pts (Module 1 temporal coverage)",
        "quality_component":  f"{qs:.1f}% × {w['quality']:.0%} = {w['quality']*qs:.1f}pts (Module 1 image quality)",
    }

    logger.info(
        "Module 5 progress score: %.2f%% (change=%.1f, activity=%.1f, temporal=%.1f, quality=%.1f)",
        score, cs, acs, ts, qs
    )

    return {
        "progress_score": score,
        "sub_scores": {
            "change_score":   cs,
            "activity_score": acs,
            "temporal_score": ts,
            "quality_score":  qs,
            "change":         cs,
            "activity":       acs,
            "temporal":       ts,
            "quality":        qs,
        },
        "weights_used":  w,
        "breakdown":     breakdown,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Delay Prediction
# ─────────────────────────────────────────────────────────────────────────────

def predict_delay(
    progress_score:          float,
    elapsed_days:            int,
    planned_duration_days:   int    = 365,
    planned_start_date:      Optional[str] = None,
) -> Dict[str, Any]:
    """
    Predict schedule delay based on actual vs expected progress.

    Args:
        progress_score:        Actual progress percentage [0–100].
        elapsed_days:          Days elapsed since project start.
        planned_duration_days: Total planned project duration in days.
        planned_start_date:    ISO date string for project start.

    Returns:
        Dict with delay_days, expected_progress, confidence, predicted_completion.
    """
    if planned_duration_days <= 0:
        planned_duration_days = 365

    elapsed_days = max(elapsed_days, 1)

    expected_progress = min((elapsed_days / planned_duration_days) * 100.0, 100.0)
    delta             = progress_score - expected_progress   # positive = ahead
    delay_days        = round(-delta / 100.0 * planned_duration_days)

    # Confidence: higher when more elapsed time (more data)
    elapsed_frac = min(elapsed_days / planned_duration_days, 1.0)
    confidence   = round(30.0 + elapsed_frac * 70.0, 1)   # 30–100 %

    # Predicted completion date
    remaining_progress = max(100.0 - progress_score, 0.0)
    if progress_score > 0:
        days_per_pct = elapsed_days / progress_score
        days_remaining = remaining_progress * days_per_pct
    else:
        days_remaining = planned_duration_days

    predicted_completion = None
    if planned_start_date:
        try:
            start = datetime.fromisoformat(planned_start_date.replace("Z", "+00:00"))
            completion = start + timedelta(days=elapsed_days + days_remaining)
            predicted_completion = completion.strftime("%Y-%m-%d")
        except Exception:
            pass

    if predicted_completion is None:
        predicted_completion = f"~{int(days_remaining)} days remaining"

    logger.info(
        "Module 5 delay prediction: expected=%.1f%%, actual=%.1f%%, delay=%+d days, confidence=%.0f%%",
        expected_progress, progress_score, delay_days, confidence
    )

    return {
        "progress_score":      round(progress_score, 2),
        "expected_progress":   round(expected_progress, 2),
        "delta_progress":      round(delta, 2),
        "delay_days":          delay_days,
        "ahead_of_schedule":   delay_days < 0,
        "confidence":          confidence,
        "predicted_completion": predicted_completion,
        "days_remaining":      int(days_remaining),
        "elapsed_days":        elapsed_days,
        "planned_duration_days": planned_duration_days,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Risk Classification
# ─────────────────────────────────────────────────────────────────────────────

def classify_risk_level(
    delay_days:      int,
    progress_score:  float,
    thresholds:      Optional[Dict] = None,
) -> Dict[str, str]:
    """
    Classify the overall project risk level.

    Args:
        delay_days:     Predicted delay (negative = ahead of schedule).
        progress_score: Actual progress percentage.
        thresholds:     Optional override of delay thresholds.

    Returns:
        Dict with risk_level, color, label, recommendation.
    """
    t = {**RISK_THRESHOLDS, **(thresholds or {})}

    if delay_days <= 0:
        level = "on_track"
    elif delay_days < t["at_risk"]:
        level = "on_track"
    elif delay_days < t["delayed"]:
        level = "at_risk"
    elif delay_days < t["critical"]:
        level = "delayed"
    else:
        level = "critical"

    recommendations = {
        "on_track": "Project is progressing as planned. Continue monitoring.",
        "at_risk":  "Minor schedule slippage detected. Review resource allocation.",
        "delayed":  "Significant delay detected. Immediate corrective action recommended.",
        "critical": "Critical delay — project requires urgent intervention and replanning.",
    }

    labels = {
        "on_track": "On Schedule",
        "at_risk":  "At Risk",
        "delayed":  "Delayed",
        "critical": "Critical Delay",
    }

    return {
        "risk_level":      level,
        "color":           RISK_COLORS[level],
        "label":           labels[level],
        "recommendation":  recommendations[level],
        "delay_days":      delay_days,
        "progress_score":  round(progress_score, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Full Prediction Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_full_prediction(
    project_data:          Dict,
    detection_results:     Dict,
    change_results:        Dict,
    planned_duration_days: int  = 365,
    planned_start_date:    Optional[str] = None,
    weights:               Optional[Dict] = None,
    risk_thresholds:       Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Run the complete Module 5 prediction pipeline.

    Computes progress score → delay prediction → risk classification.

    Args:
        project_data:          Project dict from project store.
        detection_results:     Module 3 aggregate detection results.
        change_results:        Module 4 batch change detection results.
        planned_duration_days: Project planned total duration.
        planned_start_date:    ISO date string for project start (optional).
        weights:               Score weight overrides.
        risk_thresholds:       Risk threshold overrides.

    Returns:
        Comprehensive prediction dict.
    """
    from backend.modules.module5_prediction.s_curve import build_s_curve_data

    # ── Determine elapsed days ────────────────────────────────────────────────
    images = project_data.get("images", [])
    created_at = project_data.get("created_at")
    elapsed_days = 1

    if planned_start_date:
        try:
            start = datetime.fromisoformat(planned_start_date.replace("Z", "+00:00"))
            elapsed_days = max((datetime.utcnow() - start.replace(tzinfo=None)).days, 1)
        except Exception:
            pass
    elif created_at:
        try:
            start = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            elapsed_days = max((datetime.utcnow() - start.replace(tzinfo=None)).days, 1)
        except Exception:
            pass

    # ── Score computation ─────────────────────────────────────────────────────
    score_result = compute_progress_score(
        project_data      = project_data,
        detection_results = detection_results,
        change_results    = change_results,
        weights           = weights,
    )

    # ── Delay prediction ──────────────────────────────────────────────────────
    delay_result = predict_delay(
        progress_score        = score_result["progress_score"],
        elapsed_days          = elapsed_days,
        planned_duration_days = planned_duration_days,
        planned_start_date    = planned_start_date,
    )

    # ── Risk classification ───────────────────────────────────────────────────
    risk_result = classify_risk_level(
        delay_days     = delay_result["delay_days"],
        progress_score = score_result["progress_score"],
        thresholds     = risk_thresholds,
    )

    # ── S-curve data ──────────────────────────────────────────────────────────
    s_curve = build_s_curve_data(
        temporal_images   = images,
        change_results    = change_results,
        planned_duration  = planned_duration_days,
        planned_start     = planned_start_date,
    )

    # ── Aggregate stats ───────────────────────────────────────────────────────
    summary_stats = {
        "total_images":       len(images),
        "total_detections":   detection_results.get("total_detections", 0),
        "avg_change_percent": change_results.get("avg_change", 0.0),
        "max_change_percent": change_results.get("max_change", 0.0),
        "change_pairs":       change_results.get("succeeded", 0),
        "severity_counts":    {},
    }

    # Extract severity counts from change results
    for r in change_results.get("results", []):
        sev = r.get("severity", "low")
        summary_stats["severity_counts"][sev] = summary_stats["severity_counts"].get(sev, 0) + 1

    return {
        "module":              "Module 5: Delay Prediction & Progress Assessment",
        "project_id":          project_data.get("project_id"),
        "project_name":        project_data.get("name"),
        "predicted_at":        datetime.utcnow().isoformat() + "Z",
        "progress":            score_result,
        "delay":               delay_result,
        "risk":                risk_result,
        "s_curve":             s_curve,
        "summary_stats":       summary_stats,
        "planned_duration_days": planned_duration_days,
        "planned_start_date":  planned_start_date,
    }
