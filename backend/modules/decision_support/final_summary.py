"""
Final Inspection Summary Generator
==================================

Produces the consolidated human-readable project inspection summary:
key findings, recommended actions, health score and schedule status —
all traceable to measurable evidence stored by Modules 1–6.

The generated report is saved per-project under
    processed/module7_decision/<project_id>/final_inspection_summary.json
and served via the API.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.utils.score_utils import format_schedule_variance

logger = logging.getLogger("decision.summary")


def _fmt_pct(v: Optional[float]) -> str:
    return f"{v:.1f}%" if isinstance(v, (int, float)) else "N/A"


def build_key_findings(
    project: Dict[str, Any],
    schedule_metrics: Dict[str, Any],
    variance_band: Dict[str, Any],
    change_summary: Dict[str, Any],
    detection_summary: Dict[str, Any],
    health: Dict[str, Any],
    image_count: int,
) -> List[str]:
    """Derive key findings strictly from available measured evidence."""
    findings: List[str] = []

    det = detection_summary or {}
    counts = det.get("aggregate_counts") or {}
    people = counts.get("Person", 0)
    machinery = counts.get("machinery", 0)
    vehicles = counts.get("vehicle", 0)

    if people or machinery or vehicles:
        findings.append(
            f"Construction activity is visible in the inspected imagery "
            f"({people} personnel, {machinery} machinery and {vehicles} vehicle instances detected)."
        )

    chg = change_summary or {}
    if chg.get("available"):
        if chg["avg_change_pct"] >= 5.0:
            findings.append(
                f"Structural changes were detected compared with the previous period "
                f"(average changed area {chg['avg_change_pct']}% across {chg['pairs_analysed']} image pair(s))."
            )
        else:
            findings.append(
                f"No significant structural progress was detected between inspection periods "
                f"(average changed area only {chg['avg_change_pct']}%)."
            )

    band = variance_band or {}
    if band.get("band") not in (None, "unknown"):
        findings.append(band.get("interpretation", ""))

    violations = sum(
        int(counts.get(k, 0) or 0)
        for k in ("NO-Hardhat", "NO-Mask", "NO-Safety Vest")
    )
    if violations:
        findings.append(f"{violations} PPE-related safety violation instance(s) require attention.")

    comp = det.get("avg_compliance")
    if comp is not None and not violations:
        findings.append(f"PPE compliance is high (average compliance rate {comp}%).")

    conf = health.get("components", {}).get("confidence", {})
    if conf.get("available") and (conf.get("raw_value") or 0) < 60:
        findings.append(
            "Inspection confidence is limited due to insufficient image coverage or quality; "
            "additional consistent-viewpoint imagery is recommended."
        )

    if not findings:
        findings.append(
            "No measurable evidence is available yet. Upload UAV images and run the AI inspection pipeline."
        )
    return findings


def build_recommendations(
    variance_band: Dict[str, Any],
    change_summary: Dict[str, Any],
    detection_summary: Dict[str, Any],
    health_components: Dict[str, Any],
) -> List[str]:
    """Actionable recommendations mapped one-to-one from observed evidence."""
    recs: List[str] = []
    band = (variance_band or {}).get("band")
    if band in ("minor_delay_risk", "moderate_delay", "high_delay_risk"):
        recs.append("Review delayed construction zones and re-sequence critical-path activities.")
    if band == "high_delay_risk":
        recs.append("Escalate schedule recovery planning to project management immediately.")
    if band == "on_track":
        recs.append("Maintain current construction pace and monitoring cadence.")

    det = detection_summary or {}
    counts = det.get("aggregate_counts") or {}
    if any(int(counts.get(k, 0) or 0) for k in ("NO-Hardhat", "NO-Mask", "NO-Safety Vest")):
        recs.append("Conduct a focused PPE compliance inspection and toolbox safety briefing.")

    chg = change_summary or {}
    if chg.get("available") and chg["avg_change_pct"] < 5.0:
        recs.append("Verify that imagery covers active work fronts; capture new UAV flights over planned zones.")

    conf = health_components.get("confidence", {})
    if not conf.get("available") or (conf.get("raw_value") or 0) < 60:
        recs.append("Capture additional UAV imagery from consistent viewpoints to improve analysis confidence.")

    recs.append("Perform another inspection after the next planned construction milestone to track progress delta.")
    return recs


def build_final_summary(
    project: Dict[str, Any],
    schedule_metrics: Dict[str, Any],
    variance_band: Dict[str, Any],
    change_summary: Dict[str, Any],
    detection_summary: Dict[str, Any],
    health: Dict[str, Any],
    output_path: Optional[Path] = None,
    inspection_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Assemble the complete final inspection summary dict.
    Optionally persists it as JSON at output_path.
    """
    now = datetime.now(timezone.utc).isoformat()
    image_count = int(project.get("image_count", 0) or 0)

    key_findings = build_key_findings(
        project, schedule_metrics, variance_band, change_summary, detection_summary, health, image_count,
    )
    recommendations = build_recommendations(
        variance_band, change_summary, detection_summary, health.get("components", {}),
    )

    score = health.get("score")

    summary = {
        "title": "PROJECT INSPECTION SUMMARY",
        "generated_at":   now,
        "project": {
            "project_id":     project.get("project_id"),
            "name":           project.get("name", ""),
            "location":       project.get("location", ""),
            "project_type":   project.get("project_type", ""),
            "project_manager": project.get("project_manager", ""),
            "status":         project.get("status", ""),
            "start_date":     project.get("start_date"),
            "estimated_completion": project.get("approximate_end_date"),
        },
        "inspection_id":  inspection_id,
        "images_analyzed": image_count,
        "progress": {
            "physical_progress_pct":  schedule_metrics.get("actual_progress"),
            "timeline_progress_pct":  schedule_metrics.get("expected_progress"),
            "schedule_variance_pct":  schedule_metrics.get("progress_deviation"),
            "schedule_variance_text": format_schedule_variance(
                delay_days=schedule_metrics.get("delay_days"),
                variance_pct=schedule_metrics.get("progress_deviation")
            ),
            "schedule_status_label":  (variance_band or {}).get("label"),
            "interpretation":         (variance_band or {}).get("interpretation"),
        },
        "safety": {
            "violation_instances": sum(
                int((detection_summary or {}).get("aggregate_counts", {}).get(k, 0) or 0)
                for k in ("NO-Hardhat", "NO-Mask", "NO-Safety Vest")
            ),
            "compliance_rate": (detection_summary or {}).get("avg_compliance"),
            "risk_level": (
                "LOW RISK" if not any(
                    int((detection_summary or {}).get("aggregate_counts", {}).get(k, 0) or 0)
                    for k in ("NO-Hardhat", "NO-Mask", "NO-Safety Vest")
                ) else ("MODERATE RISK" if sum(
                    int((detection_summary or {}).get("aggregate_counts", {}).get(k, 0) or 0)
                    for k in ("NO-Hardhat", "NO-Mask", "NO-Safety Vest")
                ) <= 8 else "HIGH RISK")
            ),
        },
        "change_detection": {
            "pairs_analysed":  (change_summary or {}).get("pairs_analysed", 0),
            "avg_change_pct":  (change_summary or {}).get("avg_change_pct"),
            "total_regions":   (change_summary or {}).get("total_regions", 0),
        },
        "health_score": {
            "score":          score,
            "classification": health.get("classification"),
            "breakdown":      health.get("breakdown"),
            "interpretation": health.get("interpretation"),
        },
        "key_findings":       key_findings,
        "recommended_actions": recommendations,
        "data_integrity_note": (
            "All values are computed from actual stored module outputs. Physical progress is an "
            "AI-derived estimate from visual analysis; it should be interpreted alongside official site records."
        ),
    }

    # Human-readable text block for reports / PDF embedding
    summary["text_report"] = _render_text(summary)

    if output_path:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, default=str)
            logger.info("Final summary saved: %s", output_path)
        except Exception as exc:
            logger.warning("Failed to save final summary: %s", exc)

    return summary


def _render_text(s: Dict[str, Any]) -> str:
    """Plain-text rendering of the summary for quick display / download."""
    var = s['progress']['schedule_variance_pct']
    change_area = s['change_detection'].get('avg_change_pct')
    hp = s["health_score"]
    lines = [
        "PROJECT INSPECTION SUMMARY",
        "=" * 60,
        f"Project:              {s['project']['name']}",
        f"Location:             {s['project']['location'] or '—'}",
        f"Inspection Date:      {s['generated_at'][:10]}",
        f"Images Analyzed:      {s['images_analyzed']}",
        "",
        f"Physical Progress:    {_fmt_pct(s['progress']['physical_progress_pct'])}",
        f"Timeline Progress:    {_fmt_pct(s['progress']['timeline_progress_pct'])}",
        (f"Schedule Variance:    {var:+.1f}%" if isinstance(var, (int, float)) else "Schedule Variance:    N/A"),
        f"Safety Violations:    {s['safety']['violation_instances']}",
        (f"Detected Change Area: {change_area}%" if change_area is not None else "Detected Change Area: N/A"),
        "",
        f"Overall Project Health: {hp['score'] if hp['score'] is not None else 'N/A'} / 100",
        f"Status:               {hp['classification']}",
        "",
        "KEY FINDINGS:",
    ]
    for i, kf in enumerate(s["key_findings"], 1):
        lines.append(f"  {i}. {kf}")
    lines += ["", "RECOMMENDED ACTIONS:"]
    for i, r in enumerate(s["recommended_actions"], 1):
        lines.append(f"  - {r}")
    return "\n".join(lines)
