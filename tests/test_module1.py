"""
Module 1 Automated Tests
IEEE M.Tech Project: UAV Image Acquisition

Tests:
  1. Project creation
  2. Image upload (valid files)
  3. Validation (corrupt, wrong extension, duplicate)
  4. Metadata extraction
  5. Temporal ordering
  6. Quality assessment
  7. Preprocessing
  8. Logging
"""

import os
import sys
import json
import struct
import zlib
import hashlib
import tempfile
import shutil
import logging
from pathlib import Path
from datetime import datetime

import numpy as np

# ── Path setup ─────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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


def make_test_image(
    width: int = 640,
    height: int = 480,
    color: tuple = (100, 150, 200),
    path: Path = None,
) -> Path:
    """
    Create a minimal valid PNG file for testing.
    
    Args:
        width:  Image width.
        height: Image height.
        color:  RGB fill color.
        path:   Output path (auto-generated if None).

    Returns:
        Path to the created PNG file.
    """
    if path is None:
        path = Path(tempfile.mktemp(suffix=".png"))

    # Build PNG manually
    def png_chunk(chunk_type, data):
        c = chunk_type + data
        return (
            struct.pack(">I", len(data)) + c +
            struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        )

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr      = png_chunk(b"IHDR", ihdr_data)

    # Create raw image data
    raw_rows  = b"".join(
        b"\x00" + bytes(color) * width
        for _ in range(height)
    )
    idat = png_chunk(b"IDAT", zlib.compress(raw_rows))
    iend = png_chunk(b"IEND", b"")

    with open(path, "wb") as f:
        f.write(signature + ihdr + idat + iend)

    return path


def make_corrupt_file(path: Path) -> Path:
    """Create a file that looks like a PNG but has corrupt data."""
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50 + b"CORRUPT")
    return path


# ─────────────────────────────────────────────────────────────────
# SECTION 1: Validator Tests
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 1: Image Validation{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

from backend.modules.module1_acquisition.validator import validate_image, validate_batch

_tmp_dir = Path(tempfile.mkdtemp())

@test("Valid PNG passes validation")
def _():
    img = make_test_image(640, 480, path=_tmp_dir / "test_valid.png")
    result = validate_image(img, seen_hashes={})
    assert result["valid"], f"Expected valid, got errors: {result['errors']}"
    assert result["width"]  == 640
    assert result["height"] == 480
    assert result["md5"] != ""

@test("Unsupported extension rejected")
def _():
    p = _tmp_dir / "file.bmp"
    make_test_image(path=_tmp_dir / "temp.png")
    shutil.copy(_tmp_dir / "temp.png", p)
    result = validate_image(p, seen_hashes={})
    assert not result["valid"]
    assert any("extension" in e.lower() for e in result["errors"])

@test("Corrupt file rejected")
def _():
    p = _tmp_dir / "corrupt.png"
    make_corrupt_file(p)
    result = validate_image(p, seen_hashes={})
    assert not result["valid"]

@test("Empty file rejected")
def _():
    p = _tmp_dir / "empty.png"
    p.touch()
    result = validate_image(p, seen_hashes={})
    assert not result["valid"]

@test("Duplicate file rejected")
def _():
    img  = make_test_image(640, 480, path=_tmp_dir / "orig.png")
    dup  = _tmp_dir / "dup.png"
    shutil.copy(img, dup)
    seen = {}
    validate_image(img, seen)
    result = validate_image(dup, seen)
    assert not result["valid"]
    assert result["duplicate_of"] is not None

@test("Small resolution rejected")
def _():
    p = make_test_image(50, 50, path=_tmp_dir / "tiny.png")
    result = validate_image(p, seen_hashes={})
    assert not result["valid"]
    assert any("resolution" in e.lower() for e in result["errors"])

@test("Batch validation returns correct counts")
def _():
    valid1 = make_test_image(640, 480, path=_tmp_dir / "b1.png")
    valid2 = make_test_image(800, 600, path=_tmp_dir / "b2.png")
    corrupt = _tmp_dir / "bc.png"; make_corrupt_file(corrupt)
    result = validate_batch([valid1, valid2, corrupt])
    assert result["total"]  == 3
    assert result["passed"] == 2
    assert result["failed"] == 1

# ─────────────────────────────────────────────────────────────────
# SECTION 2: Metadata Extraction Tests
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 2: Metadata Extraction{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

from backend.modules.module1_acquisition.metadata import extract_metadata

@test("Metadata extraction returns filename and dimensions")
def _():
    img  = make_test_image(800, 600, path=_tmp_dir / "meta_test.png")
    meta = extract_metadata(img)
    assert meta["filename"] == "meta_test.png"
    assert meta["width"]    == 800
    assert meta["height"]   == 600
    assert meta["file_size_bytes"] > 0
    assert "exif" in meta
    assert "image_properties" in meta

@test("Metadata contains file timestamps")
def _():
    img  = make_test_image(path=_tmp_dir / "ts_test.png")
    meta = extract_metadata(img)
    assert "file_modified_at" in meta
    assert "file_created_at"  in meta
    datetime.fromisoformat(meta["file_modified_at"])

@test("Metadata handles missing EXIF gracefully")
def _():
    img  = make_test_image(path=_tmp_dir / "no_exif.png")
    meta = extract_metadata(img)
    assert isinstance(meta["exif"], dict)
    assert meta["camera_make"]  == "Unknown"
    assert meta["camera_model"] == "Unknown"

@test("Metadata megapixels computed correctly")
def _():
    img  = make_test_image(1000, 1000, path=_tmp_dir / "mp_test.png")
    meta = extract_metadata(img)
    assert meta["megapixels"] == 1.0

# ─────────────────────────────────────────────────────────────────
# SECTION 3: Quality Assessment Tests
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 3: Quality Assessment{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

from backend.modules.module1_acquisition.quality import (
    assess_quality, generate_quality_report,
    compute_blur_score, compute_brightness_score,
    compute_contrast_score, compute_resolution_score,
)

@test("Quality assessment returns all required fields")
def _():
    img  = make_test_image(640, 480, path=_tmp_dir / "q_test.png")
    qual = assess_quality(img)
    for field in ["blur_score", "brightness_score", "contrast_score",
                  "resolution_score", "overall_score", "accepted"]:
        assert field in qual, f"Missing field: {field}"

@test("Blur score is numeric 0-100")
def _():
    img  = make_test_image(640, 480, path=_tmp_dir / "blur_test.png")
    qual = assess_quality(img)
    assert 0 <= qual["blur_score"] <= 100

@test("Brightness score is numeric 0-100")
def _():
    img  = make_test_image(640, 480, path=_tmp_dir / "bri_test.png")
    qual = assess_quality(img)
    assert 0 <= qual["brightness_score"] <= 100

@test("High resolution image gets good resolution score")
def _():
    img  = make_test_image(1920, 1080, path=_tmp_dir / "hires.png")
    qual = assess_quality(img)
    assert qual["resolution_score"] >= 70

@test("Low resolution image gets low resolution score")
def _():
    img  = make_test_image(200, 200, path=_tmp_dir / "lowres.png")
    qual = assess_quality(img)
    assert qual["resolution_score"] < 60

@test("Quality report aggregates batch correctly")
def _():
    results = [
        {"overall_score": 80.0, "accepted": True,
         "blur_score": 80, "brightness_score": 85, "contrast_score": 75, "resolution_score": 80},
        {"overall_score": 40.0, "accepted": False,
         "blur_score": 40, "brightness_score": 45, "contrast_score": 35, "resolution_score": 40},
    ]
    report = generate_quality_report(results)
    assert report["total"]    == 2
    assert report["accepted"] == 1
    assert report["rejected"] == 1
    assert report["score_stats"]["mean"] == 60.0

# ─────────────────────────────────────────────────────────────────
# SECTION 4: Temporal Ordering Tests
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 4: Temporal Ordering{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

from backend.modules.module1_acquisition.temporal import (
    sort_images_temporally, build_timeline
)

@test("Filename-based natural sort is correct")
def _():
    records = [
        {"filename": "day10.jpg", "exif": {}},
        {"filename": "day2.jpg",  "exif": {}},
        {"filename": "day1.jpg",  "exif": {}},
        {"filename": "day5.jpg",  "exif": {}},
    ]
    sorted_r = sort_images_temporally(records, fallback="filename")
    names    = [r["filename"] for r in sorted_r]
    assert names == ["day1.jpg", "day2.jpg", "day5.jpg", "day10.jpg"], f"Got: {names}"

@test("EXIF date sort takes priority over filename")
def _():
    records = [
        {"filename": "img_b.jpg", "exif": {"DateTimeOriginal": "2024:03:15 10:00:00"}},
        {"filename": "img_a.jpg", "exif": {"DateTimeOriginal": "2024:01:01 08:00:00"}},
        {"filename": "img_c.jpg", "exif": {"DateTimeOriginal": "2024:06:20 14:00:00"}},
    ]
    sorted_r = sort_images_temporally(records)
    names    = [r["filename"] for r in sorted_r]
    assert names == ["img_a.jpg", "img_b.jpg", "img_c.jpg"], f"Got: {names}"

@test("Temporal indices are assigned correctly")
def _():
    records = [
        {"filename": "a.jpg", "exif": {}},
        {"filename": "b.jpg", "exif": {}},
        {"filename": "c.jpg", "exif": {}},
    ]
    sorted_r = sort_images_temporally(records)
    assert [r["temporal_index"] for r in sorted_r] == [0, 1, 2]

@test("Timeline builder produces correct structure")
def _():
    records = [
        {"filename": "t1.jpg", "exif": {"DateTimeOriginal": "2024:01:01 08:00:00"}, "temporal_index": 0,
         "image_id": "aaa", "status": "processed", "quality_score": 80},
        {"filename": "t2.jpg", "exif": {"DateTimeOriginal": "2024:01:05 09:00:00"}, "temporal_index": 1,
         "image_id": "bbb", "status": "processed", "quality_score": 75},
    ]
    sorted_r = sort_images_temporally(records)
    timeline = build_timeline(sorted_r)
    assert timeline["total_images"] == 2
    assert timeline["date_range"] is not None

@test("Empty list returns empty timeline")
def _():
    timeline = build_timeline([])
    assert timeline["total_images"] == 0
    assert timeline["entries"] == []

# ─────────────────────────────────────────────────────────────────
# SECTION 5: Preprocessing Tests
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 5: Image Preprocessing{RESET}")
print(f"{BOLD}{'='*55}{RESET}")

from backend.modules.module1_acquisition.preprocessor import preprocess_image

_out_dir = _tmp_dir / "processed"

@test("Preprocessing succeeds on valid image")
def _():
    img    = make_test_image(640, 480, path=_tmp_dir / "pre_input.png")
    result = preprocess_image(img, _out_dir)
    assert result["success"], f"Error: {result.get('error')}"
    assert result["output_path"] is not None
    assert Path(result["output_path"]).exists()

@test("Preprocessing output is saved as PNG")
def _():
    img    = make_test_image(640, 480, path=_tmp_dir / "pre_png.png")
    result = preprocess_image(img, _out_dir)
    assert result["output_path"].endswith(".png")

@test("Preprocessing output has correct dimensions")
def _():
    img    = make_test_image(800, 600, path=_tmp_dir / "pre_size.png")
    result = preprocess_image(img, _out_dir, target_size=(512, 512))
    assert result["processed_size"]["width"]  == 512
    assert result["processed_size"]["height"] == 512

@test("Original file is NOT overwritten")
def _():
    img      = make_test_image(640, 480, path=_tmp_dir / "pre_orig.png")
    orig_md5 = hashlib.md5(img.read_bytes()).hexdigest()
    preprocess_image(img, _out_dir)
    new_md5  = hashlib.md5(img.read_bytes()).hexdigest()
    assert orig_md5 == new_md5, "Original file was modified!"

@test("All preprocessing steps are logged")
def _():
    img    = make_test_image(640, 480, path=_tmp_dir / "pre_steps.png")
    result = preprocess_image(img, _out_dir)
    assert "resize_with_padding"  in result["steps_applied"]
    assert "clahe_equalization"   in result["steps_applied"]
    assert "gaussian_denoise"     in result["steps_applied"]
    assert "normalization"        in result["steps_applied"]
    assert "saved_png"            in result["steps_applied"]

# ─────────────────────────────────────────────────────────────────
# SECTION 6: Flask API Tests
# ─────────────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*55}{RESET}")
print(f"{BOLD}  Section 6: Flask API (Unit-level){RESET}")
print(f"{BOLD}{'='*55}{RESET}")

try:
    import requests
    BASE = "http://localhost:5000/api/v1"

    @test("Health endpoint returns 200")
    def _():
        r = requests.get(f"{BASE}/health", timeout=3)
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True

    @test("Create project returns 201")
    def _():
        r = requests.post(f"{BASE}/projects",
                          json={"name": "Test Project", "description": "Auto test"},
                          timeout=3)
        assert r.status_code == 201
        data = r.json()
        assert data["success"]
        assert data["data"]["project_id"]

    @test("List projects returns array")
    def _():
        r = requests.get(f"{BASE}/projects", timeout=3)
        assert r.status_code == 200
        data = r.json()
        assert "projects" in data["data"]

except ImportError:
    print(f"  {YELLOW}⚠{RESET}  requests not installed — skipping Flask API tests")
except Exception as e:
    print(f"  {YELLOW}⚠{RESET}  Flask API tests skipped (server not running): {e}")

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
print(f"{BOLD}  MODULE 1 TEST REPORT{RESET}")
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
    "module":      "Module 1: UAV Image Acquisition",
    "timestamp":   datetime.utcnow().isoformat() + "Z",
    "total":       total,
    "passed":      passed,
    "failed":      failed,
    "pass_rate":   rate,
    "failed_tests": [{"name": n, "reason": r} for n, r in failed_tests],
}

report_dir = PROJECT_ROOT / "reports"
report_dir.mkdir(exist_ok=True)
with open(report_dir / "module1_test_report.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"  Report saved to: reports/module1_test_report.json")
sys.exit(0 if failed == 0 else 1)
