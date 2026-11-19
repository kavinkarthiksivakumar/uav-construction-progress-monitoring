"""
Unit Tests: Centralized Score Normalization & Metrics Utilities
Tests out-of-bounds inputs, percentage scaling, confidence aggregation, and schedule variance formatting.
"""

import sys
from pathlib import Path
import pytest

# Ensure backend root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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


class TestNormalizePercentage:
    """Verifies that all values normalize strictly into [0.0, 100.0]."""

    def test_probability_ratio_to_percentage(self):
        # 0.84 probability -> 84.0%
        assert normalize_percentage(0.84) == 84.0
        assert normalize_percentage(0.05) == 5.0
        assert normalize_percentage(1.0) == 100.0

    def test_existing_percentage_preserved(self):
        # 84.0% remains 84.0% (not multiplied again to 8400)
        assert normalize_percentage(84.0) == 84.0
        assert normalize_percentage(39.55) == 39.55
        assert normalize_percentage(100.0) == 100.0

    def test_out_of_bounds_inputs_clamped(self):
        # 3955 -> 100
        assert normalize_percentage(3955) == 100.0
        # 3020 -> 100
        assert normalize_percentage(3020) == 100.0
        # -20 -> 0
        assert normalize_percentage(-20) == 0.0
        # 1.25 -> 100 (when > 1.0 it's treated as percentage, or clamped if max is 100)
        assert normalize_percentage(1.25) == 1.25

    def test_none_and_invalid_inputs(self):
        assert normalize_percentage(None, default=0.0) == 0.0
        assert normalize_percentage("invalid", default=50.0) == 50.0
        assert normalize_percentage(float("nan"), default=0.0) == 0.0


class TestNormalizeProbability:
    """Verifies that all values normalize strictly into [0.0, 1.0]."""

    def test_probability_preserved(self):
        assert normalize_probability(0.84) == 0.84
        assert normalize_probability(0.0) == 0.0
        assert normalize_probability(1.0) == 1.0

    def test_percentage_to_probability(self):
        assert normalize_probability(84.0) == 0.84
        assert normalize_probability(39.55) == 0.3955

    def test_out_of_bounds_clamped(self):
        assert normalize_probability(3020) == 1.0
        assert normalize_probability(-5) == 0.0


class TestCalculateProgressScore:
    """Verifies composite progress calculation."""

    def test_progress_score_composite_range(self):
        sub_scores = {
            "change": 45.0,
            "activity": 80.0,
            "temporal": 60.0,
            "quality": 90.0,
        }
        res = calculate_progress_score(sub_scores)
        assert 0.0 <= res["progress_score"] <= 100.0
        assert "sub_scores" in res
        assert "weights_used" in res
        assert "breakdown" in res

    def test_progress_score_with_probabilities(self):
        # Passing 0-1 values should automatically scale without overflow
        sub_scores = {
            "change": 0.45,
            "activity": 0.80,
            "temporal": 0.60,
            "quality": 0.90,
        }
        res = calculate_progress_score(sub_scores)
        assert 0.0 <= res["progress_score"] <= 100.0
        assert abs(res["progress_score"] - (0.4*45 + 0.3*80 + 0.2*60 + 0.1*90)) < 0.1


class TestCalculateAIConfidence:
    """Verifies that multi-factor confidence never exceeds 100%."""

    def test_confidence_under_100(self):
        comps = {
            "detection": 85.0,
            "change": 90.0,
            "temporal": 70.0,
            "quality": 95.0,
        }
        conf = calculate_ai_confidence(comps)
        assert 0.0 <= conf <= 100.0

    def test_confidence_with_probabilities(self):
        comps = {
            "detection": 0.85,
            "change": 0.90,
            "temporal": 0.70,
            "quality": 0.95,
        }
        conf = calculate_ai_confidence(comps)
        assert 0.0 <= conf <= 100.0
        assert conf > 80.0


class TestScheduleVarianceFormatting:
    """Verifies human-friendly non-technical schedule variance strings."""

    def test_ahead_of_schedule(self):
        assert format_schedule_variance(delay_days=-143) == "143 days ahead of schedule"
        assert format_schedule_variance(delay_days=-1) == "1 day ahead of schedule"

    def test_behind_schedule(self):
        assert format_schedule_variance(delay_days=14) == "14 days behind schedule"
        assert format_schedule_variance(delay_days=1) == "1 day behind schedule"

    def test_on_schedule(self):
        assert format_schedule_variance(delay_days=0) == "On schedule"

    def test_variance_pct_formatting(self):
        assert format_schedule_variance(variance_pct=15.2) == "15.2 pts ahead of schedule"
        assert format_schedule_variance(variance_pct=-25.4) == "25.4 pts behind schedule"
        assert format_schedule_variance(variance_pct=0.0) == "On schedule"


class TestClassifyScheduleStatus:
    """Verifies schedule status thresholds."""

    def test_ahead_of_schedule(self):
        assert classify_schedule_status(12.5) == "Ahead of Schedule"

    def test_on_track(self):
        assert classify_schedule_status(5.0) == "On Track"
        assert classify_schedule_status(-8.0) == "On Track"

    def test_at_risk(self):
        assert classify_schedule_status(-15.0) == "At Risk"

    def test_delayed(self):
        assert classify_schedule_status(-30.0) == "Delayed"
