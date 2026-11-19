"""
Decision Support Layer — Project Health, Explainability Queries,
Final Inspection Summaries and Dataset Evaluation Store.

This package connects the six existing AI modules into a unified
construction monitoring decision-support workflow:

    Inspection data -> Health Score -> XAI Queries -> Final Summary -> Report

All values are computed from actual stored module outputs.
No metrics are fabricated; unavailable inputs degrade gracefully with
explicit "not available" reasons.
"""

from backend.modules.decision_support.health_score import (
    compute_health_score,
    HEALTH_WEIGHTS,
    HEALTH_CLASSIFICATIONS,
)
from backend.modules.decision_support.xai_query import (
    answer_query,
    AVAILABLE_QUERIES,
    QUERY_LABELS,
)
from backend.modules.decision_support.final_summary import (
    build_final_summary,
)
from backend.modules.decision_support.evidence_report import (
    build_evidence_report,
)
from backend.modules.decision_support.evaluation_store import (
    load_change_detection_eval,
    load_detection_eval,
)

__all__ = [
    "compute_health_score",
    "HEALTH_WEIGHTS",
    "HEALTH_CLASSIFICATIONS",
    "answer_query",
    "AVAILABLE_QUERIES",
    "QUERY_LABELS",
    "build_final_summary",
    "build_evidence_report",
    "load_change_detection_eval",
    "load_detection_eval",
]

