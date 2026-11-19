"""
Module 4 Automated Tests
Final Year Project: Construction Change Detection

Tests:
  1. Change severity classification
  2. Intersection-over-Union (IoU) calculation with ground truth
  3. Batch change metrics aggregation
  4. Change report generation
  5. Bi-temporal pair change detection (pixel difference-based)
  6. Connected component analysis and bounding box detection for change areas
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

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


def make_test_mask(width: int = 100, height: int = 100, fill_box: tuple = None) -> np.ndarray:
    """Create a dummy binary mask image (uint8, grayscale)."""
    mask = np.zeros((height, width), dtype=np.uint8)
    if fill_box:
        x1, y1, x2, y2 = fill_box
        mask[y1:y2, x1:x2] = 255
    return mask


# Create temp working directory for tests
_tmp_dir = Path(tempfile.mkdtemp())
_out_dir = _tmp_dir / "processed_m4"
_out_dir.mkdir(parents=True, exist_ok=True)

# Imports
from backend.modules.module4_change.metrics import (
    classify_severity,
    compute_iou,
    aggregate_batch_metrics,
    generate_change_report,
)
from backend.modules.module4_change.change_detector import (
    detect_change_pair,
    detect_levir_batch,
)

# ─────────────────────────────────────────────────────────────────
# SECTION 1: Metrics & Calculations
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 1: Change Severity & Ground-Truth IoU{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

@test("classify_severity categorizes change percents correctly")
def _():
    assert classify_severity(2.0)  == "low"
    assert classify_severity(12.5) == "moderate"
    assert classify_severity(35.0) == "high"
    assert classify_severity(60.0) == "critical"

@test("compute_iou calculates IoU, Precision, Recall, and F1 between two masks")
def _():
    import cv2
    mask_a_path = _tmp_dir / "mask_a.png"
    mask_b_path = _tmp_dir / "mask_b.png"
    
    # Mask A has a 20x20 box in the center
    # Mask B has an overlapping 20x20 box shifted by 10 pixels
    mask_a = make_test_mask(100, 100, fill_box=(40, 40, 60, 60))
    mask_b = make_test_mask(100, 100, fill_box=(50, 40, 70, 60))
    
    cv2.imwrite(str(mask_a_path), mask_a)
    cv2.imwrite(str(mask_b_path), mask_b)
    
    metrics = compute_iou(mask_a_path, mask_b_path)
    assert metrics is not None
    # Intersection = 10x20 = 200 pixels
    # Union = 400 + 400 - 200 = 600 pixels
    # IoU = 200 / 600 = 0.3333
    assert abs(metrics["iou"] - 0.3333) < 0.05
    assert abs(metrics["precision"] - 0.5) < 0.05
    assert abs(metrics["recall"] - 0.5) < 0.05

@test("aggregate_batch_metrics computes mean change and severity counts")
def _():
    batch = [
        {"success": True,  "change_percent": 4.0,   "num_regions": 2},
        {"success": True,  "change_percent": 18.0,  "num_regions": 5},
        {"success": False, "change_percent": 0.0,   "num_regions": 0},
    ]
    agg = aggregate_batch_metrics(batch)
    assert agg["total"] == 3
    assert agg["succeeded"] == 2
    assert agg["avg_change"] == 11.0
    assert agg["total_regions"] == 7
    assert agg["severity_counts"]["low"] == 1
    assert agg["severity_counts"]["moderate"] == 1
    assert agg["dominant_severity"] == "low" or agg["dominant_severity"] == "moderate"

# ─────────────────────────────────────────────────────────────────
# SECTION 2: Change Detector Runs
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 2: Change Detection Pair Processing{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

@test("detect_change_pair detects modified regions between Time-1 and Time-2")
def _():
    import cv2
    img_a_path = _tmp_dir / "time1.png"
    img_b_path = _tmp_dir / "time2.png"
    
    # Image A is solid gray
    # Image B has a solid white block in the center
    img_a = np.ones((100, 100, 3), dtype=np.uint8) * 128
    img_b = img_a.copy()
    img_b[30:70, 30:70] = 255
    
    cv2.imwrite(str(img_a_path), img_a)
    cv2.imwrite(str(img_b_path), img_b)
    
    res = detect_change_pair(
        image_a=img_a_path,
        image_b=img_b_path,
        output_dir=_out_dir / "pair_chg",
        config={
            "target_size": (100, 100),
            "threshold_method": "fixed",
            "fixed_threshold": 30,
            "min_change_area": 50,
        }
    )
    
    assert res["success"] is True
    assert res["change_percent"] > 0.0
    assert res["num_regions"] == 1
    assert Path(res["mask_path"]).exists()
    assert Path(res["overlay_path"]).exists()

# ─────────────────────────────────────────────────────────────────
# SECTION 3: Report Verification
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 3: Change Report Generation{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

@test("generate_change_report creates a formatted report JSON file")
def _():
    batch = {
        "results": [
            {"pair_id": "pair1", "success": True, "change_percent": 15.0, "num_regions": 3, "mode": "otsu"},
            {"pair_id": "pair2", "success": True, "change_percent": 30.0, "num_regions": 8, "mode": "otsu"},
        ]
    }
    rpt_path = _out_dir / "change_report_output.json"
    generate_change_report(batch, rpt_path)
    
    assert rpt_path.exists()
    with open(rpt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["module"].startswith("Module 4")
    assert "summary" in data
    assert data["summary"]["total"] == 2
    assert len(data["pair_results"]) == 2

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
print(f"  MODULE 4 TEST REPORT")
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
    "module":      "Module 4: Construction Change Detection",
    "timestamp":   datetime.now(timezone.utc).isoformat(),
    "total":       total,
    "passed":      passed,
    "failed":      failed,
    "pass_rate":   rate,
    "failed_tests": [{"name": n, "reason": r} for n, r in failed_tests],
}

report_dir = PROJECT_ROOT / "reports"
report_dir.mkdir(exist_ok=True)
with open(report_dir / "module4_test_report.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"  Report saved to: reports/module4_test_report.json")
sys.exit(0 if failed == 0 else 1)
