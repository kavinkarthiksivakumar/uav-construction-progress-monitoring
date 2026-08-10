"""
Self-contained validation runner.
Runs all Module 1 logic tests WITHOUT needing pip install.
Uses only Python stdlib + already-available packages.
"""
import sys, os, struct, zlib, hashlib, shutil, json, tempfile, re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

GREEN  = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"
BOLD   = "\033[1m";  RESET = "\033[0m"

passed = []; failed = []

def test(name):
    def dec(fn):
        try:
            fn()
            print(f"  {GREEN}✓{RESET} {name}")
            passed.append(name)
        except Exception as e:
            print(f"  {RED}✗{RESET} {name}: {e}")
            failed.append((name, str(e)))
        return fn
    return dec

# ── Minimal PNG generator (stdlib only) ──────────────────────────
def make_png(w=640, h=480, color=(120,150,180)):
    def chunk(t, d):
        c = t+d; return struct.pack(">I",len(d))+c+struct.pack(">I",zlib.crc32(c)&0xFFFFFFFF)
    sig  = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB",w,h,8,2,0,0,0))
    raw  = b"".join(b"\x00"+bytes(color)*w for _ in range(h))
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig+ihdr+idat+iend

tmp = Path(tempfile.mkdtemp())

# ─────────────────────────────────────────────────────────────────
# SECTION 1: Temporal Ordering (pure stdlib — always runs)
# ─────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{'='*50}{RESET}")
print(f"{BOLD}  SECTION 1: Temporal Ordering (stdlib){RESET}")
print(f"{BOLD}{'='*50}{RESET}")

from backend.modules.module1_acquisition.temporal import sort_images_temporally, build_timeline

@test("Filename natural sort: day1 < day2 < day5 < day10")
def _():
    recs = [{"filename":"day10.jpg","exif":{}},{"filename":"day2.jpg","exif":{}},
            {"filename":"day1.jpg","exif":{}},{"filename":"day5.jpg","exif":{}}]
    out  = sort_images_temporally(recs, fallback="filename")
    names = [r["filename"] for r in out]
    assert names == ["day1.jpg","day2.jpg","day5.jpg","day10.jpg"], names

@test("EXIF date sort takes priority over filename")
def _():
    recs = [
        {"filename":"img_b.jpg","exif":{"DateTimeOriginal":"2024:03:15 10:00:00"}},
        {"filename":"img_a.jpg","exif":{"DateTimeOriginal":"2024:01:01 08:00:00"}},
        {"filename":"img_c.jpg","exif":{"DateTimeOriginal":"2024:06:20 14:00:00"}},
    ]
    out   = sort_images_temporally(recs)
    names = [r["filename"] for r in out]
    assert names == ["img_a.jpg","img_b.jpg","img_c.jpg"], names

@test("Temporal indices assigned 0,1,2")
def _():
    recs = [{"filename":"a.jpg","exif":{}},{"filename":"b.jpg","exif":{}},{"filename":"c.jpg","exif":{}}]
    out  = sort_images_temporally(recs)
    assert [r["temporal_index"] for r in out] == [0,1,2]

@test("Timeline builder: total_images and date_range populated")
def _():
    recs = [
        {"filename":"t1.jpg","exif":{"DateTimeOriginal":"2024:01:01 08:00:00"},
         "temporal_index":0,"image_id":"aaa","status":"processed","quality_score":80},
        {"filename":"t2.jpg","exif":{"DateTimeOriginal":"2024:01:05 09:00:00"},
         "temporal_index":1,"image_id":"bbb","status":"processed","quality_score":75},
    ]
    out = sort_images_temporally(recs)
    tl  = build_timeline(out)
    assert tl["total_images"] == 2
    assert tl["date_range"] is not None

@test("Empty list → empty timeline")
def _():
    tl = build_timeline([])
    assert tl["total_images"] == 0
    assert tl["entries"] == []

@test("Sort method recorded as 'exif_date' when EXIF present")
def _():
    recs = [{"filename":"x.jpg","exif":{"DateTimeOriginal":"2024:01:01 08:00:00"}}]
    out  = sort_images_temporally(recs)
    assert out[0]["sort_method"] == "exif_date"

@test("Sort method recorded as 'filename' when no EXIF")
def _():
    recs = [{"filename":"abc.jpg","exif":{}},{"filename":"xyz.jpg","exif":{}}]
    out  = sort_images_temporally(recs, fallback="filename")
    assert out[0]["sort_method"] == "filename"

# ─────────────────────────────────────────────────────────────────
# SECTION 2: Quality Metrics (pure numpy — available in most envs)
# ─────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{'='*50}{RESET}")
print(f"{BOLD}  SECTION 2: Quality Metrics{RESET}")
print(f"{BOLD}{'='*50}{RESET}")

try:
    import numpy as np
    from backend.modules.module1_acquisition.quality import (
        compute_brightness_score, compute_contrast_score,
        compute_resolution_score, compute_overall_score, generate_quality_report
    )

    @test("Brightness: bright image → high score")
    def _():
        gray = np.full((100,100), 180, dtype=np.float64)
        score, status = compute_brightness_score(gray)
        assert score >= 50, f"Got {score}"
        assert status == "good"

    @test("Brightness: dark image → too_dark")
    def _():
        gray = np.full((100,100), 10, dtype=np.float64)
        score, status = compute_brightness_score(gray)
        assert status == "too_dark"

    @test("Contrast: uniform image → low contrast")
    def _():
        gray = np.full((100,100), 128, dtype=np.float64)
        score, status = compute_contrast_score(gray)
        assert status == "low_contrast", f"Got {status}"

    @test("Resolution score: 1920×1080 → ≥90")
    def _():
        score, status = compute_resolution_score(1920, 1080)
        assert score >= 90, f"Got {score}"

    @test("Resolution score: 200×200 → <60")
    def _():
        score, status = compute_resolution_score(200, 200)
        assert score < 60, f"Got {score}"

    @test("Overall score: weighted average correct")
    def _():
        metrics = {"blur":100,"brightness":100,"contrast":100,"resolution":100}
        overall = compute_overall_score(metrics)
        assert overall == 100.0

    @test("Quality report: accepted/rejected counts")
    def _():
        results = [
            {"overall_score":80,"accepted":True,"blur_score":80,"brightness_score":85,"contrast_score":75,"resolution_score":80},
            {"overall_score":40,"accepted":False,"blur_score":40,"brightness_score":45,"contrast_score":35,"resolution_score":40},
        ]
        rpt = generate_quality_report(results)
        assert rpt["total"] == 2
        assert rpt["accepted"] == 1
        assert rpt["rejected"] == 1
        assert rpt["score_stats"]["mean"] == 60.0

except ImportError as e:
    print(f"  {YELLOW}⚠  numpy not available, skipping quality metric tests: {e}{RESET}")

# ─────────────────────────────────────────────────────────────────
# SECTION 3: Validator (needs Pillow)
# ─────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{'='*50}{RESET}")
print(f"{BOLD}  SECTION 3: Validator{RESET}")
print(f"{BOLD}{'='*50}{RESET}")

try:
    from PIL import Image
    from backend.modules.module1_acquisition.validator import validate_image, validate_batch, compute_md5

    @test("Valid PNG passes all validation checks")
    def _():
        p = tmp / "valid.png"
        p.write_bytes(make_png(640, 480))
        res = validate_image(p, seen_hashes={})
        assert res["valid"], res["errors"]
        assert res["width"] == 640 and res["height"] == 480

    @test("Bad extension (.bmp) is rejected")
    def _():
        p = tmp / "img.bmp"
        p.write_bytes(make_png(640,480))
        res = validate_image(p, seen_hashes={})
        assert not res["valid"]
        assert any("extension" in e.lower() for e in res["errors"])

    @test("Empty file rejected")
    def _():
        p = tmp / "empty.png"; p.touch()
        res = validate_image(p, seen_hashes={})
        assert not res["valid"]

    @test("Corrupt PNG data rejected")
    def _():
        p = tmp/"corrupt.png"
        p.write_bytes(b"\x89PNG\r\n\x1a\n"+b"\x00"*50+b"BADDATA")
        res = validate_image(p, seen_hashes={})
        assert not res["valid"]

    @test("Duplicate file detected by MD5")
    def _():
        data = make_png(640,480)
        p1 = tmp/"orig.png"; p1.write_bytes(data)
        p2 = tmp/"dup.png";  p2.write_bytes(data)
        seen = {}
        validate_image(p1, seen)
        res = validate_image(p2, seen)
        assert not res["valid"]
        assert res["duplicate_of"] == "orig.png"

    @test("Small image (50×50) rejected for resolution")
    def _():
        p = tmp/"tiny.png"; p.write_bytes(make_png(50,50))
        res = validate_image(p, seen_hashes={})
        assert not res["valid"]
        assert any("resolution" in e.lower() for e in res["errors"])

    @test("Batch validation counts: 2 valid + 1 corrupt")
    def _():
        v1 = tmp/"bv1.png"; v1.write_bytes(make_png(640,480))
        v2 = tmp/"bv2.png"; v2.write_bytes(make_png(800,600))
        co = tmp/"bco.png"; co.write_bytes(b"\x89PNG\r\n\x1a\nBAD")
        res = validate_batch([v1, v2, co])
        assert res["total"] == 3
        assert res["passed"] == 2
        assert res["failed"] == 1

except ImportError as e:
    print(f"  {YELLOW}⚠  Pillow not available, skipping validator tests: {e}{RESET}")

# ─────────────────────────────────────────────────────────────────
# SECTION 4: Metadata Extractor
# ─────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{'='*50}{RESET}")
print(f"{BOLD}  SECTION 4: Metadata Extractor{RESET}")
print(f"{BOLD}{'='*50}{RESET}")

try:
    from PIL import Image
    from backend.modules.module1_acquisition.metadata import extract_metadata

    @test("Metadata: filename, width, height extracted")
    def _():
        p = tmp/"meta.png"; p.write_bytes(make_png(800,600))
        m = extract_metadata(p)
        assert m["filename"] == "meta.png"
        assert m["width"] == 800 and m["height"] == 600

    @test("Metadata: file_size_bytes > 0")
    def _():
        p = tmp/"meta2.png"; p.write_bytes(make_png())
        m = extract_metadata(p)
        assert m["file_size_bytes"] > 0

    @test("Metadata: missing EXIF returns empty dict gracefully")
    def _():
        p = tmp/"noexif.png"; p.write_bytes(make_png())
        m = extract_metadata(p)
        assert isinstance(m["exif"], dict)
        assert m["camera_make"] == "Unknown"

    @test("Metadata: megapixels computed (1000×1000 = 1.0 MP)")
    def _():
        p = tmp/"mp.png"; p.write_bytes(make_png(1000,1000))
        m = extract_metadata(p)
        assert m["megapixels"] == 1.0

    @test("Metadata: timestamps in ISO format")
    def _():
        p = tmp/"ts.png"; p.write_bytes(make_png())
        m = extract_metadata(p)
        datetime.fromisoformat(m["file_modified_at"])

except ImportError as e:
    print(f"  {YELLOW}⚠  Pillow not available, skipping metadata tests: {e}{RESET}")

# ─────────────────────────────────────────────────────────────────
# SECTION 5: Preprocessor
# ─────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{'='*50}{RESET}")
print(f"{BOLD}  SECTION 5: Preprocessor{RESET}")
print(f"{BOLD}{'='*50}{RESET}")

try:
    import cv2, numpy as np
    from backend.modules.module1_acquisition.preprocessor import (
        preprocess_image, resize_with_padding, apply_clahe, remove_noise, normalize_image
    )
    out_dir = tmp / "processed"

    @test("resize_with_padding: output is target size")
    def _():
        img = np.random.randint(0,255,(480,640,3),dtype=np.uint8)
        res = resize_with_padding(img, target_size=(512,512))
        assert res.shape == (512,512,3)

    @test("apply_clahe: output shape preserved")
    def _():
        img = np.random.randint(0,255,(480,640,3),dtype=np.uint8)
        out = apply_clahe(img)
        assert out.shape == img.shape

    @test("remove_noise: output shape preserved")
    def _():
        img = np.random.randint(0,255,(480,640,3),dtype=np.uint8)
        out = remove_noise(img)
        assert out.shape == img.shape

    @test("normalize_image: output in [0,1]")
    def _():
        img = np.array([[[0,128,255]]], dtype=np.uint8)
        out = normalize_image(img)
        assert out.min() >= 0.0 and out.max() <= 1.0
        assert out.dtype == np.float32

    @test("preprocess_image: full pipeline succeeds")
    def _():
        p = tmp/"pre.png"; p.write_bytes(make_png(640,480))
        res = preprocess_image(p, out_dir)
        assert res["success"], res.get("error")
        assert Path(res["output_path"]).exists()

    @test("preprocess_image: output is .png")
    def _():
        p = tmp/"pre2.png"; p.write_bytes(make_png(640,480))
        res = preprocess_image(p, out_dir)
        assert res["output_path"].endswith(".png")

    @test("preprocess_image: output dimensions correct (512×512)")
    def _():
        p = tmp/"pre3.png"; p.write_bytes(make_png(800,600))
        res = preprocess_image(p, out_dir, target_size=(512,512))
        assert res["processed_size"]["width"]  == 512
        assert res["processed_size"]["height"] == 512

    @test("preprocess_image: original file NOT modified")
    def _():
        p = tmp/"pre4.png"; data = make_png(640,480); p.write_bytes(data)
        md5_before = hashlib.md5(data).hexdigest()
        preprocess_image(p, out_dir)
        md5_after  = hashlib.md5(p.read_bytes()).hexdigest()
        assert md5_before == md5_after, "Original was modified!"

    @test("preprocess_image: all 5 steps in steps_applied")
    def _():
        p = tmp/"pre5.png"; p.write_bytes(make_png())
        res = preprocess_image(p, out_dir)
        for step in ["resize_with_padding","clahe_equalization","gaussian_denoise","normalization","saved_png"]:
            assert step in res["steps_applied"], f"Missing: {step}"

except ImportError as e:
    print(f"  {YELLOW}⚠  OpenCV/numpy not available, skipping preprocessor tests: {e}{RESET}")

# ─────────────────────────────────────────────────────────────────
# SECTION 6: Config & Directory Structure
# ─────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{'='*50}{RESET}")
print(f"{BOLD}  SECTION 6: Config & Project Structure{RESET}")
print(f"{BOLD}{'='*50}{RESET}")

@test("settings.py imports without error")
def _():
    from backend.config.settings import (
        UPLOADS_DIR, PROCESSED_DIR, METADATA_DIR,
        LOGS_DIR, QUALITY, PREPROCESSING, TEMPORAL, API
    )
    assert isinstance(QUALITY["accept_score_threshold"], float)
    assert PREPROCESSING["target_size"] == (1024, 1024)
    assert TEMPORAL["fallback_order"] == "filename"
    assert API["version"] == "1.0.0"

@test("ensure_directories() creates all required dirs")
def _():
    from backend.config.settings import ensure_directories, UPLOADS_DIR, PROCESSED_DIR
    ensure_directories()
    assert UPLOADS_DIR.exists()
    assert PROCESSED_DIR.exists()

@test("requirements.txt exists and has content")
def _():
    req = PROJECT_ROOT / "requirements.txt"
    assert req.exists()
    content = req.read_text()
    assert "flask" in content.lower()
    assert "pillow" in content.lower()
    assert "opencv" in content.lower()

@test("All module __init__.py files present")
def _():
    inits = [
        PROJECT_ROOT / "backend/__init__.py",
        PROJECT_ROOT / "backend/config/__init__.py",
        PROJECT_ROOT / "backend/modules/__init__.py",
        PROJECT_ROOT / "backend/modules/module1_acquisition/__init__.py",
    ]
    for f in inits:
        assert f.exists(), f"Missing: {f}"

@test("README.md exists and has API section")
def _():
    readme = PROJECT_ROOT / "README.md"
    assert readme.exists()
    content = readme.read_text()
    assert "api" in content.lower()
    assert "module" in content.lower()

@test("INSTALLATION.md exists")
def _():
    assert (PROJECT_ROOT / "INSTALLATION.md").exists()

# ─────────────────────────────────────────────────────────────────
# Cleanup
# ─────────────────────────────────────────────────────────────────
shutil.rmtree(tmp, ignore_errors=True)

# ─────────────────────────────────────────────────────────────────
# Final Report
# ─────────────────────────────────────────────────────────────────
total = len(passed) + len(failed)
rate  = int(len(passed) / total * 100) if total else 0

print(f"\n{BOLD}{'='*50}{RESET}")
print(f"{BOLD}  MODULE 1 — VALIDATION REPORT{RESET}")
print(f"{BOLD}{'='*50}{RESET}")
print(f"  Total Tests : {total}")
print(f"  {GREEN}Passed      : {len(passed)}{RESET}")
if failed:
    print(f"  {RED}Failed      : {len(failed)}{RESET}")
    for n, r in failed:
        print(f"    {RED}✗{RESET} {n}")
        print(f"      → {r}")
print(f"  Pass Rate   : {rate}%")
print(f"{BOLD}{'='*50}{RESET}\n")

# Save JSON report
report_dir = PROJECT_ROOT / "reports"
report_dir.mkdir(exist_ok=True)
report = {
    "module": "Module 1: UAV Image Acquisition",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "total": total, "passed": len(passed), "failed": len(failed), "pass_rate": rate,
    "failed_tests": [{"name": n, "reason": r} for n, r in failed],
}
with open(report_dir / "module1_validation_report.json", "w") as f:
    json.dump(report, f, indent=2)
print(f"  Report saved → reports/module1_validation_report.json\n")

sys.exit(0 if not failed else 1)
