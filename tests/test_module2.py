"""
Module 2 Automated Tests
Final Year Project: Image Processing

Tests:
  1. Image resizing
  2. Color space conversions
  3. Edge detection (Canny & Sobel)
  4. LBP Texture extraction
  5. Gabor filter feature extraction
  6. Morphological filtering
  7. Single-image preprocessing pipeline
  8. Bi-temporal pair preprocessing pipeline
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


def make_dummy_bgr_image(w=100, h=100) -> np.ndarray:
    """Create a dummy BGR image array (uint8)."""
    # Create simple pattern (e.g. half black, half white) with a center square
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:h//2, :] = [255, 120, 50]  # Light blue-ish
    img[h//2:, :] = [50, 120, 255]  # Orange-ish
    img[h//4:3*h//4, w//4:3*w//4] = [255, 255, 255] # White center square
    return img


# Create temp working directory for tests
_tmp_dir = Path(tempfile.mkdtemp())
_out_dir = _tmp_dir / "processed_m2"
_out_dir.mkdir(parents=True, exist_ok=True)

# Import module functions
from backend.modules.module2_processing.processor import (
    resize_image,
    extract_color_spaces,
    detect_edges,
    extract_lbp,
    extract_gabor,
    apply_morphology,
    process_single_image,
    process_levir_pair,
)

# ─────────────────────────────────────────────────────────────────
# SECTION 1: Resizing & Basic Conversions
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 1: Resizing and Color conversions{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

@test("resize_image scales BGR image to exact target dimensions")
def _():
    img = make_dummy_bgr_image(w=120, h=80)
    resized = resize_image(img, (200, 150))
    assert resized.shape == (150, 200, 3), f"Expected (150, 200, 3) but got {resized.shape}"

@test("extract_color_spaces converts BGR to RGB, HSV, LAB, and GRAY")
def _():
    img = make_dummy_bgr_image(w=50, h=50)
    spaces = extract_color_spaces(img)
    assert "RGB" in spaces and spaces["RGB"].shape == (50, 50, 3)
    assert "HSV" in spaces and spaces["HSV"].shape == (50, 50, 3)
    assert "LAB" in spaces and spaces["LAB"].shape == (50, 50, 3)
    assert "GRAY" in spaces and spaces["GRAY"].shape == (50, 50)

# ─────────────────────────────────────────────────────────────────
# SECTION 2: Edge & Texture Extraction
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 2: Edge and Texture Feature Extraction{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

@test("detect_edges returns Canny and Sobel magnitude/direction maps")
def _():
    img = make_dummy_bgr_image(w=60, h=60)
    gray = extract_color_spaces(img)["GRAY"]
    edges = detect_edges(gray, canny_low=50, canny_high=150, sobel_k=3)
    assert "canny" in edges and edges["canny"].shape == (60, 60)
    assert "sobel_mag" in edges and edges["sobel_mag"].shape == (60, 60)

@test("extract_lbp computes local binary patterns texture map")
def _():
    img = make_dummy_bgr_image(w=60, h=60)
    gray = extract_color_spaces(img)["GRAY"]
    lbp = extract_lbp(gray, radius=2, points=16)
    assert lbp.shape == (60, 60), f"LBP shape mismatch: {lbp.shape}"
    assert lbp.dtype == np.uint8 or lbp.dtype == np.float32 or lbp.dtype == np.float64

@test("extract_gabor computes multiple frequency and orientation maps")
def _():
    img = make_dummy_bgr_image(w=40, h=40)
    gray = extract_color_spaces(img)["GRAY"]
    gabor_maps = extract_gabor(gray, frequencies=[0.1, 0.3], thetas=[0, 45])
    assert len(gabor_maps) == 4, f"Expected 4 maps, got {len(gabor_maps)}"
    for name, gmap in gabor_maps.items():
        assert gmap.shape == (40, 40), f"Gabor map shape mismatch for {name}: {gmap.shape}"

# ─────────────────────────────────────────────────────────────────
# SECTION 3: Morphological and Multi-stage Pipelines
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 3: Morphology and Multi-stage Pipelines{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

@test("apply_morphology applies opening and closing operations")
def _():
    img = make_dummy_bgr_image(w=40, h=40)
    gray = extract_color_spaces(img)["GRAY"]
    # Binarize
    binary = (gray > 127).astype(np.uint8) * 255
    morphed = apply_morphology(binary, kernel_size=3)
    assert morphed.shape == (40, 40)

@test("process_single_image processes whole pipeline and saves results")
def _():
    import cv2
    img_path = _tmp_dir / "test_uav.png"
    cv2.imwrite(str(img_path), make_dummy_bgr_image(w=100, h=100))
    
    result = process_single_image(
        image_path=img_path,
        output_dir=_out_dir / "uav_single",
        config={
            "target_size": (128, 128),
            "edge_canny_low": 50,
            "edge_canny_high": 150,
            "lbp_radius": 2,
            "lbp_points": 16,
            "gabor_frequencies": [0.1],
            "gabor_thetas": [0, 90],
            "color_spaces": ["RGB", "HSV", "GRAY"],
        }
    )
    assert result["success"] is True
    assert Path(result["feature_map_path"]).exists()
    assert Path(result["visualization_path"]).exists()
    assert result["dimensions"] == [128, 128]
    assert "edge_density" in result["feature_stats"]

@test("process_levir_pair processes bi-temporal pairs and computes diffs")
def _():
    import cv2
    img_a = _tmp_dir / "levir_a.png"
    img_b = _tmp_dir / "levir_b.png"
    cv2.imwrite(str(img_a), make_dummy_bgr_image(w=100, h=100))
    
    # Create slightly changed image B
    b_arr = make_dummy_bgr_image(w=100, h=100)
    b_arr[10:30, 10:30] = [0, 0, 0]  # Add black square change
    cv2.imwrite(str(img_b), b_arr)
    
    result = process_levir_pair(
        image_a_path=img_a,
        image_b_path=img_b,
        output_dir=_out_dir / "levir_pair",
        config={
            "target_size": (128, 128),
            "change_threshold": 30,
        }
    )
    assert result["success"] is True
    assert Path(result["diff_map_path"]).exists()
    assert Path(result["visualization_path"]).exists()
    assert result["change_stats"]["change_percent"] > 0.0

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
print(f"  MODULE 2 TEST REPORT")
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
    "module":      "Module 2: Advanced Image Processing",
    "timestamp":   datetime.now(timezone.utc).isoformat(),
    "total":       total,
    "passed":      passed,
    "failed":      failed,
    "pass_rate":   rate,
    "failed_tests": [{"name": n, "reason": r} for n, r in failed_tests],
}

report_dir = PROJECT_ROOT / "reports"
report_dir.mkdir(exist_ok=True)
with open(report_dir / "module2_test_report.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"  Report saved to: reports/module2_test_report.json")
sys.exit(0 if failed == 0 else 1)
