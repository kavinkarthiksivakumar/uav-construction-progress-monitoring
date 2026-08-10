"""
Module 6 — SHAP Feature Importance Explainer
IEEE M.Tech Project — Explainable Vision-Based Construction Progress Assessment

Generates SHAP (SHapley Additive exPlanations) values to explain the
Module 5 progress prediction model's decisions.

Operating Modes:
  1. XGBoost SHAP Mode — when xgboost + shap libraries are installed,
     trains/loads an XGBoost model and computes exact SHAP TreeExplainer values.

  2. Simulation Mode — generates statistically valid SHAP-like attribution
     values derived from feature magnitudes when libraries are unavailable.

Explains the 4-feature input vector:
    [change_score, activity_score, temporal_score, quality_score]

Outputs:
  - SHAP bar chart PNG
  - SHAP waterfall PNG
  - Feature importance JSON
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("module6.shap_explain")

# ─────────────────────────────────────────────────────────────────────────────
# Feature definitions (must match Module 5 predictor)
# ─────────────────────────────────────────────────────────────────────────────

FEATURE_NAMES = ["change_score", "activity_score", "temporal_score", "quality_score"]
FEATURE_LABELS = {
    "change_score":    "Change Detection (M4)",
    "activity_score":  "Activity Density (M3)",
    "temporal_score":  "Temporal Coverage (M1)",
    "quality_score":   "Image Quality (M1)",
}
FEATURE_WEIGHTS = {
    "change_score":   0.40,
    "activity_score": 0.30,
    "temporal_score": 0.20,
    "quality_score":  0.10,
}

# ─────────────────────────────────────────────────────────────────────────────
# Simulation-mode attribution
# ─────────────────────────────────────────────────────────────────────────────

def _simulate_shap_values(features: Dict[str, float]) -> Dict[str, float]:
    """
    Compute simulated SHAP attributions proportional to weighted contribution.

    For a linear additive model (progress = Σ wᵢ × fᵢ), SHAP values are
    exactly wᵢ × (fᵢ − E[fᵢ]).  Assuming uniform expected value of 50:
        shap_i = w_i × (f_i − 50)
    """
    shap_vals = {}
    expected_base = 50.0  # baseline expected progress
    for fname in FEATURE_NAMES:
        fval = features.get(fname, 50.0)
        w    = FEATURE_WEIGHTS.get(fname, 0.25)
        shap_vals[fname] = round(w * (fval - expected_base), 4)
    return shap_vals


# ─────────────────────────────────────────────────────────────────────────────
# Chart generation (matplotlib)
# ─────────────────────────────────────────────────────────────────────────────

def _plot_shap_bar(
    shap_values: Dict[str, float],
    output_path: Path,
    title: str = "SHAP Feature Importance",
) -> bool:
    """Save a horizontal SHAP bar chart PNG."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        labels  = [FEATURE_LABELS.get(k, k) for k in FEATURE_NAMES]
        values  = [shap_values.get(k, 0.0)  for k in FEATURE_NAMES]
        colors  = ["#ef4444" if v < 0 else "#22c55e" for v in values]

        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.barh(labels, values, color=colors, edgecolor="white", linewidth=0.5)

        ax.axvline(x=0, color="gray", linewidth=0.8, linestyle="--")
        ax.set_xlabel("SHAP Value (impact on progress %)", fontsize=10)
        ax.set_title(title, fontsize=12, fontweight="bold", pad=10)

        # Value labels
        for bar, val in zip(bars, values):
            x_pos = val + (0.3 if val >= 0 else -0.3)
            ha    = "left" if val >= 0 else "right"
            ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
                    f"{val:+.2f}", va="center", ha=ha, fontsize=9)

        ax.set_facecolor("#1e293b")
        fig.patch.set_facecolor("#0f172a")
        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.title.set_color("white")
        ax.spines[:].set_color("#334155")

        plt.tight_layout()
        plt.savefig(str(output_path), dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        return True
    except Exception as exc:
        logger.warning("SHAP bar chart failed: %s", exc)
        return False


def _plot_shap_waterfall(
    shap_values: Dict[str, float],
    base_value: float,
    output_path: Path,
    title: str = "SHAP Waterfall",
) -> bool:
    """Save a waterfall SHAP chart PNG showing cumulative contribution."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        labels  = [FEATURE_LABELS.get(k, k) for k in FEATURE_NAMES]
        values  = [shap_values.get(k, 0.0)  for k in FEATURE_NAMES]

        cumulative = [base_value]
        for v in values:
            cumulative.append(cumulative[-1] + v)

        fig, ax = plt.subplots(figsize=(9, 5))

        for i, (label, val) in enumerate(zip(labels, values)):
            start = cumulative[i]
            color = "#22c55e" if val >= 0 else "#ef4444"
            ax.bar(i, abs(val), bottom=min(start, start + val),
                   color=color, width=0.5, edgecolor="white", linewidth=0.4)
            ax.text(i, cumulative[i + 1] + (0.5 if val >= 0 else -1),
                    f"{val:+.1f}", ha="center", va="bottom" if val >= 0 else "top",
                    fontsize=9, color="white")

        ax.axhline(y=base_value,   color="#94a3b8", linewidth=1, linestyle="--", label=f"Base: {base_value:.1f}%")
        ax.axhline(y=cumulative[-1], color="#f59e0b", linewidth=1.5, linestyle="-", label=f"Prediction: {cumulative[-1]:.1f}%")

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=9, rotation=12, ha="right")
        ax.set_ylabel("Progress Score (%)", fontsize=10)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.legend(fontsize=9, facecolor="#1e293b", labelcolor="white")

        ax.set_facecolor("#1e293b")
        fig.patch.set_facecolor("#0f172a")
        ax.tick_params(colors="white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        ax.spines[:].set_color("#334155")

        plt.tight_layout()
        plt.savefig(str(output_path), dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        return True
    except Exception as exc:
        logger.warning("SHAP waterfall chart failed: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# XGBoost-based SHAP (optional)
# ─────────────────────────────────────────────────────────────────────────────

def _xgboost_shap(
    features: Dict[str, float],
    historical_data: Optional[List[Dict]] = None,
) -> Optional[Dict[str, float]]:
    """
    Train an XGBoost model on historical project data (or synthetic data)
    and compute exact SHAP TreeExplainer values for the current sample.

    Returns None if xgboost or shap is unavailable.
    """
    try:
        import xgboost as xgb
        import shap

        # Build training set from historical data or synthetic samples
        if historical_data and len(historical_data) >= 5:
            X_train = np.array([[
                d.get("change_score",   50.0),
                d.get("activity_score", 50.0),
                d.get("temporal_score", 50.0),
                d.get("quality_score",  50.0),
            ] for d in historical_data])
            y_train = np.array([d.get("progress_score", 50.0) for d in historical_data])
        else:
            # Synthetic training data derived from known weighted formula
            rng = np.random.default_rng(2024)
            n   = 200
            X_train = rng.uniform(0, 100, size=(n, 4)).astype(np.float32)
            y_train = (
                0.40 * X_train[:, 0] +
                0.30 * X_train[:, 1] +
                0.20 * X_train[:, 2] +
                0.10 * X_train[:, 3] +
                rng.normal(0, 2, n)
            ).clip(0, 100)

        model = xgb.XGBRegressor(
            n_estimators=100, max_depth=4, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8, random_state=42,
            verbosity=0,
        )
        model.fit(X_train, y_train)

        X_sample = np.array([[
            features.get(k, 50.0) for k in FEATURE_NAMES
        ]], dtype=np.float32)

        explainer   = shap.TreeExplainer(model)
        shap_matrix = explainer.shap_values(X_sample)  # shape [1, 4]
        shap_row    = shap_matrix[0]

        return {name: round(float(val), 4) for name, val in zip(FEATURE_NAMES, shap_row)}

    except Exception as exc:
        logger.warning("XGBoost SHAP unavailable (%s) — using simulation", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_shap_explanation(
    prediction: Dict[str, Any],
    output_dir: Path,
    historical_data: Optional[List[Dict]] = None,
    config: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Generate SHAP feature importance explanation for a Module 5 prediction.

    Args:
        prediction:      Module 5 prediction dict (from run_full_prediction).
        output_dir:      Directory to save charts and JSON.
        historical_data: Optional list of past prediction dicts for XGBoost training.
        config:          Optional config overrides.

    Returns:
        SHAP explanation dict with feature_importance, charts, and narrative.
    """
    cfg = config or {}
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result: Dict[str, Any] = {
        "method":       "SHAP",
        "success":      False,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    try:
        # ── Extract feature scores from prediction ─────────────────────────
        sub = prediction.get("sub_scores", {})
        features = {
            "change_score":   sub.get("change_score",   prediction.get("change_score",   50.0)),
            "activity_score": sub.get("activity_score", prediction.get("activity_score", 50.0)),
            "temporal_score": sub.get("temporal_score", prediction.get("temporal_score", 50.0)),
            "quality_score":  sub.get("quality_score",  prediction.get("quality_score",  50.0)),
        }
        progress_score = prediction.get("progress", {}).get("progress_score", 50.0)
        base_value     = 50.0  # expected value of progress

        logger.info("SHAP: features=%s", features)

        # ── Compute SHAP values ────────────────────────────────────────────
        shap_vals = _xgboost_shap(features, historical_data)
        mode = "xgboost"
        if shap_vals is None:
            shap_vals = _simulate_shap_values(features)
            mode = "simulation"

        result["mode"] = mode

        # ── Feature importance ranking ─────────────────────────────────────
        importance = sorted(
            [{"feature": k, "label": FEATURE_LABELS.get(k, k),
              "shap_value": v, "feature_value": features.get(k, 50.0),
              "abs_importance": abs(v)}
             for k, v in shap_vals.items()],
            key=lambda x: x["abs_importance"], reverse=True,
        )

        # ── Generate charts ────────────────────────────────────────────────
        bar_path = output_dir / "shap_bar.png"
        wf_path  = output_dir / "shap_waterfall.png"
        bar_ok = _plot_shap_bar(shap_vals, bar_path, title="SHAP Feature Importance — Progress Score")
        wf_ok  = _plot_shap_waterfall(shap_vals, base_value, wf_path,
                                       title="SHAP Waterfall — Progress Contribution")

        # ── Natural language explanation ───────────────────────────────────
        top_pos = [f for f in importance if f["shap_value"] > 0]
        top_neg = [f for f in importance if f["shap_value"] < 0]

        narratives = []
        if top_pos:
            top = top_pos[0]
            narratives.append(
                f"The strongest positive driver is **{top['label']}** "
                f"(SHAP: +{top['shap_value']:.2f}), reflecting high activity level."
            )
        if top_neg:
            top = top_neg[0]
            narratives.append(
                f"The most significant constraint is **{top['label']}** "
                f"(SHAP: {top['shap_value']:.2f}), which is pulling the prediction lower."
            )
        if not top_pos and not top_neg:
            narratives.append("All features are at baseline — the prediction aligns with the expected schedule.")

        # ── Save JSON ──────────────────────────────────────────────────────
        shap_json_path = output_dir / "shap_explanation.json"
        explanation_data = {
            "features":         features,
            "shap_values":      shap_vals,
            "base_value":       base_value,
            "predicted_value":  progress_score,
            "feature_importance": importance,
            "narrative":        " ".join(narratives),
            "mode":             mode,
            "generated_at":     result["generated_at"],
        }
        with open(shap_json_path, "w", encoding="utf-8") as f:
            json.dump(explanation_data, f, indent=2, default=str)

        result.update({
            "success":            True,
            "features":           features,
            "shap_values":        shap_vals,
            "base_value":         base_value,
            "predicted_value":    progress_score,
            "feature_importance": importance,
            "narrative":          " ".join(narratives),
            "bar_chart_path":     str(bar_path)  if bar_ok  else None,
            "waterfall_path":     str(wf_path)   if wf_ok   else None,
            "json_path":          str(shap_json_path),
        })

        logger.info("SHAP explanation complete (mode=%s)", mode)

    except Exception as exc:
        logger.error("SHAP explanation failed: %s", exc, exc_info=True)
        result["error"] = str(exc)

    return result
