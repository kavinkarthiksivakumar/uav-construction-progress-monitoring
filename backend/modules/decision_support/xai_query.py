"""
Structured Explainable AI Query Engine
======================================

Answers standard decision-support questions using ONLY stored evidence from
the AI pipeline (Modules 1–6) and project timeline data. Every answer follows
the same transparent structure:

    finding        — what was detected / decided
    location       — where it was detected (when spatial info exists)
    explanation    — why the system made the decision
    confidence     — qualitative confidence level with justification basis
    evidence       — list of concrete supporting artifacts/metrics
    limitations    — known caveats of this analysis
    recommendation — suggested management action

Available queries:
    what_changed          — site changes between inspection periods
    progress_status       — current physical vs timeline progress
    why_delayed           — schedule variance root-cause summary
    safety_concerns       — PPE violations and compliance issues
    region_attention      — regions requiring attention (change/XAI hotspots)
    evidence              — inventory of all supporting artifacts
    limitations           — system-wide analysis limitations
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("decision.xai_query")

AVAILABLE_QUERIES = [
    "what_changed",
    "progress_status",
    "why_delayed",
    "safety_concerns",
    "region_attention",
    "evidence",
    "limitations",
]

QUERY_LABELS = {
    "what_changed":     "What changed on the construction site?",
    "progress_status":  "What is the current construction progress?",
    "why_delayed":      "Why is the project delayed?",
    "safety_concerns":  "What are the main safety concerns?",
    "region_attention": "Which region requires attention?",
    "evidence":         "What evidence supports these results?",
    "limitations":      "What are the limitations of this analysis?",
}


# ─────────────────────────────────────────────────────────────────────────────
# Evidence collectors — read only real stored module outputs
# ─────────────────────────────────────────────────────────────────────────────

def _collect_change_evidence(change_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarise Module 4 change results into query-ready evidence."""
    if not change_results:
        return {"available": False}
    pcts = [float(r.get("change_percent", 0) or 0) for r in change_results]
    regions = sum(int(r.get("num_regions", 0) or 0) for r in change_results)
    largest = max(change_results, key=lambda r: float(r.get("change_percent", 0) or 0))
    overlays = [r.get("overlay_url") for r in change_results if r.get("overlay_url")]
    masks = [r.get("mask_url") for r in change_results if r.get("mask_url")]
    return {
        "available": True,
        "pairs_analysed": len(change_results),
        "avg_change_pct": round(sum(pcts) / len(pcts), 2),
        "max_change_pct": round(max(pcts), 2),
        "total_regions": regions,
        "largest_pair_id": largest.get("pair_id"),
        "largest_change_pct": round(float(largest.get("change_percent", 0) or 0), 2),
        "overlay_urls": overlays,
        "mask_urls": masks,
    }


def _collect_detection_evidence(detection_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Summarise Module 3 detection aggregates into query-ready evidence."""
    if not detection_summary:
        return {"available": False}
    counts = detection_summary.get("aggregate_counts") or {}
    violations = {}
    for k in ("NO-Hardhat", "NO-Mask", "NO-Safety Vest"):
        try:
            v = int(counts.get(k, 0))
            if v > 0:
                violations[k] = v
        except (TypeError, ValueError):
            pass
    activity = {}
    for k in ("Person", "machinery", "vehicle", "Safety Cone"):
        try:
            activity[k] = int(counts.get(k, 0))
        except (TypeError, ValueError):
            pass
    return {
        "available":       True,
        "images_analysed": detection_summary.get("image_count", 0),
        "total_detections": detection_summary.get("total_detections", 0),
        "violations":      violations,
        "activity":        activity,
        "compliance_rate": detection_summary.get("avg_compliance"),
        "mode_note":       detection_summary.get("mode_note"),
    }


def _confidence_label(evidence_count: int, has_change: bool, has_detection: bool) -> Dict[str, str]:
    """Qualitative confidence derived from breadth of supporting evidence."""
    score = evidence_count + (1 if has_change else 0) + (1 if has_detection else 0)
    if score >= 4:
        return {"level": "High", "basis": "Multiple independent analysis stages support this answer."}
    if score >= 2:
        return {"level": "Moderate", "basis": "Several analysis stages agree; some data was unavailable."}
    return {"level": "Low", "basis": "Limited evidence available for this question."}


def _limitation_lines(has_change: bool, has_detection: bool, mode_notes: List[str]) -> List[str]:
    lim = []
    lim.append(
        "UAV viewpoint variation and illumination differences can create false-positive "
        "change regions in classical differencing."
    )
    if not has_change:
        lim.append("No bi-temporal image pair was analysed, so no structural-change conclusions can be drawn.")
    if not has_detection:
        lim.append("No object-detection results were available; safety and activity statements are omitted.")
    lim.extend(mode_notes)
    return lim


# ─────────────────────────────────────────────────────────────────────────────
# Individual query handlers
# ─────────────────────────────────────────────────────────────────────────────

def _q_what_changed(ctx: Dict[str, Any]) -> Dict[str, Any]:
    chg = ctx["change"]
    det = ctx["detection"]
    ev_items: List[str] = []
    if chg.get("available"):
        ev_items.append(f"{chg['pairs_analysed']} bi-temporal image pair(s) analysed")
        ev_items.append(f"Average changed area {chg['avg_change_pct']}% of image footprint")
        ev_items.append(f"Largest change {chg['max_change_pct']}% (pair {chg['largest_pair_id']})")
    if det.get("available"):
        act = ", ".join(f"{v} {k}" for k, v in det["activity"].items() if v)
        if act:
            ev_items.append(f"Site activity detected: {act}")

    if not chg.get("available"):
        return {
            "finding": "No multi-temporal comparison is available yet.",
            "explanation": (
                "At least two images from different dates are required to run "
                "bi-temporal change detection."
            ),
            "recommendation": "Upload a before/after UAV image pair and re-run the inspection.",
        }

    significant = chg["avg_change_pct"] >= 5.0
    finding = (
        f"Structural change detected across {chg['pairs_analysed']} image pair(s); "
        f"average changed area {chg['avg_change_pct']}% with {chg['total_regions']} distinct change region(s)."
        if significant else
        f"Minimal structural change detected across {chg['pairs_analysed']} image pair(s); "
        f"average changed area only {chg['avg_change_pct']}%."
    )
    explanation = (
        "The system compares preprocessed before/after imagery using CLAHE contrast "
        "enhancement, absolute pixel differencing and Otsu thresholding to isolate "
        "structural change regions."
        if significant else
        "The differencing pipeline found few pixels above the automatic change threshold, "
        "indicating little visible structural development between the two periods."
    )
    return {
        "finding": finding,
        "location": f"Largest concentrated change region: pair '{chg['largest_pair_id']}' ({chg['largest_change_pct']}% of area)."
                    if chg.get("largest_pair_id") else None,
        "explanation": explanation,
        "evidence_items": ev_items,
        "artifacts": {
            "overlays": chg.get("overlay_urls")[:6],
            "masks": chg.get("mask_urls")[:6],
        },
        "recommendation": (
            "Review the change overlay imagery to verify that detected regions correspond to planned work zones."
            if significant else
            "If construction was expected during this period, verify image coverage and consider recapturing imagery."
        ),
    }


def _q_progress_status(ctx: Dict[str, Any]) -> Dict[str, Any]:
    sched = ctx["schedule_metrics"]
    actual = sched.get("actual_progress")
    expected = sched.get("expected_progress")
    variance = sched.get("progress_deviation")
    band = ctx["variance_band"]

    ev_items = []
    if expected is not None:
        ev_items.append(f"Timeline progress: {expected}% (elapsed/planned days)")
    if actual is not None:
        ev_items.append(f"Physical progress estimate: {actual}% (AI weighted composite)")
    if variance is not None:
        ev_items.append(f"Schedule variance: {variance:+.1f} percentage points")

    if actual is None:
        return {
            "finding": "Physical construction progress has not been estimated yet.",
            "explanation": "Run the full AI analysis pipeline on an inspection with uploaded images to estimate progress.",
            "recommendation": "Upload UAV images and run 'Full Assessment'.",
        }

    finding = (
        f"Physical construction progress is estimated at {actual}%. "
        + (band["interpretation"] if expected is not None else "")
    ).strip()
    return {
        "finding": finding,
        "explanation": (
            "Progress combines four weighted signals: detected site change (40%), "
            "construction activity density (30%), temporal coverage (20%) and image quality (10%)."
        ),
        "evidence_items": ev_items,
        "recommendation": (
            "Maintain current monitoring cadence." if variance is not None and variance >= 0 else
            "Review resourcing on lagging work fronts and confirm the next inspection captures recovery."
        ),
    }


def _q_why_delayed(ctx: Dict[str, Any]) -> Dict[str, Any]:
    sched = ctx["schedule_metrics"]
    variance = sched.get("progress_deviation")
    band = ctx["variance_band"]
    delay_days = ctx["project"].get("module5_delay_days")

    if variance is None:
        return {
            "finding": "Delay status cannot be determined yet.",
            "explanation": "A delay classification requires both the project timeline (start/end dates) and an AI physical progress estimate.",
            "recommendation": "Set the project start/completion dates and run a full assessment.",
        }

    if variance >= 0:
        finding = "The project is not delayed — physical progress matches or exceeds the planned timeline."
        explanation = band["interpretation"]
        recommendation = "Continue scheduled monitoring to maintain oversight."
    else:
        finding = (
            f"The project shows a schedule variance of {variance:.1f} percentage points "
            f"({band['label']})."
        )
        causes: List[str] = []
        chg = ctx["change"]
        det = ctx["detection"]
        if chg.get("available") and chg["avg_change_pct"] < 5.0:
            causes.append(f"Low structural change between inspection periods (avg {chg['avg_change_pct']}%)")
        if chg.get("available") and chg["avg_change_pct"] >= 5.0:
            causes.append(f"Active structural change observed (avg {chg['avg_change_pct']}%), suggesting progress is occurring but slower than planned")
        if det.get("available"):
            mach = det["activity"].get("machinery", 0) + det["activity"].get("vehicle", 0)
            people = det["activity"].get("Person", 0)
            if mach == 0 and people == 0:
                causes.append("No machinery, vehicle or personnel activity detected in inspected images")
            elif mach <= 2:
                causes.append(f"Limited machinery/vehicle activity detected ({mach} instances)")
        causes.append(f"Negative schedule variance of {abs(variance):.1f} percentage points")
        explanation = (
            "The project is classified as delayed because the estimated physical construction "
            "progress is substantially lower than the planned timeline progress. Supporting factors: "
            + "; ".join(causes) + "."
        )
        recommendation = (
            "Review critical-path activities, verify resource allocation on lagging work fronts, "
            "and schedule a follow-up inspection after corrective actions."
        )

    ev_items = []
    if sched.get("expected_progress") is not None:
        ev_items.append(f"Timeline progress: {sched['expected_progress']}%")
    if sched.get("actual_progress") is not None:
        ev_items.append(f"Observed physical progress: {sched['actual_progress']}%")
    if delay_days is not None:
        ev_items.append(f"Module 5 predicted schedule deviation: {delay_days:+d} days")

    return {
        "finding": finding,
        "explanation": explanation,
        "evidence_items": ev_items,
        "recommendation": recommendation,
    }


def _q_safety_concerns(ctx: Dict[str, Any]) -> Dict[str, Any]:
    det = ctx["detection"]
    if not det.get("available"):
        return {
            "finding": "No safety analysis is available yet.",
            "explanation": "Run activity/safety detection on uploaded UAV images to identify PPE compliance issues.",
            "recommendation": "Upload site images containing personnel and run detection.",
        }
    violations = det["violations"]
    total_violations = sum(violations.values())
    compliance = det.get("compliance_rate")
    risk_label = "LOW RISK" if total_violations == 0 else ("MODERATE RISK" if total_violations <= 8 else "HIGH RISK")

    viol_str = ", ".join(f"{k}: {v}" for k, v in violations.items()) if violations else "none recorded"
    finding = (
        f"Safety analysis detected {total_violations} missing-PPE instance(s) "
        f"({viol_str}). Overall safety risk: {risk_label}."
    )
    explanation = (
        "Personnel were analysed against required protective equipment classes "
        "(hardhat, safety vest, mask). Instances labelled NO-* indicate observed non-compliance."
        if violations else
        "All analysed personnel instances included required protective equipment classes."
    )
    ev_items = [
        f"{det['images_analysed']} image(s) analysed with {det['total_detections']} total detections",
    ]
    if compliance is not None:
        ev_items.append(f"Average PPE compliance rate: {compliance}%")
    for k, v in violations.items():
        ev_items.append(f"{k}: {v} instance(s)")

    return {
        "finding": finding,
        "explanation": explanation,
        "evidence_items": ev_items,
        "recommendation": (
            "Conduct a targeted on-site safety briefing and verify PPE distribution at entry points."
            if total_violations > 0 else
            "Maintain current PPE enforcement practices."
        ),
    }


def _q_region_attention(ctx: Dict[str, Any]) -> Dict[str, Any]:
    chg = ctx["change"]
    gradcam_urls = ctx.get("gradcam_urls") or []
    if not chg.get("available") and not gradcam_urls:
        return {
            "finding": "No spatial analysis is available to prioritise regions.",
            "explanation": "Region-level guidance requires either bi-temporal change results or visual attention outputs.",
            "recommendation": "Upload a temporal image pair and run the inspection analysis pipeline.",
        }
    parts = []
    if chg.get("available"):
        parts.append(
            f"The highest-change image pair '{chg['largest_pair_id']}' shows {chg['largest_change_pct']}% "
            f"changed area across {chg['total_regions']} region(s) — review this zone first."
        )
    if gradcam_urls:
        parts.append(
            f"{len(gradcam_urls)} AI spatial attention overlay(s) are available showing where the "
            "visual analysis focused most strongly."
        )
    finding = " ".join(parts)
    return {
        "finding": finding,
        "explanation": (
            "Change concentration and AI attention overlays are used as proxies for areas "
            "with the greatest observed development activity."
        ),
        "artifacts": {
            "overlays": chg.get("overlay_urls", [])[:4],
            "gradcam_overlays": gradcam_urls[:4],
        },
        "recommendation": "Cross-check flagged regions against the construction programme and assign site supervision accordingly.",
    }


def _q_evidence(ctx: Dict[str, Any]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    chg = ctx["change"]
    det = ctx["detection"]
    if chg.get("available"):
        items.append({
            "type": "Change detection masks & overlays",
            "detail": f"{chg['pairs_analysed']} pair(s); avg change {chg['avg_change_pct']}%",
            "urls": chg.get("overlay_urls", [])[:6],
        })
    if det.get("available"):
        items.append({
            "type": "Activity & PPE detections",
            "detail": f"{det['total_detections']} detections over {det['images_analysed']} image(s)",
        })
    if ctx.get("qualitative_count"):
        items.append({
            "type": "Qualitative result records",
            "detail": f"{ctx['qualitative_count']} structured visual result(s) available",
        })
    if ctx.get("prediction_available"):
        items.append({
            "type": "Progress assessment prediction",
            "detail": "Weighted composite progress score, delay days and S-curve saved on disk",
        })
    if ctx.get("xai_report_url"):
        items.append({
            "type": "AI intelligence report (attention maps + decision factors)",
            "url_reference": ctx["xai_report_url"],
        })
    return {
        "finding": f"{len(items)} evidence group(s) available supporting the current assessment." if items
                   else "No analysis evidence is stored yet.",
        "evidence_groups": items,
        "explanation": "Evidence is limited to artifacts actually generated by executed pipeline modules.",
        "recommendation": "Run the complete inspection workflow to build a full evidence chain." if not items else
                          "Download the XAI report for the consolidated evidence document.",
    }


def _q_limitations(ctx: Dict[str, Any]) -> Dict[str, Any]:
    notes = list(dict.fromkeys(ctx.get("mode_notes") or []))
    lines = _limitation_lines(ctx["change"].get("available", False), ctx["detection"].get("available", False), notes)
    return {
        "finding": f"This analysis carries {len(lines)} documented limitation(s).",
        "limitations_list": lines,
        "explanation": (
            "Limitations are disclosed so results are interpreted responsibly. Classical CV baselines "
            "(differencing + Otsu) and label-based simulation are used where trained deep models are not present."
        ),
        "recommendation": "Treat single-inspection conclusions as indicative; confirm important decisions with repeated inspections.",
    }


_HANDLERS = {
    "what_changed":     _q_what_changed,
    "progress_status":  _q_progress_status,
    "why_delayed":      _q_why_delayed,
    "safety_concerns":  _q_safety_concerns,
    "region_attention": _q_region_attention,
    "evidence":         _q_evidence,
    "limitations":      _q_limitations,
}


def answer_query(
    query: str,
    project: Dict[str, Any],
    schedule_metrics: Dict[str, Any],
    variance_band: Dict[str, Any],
    change_results: List[Dict[str, Any]],
    detection_summary: Dict[str, Any],
    gradcam_urls: Optional[List[str]] = None,
    qualitative_count: int = 0,
    prediction_available: bool = False,
    xai_report_url: Optional[str] = None,
    mode_notes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Answer a structured explainability query.

    Args mirror app.py's loaded stores. Returns a dict with the standard
    explanation structure (finding / explanation / evidence / confidence /
    limitations / recommendation).
    """
    query = (query or "").strip().lower()
    if query not in _HANDLERS:
        return {
            "error": f"Unknown query '{query}'.",
            "available_queries": AVAILABLE_QUERIES,
            "query_labels": QUERY_LABELS,
        }

    ctx = {
        "project": project,
        "schedule_metrics": schedule_metrics or {},
        "variance_band": variance_band or {},
        "change": _collect_change_evidence(change_results or []),
        "detection": _collect_detection_evidence(detection_summary or {}),
        "gradcam_urls": gradcam_urls or [],
        "qualitative_count": qualitative_count,
        "prediction_available": prediction_available,
        "xai_report_url": xai_report_url,
        "mode_notes": mode_notes or [],
    }

    core = _HANDLERS[query](ctx)

    # Assemble the uniform response structure
    has_change = ctx["change"].get("available", False)
    has_det = ctx["detection"].get("available", False)
    ev_n = len(core.get("evidence_items", [])) + len(core.get("evidence_groups", [])) + len(core.get("artifacts", {}) or {})
    confidence = _confidence_label(ev_n, has_change, has_det)

    response = {
        "query":          query,
        "question":       QUERY_LABELS.get(query, query),
        "finding":        core.get("finding", ""),
        "location":       core.get("location"),
        "why":            core.get("explanation", ""),
        "confidence":     confidence,
        "evidence":       core.get("evidence_items", core.get("evidence_groups", [])),
        "artifacts":      core.get("artifacts"),
        "limitations":    _limitation_lines(has_change, has_det, ctx["mode_notes"]),
        "recommendation": core.get("recommendation", ""),
    }
    logger.info("XAI query answered: %s", query)
    return response
