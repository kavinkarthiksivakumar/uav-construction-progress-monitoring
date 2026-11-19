"""
Module 5 Automated Tests
Final Year Project: Delay Prediction & Progress Assessment

Tests:
  1. Composite progress score computation (weighted)
  2. Delay prediction calculation
  3. Risk level classification (on track, at risk, delayed, critical)
  4. Planned vs Actual S-curve generation
  5. Project milestone assessment
  6. Comprehensive progress report generation
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta, timezone

# ── Path setup ─────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────
# Test Helpers
# ─────────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

passed_tests = []
failed_tests = []

def test(name: str):
    """Decorator to register and run a test."""
    def decorator(fn):
        try:
            fn()
            print(f"  {GREEN}✓{RESET} {name}")
            passed_tests.append(name)
        except AssertionError as e:
            print(f"  {RED}✗{RESET} {name}: {e}")
            failed_tests.append((name, str(e)))
        except Exception as e:
            print(f"  {RED}✗{RESET} {name}: [Exception] {e}")
            failed_tests.append((name, f"Exception: {e}"))
        return fn
    return decorator


# Create temp working directory for tests
_tmp_dir = Path(tempfile.mkdtemp())
_out_dir = _tmp_dir / "processed_m5"
_out_dir.mkdir(parents=True, exist_ok=True)

# Imports
from backend.modules.module5_prediction.predictor import (
    compute_progress_score,
    predict_delay,
    classify_risk_level,
    run_full_prediction,
)
from backend.modules.module5_prediction.s_curve import (
    build_s_curve_data,
    get_schedule_milestones,
)
from backend.modules.module5_prediction.report import (
    generate_progress_report,
)

# Dummy project details
dummy_project = {
    "project_id": "proj_123",
    "name": "Site Overpass construction",
    "location": "Vandalur, Chennai",
    "created_at": (datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),
    "images": [
        {"image_id": "img1", "filename": "day1.png", "accepted": True, "quality": {"overall_score": 80}},
        {"image_id": "img2", "filename": "day10.png", "accepted": True, "quality": {"overall_score": 85}},
        {"image_id": "img3", "filename": "day30.png", "accepted": True, "quality": {"overall_score": 75}},
        {"image_id": "img4", "filename": "day60.png", "accepted": True, "quality": {"overall_score": 90}},
    ]
}

dummy_detection = {
    "total_detections": 12,
    "image_count": 4,
    "aggregate_counts": {"helmet": 6, "vest": 4, "person": 6, "no-helmet": 0, "no-vest": 0},
    "avg_compliance": 100.0
}

dummy_change = {
    "results": [
        {"pair_id": "img1__img2", "success": True, "change_percent": 15.0, "num_regions": 3},
        {"pair_id": "img2__img3", "success": True, "change_percent": 25.0, "num_regions": 6},
        {"pair_id": "img3__img4", "success": True, "change_percent": 10.0, "num_regions": 2},
    ],
    "succeeded": 3,
    "avg_change": 16.67,
    "max_change": 25.0,
    "min_change": 10.0
}

# ─────────────────────────────────────────────────────────────────
# SECTION 1: Progress Score and Delay Calculation
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 1: Weighted Score & Delay Calculation{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

@test("compute_progress_score calculates a score within [0, 100] based on weights")
def _():
    weights = {"change": 0.40, "activity": 0.30, "temporal": 0.20, "quality": 0.10}
    res = compute_progress_score(
        project_data=dummy_project,
        detection_results=dummy_detection,
        change_results=dummy_change,
        weights=weights
    )
    assert 0.0 <= res["progress_score"] <= 100.0
    assert "sub_scores" in res
    assert "change" in res["sub_scores"]
    assert "activity" in res["sub_scores"]

@test("predict_delay predicts ahead/behind schedule in days correctly")
def _():
    # Progress = 30%, elapsed = 100 days, planned = 300 days
    # Expected progress = 100/300 * 100 = 33.33%
    # Actual progress = 30% -> Behind schedule
    res = predict_delay(
        progress_score=30.0,
        elapsed_days=100,
        planned_duration_days=300,
        planned_start_date=None
    )
    assert res["delay_days"] > 0, f"Expected delay_days > 0, got {res['delay_days']}"
    assert abs(res["expected_progress"] - 33.33) < 0.1
    assert res["ahead_of_schedule"] is False

@test("classify_risk_level maps delay to on_track, at_risk, delayed, critical")
def _():
    thresholds = {"at_risk": 10, "delayed": 20, "critical": 35}
    # Ahead of schedule (negative delay) -> on_track
    assert classify_risk_level(-5, 50.0, thresholds)["risk_level"] == "on_track"
    # Delay = 15 -> at_risk
    assert classify_risk_level(15, 50.0, thresholds)["risk_level"] == "at_risk"
    # Delay = 25 -> delayed
    assert classify_risk_level(25, 50.0, thresholds)["risk_level"] == "delayed"
    # Delay = 40 -> critical
    assert classify_risk_level(40, 50.0, thresholds)["risk_level"] == "critical"

# ─────────────────────────────────────────────────────────────────
# SECTION 2: S-Curve & Milestones
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 2: S-Curve & Project Milestones{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

@test("build_s_curve_data builds planned S-curve points and actual progress")
def _():
    scurve = build_s_curve_data(
        temporal_images=dummy_project["images"],
        change_results=dummy_change,
        planned_duration=365,
        planned_start=(datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    )
    assert scurve["n_points"] > 0
    assert "points" in scurve
    first = scurve["points"][0]
    last  = scurve["points"][-1]
    assert first["planned"] == 0.0
    assert last["planned"] == 100.0

@test("get_schedule_milestones evaluates status of milestones based on progress")
def _():
    # Progress = 50%
    # Milestones: Foundation (15%) -> completed, Structural Frame (35%) -> completed, Building Envelope (55%) -> upcoming/in_progress
    milestones = get_schedule_milestones(
        planned_start=(datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),
        planned_duration=180,
        current_progress=50.0
    )
    foundation = next(m for m in milestones if m["name"] == "Foundation Complete")
    assert foundation["status"] == "completed"
    envelope = next(m for m in milestones if m["name"] == "Building Envelope")
    assert envelope["status"] in ("in_progress", "upcoming")

# ─────────────────────────────────────────────────────────────────
# SECTION 3: Progress Report
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 3: Progress Report Generation{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

@test("generate_progress_report compiles full Module 5 data to report JSON")
def _():
    full_pred = run_full_prediction(
        project_data=dummy_project,
        detection_results=dummy_detection,
        change_results=dummy_change,
        planned_duration_days=180,
        planned_start_date=dummy_project["created_at"]
    )
    
    report_path = _out_dir / "progress_report.json"
    report = generate_progress_report(
        project_data=dummy_project,
        prediction=full_pred,
        output_path=report_path
    )
    
    assert report_path.exists()
    assert report["project"]["project_id"] == "proj_123"
    assert "schedule_analysis" in report
    assert "risk_assessment" in report
    assert report["progress_assessment"]["overall_score"] == full_pred["progress"]["progress_score"]

# ─────────────────────────────────────────────────────────────────
# Cleanup
# ─────────────────────────────────────────────────────────────────
try:
    shutil.rmtree(_tmp_dir, ignore_errors=True)
except Exception:
    pass

# ─────────────────────────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────────────────────────
total   = len(passed_tests) + len(failed_tests)
passed  = len(passed_tests)
failed  = len(failed_tests)
rate    = int(passed / total * 100) if total else 0

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"  MODULE 5 TEST REPORT")
print(f"{BOLD}{'='*55}{RESET}")
print(f"  Total:   {total}")
print(f"  {GREEN}Passed:  {passed}{RESET}")
if failed:
    print(f"  {RED}Failed:  {failed}{RESET}")
    for name, reason in failed_tests:
        print(f"    {RED}✗{RESET} {name}: {reason}")
print(f"  Score:   {rate}%")
print(f"{BOLD}{'='*55}{RESET}\n")

# Save report
report = {
    "module":      "Module 5: Delay Prediction & Progress Assessment",
    "timestamp":   datetime.now(timezone.utc).isoformat(),
    "total":       total,
    "passed":      passed,
    "failed":      failed,
    "pass_rate":   rate,
    "failed_tests": [{"name": n, "reason": r} for n, r in failed_tests],
}

report_dir = PROJECT_ROOT / "reports"
report_dir.mkdir(exist_ok=True)
with open(report_dir / "module5_test_report.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"  Report saved to: reports/module5_test_report.json")
sys.exit(0 if failed == 0 else 1)
