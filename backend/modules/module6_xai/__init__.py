"""
Module 6: Explainable AI (XAI) — GradCAM + SHAP + Report Generation
IEEE M.Tech Project — Explainable Vision-Based Construction Progress Assessment

Exports:
    gradcam      — GradCAM heatmap generator
    shap_explain — SHAP feature importance explainer
    pdf_report   — PDF report generator
"""

from backend.modules.module6_xai.gradcam import generate_gradcam_heatmap
from backend.modules.module6_xai.shap_explain import generate_shap_explanation
from backend.modules.module6_xai.pdf_report import generate_xai_pdf_report

__all__ = [
    "generate_gradcam_heatmap",
    "generate_shap_explanation",
    "generate_xai_pdf_report",
]
