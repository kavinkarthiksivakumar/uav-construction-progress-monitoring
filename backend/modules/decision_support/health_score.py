"""
Project Health Score — Transparent Weighted Assessment
======================================================

Computes a single 0–100 project health score from measurable evidence:

    HEALTH = w_progress   × Progress Score            (Module 5 physical progress)
           + w_schedule   × Schedule Score             (timeline vs physical variance)
           + w_safety     × Safety Score               (Module 3 PPE compliance)
           + w_confidence × Inspection Confidence      (data quality / coverage)
           + w_activity   × Activity Score             (Module 3 site activity density)

Every sub-score is derived from actually stored module outputs. When an input
is unavailable the sub-score is marked as such and the weights of the remaining
available components are renormalised so the total remains comparable.

Classifications:
    80–100  HEALTHY
    60–79   STABLE
    40–59   AT RISK
    0–39    CRITICAL
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("decision.health")

# Default configurable weights (must sum to 1.0)
HEALTH_WEIGHTS = {
    "progress":   0.35,
    "schedule":   0.25,
    "safety":     0.20,
    "confidence": 0.10,
    "activity":   0.10,
}

HEALTH_CLASSIFICATIONS = [
    {"min": 80, "label": "HEALTHY",  "color": "#22c55e",
     "description": "Project demonstrates strong progress, schedule adherence and safety compliance."},
    {"min": 60, "label": "STABLE",   "color": "#84cc16",
     "description": "Project is progressing but with areas that need attention."},
    {"min": 40, "label": "AT RISK",  "color": "#f59e0b",
     "description": "Project shows significant deviations requiring management action."},
    {"min": 0,  "label": "CRITICAL", "color": "#ef4444",
     "description": "Project requires urgent intervention and replanning."},
]

# Schedule variance classification thresholds (percentage points)
SCHEDULE_VARIANCE_BANDS = {
    "on_track":         0,    # variance >= 0        -> ON TRACK
    "minor_delay_risk": -10,  # -10 <= variance < 0  -> MINOR DELAY RISK
    "moderate_delay":   -20,  # -20 <= variance < -10-> MODERATE DELAY
    # variance < -20                          -> HIGH DELAY RISK
}


def classify_schedule_variance(variance: Optional[float]) -> Dict[str, Any]:
    """Classify a schedule variance (physical% − timeline%) into a delay band."""
    if variance is None:
        return {
            "band": "unknown",
            "label": "Unknown",
            "color": "#9ca3af",
            "interpretation": (
                "Schedule variance cannot be calculated until both a project "
                "timeline and an AI-based physical progress estimate are available."
            ),
        }
    if variance >= SCHEDULE_VARIANCE_BANDS["on_track"]:
        return {
            "band": "on_track", "label": "ON TRACK", "color": "#22c55e",
            "interpretation": "Physical construction progress is at or ahead of the planned timeline.",
        }
    if variance >= SCHEDULE_VARIANCE_BANDS["minor_delay_risk"]:
        return {
            "band": "minor_delay_risk", "label": "MINOR DELAY RISK", "color": "#eab308",
            "interpretation": (
                f"Physical construction progress is {abs(variance):.1f} percentage points "
                f"behind the planned timeline."
            ),
        }
    if variance >= SCHEDULE_VARIANCE_BANDS["moderate_delay"]:
        return {
            "band": "moderate_delay", "label": "MODERATE DELAY", "color": "#f59e0b",
            "interpretation": (
                f"Physical construction progress is {abs(variance):.1f} percentage points "
                f"behind the planned timeline — moderate delay detected."
            ),
        }
    return {
        "band": "high_delay_risk", "label": "HIGH DELAY RISK", "color": "#ef4444",
        "interpretation": (
            f"Physical construction progress is {abs(variance):.1f} percentage points "
            f"behind the planned timeline — high delay risk."
        ),
    }


def _sub_score(value: Any) -> Optional[float]:
    """Coerce a stored value to a 0–100 float or None when unusable."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return min(max(v, 0.0), 100.0)


def compute_health_score(
    project: Dict[str, Any],
    schedule_metrics: Dict[str, Any],
    detection_summary: Optional[Dict[str, Any]] = None,
    inspection_stats: Optional[Dict[str, Any]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compute the transparent weighted project health score.

    Args:
        project:           Project store record.
        schedule_metrics:  Output of app._compute_project_metrics() (timeline data).
        detection_summary: Aggregate Module 3 results (optional).
            Expected keys: avg_compliance, total_detections, image_count.
        inspection_stats:  Optional dict with image_count / quality info for confidence.
        weights:           Optional weight overrides.

    Returns:
        Dict with score (0–100), classification, breakdown (points earned vs max),
        sub-scores and per-component availability flags.
    """
    w = {**HEALTH_WEIGHTS, **(weights or {})}
    detection_summary = detection_summary or {}
    inspection_stats = inspection_stats or {}

    components: Dict[str, Dict[str, Any]] = {}

    # ── 1. Progress Score — Module 5 physical progress ────────────────────────
    raw_progress = (
        project.get("module5_score")
        or project.get("progress_score")
        or schedule_metrics.get("actual_progress")
    )
    progress_val = _sub_score(raw_progress)
    components["progress"] = {
        "raw_value":   round(progress_val, 2) if progress_val is not None else None,
        "max_points":  round(100 * w["progress"], 2),
        "earned":      round(progress_val * w["progress"], 2) if progress_val is not None else 0.0,
        "available":   progress_val is not None,
        "source":      "Module 5 weighted composite physical progress estimate" if progress_val is not None else None,
        "unavailable_reason": None if progress_val is not None else "Run AI analysis to obtain a physical progress estimate.",
    }

    # ── 2. Schedule Score — how close physical is to timeline progress ────────
    expected = schedule_metrics.get("expected_progress")
    actual   = schedule_metrics.get("actual_progress")
    variance = None
    schedule_val = None
    if expected is not None and actual is not None:
        variance = round(float(actual) - float(expected), 2)
        # 100 pts when on/ahead; lose 2.5 pts per percentage point behind;
        # reaches 0 at 40 points behind.
        schedule_val = min(max(100.0 + variance * 2.5, 0.0), 100.0)
    components["schedule"] = {
        "raw_value":   round(schedule_val, 2) if schedule_val is not None else None,
        "variance":    variance,
        "variance_band": classify_schedule_variance(variance),
        "max_points":  round(100 * w["schedule"], 2),
        "earned":      round(schedule_val * w["schedule"], 2) if schedule_val is not None else 0.0,
        "available":   schedule_val is not None,
        "source":      "Timeline progress (elapsed/planned days) vs Module 5 physical progress" if schedule_val is not None else None,
        "unavailable_reason": (
            None if schedule_val is not None
            else "Requires both project start/end dates and an AI physical progress estimate."
        ),
    }

    # ── 3. Safety Score — PPE compliance rate from Module 3 ───────────────────
    compliance_raw = detection_summary.get("avg_compliance")
    safety_val = _sub_score(compliance_raw)
    violations = 0
    counts = detection_summary.get("aggregate_counts") or {}
    for k in ("NO-Hardhat", "NO-Mask", "NO-Safety Vest"):
        try:
            violations += int(counts.get(k, 0))
        except (TypeError, ValueError):
            pass
    if safety_val is None and detection_summary:
        # Detections exist but no compliance rate — treat as neutral-poor
        safety_val = 50.0
    components["safety"] = {
        "raw_value":          round(safety_val, 2) if safety_val is not None else None,
        "compliance_rate":    compliance_raw,
        "violation_count":    violations,
        "max_points":         round(100 * w["safety"], 2),
        "earned":             round(safety_val * w["safety"], 2) if safety_val is not None else 0.0,
        "available":          safety_val is not None,
        "source":             "Module 3 PPE compliance analysis" if safety_val is not None else None,
        "unavailable_reason": None if safety_val is not None else "Run activity/safety detection on uploaded images.",
    }

    # ── 4. Inspection Confidence — data volume + quality ──────────────────────
    conf_val: Optional[float] = None
    img_count = int(inspection_stats.get("image_count") or project.get("image_count") or 0)
    avg_quality = inspection_stats.get("avg_quality_score")
    if img_count > 0 or avg_quality is not None:
        coverage = min(img_count / 8.0, 1.0) * 100.0       # 8+ images → full coverage credit
        quality_component = _sub_score(avg_quality)
        if quality_component is None:
            quality_component = 70.0                        # neutral assumption, disclosed
        conf_val = round(0.6 * coverage + 0.4 * quality_component, 2)
    components["confidence"] = {
        "raw_value":          conf_val,
        "image_count":        img_count,
        "avg_quality_score":  avg_quality,
        "max_points":         round(100 * w["confidence"], 2),
        "earned":             round(conf_val * w["confidence"], 2) if conf_val is not None else 0.0,
        "available":          conf_val is not None,
        "source":             "UAV image count and Module 1 quality scores" if conf_val is not None else None,
        "unavailable_reason": None if conf_val is not None else "No UAV images uploaded yet.",
    }

    # ── 5. Activity Score — site activity density from Module 3 ───────────────
    act_val: Optional[float] = None
    total_dets = detection_summary.get("total_detections")
    det_images = detection_summary.get("image_count") or 0
    if total_dets is not None and det_images:
        density = float(total_dets) / max(int(det_images), 1)
        act_val = round(min(density / 20.0, 1.0) * 100.0, 2)
    elif total_dets:
        act_val = round(min(float(total_dets) / 20.0, 1.0) * 100.0, 2)
    components["activity"] = {
        "raw_value":          act_val,
        "total_detections":   total_dets,
        "detection_density":  round(total_dets / max(det_images, 1), 2) if (total_dets is not None and det_images) else None,
        "max_points":         round(100 * w["activity"], 2),
        "earned":             round(act_val * w["activity"], 2) if act_val is not None else 0.0,
        "available":          act_val is not None,
        "source":             "Module 3 person/machinery/vehicle detections" if act_val is not None else None,
        "unavailable_reason": None if act_val is not None else "Run activity detection to measure site activity.",
    }

    # ── Aggregate with renormalisation over available components ──────────────
    # `earned` is expressed in absolute points on a 0–100 scale:
    #   earned_k = (raw_k / 100) * w_k * 100
    # When every component is available (Σw = 1) the total is directly the score;
    # otherwise renormalise by the weight mass actually covered.
    available_weight = sum(w[k] for k, c in components.items() if c["available"])
    earned = sum(c["earned"] for c in components.values())
    if available_weight > 0:
        score = round(min(max(earned / available_weight, 0.0), 100.0), 1)
    else:
        score = None

    classification = None
    if score is not None:
        for band in HEALTH_CLASSIFICATIONS:
            if score >= band["min"]:
                classification = band
                break

    breakdown = {
        k: {
            "earned":    c["earned"],
            "max":       c["max_points"],
            "display":   f"{c['earned']:.1f} / {c['max_points']:.0f}" if c["available"] else "n/a",
        }
        for k, c in components.items()
    }

    interpretation = _build_interpretation(score, classification, components)

    logger.info(
        "Health score computed: score=%s class=%s (progress=%s schedule=%s safety=%s conf=%s activity=%s)",
        score,
        classification["label"] if classification else "n/a",
        progress_val, schedule_val, safety_val, conf_val, act_val,
    )

    return {
        "score":              score,
        "max_score":          100,
        "classification":     classification["label"] if classification else "NOT ASSESSABLE",
        "classification_color": classification["color"] if classification else "#9ca3af",
        "classification_description": classification["description"] if classification else (
            "Insufficient data. Upload UAV images and run the AI analysis pipeline first."
        ),
        "weights_used":       w,
        "breakdown":          breakdown,
        "components":         components,
        "schedule_variance":  components["schedule"]["variance"],
        "variance_interpretation": components["schedule"]["variance_band"]["interpretation"],
        "renormalised":       available_weight < 0.999,
        "interpretation":     interpretation,
    }


def _build_interpretation(score, classification, components) -> str:
    """Generate the human-readable 'why' behind the health score."""
    if score is None:
        return (
            "A health score cannot be produced yet because no measured component "
            "(progress, schedule, safety, confidence or activity) has data. "
            "Upload UAV images and run the inspection pipeline."
        )

    parts = []
    p = components["progress"]
    s = components["schedule"]
    sf = components["safety"]

    if s["available"]:
        parts.append(s["variance_band"]["interpretation"])
    if p["available"]:
        parts.append(f"The estimated physical construction progress is {p['raw_value']:.0f}%.")
    if sf["available"]:
        if sf["violation_count"]:
            parts.append(
                f"Safety analysis recorded {sf['violation_count']} PPE violation instance(s); "
                f"average compliance is {sf['compliance_rate']}%."
            )
        else:
            parts.append("No missing-PPE violation instances were recorded in the analysed images.")
    if classification:
        parts.append(classification["description"])

    return " ".join(parts)
