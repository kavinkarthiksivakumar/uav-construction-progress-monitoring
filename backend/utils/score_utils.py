"""
UAV Construction Progress Assessment — Centralized Score Normalization & Metrics Utilities
Defines standardized calculation, normalization, and formatting helpers across all modules.
"""

from typing import Any, Dict, List, Optional, Tuple
import math
import logging

logger = logging.getLogger("utils.score_utils")

# ─────────────────────────────────────────────────────────────────────────────
# 1. CORE NORMALIZATION PRIMITIVES
# ─────────────────────────────────────────────────────────────────────────────

def normalize_percentage(
    value: Any,
    default: float = 0.0,
    min_val: float = 0.0,
    max_val: float = 100.0,
    round_digits: int = 2
) -> float:
    """
    Normalize any numerical metric to a valid percentage in [min_val, max_val] (default [0, 100]).

    Intelligent handling:
      - None / non-numeric → default
      - 0.0 < value <= 1.0 (probabilities/ratios) → scaled to value * 100.0 (e.g. 0.84 → 84.0)
      - 1.0 < value <= 100.0 (existing percentages) → preserved (e.g. 39.55 → 39.55)
      - value > 100.0 (erroneous / unnormalized inputs like 3955) → clamped to max_val (100.0)
      - value < 0.0 (negative percentages) → clamped to min_val (0.0)
    """
    if value is None:
        return float(default)
    try:
        val = float(value)
    except (ValueError, TypeError):
        return float(default)

    if math.isnan(val) or math.isinf(val):
        return float(default)

    # If it is a probability ratio between 0 and 1, convert to 0-100%
    if 0.0 < val <= 1.0:
        val = val * 100.0

    # Strict clamping
    clamped = max(min_val, min(max_val, val))
    return round(clamped, round_digits)


def normalize_probability(value: Any, default: float = 0.0, round_digits: int = 4) -> float:
    """
    Normalize any numerical metric to a valid probability in [0.0, 1.0].

    Intelligent handling:
      - None / non-numeric → default
      - 1.0 < value <= 100.0 (percentage) → scaled to value / 100.0 (e.g. 84.0 → 0.84)
      - value > 100.0 → clamped to 1.0
      - value < 0.0 → clamped to 0.0
    """
    if value is None:
        return float(default)
    try:
        val = float(value)
    except (ValueError, TypeError):
        return float(default)

    if math.isnan(val) or math.isinf(val):
        return float(default)

    # If given as percentage > 1.0, convert to ratio
    if 1.0 < val <= 100.0:
        val = val / 100.0
    elif val > 100.0:
        val = 1.0
    elif val < 0.0:
        val = 0.0

    clamped = max(0.0, min(1.0, val))
    return round(clamped, round_digits)


def validate_metric_range(
    value: Any,
    min_val: float = 0.0,
    max_val: float = 100.0,
    default: float = 0.0,
    round_digits: int = 2
) -> float:
    """
    Defensive clamp that strictly enforces [min_val, max_val].
    Unlike normalize_percentage, this does not scale ratios, only clamps.
    """
    if value is None:
        return float(default)
    try:
        val = float(value)
    except (ValueError, TypeError):
        return float(default)

    if math.isnan(val) or math.isinf(val):
        return float(default)

    clamped = max(min_val, min(max_val, val))
    return round(clamped, round_digits)


# ─────────────────────────────────────────────────────────────────────────────
# 2. PROGRESS SCORE COMPOSITE CALCULATION
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_PROGRESS_WEIGHTS = {
    "change":   0.40,   # Module 4 visual change %
    "activity": 0.30,   # Module 3 detection density & compliance
    "temporal": 0.20,   # Module 1 temporal span
    "quality":  0.10,   # Module 1 image quality score
}

def calculate_progress_score(
    sub_scores: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Compute a weighted composite progress score strictly within [0.0, 100.0].

    Args:
        sub_scores: Dictionary of raw or normalized sub-scores (change, activity, temporal, quality).
        weights: Optional weight overrides.

    Returns:
        Dict with:
          progress_score: float in [0.0, 100.0]
          sub_scores: normalized sub scores
          weights_used: normalized weights summing to 1.0
          breakdown: human-readable strings
    """
    w = {**DEFAULT_PROGRESS_WEIGHTS, **(weights or {})}
    total_w = sum(max(0.0, float(v)) for v in w.values())
    if total_w > 0:
        w = {k: max(0.0, float(v)) / total_w for k, v in w.items()}
    else:
        w = DEFAULT_PROGRESS_WEIGHTS.copy()

    # Normalize each sub-score to [0, 100]
    norm_sub = {
        k: normalize_percentage(sub_scores.get(k, 0.0))
        for k in w.keys()
    }

    composite = sum(w[k] * norm_sub[k] for k in w.keys())
    final_score = validate_metric_range(composite, 0.0, 100.0)

    breakdown = {
        f"{k}_component": f"{norm_sub[k]:.1f}% × {w[k]:.0%} = {w[k]*norm_sub[k]:.1f}pts"
        for k in w.keys()
    }

    return {
        "progress_score": final_score,
        "sub_scores": norm_sub,
        "weights_used": w,
        "breakdown": breakdown,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. AI CONFIDENCE AGGREGATION
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_CONFIDENCE_WEIGHTS = {
    "detection":  0.35,  # Detection confidence
    "change":     0.35,  # Change detection confidence
    "temporal":   0.20,  # Temporal data span completeness
    "quality":    0.10,  # Image sharpness and exposure quality
}

def calculate_ai_confidence(
    components: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Compute multi-factor AI confidence strictly within [0.0, 100.0] %.
    Weights are always normalized to sum to 1.0, preventing values > 100%.

    Args:
        components: Dict of confidence components (0-1 or 0-100).
        weights: Optional weight dictionary.

    Returns:
        float confidence score in [0.0, 100.0]
    """
    if not components:
        return 50.0

    w = {**DEFAULT_CONFIDENCE_WEIGHTS, **(weights or {})}
    # Filter to components present or with positive weights
    active_keys = [k for k in w.keys() if k in components]
    if not active_keys:
        active_keys = list(components.keys())
        w = {k: 1.0 / len(active_keys) for k in active_keys}
    else:
        total_w = sum(w[k] for k in active_keys)
        w = {k: w[k] / total_w for k in active_keys}

    total_conf = 0.0
    for k in active_keys:
        val = normalize_percentage(components.get(k, 50.0))
        total_conf += w[k] * val

    return validate_metric_range(total_conf, 0.0, 100.0)


# ─────────────────────────────────────────────────────────────────────────────
# 4. SCHEDULE AND DELAY FORMATTING
# ─────────────────────────────────────────────────────────────────────────────

def classify_schedule_status(variance_pct: Optional[float]) -> str:
    """
    Classify schedule status based on progress deviation (actual_progress - expected_progress).

    Thresholds:
      variance >= +10.0 pts  → "Ahead of Schedule"
      -10.0 <= variance < 10.0 pts → "On Track"
      -25.0 <= variance < -10.0 pts → "At Risk"
      variance < -25.0 pts   → "Delayed"
    """
    if variance_pct is None:
        return "Unknown"

    v = float(variance_pct)
    if v >= 10.0:
        return "Ahead of Schedule"
    elif v >= -10.0:
        return "On Track"
    elif v >= -25.0:
        return "At Risk"
    else:
        return "Delayed"


def format_schedule_variance(
    delay_days: Optional[int] = None,
    variance_pct: Optional[float] = None
) -> str:
    """
    Convert schedule delay or deviation numbers into human-friendly statements.

    Examples:
      delay_days = -143 → "143 days ahead of schedule"
      delay_days = 0    → "On schedule"
      delay_days = 14   → "14 days behind schedule"
      variance_pct = -12.5 → "12.5 pts behind schedule"
    """
    if delay_days is not None:
        d = int(delay_days)
        if d == 0:
            return "On schedule"
        elif d < 0:
            return f"{abs(d)} day{'s' if abs(d) != 1 else ''} ahead of schedule"
        else:
            return f"{d} day{'s' if d != 1 else ''} behind schedule"

    if variance_pct is not None:
        v = float(variance_pct)
        if abs(v) < 0.5:
            return "On schedule"
        elif v > 0:
            return f"{v:.1f} pts ahead of schedule"
        else:
            return f"{abs(v):.1f} pts behind schedule"

    return "Schedule status unavailable"


# ─────────────────────────────────────────────────────────────────────────────
# 5. RISK SCORE CALCULATION
# ─────────────────────────────────────────────────────────────────────────────

RISK_LEVEL_THRESHOLDS = {
    "on_track": (0.0, 25.0),
    "at_risk":  (25.0, 50.0),
    "delayed":  (50.0, 75.0),
    "critical": (75.0, 100.0),
}

def calculate_risk_score(
    delay_days: int = 0,
    progress_deviation: float = 0.0,
    safety_violations: int = 0,
    uninspected_days: int = 0
) -> Dict[str, Any]:
    """
    Calculate an integrated project risk score [0, 100].

    Components:
      - Schedule risk: derived from delay days and negative deviation
      - Safety risk: derived from open PPE/hazard violations
      - Inspection latency risk: derived from days since last inspection
    """
    # 1. Schedule risk component (0–60 pts)
    sched_risk = 0.0
    if delay_days > 0:
        sched_risk += min(delay_days * 1.5, 40.0)
    if progress_deviation < 0:
        sched_risk += min(abs(progress_deviation) * 0.8, 20.0)
    sched_risk = min(sched_risk, 60.0)

    # 2. Safety risk component (0–25 pts)
    safety_risk = min(safety_violations * 5.0, 25.0)

    # 3. Latency risk component (0–15 pts)
    latency_risk = min(max(0, uninspected_days - 14) * 0.5, 15.0)

    total_risk = round(validate_metric_range(sched_risk + safety_risk + latency_risk, 0.0, 100.0), 1)

    if total_risk < 25.0:
        level = "on_track"
        label = "Low Risk"
        color = "#22c55e"
    elif total_risk < 50.0:
        level = "at_risk"
        label = "Medium Risk"
        color = "#f59e0b"
    elif total_risk < 75.0:
        level = "delayed"
        label = "High Risk"
        color = "#ef4444"
    else:
        level = "critical"
        label = "Critical Risk"
        color = "#dc2626"

    return {
        "risk_score": total_risk,
        "risk_level": level,
        "label": label,
        "color": color,
        "breakdown": {
            "schedule_risk": round(sched_risk, 1),
            "safety_risk": round(safety_risk, 1),
            "latency_risk": round(latency_risk, 1),
        }
    }
