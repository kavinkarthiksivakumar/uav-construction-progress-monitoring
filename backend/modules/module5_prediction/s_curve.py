"""
Module 5: S-Curve Builder
IEEE M.Tech Project — Explainable Vision-Based Construction Progress Assessment

Generates S-curve data (planned vs actual cumulative progress) for charting.

Construction S-curves typically follow a logistic/sigmoid shape:
  - Slow start (mobilisation)
  - Rapid mid-phase (active construction)
  - Deceleration at completion

Output format (list of data points):
  [
    {
      "label":          "Day 0" or "2024-01-01",
      "planned":        0.0,        # planned cumulative % (0–100)
      "actual":         0.0,        # actual cumulative % (0–100)
      "change_event":   false,      # whether a change was detected at this point
      "change_percent": 0.0,        # change % for this period
    },
    ...
  ]
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("module5.s_curve")


# ─────────────────────────────────────────────────────────────────────────────
# Planned S-Curve Generator (Logistic)
# ─────────────────────────────────────────────────────────────────────────────

def _planned_logistic(t: float, total: float = 1.0) -> float:
    """
    Logistic (sigmoid) S-curve for planned progress.
    t        : elapsed fraction [0, 1]
    Returns  : planned progress fraction [0, 1]
    """
    if total <= 0:
        return 0.0
    frac = t / total
    # Standard logistic: inflection at 50%, steepness k=8
    k  = 8.0
    x0 = 0.5
    raw = 1.0 / (1.0 + math.exp(-k * (frac - x0)))
    # Normalise so planned(0)=0, planned(1)=1
    raw_0 = 1.0 / (1.0 + math.exp(-k * (0.0 - x0)))
    raw_1 = 1.0 / (1.0 + math.exp(-k * (1.0 - x0)))
    if raw_1 - raw_0 < 1e-9:
        return frac * 100.0
    return ((raw - raw_0) / (raw_1 - raw_0)) * 100.0


# ─────────────────────────────────────────────────────────────────────────────
# Actual Progress from Change Detection Results
# ─────────────────────────────────────────────────────────────────────────────

def _extract_actual_progress(change_results: Dict) -> List[float]:
    """
    Extract per-pair change percentages from Module 4 results.
    Returns a list of cumulative progress values (0–100).
    """
    results = change_results.get("results", [])
    if not results:
        return []

    cumulative = []
    running = 0.0
    for r in results:
        if r.get("success"):
            running += r.get("change_percent", 0.0)
            # Cap cumulative at 100 for display
            cumulative.append(min(running, 100.0))
        else:
            cumulative.append(cumulative[-1] if cumulative else 0.0)

    # Normalise to 0–100 range based on max observed change
    if cumulative:
        max_val = max(cumulative)
        if max_val > 0:
            cumulative = [round(v / max_val * 100.0, 2) for v in cumulative]

    return cumulative


# ─────────────────────────────────────────────────────────────────────────────
# Build S-Curve Data Points
# ─────────────────────────────────────────────────────────────────────────────

def build_s_curve_data(
    temporal_images:  List[Dict],
    change_results:   Dict,
    planned_duration: int           = 365,
    planned_start:    Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build S-curve data for both planned and actual progress.

    Args:
        temporal_images:   List of project image dicts (with optional timestamps).
        change_results:    Module 4 batch result dict.
        planned_duration:  Total planned duration in days.
        planned_start:     Optional ISO date string for project start.

    Returns:
        Dict with:
          points        — list of {label, planned, actual, change_event, change_percent}
          x_labels      — list of label strings
          planned_data  — list of planned progress values
          actual_data   — list of actual progress values
          has_dates     — whether real dates were available
    """
    pairs_results = change_results.get("results", [])
    actual_vals   = _extract_actual_progress(change_results)

    # ── Determine time axis ───────────────────────────────────────────────────
    has_dates = False
    date_labels = []

    # Try extracting dates from images
    image_dates = []
    for img in temporal_images:
        ts = img.get("timestamp") or img.get("capture_date") or img.get("upload_time")
        if ts:
            try:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                image_dates.append(dt)
            except Exception:
                pass

    if len(image_dates) >= 2:
        has_dates = True
        image_dates.sort()

    # ── Generate planned curve points ─────────────────────────────────────────
    # We generate N+1 points spanning the planned duration
    # N = max(len(pairs_results), 10) for reasonable resolution
    n_points = max(len(pairs_results) + 1, 10, 20)

    planned_data = []
    x_labels     = []

    if has_dates and planned_start:
        try:
            start_dt = datetime.fromisoformat(planned_start.replace("Z", "+00:00"))
        except Exception:
            start_dt = image_dates[0] if image_dates else datetime.utcnow()
    elif has_dates and image_dates:
        start_dt = image_dates[0]
    else:
        start_dt = None

    for i in range(n_points):
        t = i / (n_points - 1)   # 0 to 1
        planned_val = round(_planned_logistic(t, 1.0), 2)
        planned_data.append(planned_val)

        if start_dt:
            point_date = start_dt + timedelta(days=t * planned_duration)
            x_labels.append(point_date.strftime("%b %d"))
        else:
            x_labels.append(f"Day {int(t * planned_duration)}")

    # ── Build actual data aligned to planned axis ─────────────────────────────
    # Map actual values onto the same n_points axis
    actual_data = [None] * n_points   # None = not yet reached

    if actual_vals:
        # Distribute actual data points across the first portion of the axis
        # (observations cover elapsed time, not full duration)
        n_actual = len(actual_vals)
        elapsed_frac = min(
            max((n_actual / max(len(temporal_images), 1)), 0.1),
            1.0
        )

        for idx, val in enumerate(actual_vals):
            axis_pos = int((idx / max(n_actual - 1, 1)) * elapsed_frac * (n_points - 1))
            axis_pos = min(axis_pos, n_points - 1)
            actual_data[axis_pos] = val

        # Fill gaps with linear interpolation
        last_known = 0.0
        last_set   = 0
        for i in range(n_points):
            if actual_data[i] is not None:
                last_known = actual_data[i]
                last_set   = i
            elif i > last_set and i <= int(elapsed_frac * (n_points - 1)):
                actual_data[i] = last_known

    # ── Assemble data points ──────────────────────────────────────────────────
    points = []
    for i in range(n_points):
        actual_val = actual_data[i]

        # Match change events to this point
        pair_idx     = None
        change_pct_v = 0.0
        change_event = False

        if pairs_results and actual_vals:
            # Find the closest pair to this axis position
            n_actual = len(pairs_results)
            elapsed_frac = min(
                max((n_actual / max(len(temporal_images), 1)), 0.1), 1.0
            )
            expected_pair = int(i / (n_points - 1) / elapsed_frac * n_actual)
            if 0 <= expected_pair < n_actual:
                pair_idx   = expected_pair
                change_pct_v = pairs_results[pair_idx].get("change_percent", 0.0)
                change_event = change_pct_v > 0.1

        points.append({
            "label":          x_labels[i],
            "planned":        planned_data[i],
            "actual":         actual_val,
            "change_event":   change_event,
            "change_percent": round(change_pct_v, 2),
        })

    logger.info("S-curve built: %d points, has_dates=%s", n_points, has_dates)

    return {
        "points":       points,
        "x_labels":     x_labels,
        "planned_data": planned_data,
        "actual_data":  actual_data,
        "has_dates":    has_dates,
        "n_points":     n_points,
        "label_mode":   "calendar" if has_dates else "sequence",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Schedule Milestones
# ─────────────────────────────────────────────────────────────────────────────

def get_schedule_milestones(
    planned_start:    Optional[str] = None,
    planned_duration: int           = 365,
    current_progress: float         = 0.0,
) -> List[Dict[str, Any]]:
    """
    Return standard construction project milestones for the timeline.

    Milestones are defined as % of project duration (standard construction phases):
      0%   → Project Start / Mobilisation
      15%  → Foundation Complete
      35%  → Structural Frame Complete
      55%  → Building Envelope Complete
      70%  → MEP Rough-In Complete
      85%  → Interior Finishing
      95%  → Snag List / Commissioning
      100% → Project Handover

    Args:
        planned_start:    ISO date string for project start.
        planned_duration: Planned duration in days.
        current_progress: Current actual progress %.

    Returns:
        List of milestone dicts.
    """
    milestones_def = [
        (0,   "Mobilisation",           "🏗️"),
        (15,  "Foundation Complete",     "🪨"),
        (35,  "Structural Frame",        "🔩"),
        (55,  "Building Envelope",       "🧱"),
        (70,  "MEP Rough-In",            "⚡"),
        (85,  "Interior Finishing",      "🎨"),
        (95,  "Commissioning",           "✅"),
        (100, "Project Handover",        "🏁"),
    ]

    start_dt = None
    if planned_start:
        try:
            start_dt = datetime.fromisoformat(planned_start.replace("Z", "+00:00"))
        except Exception:
            pass

    milestones = []
    for pct, name, icon in milestones_def:
        days_offset = int(pct / 100.0 * planned_duration)
        date_str    = None

        if start_dt:
            ms_date  = start_dt + timedelta(days=days_offset)
            date_str = ms_date.strftime("%b %d, %Y")

        status = "completed" if current_progress >= pct else (
            "in_progress" if current_progress >= pct - 15 else "upcoming"
        )

        milestones.append({
            "name":        name,
            "icon":        icon,
            "percent":     pct,
            "days_offset": days_offset,
            "date":        date_str,
            "status":      status,
            "color": {
                "completed":   "#22c55e",
                "in_progress": "#f59e0b",
                "upcoming":    "#6b7280",
            }[status],
        })

    return milestones
