"""
Module 6 — AI Explainability Report Generator
UAV Vision — AI-Powered Construction Intelligence Platform

Generates a comprehensive explainability report combining:
  - AI attention map visualisations
  - Key decision factors analysis
  - Progress prediction summary
  - Actionable narrative and recommendations
  - Executive summary for project review

Output: HTML report (always) + PDF (if reportlab/fpdf2 available)
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("module6.pdf_report")

# ─────────────────────────────────────────────────────────────────────────────
# HTML Report Template
# ─────────────────────────────────────────────────────────────────────────────

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>AI Construction Intelligence Report — {project_name}</title>
<style>
  :root {{
    --bg: #0f172a; --surface: #1e293b; --border: #334155;
    --text: #f1f5f9; --muted: #94a3b8; --accent: #3b82f6;
    --green: #22c55e; --yellow: #f59e0b; --red: #ef4444;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', Arial, sans-serif;
         font-size: 14px; line-height: 1.6; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 32px 24px; }}
  h1 {{ font-size: 28px; color: var(--accent); margin-bottom: 4px; }}
  h2 {{ font-size: 20px; color: var(--text); margin: 32px 0 12px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
  h3 {{ font-size: 16px; color: var(--muted); margin: 16px 0 8px; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }}
  .badge-green {{ background: rgba(34,197,94,.15); color: var(--green); border: 1px solid var(--green); }}
  .badge-yellow {{ background: rgba(245,158,11,.15); color: var(--yellow); border: 1px solid var(--yellow); }}
  .badge-red {{ background: rgba(239,68,68,.15); color: var(--red); border: 1px solid var(--red); }}
  .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
           padding: 20px; margin-bottom: 20px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  .stat {{ text-align: center; }}
  .stat .value {{ font-size: 36px; font-weight: 700; color: var(--accent); }}
  .stat .label {{ font-size: 12px; color: var(--muted); margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
  th {{ background: var(--border); padding: 8px 12px; text-align: left; font-size: 12px; color: var(--muted); }}
  td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); }}
  tr:last-child td {{ border: none; }}
  img.chart {{ width: 100%; border-radius: 8px; margin-top: 8px; border: 1px solid var(--border); }}
  .narrative {{ background: rgba(59,130,246,.08); border-left: 3px solid var(--accent);
                padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 12px 0; font-style: italic; }}
  .rec-item {{ display: flex; gap: 10px; margin: 8px 0; align-items: flex-start; }}
  .rec-icon {{ color: var(--accent); font-size: 16px; margin-top: 2px; flex-shrink: 0; }}
  .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border);
             text-align: center; color: var(--muted); font-size: 12px; }}
  .progress-bar {{ height: 12px; background: var(--border); border-radius: 6px; overflow: hidden; margin: 6px 0; }}
  .progress-fill {{ height: 100%; border-radius: 6px; transition: width .3s; }}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <h1>📋 AI Construction Intelligence Report</h1>
  <p style="color:var(--muted); margin-bottom: 8px;">{project_name} &bull; Generated {generated_at}</p>
  <span class="badge badge-{risk_badge}">{risk_label}</span>

  <!-- Executive Summary -->
  <h2>Executive Summary</h2>
  <div class="card">
    <div class="grid-2">
      <div class="stat">
        <div class="value" style="color:{progress_color}">{progress_score:.1f}%</div>
        <div class="label">Construction Progress</div>
      </div>
      <div class="stat">
        <div class="value" style="color:{delay_color}">{delay_days:+d} days</div>
        <div class="label">Schedule Deviation</div>
      </div>
    </div>
    <div style="margin-top:20px;">
      <strong>Progress Score</strong>
      <div class="progress-bar"><div class="progress-fill" style="width:{progress_score}%;background:{progress_color}"></div></div>
    </div>
  </div>

  <!-- Analysis Input Factors -->
  <h2>Analysis Input Factors</h2>
  <div class="card">
    <table>
      <thead><tr>
        <th>Factor</th><th>Analysis Stage</th><th>Score</th><th>Weight</th><th>Contribution</th>
      </tr></thead>
      <tbody>
        {feature_rows}
      </tbody>
    </table>
  </div>

  <!-- Key Decision Factors -->
  <h2>Key Decision Factors</h2>
  <div class="card">
    <p style="color:var(--muted); margin-bottom:12px;">
      Decision factors quantify each visual indicator's contribution to the overall progress score relative to baseline.
      Positive impacts indicate progress milestones on track; negative impacts highlight delay factors requiring attention.
    </p>
    {shap_narrative}
    {shap_bar_img}
    {shap_wf_img}
    <h3>Factor Contributions</h3>
    <table>
      <thead><tr><th>Factor</th><th>Measured Value</th><th>Influence</th><th>Impact</th></tr></thead>
      <tbody>
        {shap_rows}
      </tbody>
    </table>
  </div>

  <!-- AI Attention Map Analysis -->
  <h2>AI Attention Map Analysis</h2>
  <div class="card">
    <p style="color:var(--muted); margin-bottom:12px;">
      AI attention maps highlight spatial regions that most influenced construction activity and safety observations.
      Warmer colours (red/yellow) indicate high visual focus and detected site features.
    </p>
    {gradcam_section}
  </div>

  <!-- Recommendations -->
  <h2>AI-Generated Recommendations</h2>
  <div class="card">
    {recommendations}
  </div>

  <!-- Analysis Metadata -->
  <h2>Analysis Metadata</h2>
  <div class="card">
    <table>
      <thead><tr><th>Parameter</th><th>Value</th></tr></thead>
      <tbody>
        {meta_rows}
      </tbody>
    </table>
  </div>

  <div class="footer">
    <p>UAV Vision &mdash; AI-Powered Construction Monitoring & Progress Assessment</p>
    <p>Computer Vision &bull; Multi-Temporal Analysis &bull; Predictive Intelligence &bull; Explainable AI</p>
  </div>
</div>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _risk_badge(risk_level: str) -> str:
    return {"on_track": "green", "at_risk": "yellow",
            "delayed": "red", "critical": "red"}.get(risk_level, "yellow")


def _progress_color(score: float) -> str:
    if score >= 70: return "#22c55e"
    if score >= 40: return "#f59e0b"
    return "#ef4444"


def _delay_color(delay_days: int) -> str:
    if delay_days <= 0: return "#22c55e"
    if delay_days <= 10: return "#f59e0b"
    return "#ef4444"


def _img_tag(path: Optional[str], alt: str = "chart") -> str:
    if not path or not Path(path).exists():
        return f'<p style="color:#94a3b8;font-style:italic">Chart not available</p>'
    # Embed as base64 for portability
    import base64
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f'<img class="chart" src="data:image/png;base64,{b64}" alt="{alt}"/>'


def _feature_rows(features: Dict, shap_vals: Dict) -> str:
    weight_map = {"change_score": 0.40, "activity_score": 0.30,
                  "temporal_score": 0.20, "quality_score": 0.10}
    label_map  = {"change_score": "Change Detection", "activity_score": "Activity Detection",
                  "temporal_score": "Temporal Coverage", "quality_score": "Image Quality"}
    src_map    = {"change_score": "Change Analysis", "activity_score": "Activity Detection",
                  "temporal_score": "Temporal Alignment", "quality_score": "Image Quality Check"}
    rows = []
    for k, w in weight_map.items():
        v    = features.get(k, 50.0)
        cont = round(v * w, 2)
        bar  = f'<div class="progress-bar"><div class="progress-fill" style="width:{v}%;background:#3b82f6"></div></div>'
        rows.append(f"<tr><td>{label_map[k]}</td><td>{src_map[k]}</td>"
                    f"<td>{v:.1f}%{bar}</td><td>{int(w*100)}%</td><td>{cont:.1f}</td></tr>")
    return "\n".join(rows)


def _shap_rows(shap_vals: Dict, features: Dict) -> str:
    rows = []
    for k, sv in shap_vals.items():
        fv    = features.get(k, 50.0)
        color = "#22c55e" if sv >= 0 else "#ef4444"
        sign  = "↑ Positive" if sv >= 0 else "↓ Negative"
        rows.append(f"<tr><td>{k.replace('_',' ').title()}</td><td>{fv:.1f}%</td>"
                    f"<td style='color:{color};font-weight:600'>{sv:+.3f}</td>"
                    f"<td style='color:{color}'>{sign}</td></tr>")
    return "\n".join(rows)


def _gradcam_section(gradcam_results: List[Dict]) -> str:
    if not gradcam_results:
        return "<p style='color:#94a3b8;font-style:italic'>No attention map results available. Upload project images and run analysis.</p>"
    parts = []
    for r in gradcam_results[:4]:  # show max 4
        stem  = Path(r.get("image_path", "image")).stem
        stats = r.get("stats", {})
        parts.append(f"<h3>{stem}</h3>")
        parts.append(f"<p style='color:#94a3b8'>Max Focus Intensity: {stats.get('max_activation',0):.3f} | "
                     f"High-Focus Area: {stats.get('high_activation_pct',0):.1f}%</p>")
        parts.append(_img_tag(r.get("overlay_path"), f"AI Attention overlay — {stem}"))
    return "\n".join(parts)


def _recommendations(prediction: Dict, shap_vals: Dict) -> str:
    recs = []
    risk  = prediction.get("risk", {}).get("risk_level", "on_track")
    delay = prediction.get("delay", {}).get("delay_days", 0)
    score = prediction.get("progress", {}).get("progress_score", 50.0)

    if risk in ("delayed", "critical"):
        recs.append(("🔴", "Schedule is significantly behind. Immediately mobilise additional resources and revise work plan."))
    elif risk == "at_risk":
        recs.append(("🟡", "Project is at risk of delay. Review milestone completion and accelerate critical-path activities."))
    else:
        recs.append(("🟢", "Project is progressing on schedule. Maintain current resource allocation and monitor weekly."))

    if shap_vals.get("change_score", 0) < -5:
        recs.append(("📊", "Low change detection score indicates minimal construction activity. Verify site progress and worker deployment."))
    if shap_vals.get("activity_score", 0) < -3:
        recs.append(("👷", "Reduced activity density detected. Check PPE compliance and workforce availability."))
    if shap_vals.get("quality_score", 0) < -2:
        recs.append(("📸", "Image quality is affecting analysis accuracy. Recalibrate UAV sensors and re-capture imagery."))

    recs.append(("📋", f"Next recommended UAV survey: within {max(3, abs(delay) // 5 + 7)} days."))
    recs.append(("🔬", "Continue monitoring with weekly multi-temporal comparisons for reliable delay prediction."))

    return "\n".join(
        f'<div class="rec-item"><span class="rec-icon">{icon}</span><span>{text}</span></div>'
        for icon, text in recs
    )


def _meta_rows(prediction: Dict, shap: Dict, gradcam_count: int) -> str:
    delay = prediction.get("delay", {})
    prog  = prediction.get("progress", {})
    rows  = [
        ("Generated At",           datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
        ("Progress Score",         f"{prog.get('progress_score',0):.2f}%"),
        ("Delay Days",             f"{delay.get('delay_days',0):+d} days"),
        ("Risk Level",             delay.get("risk_level", "N/A")),
        ("Decision Analysis Mode", shap.get("mode", "Standard")),
        ("Attention Map Images",   gradcam_count),
        ("Explainability Engine",  "Multi-Factor Visual Attribution"),
        ("Prediction Engine",      "Multi-Stage Progress Predictor"),
        ("Change Analysis",        "Multi-Temporal Visual Differencing"),
        ("Activity Detection",     "Deep Learning Vision Detector"),
    ]
    return "\n".join(f"<tr><td style='color:#94a3b8'>{k}</td><td>{v}</td></tr>" for k, v in rows)


# ─────────────────────────────────────────────────────────────────────────────
# PDF Generation (fpdf2 preferred, reportlab fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _html_to_pdf(html_path: Path, pdf_path: Path) -> bool:
    """Convert HTML report to PDF using available library."""
    # Method 1: fpdf2
    try:
        from fpdf import FPDF, HTMLMixin
        class ReportPDF(FPDF, HTMLMixin):
            pass
        pdf = ReportPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        # Strip tags for fpdf (simplified)
        import re
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'&[a-z]+;', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        pdf.multi_cell(0, 6, text[:8000])
        pdf.output(str(pdf_path))
        return True
    except Exception:
        pass

    # Method 2: reportlab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        doc    = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story  = []

        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        import re
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'&[a-z]+;', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        for chunk in text[:6000].split(". "):
            story.append(Paragraph(chunk + ".", styles["Normal"]))
            story.append(Spacer(1, 4))

        doc.build(story)
        return True
    except Exception as exc:
        logger.warning("PDF generation unavailable: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_xai_pdf_report(
    project: Dict[str, Any],
    prediction: Dict[str, Any],
    shap_result: Dict[str, Any],
    gradcam_results: List[Dict[str, Any]],
    output_dir: Path,
    config: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Generate a comprehensive XAI report as HTML (+ PDF if available).

    Args:
        project:         Project metadata dict from Module 1 store.
        prediction:      Module 5 full prediction dict.
        shap_result:     Module 6 SHAP explanation dict.
        gradcam_results: List of Module 6 GradCAM result dicts.
        output_dir:      Directory to save report files.
        config:          Optional config overrides.

    Returns:
        Dict with html_path, pdf_path (if available), success flag.
    """
    cfg = config or {}
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result: Dict[str, Any] = {
        "success":      False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        project_name = project.get("name", "Unknown Project")
        risk_level   = prediction.get("risk", {}).get("risk_level", "on_track")
        progress_sc  = float(prediction.get("progress", {}).get("progress_score", 0))
        delay_d      = int(prediction.get("delay", {}).get("delay_days", 0))
        features     = shap_result.get("features", {})
        shap_vals    = shap_result.get("shap_values", {})

        # Build HTML
        html = _HTML_TEMPLATE.format(
            project_name    = project_name,
            generated_at    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            risk_badge      = _risk_badge(risk_level),
            risk_label      = risk_level.replace("_", " ").title(),
            progress_score  = progress_sc,
            progress_color  = _progress_color(progress_sc),
            delay_days      = delay_d,
            delay_color     = _delay_color(delay_d),
            feature_rows    = _feature_rows(features, shap_vals),
            shap_narrative  = f'<div class="narrative">{shap_result.get("narrative","")}</div>' if shap_result.get("narrative") else "",
            shap_bar_img    = _img_tag(shap_result.get("bar_chart_path"), "SHAP bar chart"),
            shap_wf_img     = _img_tag(shap_result.get("waterfall_path"), "SHAP waterfall"),
            shap_rows       = _shap_rows(shap_vals, features),
            gradcam_section = _gradcam_section(gradcam_results),
            recommendations = _recommendations(prediction, shap_vals),
            meta_rows       = _meta_rows(prediction, shap_result, len(gradcam_results)),
        )

        html_path = output_dir / "xai_report.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        # Attempt PDF
        pdf_path = output_dir / "xai_report.pdf"
        pdf_ok   = _html_to_pdf(html_path, pdf_path)

        # Save combined JSON summary
        summary_path = output_dir / "xai_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "project":         project_name,
                "progress_score":  progress_sc,
                "delay_days":      delay_d,
                "risk_level":      risk_level,
                "shap_values":     shap_vals,
                "feature_importance": shap_result.get("feature_importance", []),
                "narrative":       shap_result.get("narrative", ""),
                "gradcam_count":   len(gradcam_results),
                "generated_at":    result["generated_at"],
            }, f, indent=2, default=str)

        result.update({
            "success":      True,
            "html_path":    str(html_path),
            "pdf_path":     str(pdf_path) if pdf_ok else None,
            "pdf_available": pdf_ok,
            "summary_path": str(summary_path),
            "project_name": project_name,
        })

        logger.info("XAI report generated: %s (PDF=%s)", html_path.name, pdf_ok)

    except Exception as exc:
        logger.error("XAI report generation failed: %s", exc, exc_info=True)
        result["error"] = str(exc)

    return result
