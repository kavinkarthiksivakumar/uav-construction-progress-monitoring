"""
Backend utility packages.
"""
from backend.utils.score_utils import (
    normalize_percentage,
    normalize_probability,
    validate_metric_range,
    calculate_progress_score,
    calculate_ai_confidence,
    calculate_risk_score,
    format_schedule_variance,
    classify_schedule_status,
)
from backend.utils.formal_report import generate_formal_inspection_html
