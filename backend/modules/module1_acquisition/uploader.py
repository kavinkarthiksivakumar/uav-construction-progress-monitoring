"""
Module 1: Image Upload Handler
IEEE M.Tech Project — UAV Image Acquisition

Manages:
  - Receiving uploaded files from the Flask API
  - Saving originals to uploads/raw/{project_id}/
  - Orchestrating the full pipeline:
      validate → extract metadata → quality → temporal sort → preprocess
  - Persisting per-image metadata to JSON
  - Returning structured results
"""

import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.modules.module1_acquisition.validator    import validate_image, validate_batch
from backend.modules.module1_acquisition.metadata     import extract_metadata
from backend.modules.module1_acquisition.quality      import assess_quality, generate_quality_report
from backend.modules.module1_acquisition.temporal     import sort_images_temporally, build_timeline
from backend.modules.module1_acquisition.preprocessor import preprocess_image

logger = logging.getLogger("module1.uploader")


# ─────────────────────────────────────────────────────────────────
# Save Raw Upload
# ─────────────────────────────────────────────────────────────────

def save_uploaded_file(
    file_obj,
    project_dir: Path,
    original_filename: str,
) -> Path:
    """
    Save an uploaded file object to the project's raw upload directory.

    Args:
        file_obj:          File-like object from werkzeug/Flask (or open file).
        project_dir:       Root directory for this project.
        original_filename: Original filename from the upload.

    Returns:
        Path where the file was saved.
    """
    raw_dir = project_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename: replace spaces, keep stem + extension
    safe_name = original_filename.replace(" ", "_")
    dest_path = raw_dir / safe_name

    # Handle duplicate filenames by appending counter
    if dest_path.exists():
        stem   = Path(safe_name).stem
        suffix = Path(safe_name).suffix
        counter = 1
        while dest_path.exists():
            dest_path = raw_dir / f"{stem}_{counter}{suffix}"
            counter  += 1

    if hasattr(file_obj, "save"):
        file_obj.save(str(dest_path))
    else:
        with open(dest_path, "wb") as out:
            shutil.copyfileobj(file_obj, out)

    logger.info("Saved upload: %s → %s", original_filename, dest_path)
    return dest_path


# ─────────────────────────────────────────────────────────────────
# Process Single Image (Full Pipeline)
# ─────────────────────────────────────────────────────────────────

def process_single_image(
    file_path:   Path,
    project_id:  str,
    output_dir:  Path,
    seen_hashes: Dict[str, str],
    config:      Dict = None,
) -> Dict[str, Any]:
    """
    Run the full Module 1 pipeline on a single image file.

    Steps:
        1. Validate
        2. Extract metadata (if valid)
        3. Quality assessment (if valid)
        4. Record for temporal sorting
        5. Preprocessing (if accepted)

    Args:
        file_path:   Absolute path to saved raw image.
        project_id:  Parent project ID.
        output_dir:  Directory for processed outputs.
        seen_hashes: Mutable dict for duplicate detection across batch.
        config:      Optional config overrides.

    Returns:
        Per-image processing result dictionary.
    """
    cfg        = config or {}
    image_id   = str(uuid.uuid4())
    started_at = datetime.utcnow().isoformat() + "Z"

    record: Dict[str, Any] = {
        "image_id":      image_id,
        "project_id":    project_id,
        "filename":      file_path.name,
        "file_path":     str(file_path),
        "started_at":    started_at,
        "status":        "pending",

        # Will be populated below
        "validation":    {},
        "metadata":      {},
        "quality":       {},
        "preprocessing": {},
        "temporal_index": None,
    }

    # ── Step 1: Validate ────────────────────────────────────────
    logger.info("[%s] Step 1: Validating %s", image_id[:8], file_path.name)
    validation = validate_image(
        file_path        = file_path,
        seen_hashes      = seen_hashes,
        max_file_size_mb = cfg.get("max_file_size_mb", 100),
        min_resolution   = cfg.get("min_resolution", 100),
    )
    record["validation"] = validation

    if not validation["valid"]:
        record["status"] = "rejected_validation"
        record["completed_at"] = datetime.utcnow().isoformat() + "Z"
        logger.warning("[%s] Rejected at validation: %s", image_id[:8], validation["errors"])
        return record

    # ── Step 2: Extract Metadata ────────────────────────────────
    logger.info("[%s] Step 2: Extracting metadata", image_id[:8])
    try:
        meta = extract_metadata(file_path)
        record["metadata"]           = meta
        record["file_modified_at"]   = meta.get("file_modified_at", "")
        record["exif"]               = meta.get("exif", {})
        record["width"]              = meta.get("width", validation.get("width", 0))
        record["height"]             = meta.get("height", validation.get("height", 0))
    except Exception as exc:
        logger.warning("[%s] Metadata extraction error: %s", image_id[:8], exc)
        record["metadata"] = {"error": str(exc)}
        record["exif"]     = {}
        record["width"]    = validation.get("width", 0)
        record["height"]   = validation.get("height", 0)

    # ── Step 3: Quality Assessment ──────────────────────────────
    logger.info("[%s] Step 3: Quality assessment", image_id[:8])
    try:
        quality = assess_quality(
            file_path = file_path,
            width     = record.get("width", 0),
            height    = record.get("height", 0),
        )
        record["quality"]       = quality
        record["quality_score"] = quality.get("overall_score", 0)
        record["accepted"]      = quality.get("accepted", False)
    except Exception as exc:
        logger.warning("[%s] Quality assessment error: %s", image_id[:8], exc)
        record["quality"]       = {"error": str(exc)}
        record["quality_score"] = 0
        record["accepted"]      = False

    # ── Step 4: Preprocessing (only for accepted images) ────────
    if record.get("accepted", False):
        logger.info("[%s] Step 4: Preprocessing", image_id[:8])
        try:
            preproc = preprocess_image(
                input_path  = file_path,
                output_dir  = output_dir,
                target_size = tuple(cfg.get("target_size", (1024, 1024))),
            )
            record["preprocessing"] = preproc
            record["status"]        = "processed" if preproc["success"] else "preprocess_failed"
        except Exception as exc:
            logger.error("[%s] Preprocessing failed: %s", image_id[:8], exc)
            record["preprocessing"] = {"error": str(exc)}
            record["status"]        = "preprocess_failed"
    else:
        record["status"] = "rejected_quality"
        logger.info(
            "[%s] Skipping preprocessing — quality score %.1f < threshold",
            image_id[:8], record.get("quality_score", 0)
        )

    record["completed_at"] = datetime.utcnow().isoformat() + "Z"
    return record


# ─────────────────────────────────────────────────────────────────
# Process Batch Upload
# ─────────────────────────────────────────────────────────────────

def process_upload_batch(
    file_objects:  List[Dict],   # [{"file": file_obj, "filename": str}]
    project_id:    str,
    uploads_root:  Path,
    processed_root: Path,
    metadata_dir:  Path,
    config:        Dict = None,
) -> Dict[str, Any]:
    """
    Process a batch of uploaded images through the full Module 1 pipeline.

    Orchestrates: save → validate → metadata → quality → temporal sort → preprocess

    Args:
        file_objects:    List of dicts with 'file' and 'filename' keys.
        project_id:      Unique project identifier.
        uploads_root:    Root upload directory.
        processed_root:  Root processed output directory.
        metadata_dir:    Directory to write metadata JSON.
        config:          Optional config overrides.

    Returns:
        Comprehensive batch processing result.
    """
    cfg         = config or {}
    project_dir = uploads_root / project_id
    output_dir  = processed_root / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    batch_started = datetime.utcnow().isoformat() + "Z"
    seen_hashes: Dict[str, str] = {}
    image_records: List[Dict]   = []

    logger.info(
        "Batch upload started: %d files for project %s",
        len(file_objects), project_id
    )

    # ── Step A: Save and process each file ──────────────────────
    for item in file_objects:
        try:
            saved_path = save_uploaded_file(
                file_obj           = item["file"],
                project_dir        = project_dir,
                original_filename  = item["filename"],
            )
            record = process_single_image(
                file_path    = saved_path,
                project_id   = project_id,
                output_dir   = output_dir,
                seen_hashes  = seen_hashes,
                config       = cfg,
            )
            image_records.append(record)

        except Exception as exc:
            logger.error("Failed to process file %s: %s", item.get("filename", "?"), exc)
            image_records.append({
                "filename":  item.get("filename", "unknown"),
                "status":    "error",
                "error":     str(exc),
                "image_id":  str(uuid.uuid4()),
            })

    # ── Step B: Temporal sort ────────────────────────────────────
    logger.info("Applying temporal sort to %d images", len(image_records))
    sorted_records = sort_images_temporally(image_records, fallback="filename")

    # ── Step C: Build timeline ───────────────────────────────────
    timeline = build_timeline(sorted_records)

    # ── Step D: Quality report ───────────────────────────────────
    quality_list   = [r["quality"] for r in sorted_records if r.get("quality")]
    quality_report = generate_quality_report(quality_list) if quality_list else {}

    # ── Step E: Persist metadata JSON ───────────────────────────
    metadata_dir.mkdir(parents=True, exist_ok=True)
    meta_file = metadata_dir / f"{project_id}_images.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(sorted_records, f, indent=2, default=str)
    logger.info("Metadata saved: %s", meta_file)

    # ── Step F: Summary ─────────────────────────────────────────
    total     = len(sorted_records)
    processed = sum(1 for r in sorted_records if r.get("status") == "processed")
    rejected  = sum(1 for r in sorted_records if "rejected" in r.get("status", ""))
    errors    = sum(1 for r in sorted_records if r.get("status") == "error")

    result = {
        "project_id":      project_id,
        "batch_started":   batch_started,
        "batch_completed": datetime.utcnow().isoformat() + "Z",
        "total_uploaded":  total,
        "processed":       processed,
        "rejected":        rejected,
        "errors":          errors,
        "timeline":        timeline,
        "quality_report":  quality_report,
        "images":          sorted_records,
        "metadata_file":   str(meta_file),
    }

    logger.info(
        "Batch complete: %d/%d processed, %d rejected, %d errors",
        processed, total, rejected, errors
    )

    return result
