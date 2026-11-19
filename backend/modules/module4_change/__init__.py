"""
Module 4: Construction Change Detection — Package Init
Final Year Project
"""

from backend.modules.module4_change.change_detector import (
    detect_change_pair,
    detect_levir_batch,
    detect_levir_split,
)
from backend.modules.module4_change.metrics import (
    classify_severity,
    compute_iou,
    aggregate_batch_metrics,
    generate_change_report,
    SEVERITY_THRESHOLDS,
    SEVERITY_COLORS,
)

__all__ = [
    "detect_change_pair",
    "detect_levir_batch",
    "detect_levir_split",
    "classify_severity",
    "compute_iou",
    "aggregate_batch_metrics",
    "generate_change_report",
    "SEVERITY_THRESHOLDS",
    "SEVERITY_COLORS",
]
