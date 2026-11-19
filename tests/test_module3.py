"""
Module 3 Automated Tests
Final Year Project: Construction Activity Detection

Tests:
  1. YOLO label parsing
  2. Image/annotation association
  3. Image detection (simulation mode)
  4. Batch detection (simulation mode)
  5. Dataset split analysis (simulation mode)
  6. Compliance metrics calculation
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


def make_dummy_yolo_label(path: Path):
    """
    Create a dummy YOLO label file with:
    0: helmet (class 0)
    3: person (class 3)
    2: no-vest (class 2)
    """
    lines = [
        "0 0.25 0.25 0.1 0.1\n",   # helmet
        "3 0.25 0.35 0.1 0.3\n",   # person
        "2 0.75 0.75 0.12 0.22\n", # no-vest
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


# Create temp working directory for tests
_tmp_dir = Path(tempfile.mkdtemp())
_out_dir = _tmp_dir / "processed_m3"
_out_dir.mkdir(parents=True, exist_ok=True)

# Imports
from backend.modules.module3_detection.annotation_parser import (
    parse_yolo_label,
    find_label_for_image,
)
from backend.modules.module3_detection.detector import (
    detect_image,
    detect_batch,
)

# ─────────────────────────────────────────────────────────────────
# SECTION 1: YOLO Parsing and Association
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 1: YOLO Label Parsing & Association{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

@test("parse_yolo_label extracts class IDs, name, and denormalized bounding box")
def _():
    lbl_path = _tmp_dir / "dummy_lbl.txt"
    make_dummy_yolo_label(lbl_path)
    
    # Let's say image size is 640x480
    detections = parse_yolo_label(lbl_path, img_w=640, img_h=480)
    assert len(detections) == 3, f"Expected 3 detections, got {len(detections)}"
    
    # Check helmet detection (class 0 in Roboflow scheme = "Hardhat")
    helmet = next(d for d in detections if d["class_id"] == 0)
    assert helmet["class_name"] == "Hardhat"
    assert "bbox" in helmet
    # Center x=0.25, width=0.10 -> xmin = 0.25 - 0.05 = 0.20 -> 0.20 * 640 = 128
    assert abs(helmet["bbox"][0] - 128) < 2
    assert helmet["bbox_norm"] == [0.25, 0.25, 0.1, 0.1]

@test("find_label_for_image locates corresponding YOLO label in dataset")
def _():
    # Set up dummy Roboflow dataset directories
    rf_root = _tmp_dir / "roboflow"
    img_dir = rf_root / "train" / "images"
    lbl_dir = rf_root / "train" / "labels"
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)
    
    img_file = img_dir / "site_frame_01.jpg"
    lbl_file = lbl_dir / "site_frame_01.txt"
    
    with open(img_file, "w") as f: f.write("img")
    with open(lbl_file, "w") as f: f.write("0 0.5 0.5 0.1 0.1")
    
    found = find_label_for_image(img_file, rf_root)
    assert found == lbl_file, f"Expected {lbl_file}, got {found}"

# ─────────────────────────────────────────────────────────────────
# SECTION 2: Image Activity Detection
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 2: Detection Pipeline (Simulation Mode){RESET}")
print(f"{BOLD}{'='*55}{RESET}")

@test("detect_image loads label file and computes compliance metrics")
def _():
    import cv2
    img_file = _tmp_dir / "test_frame.png"
    # Write a valid PNG image so cv2 can read it
    img_data = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.imwrite(str(img_file), img_data)
    
    # Write matching label file next to the image to simulate YOLO file discovery
    # Note: detector simulation mode can look up next to image, or in dataset
    lbl_file = img_file.with_suffix(".txt")
    make_dummy_yolo_label(lbl_file)
    
    result = detect_image(
        image_path=img_file,
        output_dir=_out_dir / "detect_single",
        config={"classes": ["helmet", "no-helmet", "no-vest", "person", "vest"]}
    )
    
    assert result["success"] is True
    assert result["mode"] == "simulation"
    assert result["total_objects"] == 3
    # Check compliance rate
    # Workers: 1 person, 1 helmet (compliant), 1 no-vest (non-compliant) -> 50% compliant
    comp = result["compliance"]
    assert comp["worker_count"] == 1
    assert comp["helmet_count"] == 1
    assert comp["vest_count"] == 0
    assert comp["compliance_rate"] == 0.0  # since no-vest is worn but no vest is active
    assert comp["site_compliant"] is False

@test("detect_batch runs batch compliance evaluation on multiple images")
def _():
    import cv2
    img_a = _tmp_dir / "batch_frame_a.png"
    img_b = _tmp_dir / "batch_frame_b.png"
    
    cv2.imwrite(str(img_a), np.zeros((480, 640, 3), dtype=np.uint8))
    cv2.imwrite(str(img_b), np.zeros((480, 640, 3), dtype=np.uint8))
    
    # Label for A (1 Hardhat, 1 Mask, 1 Safety Vest, 1 Person) -> Fully compliant
    # Roboflow class IDs: 0=Hardhat 1=Mask 2=NO-Hardhat 3=NO-Mask
    #                     4=NO-Safety Vest 5=Person 7=Safety Vest
    with open(img_a.with_suffix(".txt"), "w") as f:
        f.write("0 0.2 0.2 0.1 0.1\n") # Hardhat (safe)
        f.write("1 0.3 0.3 0.1 0.1\n") # Mask (safe)
        f.write("7 0.4 0.4 0.1 0.1\n") # Safety Vest (safe)
        f.write("5 0.2 0.5 0.1 0.1\n") # Person

    # Label for B (1 NO-Hardhat, 1 NO-Safety Vest, 1 Person) -> Non-compliant
    with open(img_b.with_suffix(".txt"), "w") as f:
        f.write("2 0.2 0.2 0.1 0.1\n") # NO-Hardhat
        f.write("4 0.2 0.5 0.1 0.1\n") # NO-Safety Vest
        f.write("5 0.2 0.7 0.1 0.1\n") # Person

    batch_res = detect_batch(
        images=[img_a, img_b],
        output_dir=_out_dir / "batch_out",
        config={"compliance_threshold": 0.5}
    )

    assert batch_res["total"] == 2
    assert batch_res["succeeded"] == 2
    assert batch_res["total_detections"] == 7
    assert batch_res["avg_compliance"] == 50.0  # (100% + 0%) / 2

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
print(f"  MODULE 3 TEST REPORT")
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
    "module":      "Module 3: Construction Activity Detection",
    "timestamp":   datetime.now(timezone.utc).isoformat(),
    "total":       total,
    "passed":      passed,
    "failed":      failed,
    "pass_rate":   rate,
    "failed_tests": [{"name": n, "reason": r} for n, r in failed_tests],
}

report_dir = PROJECT_ROOT / "reports"
report_dir.mkdir(exist_ok=True)
with open(report_dir / "module3_test_report.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"  Report saved to: reports/module3_test_report.json")
sys.exit(0 if failed == 0 else 1)
