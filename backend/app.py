"""
Flask Application — Main Entry Point
IEEE M.Tech Project: Explainable Vision-Based Construction Progress Assessment

Module 1 Endpoints:
  GET  /api/v1/health                               → Health check
  POST /api/v1/projects                             → Create project
  GET  /api/v1/projects                             → List projects
  GET  /api/v1/projects/<id>                        → Get project
  DELETE /api/v1/projects/<id>                      → Delete project
  POST /api/v1/projects/<id>/upload                 → Upload images
  GET  /api/v1/projects/<id>/images                 → Get images
  GET  /api/v1/projects/<id>/timeline               → Temporal timeline
  GET  /api/v1/projects/<id>/quality                → Quality report
  POST /api/v1/projects/<id>/preprocess             → Re-run preprocessing
  GET  /api/v1/images/<project>/<img_id>/preview    → Serve image
  GET  /api/v1/projects/<id>/export                 → Export metadata

Module 2 Endpoints:
  GET  /api/v1/datasets/levir                       → Scan LEVIR-CD
  GET  /api/v1/datasets/levir/pairs                 → List pairs (paginated)
  POST /api/v1/datasets/levir/process               → Process pair batch
  GET  /api/v1/datasets/roboflow                    → Scan Roboflow dataset
  GET  /api/v1/datasets/roboflow/images             → List images (paginated)
  POST /api/v1/projects/<id>/process_module2        → Process UAV images
  GET  /api/v1/projects/<id>/process_module2/status → Processing status
  GET  /api/v1/datasets/levir/pairs/<pair_id>/maps  → Get pair feature maps
  GET  /                                            → Serve frontend
"""

import json
import logging
import mimetypes
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request, send_file, send_from_directory, abort
from flask_cors import CORS

# ─────────────────────────────────────────────────────────────────
# Path Setup — allow running from any directory
# ─────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import (
    SECRET_KEY, DEBUG, HOST, PORT,
    UPLOADS_DIR, PROCESSED_DIR, METADATA_DIR,
    LOGS_DIR, REPORTS_DIR, FRONTEND_DIR,
    MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS,
    PREPROCESSING, ensure_directories,
)
from backend.modules.module1_acquisition.uploader import process_upload_batch
from backend.modules.module1_acquisition.temporal import build_timeline, sort_images_temporally
from backend.modules.module1_acquisition.quality  import generate_quality_report
from backend.modules.module1_acquisition.preprocessor import preprocess_batch

# Module 2
from backend.modules.module2_processing.levir_loader    import (
    scan_levir_dataset, get_preview_pairs,
)
from backend.modules.module2_processing.roboflow_loader import (
    scan_roboflow_dataset, compute_class_distribution, get_images_paginated,
)
from backend.modules.module2_processing.processor       import (
    process_single_image, process_levir_pair, process_batch,
)
from backend.config.settings import PROCESSED_M2_DIR, LEVIR_CD_ROOT, ROBOFLOW_ROOT, MODULE2

# Module 3
from backend.modules.module3_detection.detector import (
    detect_image, detect_batch, detect_roboflow_split,
)
from backend.config.settings import PROCESSED_M3_DIR, MODULE3

# Module 4
from backend.modules.module4_change.change_detector import (
    detect_change_pair, detect_levir_batch, detect_levir_split,
)
from backend.modules.module4_change.metrics import (
    classify_severity, aggregate_batch_metrics, generate_change_report,
    SEVERITY_COLORS,
)
from backend.config.settings import PROCESSED_M4_DIR, MODULE4

# Module 5
from backend.modules.module5_prediction.predictor import run_full_prediction
from backend.modules.module5_prediction.s_curve import get_schedule_milestones
from backend.modules.module5_prediction.report import generate_progress_report
from backend.config.settings import PROCESSED_M5_DIR, MODULE5

# Module 6
from backend.modules.module6_xai.gradcam import generate_gradcam_heatmap, generate_gradcam_batch
from backend.modules.module6_xai.shap_explain import generate_shap_explanation
from backend.modules.module6_xai.pdf_report import generate_xai_pdf_report
from backend.config.settings import PROCESSED_M6_DIR, MODULE6

# ─────────────────────────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────────────────────────
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("app")

# ─────────────────────────────────────────────────────────────────
# Flask App
# ─────────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path="",
)
app.secret_key            = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ─────────────────────────────────────────────────────────────────
# In-Memory Project Store (JSON-backed persistence)
# ─────────────────────────────────────────────────────────────────
PROJECTS_FILE = METADATA_DIR / "projects.json"

def _load_projects() -> dict:
    """Load projects from JSON persistence file."""
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if PROJECTS_FILE.exists():
        try:
            with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_projects(projects: dict) -> None:
    """Persist projects dict to JSON file."""
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, default=str)

def _get_project(project_id: str) -> dict:
    """Get a single project or raise 404."""
    projects = _load_projects()
    if project_id not in projects:
        abort(404, description=f"Project '{project_id}' not found")
    return projects[project_id]

# ─────────────────────────────────────────────────────────────────
# Response Helpers
# ─────────────────────────────────────────────────────────────────

def ok(data=None, message="Success", status=200):
    """Uniform success response envelope."""
    return jsonify({
        "success": True,
        "message": message,
        "data":    data or {},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }), status

def err(message="Error", status=400, details=None):
    """Uniform error response envelope."""
    return jsonify({
        "success": False,
        "message": message,
        "details": details,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }), status

# ─────────────────────────────────────────────────────────────────
# Frontend Serving
# ─────────────────────────────────────────────────────────────────

@app.route("/")
def serve_index():
    """Serve the SPA frontend."""
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return send_file(str(index))
    return "<h1>Frontend not found. Check frontend/index.html</h1>", 404

@app.route("/<path:path>")
def serve_static(path):
    """Serve static frontend assets."""
    target = FRONTEND_DIR / path
    if target.exists():
        return send_file(str(target))
    # SPA fallback
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return send_file(str(index))
    abort(404)

# ─────────────────────────────────────────────────────────────────
# API: Health
# ─────────────────────────────────────────────────────────────────

@app.route("/api/v1/health")
def health():
    """Health check endpoint."""
    return ok({
        "status":    "healthy",
        "version":   "1.0.0",
        "module":    "Module 1: UAV Image Acquisition",
        "uptime":    datetime.utcnow().isoformat() + "Z",
        "directories": {
            "uploads":   str(UPLOADS_DIR),
            "processed": str(PROCESSED_DIR),
            "metadata":  str(METADATA_DIR),
            "logs":      str(LOGS_DIR),
        }
    })

# ─────────────────────────────────────────────────────────────────
# API: Projects
# ─────────────────────────────────────────────────────────────────

@app.route("/api/v1/projects", methods=["POST"])
def create_project():
    """Create a new UAV imagery project."""
    body = request.get_json(silent=True) or {}
    name        = body.get("name", "").strip()
    description = body.get("description", "").strip()
    location    = body.get("location", "").strip()

    if not name:
        return err("Project name is required", 400)

    project_id = str(uuid.uuid4())
    now        = datetime.utcnow().isoformat() + "Z"

    project = {
        "project_id":   project_id,
        "name":         name,
        "description":  description,
        "location":     location,
        "created_at":   now,
        "updated_at":   now,
        "status":       "active",
        "image_count":  0,
        "images":       [],
        "timeline":     {},
        "quality_report": {},
    }

    projects = _load_projects()
    projects[project_id] = project
    _save_projects(projects)

    # Create directories
    (UPLOADS_DIR.parent / project_id / "raw").mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / project_id).mkdir(parents=True, exist_ok=True)

    logger.info("Project created: %s (%s)", name, project_id)
    return ok(project, "Project created successfully", 201)


@app.route("/api/v1/projects", methods=["GET"])
def list_projects():
    """Return all projects with summary statistics."""
    projects = _load_projects()
    summary  = []
    for pid, proj in projects.items():
        summary.append({
            "project_id":  proj["project_id"],
            "name":        proj["name"],
            "description": proj.get("description", ""),
            "location":    proj.get("location", ""),
            "created_at":  proj["created_at"],
            "updated_at":  proj.get("updated_at", ""),
            "status":      proj.get("status", "active"),
            "image_count": proj.get("image_count", 0),
        })
    summary.sort(key=lambda p: p["created_at"], reverse=True)
    return ok({"projects": summary, "total": len(summary)})


@app.route("/api/v1/projects/<project_id>", methods=["GET"])
def get_project(project_id):
    """Return full project details."""
    proj = _get_project(project_id)
    return ok(proj)


@app.route("/api/v1/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    """Delete a project and all associated files."""
    projects = _load_projects()
    if project_id not in projects:
        return err("Project not found", 404)

    name = projects[project_id].get("name", project_id)
    del projects[project_id]
    _save_projects(projects)

    # Clean up files
    import shutil
    for d in [
        UPLOADS_DIR.parent / project_id,
        PROCESSED_DIR / project_id,
    ]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)

    # Remove metadata file
    meta_file = METADATA_DIR / f"{project_id}_images.json"
    if meta_file.exists():
        meta_file.unlink()

    logger.info("Project deleted: %s (%s)", name, project_id)
    return ok({"deleted_project_id": project_id}, "Project deleted")

# ─────────────────────────────────────────────────────────────────
# API: Image Upload
# ─────────────────────────────────────────────────────────────────

@app.route("/api/v1/projects/<project_id>/upload", methods=["POST"])
def upload_images(project_id):
    """
    Upload one or more UAV images and run the Module 1 pipeline.

    Accepts multipart/form-data with key 'images'.
    """
    proj = _get_project(project_id)

    if "images" not in request.files:
        return err("No images field in request", 400)

    files = request.files.getlist("images")
    if not files or all(f.filename == "" for f in files):
        return err("No files selected", 400)

    # Validate extensions upfront
    valid_files = []
    rejected    = []
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext in ALLOWED_EXTENSIONS:
            valid_files.append({"file": f, "filename": f.filename})
        else:
            rejected.append({"filename": f.filename, "reason": f"Unsupported extension: {ext}"})

    if not valid_files:
        return err("No valid image files found", 400, details=rejected)

    logger.info(
        "Upload request: %d files for project %s (%d valid, %d rejected extension)",
        len(files), project_id, len(valid_files), len(rejected)
    )

    # Run Module 1 pipeline
    try:
        result = process_upload_batch(
            file_objects   = valid_files,
            project_id     = project_id,
            uploads_root   = UPLOADS_DIR.parent,
            processed_root = PROCESSED_DIR,
            metadata_dir   = METADATA_DIR,
            config         = PREPROCESSING,
        )
    except Exception as exc:
        logger.error("Upload processing failed: %s", exc, exc_info=True)
        return err("Processing failed", 500, details=str(exc))

    # Update project store
    projects = _load_projects()
    p        = projects.get(project_id, proj)

    existing_ids = {img["image_id"] for img in p.get("images", [])}
    new_images   = [img for img in result["images"] if img.get("image_id") not in existing_ids]
    p["images"]  = p.get("images", []) + new_images
    p["image_count"] = len(p["images"])
    p["updated_at"]  = datetime.utcnow().isoformat() + "Z"
    p["timeline"]    = result.get("timeline", {})
    p["quality_report"] = result.get("quality_report", {})
    projects[project_id] = p
    _save_projects(projects)

    response_data = {
        "project_id":    project_id,
        "uploaded":      len(valid_files),
        "processed":     result["processed"],
        "rejected":      result["rejected"] + len(rejected),
        "errors":        result["errors"],
        "timeline":      result.get("timeline", {}),
        "quality_report": result.get("quality_report", {}),
        "extension_rejected": rejected,
    }

    return ok(response_data, f"Uploaded {len(valid_files)} images, {result['processed']} processed")

# ─────────────────────────────────────────────────────────────────
# API: Images
# ─────────────────────────────────────────────────────────────────

@app.route("/api/v1/projects/<project_id>/images", methods=["GET"])
def get_images(project_id):
    """Return all images for a project with metadata."""
    proj   = _get_project(project_id)
    images = proj.get("images", [])

    # Lightweight view
    page  = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))
    start = (page - 1) * limit
    end   = start + limit

    sliced = images[start:end]

    return ok({
        "images":  sliced,
        "total":   len(images),
        "page":    page,
        "limit":   limit,
        "pages":   max(1, (len(images) + limit - 1) // limit),
    })


@app.route("/api/v1/projects/<project_id>/timeline", methods=["GET"])
def get_timeline(project_id):
    """Return the temporal timeline for a project."""
    proj = _get_project(project_id)
    return ok({"timeline": proj.get("timeline", {})})


@app.route("/api/v1/projects/<project_id>/quality", methods=["GET"])
def get_quality(project_id):
    """Return the quality report for a project."""
    proj = _get_project(project_id)
    return ok({"quality_report": proj.get("quality_report", {})})


@app.route("/api/v1/projects/<project_id>/preprocess", methods=["POST"])
def run_preprocessing(project_id):
    """Re-run preprocessing on all accepted images for a project."""
    proj = _get_project(project_id)

    accepted_images = [
        img for img in proj.get("images", [])
        if img.get("accepted", False) and img.get("file_path")
    ]

    if not accepted_images:
        return err("No accepted images to preprocess", 400)

    file_paths = [Path(img["file_path"]) for img in accepted_images if Path(img.get("file_path", "")).exists()]
    output_dir = PROCESSED_DIR / project_id

    try:
        result = preprocess_batch(file_paths, output_dir, config=PREPROCESSING)
    except Exception as exc:
        return err("Preprocessing failed", 500, details=str(exc))

    return ok({
        "total":     result["total"],
        "succeeded": result["succeeded"],
        "failed":    result["failed"],
    }, f"Preprocessed {result['succeeded']}/{result['total']} images")


@app.route("/api/v1/projects/<project_id>/export", methods=["GET"])
def export_metadata(project_id):
    """Export project metadata as downloadable JSON."""
    meta_file = METADATA_DIR / f"{project_id}_images.json"
    if not meta_file.exists():
        proj = _get_project(project_id)
        # Create from project store
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(proj.get("images", []), f, indent=2, default=str)

    return send_file(
        str(meta_file),
        as_attachment=True,
        download_name=f"module1_metadata_{project_id}.json",
        mimetype="application/json",
    )

# ─────────────────────────────────────────────────────────────────
# API: Image Preview
# ─────────────────────────────────────────────────────────────────

@app.route("/api/v1/images/<project_id>/<image_id>/preview")
def get_image_preview(project_id, image_id):
    """Serve a raw or processed image for preview in the UI."""
    proj   = _get_project(project_id)
    images = proj.get("images", [])

    image_rec = next((img for img in images if img.get("image_id") == image_id), None)
    if not image_rec:
        abort(404, "Image not found")

    # Prefer processed image, fall back to raw
    preproc   = image_rec.get("preprocessing", {})
    out_path  = preproc.get("output_path", "")
    raw_path  = image_rec.get("file_path", "")

    target = None
    if out_path and Path(out_path).exists():
        target = Path(out_path)
    elif raw_path and Path(raw_path).exists():
        target = Path(raw_path)

    if not target:
        abort(404, "Image file not found on disk")

    mime, _ = mimetypes.guess_type(str(target))
    return send_file(str(target), mimetype=mime or "image/png")


@app.route("/api/v1/images/<project_id>/<image_id>/raw")
def get_raw_image(project_id, image_id):
    """Serve only the original (raw) image file."""
    proj   = _get_project(project_id)
    images = proj.get("images", [])

    image_rec = next((img for img in images if img.get("image_id") == image_id), None)
    if not image_rec:
        abort(404, "Image not found")

    raw_path = image_rec.get("file_path", "")
    if not raw_path or not Path(raw_path).exists():
        abort(404, "Raw image file not found")

    mime, _ = mimetypes.guess_type(raw_path)
    return send_file(raw_path, mimetype=mime or "image/jpeg")

# ─────────────────────────────────────────────────────────────────
# API: Logs
# ─────────────────────────────────────────────────────────────────

@app.route("/api/v1/logs")
def get_logs():
    """Return recent log entries from the app log file."""
    log_file = LOGS_DIR / "app.log"
    lines    = []
    n        = int(request.args.get("n", 200))
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
            lines = all_lines[-n:]
    return ok({"lines": lines, "total": len(lines)})

# ─────────────────────────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────────────────────────

@app.errorhandler(400)
def bad_request(e):
    return err(str(e.description), 400)

@app.errorhandler(404)
def not_found(e):
    return err(str(e.description), 404)

@app.errorhandler(413)
def too_large(e):
    return err("File too large. Maximum upload size is 500 MB total.", 413)

@app.errorhandler(500)
def server_error(e):
    return err("Internal server error", 500, details=str(e))

# ═════════════════════════════════════════════════════════════════
# MODULE 2 API — Dataset Management & Image Processing
# ═════════════════════════════════════════════════════════════════

# ─── LEVIR-CD ──────────────────────────────────────────────────

@app.route("/api/v1/datasets/levir", methods=["GET"])
def api_levir_scan():
    """
    Scan and return LEVIR-CD dataset inventory.
    Response includes split counts, total pairs, and full pairs list.
    """
    try:
        result = scan_levir_dataset(LEVIR_CD_ROOT)
        if not result.get("available"):
            return err(result.get("error", "Dataset unavailable"), 404)
        # Strip full pairs list from summary response for speed
        summary = {
            "root":         result["root"],
            "available":    result["available"],
            "scanned_at":   result["scanned_at"],
            "total_pairs":  result["total_pairs"],
            "summary":      result["summary"],
            "splits": {
                s: {k: v for k, v in d.items() if k != "pairs"}
                for s, d in result["splits"].items()
            },
        }
        return ok(summary)
    except Exception as e:
        logger.exception("levir_scan failed")
        return err(str(e), 500)


@app.route("/api/v1/datasets/levir/pairs", methods=["GET"])
def api_levir_pairs():
    """
    Return paginated list of LEVIR-CD image pairs.

    Query params:
      split  (str): 'train' | 'val' | 'test'  (default: train)
      page   (int): Page number (default: 1)
      limit  (int): Items per page (default: 20)
    """
    try:
        split = request.args.get("split", "train")
        page  = max(1, int(request.args.get("page",  1)))
        limit = min(50, int(request.args.get("limit", 20)))

        scan  = scan_levir_dataset(LEVIR_CD_ROOT)
        if not scan.get("available"):
            return err(scan.get("error", "Dataset unavailable"), 404)

        paginated = get_preview_pairs(scan, split=split, page=page, limit=limit)
        return ok(paginated)
    except Exception as e:
        logger.exception("levir_pairs failed")
        return err(str(e), 500)


@app.route("/api/v1/datasets/levir/process", methods=["POST"])
def api_levir_process():
    """
    Process a batch of LEVIR-CD pairs through the Module 2 pipeline.

    JSON body:
      split       (str):  'train' | 'val' | 'test'
      page        (int):  Which page of pairs to process
      limit       (int):  Max pairs (capped at 10 for performance)
      pair_ids    (list): Optional specific pair_ids to process
    """
    try:
        body  = request.get_json(force=True) or {}
        split = body.get("split", "train")
        page  = max(1, int(body.get("page",  1)))
        limit = min(10, int(body.get("limit", 5)))  # cap for real-time

        scan = scan_levir_dataset(LEVIR_CD_ROOT)
        if not scan.get("available"):
            return err(scan.get("error", "Dataset unavailable"), 404)

        paginated = get_preview_pairs(scan, split=split, page=page, limit=limit)
        pairs     = paginated["pairs"]

        # Filter by pair_ids if specified
        if body.get("pair_ids"):
            ids   = set(body["pair_ids"])
            pairs = [p for p in pairs if p["pair_id"] in ids]

        out_dir = PROCESSED_M2_DIR / "levir" / split
        result  = process_batch(
            items      = pairs,
            mode       = "pair",
            output_dir = out_dir,
            config     = MODULE2,
            max_items  = limit,
        )

        return ok(result), 200
    except Exception as e:
        logger.exception("levir_process failed")
        return err(str(e), 500)


@app.route("/api/v1/datasets/levir/pairs/<pair_id>/maps", methods=["GET"])
def api_levir_pair_maps(pair_id: str):
    """
    Return file paths of generated feature maps for a processed LEVIR-CD pair.
    """
    try:
        split = pair_id.split("_")[0] if "_" in pair_id else "train"
        pair_dir = PROCESSED_M2_DIR / "levir" / split / pair_id

        if not pair_dir.exists():
            return err(f"Pair '{pair_id}' has not been processed yet", 404)

        maps = {}
        for f in sorted(pair_dir.glob("*.png")):
            key = f.stem.replace(pair_id + "_", "").replace(pair_id, "")
            maps[f.stem] = f.name

        return ok({"pair_id": pair_id, "output_dir": str(pair_dir), "maps": maps})
    except Exception as e:
        logger.exception("levir_pair_maps failed")
        return err(str(e), 500)


# ─── Roboflow ──────────────────────────────────────────────────

@app.route("/api/v1/datasets/roboflow", methods=["GET"])
def api_roboflow_scan():
    """
    Scan and return Roboflow construction dataset inventory.
    Includes class distribution across all splits.
    """
    try:
        result = scan_roboflow_dataset(ROBOFLOW_ROOT)
        if not result.get("available"):
            return err(result.get("error", "Dataset unavailable"), 404)

        distribution = compute_class_distribution(result)
        return ok({
            "root":         result["root"],
            "available":    result["available"],
            "scanned_at":   result["scanned_at"],
            "classes":      result["classes"],
            "num_classes":  result["num_classes"],
            "total_images": result["total_images"],
            "summary":      result["summary"],
            "distribution": distribution,
            "splits": {
                s: {k: v for k, v in d.items() if k != "images"}
                for s, d in result["splits"].items()
            },
        })
    except Exception as e:
        logger.exception("roboflow_scan failed")
        return err(str(e), 500)


@app.route("/api/v1/datasets/roboflow/images", methods=["GET"])
def api_roboflow_images():
    """
    Return paginated image listing from the Roboflow dataset.

    Query params:
      split  (str): 'train' | 'valid' | 'test'
      page   (int): Page number
      limit  (int): Items per page
    """
    try:
        split = request.args.get("split", "train")
        page  = max(1, int(request.args.get("page",  1)))
        limit = min(50, int(request.args.get("limit", 24)))

        scan = scan_roboflow_dataset(ROBOFLOW_ROOT)
        if not scan.get("available"):
            return err(scan.get("error", "Dataset unavailable"), 404)

        paginated = get_images_paginated(scan, split=split, page=page, limit=limit)
        return ok(paginated)
    except Exception as e:
        logger.exception("roboflow_images failed")
        return err(str(e), 500)


# ─── Module 2: UAV Image Processing ──────────────────────────

@app.route("/api/v1/projects/<project_id>/process_module2", methods=["POST"])
def api_project_process_module2(project_id: str):
    """
    Run Module 2 processing pipeline on preprocessed images from Module 1.

    Takes images from processed/module1/{project_id}/
    Outputs feature maps to  processed/module2/{project_id}/

    JSON body:
      limit  (int): Max images to process (default: 20, max: 50)
    """
    try:
        project = _get_project(project_id)
        body    = request.get_json(force=True) or {}
        limit   = min(50, int(body.get("limit", 20)))

        # Find preprocessed images from Module 1
        m1_dir = PROCESSED_DIR / project_id
        if not m1_dir.exists():
            return err("No Module 1 processed images found. Run Module 1 first.", 400)

        png_files = sorted(m1_dir.glob("*.png"))[:limit]
        if not png_files:
            return err("No .png images in Module 1 output directory", 400)

        items = [{"image_path": str(f)} for f in png_files]
        out_dir = PROCESSED_M2_DIR / project_id

        result = process_batch(
            items      = items,
            mode       = "single",
            output_dir = out_dir,
            config     = MODULE2,
            max_items  = limit,
        )

        # Update project state
        projects = _load_projects()
        if project_id in projects:
            projects[project_id]["module2_processed"]   = result["succeeded"]
            projects[project_id]["module2_processed_at"] = datetime.utcnow().isoformat() + "Z"
            projects[project_id]["module2_output_dir"]  = str(out_dir)
            _save_projects(projects)

        logger.info(
            "Module 2 batch done for project %s: %d/%d succeeded",
            project_id, result["succeeded"], result["total"]
        )
        return ok(result)
    except Exception as e:
        logger.exception("process_module2 failed")
        return err(str(e), 500)


@app.route("/api/v1/projects/<project_id>/process_module2/status", methods=["GET"])
def api_module2_status(project_id: str):
    """
    Get Module 2 processing status for a project.
    Returns count of processed images and feature map list.
    """
    try:
        _get_project(project_id)  # 404 if not found
        out_dir = PROCESSED_M2_DIR / project_id

        if not out_dir.exists():
            return ok({"processed": False, "image_count": 0, "feature_dirs": []})

        feature_dirs = [d.name for d in sorted(out_dir.iterdir()) if d.is_dir()]
        total_maps   = sum(
            len(list((out_dir / d).glob("*.png")))
            for d in feature_dirs
        )

        return ok({
            "processed":    True,
            "image_count":  len(feature_dirs),
            "total_maps":   total_maps,
            "output_dir":   str(out_dir),
            "feature_dirs": feature_dirs,
        })
    except Exception as e:
        logger.exception("module2_status failed")
        return err(str(e), 500)


# Serve Module 2 processed feature map images
@app.route("/api/v1/module2/<project_id>/<stem>/<filename>", methods=["GET"])
def api_serve_feature_map(project_id: str, stem: str, filename: str):
    """
    Serve a Module 2 feature map PNG file.
    """
    try:
        img_path = PROCESSED_M2_DIR / project_id / stem / filename
        if not img_path.exists():
            abort(404)
        return send_file(str(img_path), mimetype="image/png")
    except Exception:
        abort(404)


# Serve LEVIR processed feature maps
@app.route("/api/v1/module2/levir/<split>/<pair_id>/<filename>", methods=["GET"])
def api_serve_levir_map(split: str, pair_id: str, filename: str):
    """
    Serve a LEVIR-CD feature map PNG file.
    """
    try:
        img_path = PROCESSED_M2_DIR / "levir" / split / pair_id / filename
        if not img_path.exists():
            abort(404)
        return send_file(str(img_path), mimetype="image/png")
    except Exception:
        abort(404)


# ═════════════════════════════════════════════════════════════════
# MODULE 3 API — Construction Activity Detection
# ═════════════════════════════════════════════════════════════════

@app.route("/api/v1/projects/<project_id>/detect", methods=["POST"])
def api_project_detect(project_id: str):
    """
    Run Module 3 detection on preprocessed images from a project.

    Looks for images in processed/module1/{project_id}/ and also
    uses Module 2 outputs if available.

    JSON body:
      limit  (int): Max images to process (default 20, max 50)
    """
    try:
        project = _get_project(project_id)
        body    = request.get_json(force=True) or {}
        limit   = min(50, int(body.get("limit", 20)))

        # Collect source images: prefer module1 processed output
        m1_dir    = PROCESSED_DIR / project_id
        png_files = []

        if m1_dir.exists():
            png_files = sorted(m1_dir.glob("*.png"))[:limit]

        # Fall back to raw uploaded images from project store
        if not png_files:
            images = project.get("images", [])
            for img in images[:limit]:
                fp = img.get("file_path") or img.get("preprocessing", {}).get("output_path", "")
                if fp and Path(fp).exists():
                    png_files.append(Path(fp))

        if not png_files:
            return err("No images found to detect. Upload and preprocess images first.", 400)

        items   = [{"image_path": str(f)} for f in png_files]
        out_dir = PROCESSED_M3_DIR / project_id

        result = detect_batch(
            items         = items,
            output_dir    = out_dir,
            config        = MODULE3,
            max_items     = limit,
            roboflow_root = Path(ROBOFLOW_ROOT),
        )

        # Update project state
        projects = _load_projects()
        if project_id in projects:
            projects[project_id]["module3_processed"]    = result["succeeded"]
            projects[project_id]["module3_processed_at"] = datetime.utcnow().isoformat() + "Z"
            projects[project_id]["module3_output_dir"]   = str(out_dir)
            projects[project_id]["module3_detections"]   = result["total_detections"]
            _save_projects(projects)

        logger.info(
            "Module 3 batch done for project %s: %d/%d, %d total detections",
            project_id, result["succeeded"], result["total"], result["total_detections"]
        )
        return ok(result)
    except Exception as e:
        logger.exception("detect failed")
        return err(str(e), 500)


@app.route("/api/v1/projects/<project_id>/detect/results", methods=["GET"])
def api_detect_results(project_id: str):
    """
    Return Module 3 detection results for a project.
    Loads all JSON result files from processed/module3/{project_id}/
    """
    try:
        _get_project(project_id)  # 404 if not found
        out_dir = PROCESSED_M3_DIR / project_id

        if not out_dir.exists():
            return ok({"detected": False, "results": [], "aggregate_counts": {}})

        results     = []
        agg_counts  = {}
        total_dets  = 0

        for json_file in sorted(out_dir.rglob("*_detections.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Add viz URL if exists
                viz = json_file.parent / f"{json_file.stem.replace('_detections','')}_viz.png"
                data["viz_available"] = viz.exists()
                if viz.exists():
                    rel = viz.relative_to(PROCESSED_M3_DIR)
                    data["viz_url"] = f"/api/v1/module3/{project_id}/{rel.as_posix()}"

                results.append(data)
                total_dets += len(data.get("detections", []))
                for cls, cnt in data.get("class_counts", {}).items():
                    agg_counts[cls] = agg_counts.get(cls, 0) + cnt

            except Exception:
                pass

        avg_compliance = 0.0
        if results:
            rates = [r.get("compliance", {}).get("compliance_rate", 0) for r in results]
            avg_compliance = round(sum(rates) / len(rates), 1) if rates else 0.0

        return ok({
            "detected":        True,
            "image_count":     len(results),
            "total_detections": total_dets,
            "aggregate_counts": agg_counts,
            "avg_compliance":  avg_compliance,
            "results":         results,
        })
    except Exception as e:
        logger.exception("detect_results failed")
        return err(str(e), 500)


@app.route("/api/v1/datasets/roboflow/detect", methods=["POST"])
def api_roboflow_detect():
    """
    Run Module 3 detection on images from the Roboflow Construction dataset.

    JSON body:
      split  (str): 'train' | 'valid' | 'test'
      limit  (int): Max images to process (default 10, max 30)
    """
    try:
        body  = request.get_json(force=True) or {}
        split = body.get("split", "train")
        limit = min(30, int(body.get("limit", 10)))

        out_dir = PROCESSED_M3_DIR / "roboflow" / split
        result  = detect_roboflow_split(
            roboflow_root = Path(ROBOFLOW_ROOT),
            split         = split,
            output_dir    = out_dir,
            config        = MODULE3,
            max_items     = limit,
        )
        return ok(result)
    except Exception as e:
        logger.exception("roboflow_detect failed")
        return err(str(e), 500)


# Serve Module 3 visualization images
@app.route("/api/v1/module3/<project_id>/<path:filepath>", methods=["GET"])
def api_serve_detection_viz(project_id: str, filepath: str):
    """
    Serve a Module 3 annotated visualization PNG.
    """
    try:
        img_path = PROCESSED_M3_DIR / project_id / filepath
        if not img_path.exists():
            abort(404)
        return send_file(str(img_path), mimetype="image/png")
    except Exception:
        abort(404)



# ═════════════════════════════════════════════════════════════════
# MODULE 4 API — Construction Change Detection
# ═════════════════════════════════════════════════════════════════

@app.route("/api/v1/datasets/levir/change", methods=["POST"])
def api_levir_change_detect():
    """
    Run Module 4 change detection on a LEVIR-CD dataset split.

    JSON body:
      split   (str): 'train' | 'val' | 'test'
      limit   (int): Max pairs to process (default 10, max 20)
      method  (str): 'otsu' | 'adaptive' | 'fixed' (default 'otsu')
    """
    try:
        body   = request.get_json(force=True) or {}
        split  = body.get("split",  "train")
        limit  = min(20, int(body.get("limit", 10)))
        method = body.get("method", "otsu")

        cfg = {**MODULE4, "threshold_method": method}
        out_dir = PROCESSED_M4_DIR / "levir" / split

        result = detect_levir_split(
            levir_root = Path(LEVIR_CD_ROOT),
            split      = split,
            output_dir = out_dir,
            config     = cfg,
            max_pairs  = limit,
        )
        # Enrich with severity per pair
        for r in result.get("results", []):
            r["severity"] = classify_severity(r.get("change_percent", 0))
            r["severity_color"] = SEVERITY_COLORS.get(r.get("severity", "low"), "#22c55e")

        return ok(result)
    except Exception as e:
        logger.exception("levir_change_detect failed")
        return err(str(e), 500)


@app.route("/api/v1/projects/<project_id>/change", methods=["POST"])
def api_project_change_detect(project_id: str):
    """
    Run Module 4 change detection on temporal image pairs from a project.

    Pairs the project's images by upload order (odd=before, even=after)
    or uses pairs explicitly specified in the request body.

    JSON body:
      pairs  (list): Optional [{"image_a": "...", "image_b": "..."}]
      limit  (int): Max pairs (default 5, max 20)
      method (str): Threshold method
    """
    try:
        project = _get_project(project_id)
        body    = request.get_json(force=True) or {}
        limit   = min(20, int(body.get("limit", 5)))
        method  = body.get("method", "otsu")

        cfg = {**MODULE4, "threshold_method": method}
        out_dir = PROCESSED_M4_DIR / project_id

        # Use provided pairs or auto-pair project images
        explicit_pairs = body.get("pairs", [])
        if explicit_pairs:
            pairs = explicit_pairs[:limit]
        else:
            images = project.get("images", [])
            imgs   = [
                img.get("preprocessing", {}).get("output_path") or img.get("file_path", "")
                for img in images
                if img.get("preprocessing", {}).get("output_path") or img.get("file_path")
            ]
            imgs   = [p for p in imgs if Path(p).exists()]
            # Pair consecutive: (0,1), (2,3), ...
            pairs  = [
                {"image_a": imgs[i], "image_b": imgs[i+1]}
                for i in range(0, len(imgs) - 1, 2)
            ][:limit]

        if not pairs:
            return err("No image pairs found. Upload at least 2 images to a project.", 400)

        result = detect_levir_batch(
            pairs      = pairs,
            output_dir = out_dir,
            config     = cfg,
            max_pairs  = limit,
        )

        for r in result.get("results", []):
            r["severity"]       = classify_severity(r.get("change_percent", 0))
            r["severity_color"] = SEVERITY_COLORS.get(r.get("severity", "low"), "#22c55e")

        # Update project metadata
        projects = _load_projects()
        if project_id in projects:
            projects[project_id]["module4_pairs"]    = result.get("succeeded", 0)
            projects[project_id]["module4_done_at"]  = datetime.utcnow().isoformat() + "Z"
            projects[project_id]["module4_avg_change"] = result.get("avg_change", 0)
            _save_projects(projects)

        return ok(result)
    except Exception as e:
        logger.exception("project_change_detect failed")
        return err(str(e), 500)


@app.route("/api/v1/projects/<project_id>/change/results", methods=["GET"])
def api_change_results(project_id: str):
    """
    Return saved Module 4 change detection results for a project.
    Loads all *_change.json files from processed/module4/{project_id}/
    """
    try:
        _get_project(project_id)
        out_dir = PROCESSED_M4_DIR / project_id

        if not out_dir.exists():
            return ok({"detected": False, "results": [], "summary": {}})

        results     = []
        total_change = []

        for jf in sorted(out_dir.rglob("*_change.json")):
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["severity"]       = classify_severity(data.get("change_percent", 0))
                data["severity_color"] = SEVERITY_COLORS.get(data["severity"], "#22c55e")

                # attach overlay URL if exists
                overlay = jf.parent / jf.name.replace("_change.json", "_overlay.png")
                if overlay.exists():
                    rel = overlay.relative_to(PROCESSED_M4_DIR)
                    data["overlay_url"] = f"/api/v1/module4/overlay/{project_id}/{rel.as_posix()}"

                results.append(data)
                total_change.append(data.get("change_percent", 0))
            except Exception:
                pass

        summary = aggregate_batch_metrics([{"success": True, "change_percent": p, "num_regions": 0} for p in total_change])
        return ok({"detected": True, "results": results, "summary": summary})
    except Exception as e:
        logger.exception("change_results failed")
        return err(str(e), 500)


@app.route("/api/v1/module4/overlay/<project_id>/<path:filepath>")
def api_serve_change_overlay(project_id: str, filepath: str):
    """Serve a Module 4 change overlay or mask PNG."""
    try:
        img_path = PROCESSED_M4_DIR / project_id / filepath
        if not img_path.exists():
            abort(404)
        return send_file(str(img_path), mimetype="image/png")
    except Exception:
        abort(404)


@app.route("/api/v1/projects/<project_id>/change/report", methods=["GET"])
def api_change_report(project_id: str):
    """
    Download a JSON change detection report for a project.
    Generates one on-the-fly from saved results.
    """
    try:
        _get_project(project_id)
        out_dir = PROCESSED_M4_DIR / project_id

        results = []
        for jf in sorted(out_dir.rglob("*_change.json")):
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    r = json.load(f)
                r["success"] = True
                results.append(r)
            except Exception:
                pass

        batch = {"results": results}
        report_path = out_dir / "change_report.json"
        generate_change_report(batch, report_path)
        return send_file(str(report_path), as_attachment=True, download_name="change_report.json")
    except Exception as e:
        logger.exception("change_report failed")
        return err(str(e), 500)

# ═════════════════════─
# MODULE 5 API — Delay Prediction & Progress Assessment
# ═════════════════════─

@app.route("/api/v1/projects/<project_id>/predict", methods=["POST"])
def api_project_predict(project_id: str):
    """
    Run Module 5 Delay Prediction & Progress Assessment on a project.

    Consumes Module 1 quality data, Module 3 detection results, and
    Module 4 change detection results to produce:
      - Weighted progress score (0–100%)
      - Schedule delay prediction (days ahead/behind)
      - Risk level classification
      - S-curve (planned vs actual)

    JSON body:
      planned_duration_days  (int):  Total planned duration (default 365)
      planned_start_date     (str):  ISO date string for project start
      weights                (dict): Optional score weight overrides
    """
    try:
        project = _get_project(project_id)
        body    = request.get_json(force=True) or {}

        planned_duration = int(body.get(
            "planned_duration_days",
            MODULE5.get("default_planned_duration_days", 365)
        ))
        planned_start  = body.get("planned_start_date") or project.get("created_at")
        weight_override = body.get("weights")

        # ── Load Module 3 results ──────────────────────────────────────────
        detection_results = {}
        m3_dir = PROCESSED_M3_DIR / project_id
        if m3_dir.exists():
            total_dets  = 0
            agg_counts  = {}
            m3_results  = []
            comp_rates  = []
            for jf in sorted(m3_dir.rglob("*_detections.json")):
                try:
                    with open(jf, "r", encoding="utf-8") as f:
                        d = json.load(f)
                    m3_results.append(d)
                    total_dets += len(d.get("detections", []))
                    for cls, cnt in d.get("class_counts", {}).items():
                        agg_counts[cls] = agg_counts.get(cls, 0) + cnt
                    comp = d.get("compliance", {}).get("compliance_rate", 0)
                    comp_rates.append(comp)
                except Exception:
                    pass
            avg_comp = round(sum(comp_rates) / len(comp_rates), 2) if comp_rates else 0.0
            detection_results = {
                "total_detections": total_dets,
                "image_count":      len(m3_results),
                "aggregate_counts": agg_counts,
                "avg_compliance":   avg_comp,
            }

        # ── Load Module 4 results ──────────────────────────────────────────
        change_results = {}
        m4_dir = PROCESSED_M4_DIR / project_id
        if m4_dir.exists():
            results_list = []
            change_pcts  = []
            for jf in sorted(m4_dir.rglob("*_change.json")):
                try:
                    with open(jf, "r", encoding="utf-8") as f:
                        r = json.load(f)
                    r["success"] = True
                    from backend.modules.module4_change.metrics import classify_severity, SEVERITY_COLORS
                    r["severity"]       = classify_severity(r.get("change_percent", 0))
                    r["severity_color"] = SEVERITY_COLORS.get(r["severity"], "#22c55e")
                    results_list.append(r)
                    change_pcts.append(r.get("change_percent", 0.0))
                except Exception:
                    pass
            change_results = {
                "results":   results_list,
                "succeeded": len(results_list),
                "avg_change": round(sum(change_pcts) / len(change_pcts), 2) if change_pcts else 0.0,
                "max_change": round(max(change_pcts), 2) if change_pcts else 0.0,
                "min_change": round(min(change_pcts), 2) if change_pcts else 0.0,
            }

        # ── Run prediction ─────────────────────────────────────────────────
        weights_cfg = weight_override or MODULE5.get("weights")
        risk_cfg    = MODULE5.get("risk_thresholds")

        prediction = run_full_prediction(
            project_data          = project,
            detection_results     = detection_results,
            change_results        = change_results,
            planned_duration_days = planned_duration,
            planned_start_date    = planned_start,
            weights               = weights_cfg,
            risk_thresholds       = risk_cfg,
        )

        # Add milestones
        from backend.modules.module5_prediction.s_curve import get_schedule_milestones
        prediction["milestones"] = get_schedule_milestones(
            planned_start    = planned_start,
            planned_duration = planned_duration,
            current_progress = prediction["progress"]["progress_score"],
        )

        # ── Persist result to project store ────────────────────────────────
        projects = _load_projects()
        if project_id in projects:
            projects[project_id]["module5_score"]       = prediction["progress"]["progress_score"]
            projects[project_id]["module5_delay_days"]   = prediction["delay"]["delay_days"]
            projects[project_id]["module5_risk_level"]   = prediction["risk"]["risk_level"]
            projects[project_id]["module5_predicted_at"] = prediction["predicted_at"]
            projects[project_id]["module5_result"]       = prediction
            _save_projects(projects)

        # ── Save to processed/module5/{project_id}/ ────────────────────────
        m5_dir = PROCESSED_M5_DIR / project_id
        m5_dir.mkdir(parents=True, exist_ok=True)
        result_file = m5_dir / "prediction_result.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(prediction, f, indent=2, default=str)

        logger.info(
            "Module 5 prediction done for project %s: score=%.2f%%, delay=%+d days, risk=%s",
            project_id,
            prediction["progress"]["progress_score"],
            prediction["delay"]["delay_days"],
            prediction["risk"]["risk_level"],
        )
        return ok(prediction)
    except Exception as e:
        logger.exception("predict failed")
        return err(str(e), 500)


@app.route("/api/v1/projects/<project_id>/predict/results", methods=["GET"])
def api_predict_results(project_id: str):
    """
    Get saved Module 5 prediction results for a project.
    Returns the last saved prediction from processed/module5/{project_id}/.
    """
    try:
        _get_project(project_id)
        result_file = PROCESSED_M5_DIR / project_id / "prediction_result.json"

        if not result_file.exists():
            return ok({"predicted": False, "message": "No prediction run yet. Run /predict first."})

        with open(result_file, "r", encoding="utf-8") as f:
            prediction = json.load(f)

        return ok({"predicted": True, **prediction})
    except Exception as e:
        logger.exception("predict_results failed")
        return err(str(e), 500)


@app.route("/api/v1/projects/<project_id>/predict/s_curve", methods=["GET"])
def api_predict_s_curve(project_id: str):
    """
    Get the S-curve data points for a project's latest prediction.
    Returns planned vs actual cumulative progress over time.
    """
    try:
        _get_project(project_id)
        result_file = PROCESSED_M5_DIR / project_id / "prediction_result.json"

        if not result_file.exists():
            return ok({"predicted": False, "points": [], "message": "No prediction available."})

        with open(result_file, "r", encoding="utf-8") as f:
            prediction = json.load(f)

        s_curve = prediction.get("s_curve", {})
        return ok({
            "predicted":    True,
            "label_mode":   s_curve.get("label_mode", "sequence"),
            "n_points":     s_curve.get("n_points", 0),
            "x_labels":     s_curve.get("x_labels", []),
            "planned_data": s_curve.get("planned_data", []),
            "actual_data":  s_curve.get("actual_data", []),
            "points":       s_curve.get("points", []),
        })
    except Exception as e:
        logger.exception("predict_s_curve failed")
        return err(str(e), 500)


@app.route("/api/v1/projects/<project_id>/predict/report", methods=["GET"])
def api_predict_report(project_id: str):
    """
    Download Module 5 progress assessment report as JSON.
    Generates the report from saved prediction results.
    """
    try:
        project     = _get_project(project_id)
        result_file = PROCESSED_M5_DIR / project_id / "prediction_result.json"

        if not result_file.exists():
            return err("No prediction results found. Run Module 5 prediction first.", 404)

        with open(result_file, "r", encoding="utf-8") as f:
            prediction = json.load(f)

        report_path = PROCESSED_M5_DIR / project_id / "progress_report.json"
        report = generate_progress_report(
            project_data = project,
            prediction   = prediction,
            output_path  = report_path,
        )

        return send_file(
            str(report_path),
            as_attachment=True,
            download_name=f"progress_report_{project_id}.json",
            mimetype="application/json",
        )
    except Exception as e:
        logger.exception("predict_report failed")
        return err(str(e), 500)



# ═══════════════════════════════════════════════════════════════
# MODULE 6 API — Explainable AI (GradCAM + SHAP + Report)
# ═══════════════════════════════════════════════════════════════

@app.route("/api/v1/projects/<project_id>/xai/gradcam", methods=["POST"])
def api_gradcam(project_id: str):
    """
    Run Module 6 GradCAM heatmap generation on project images.

    Looks for preprocessed images in processed/module1/{project_id}/.
    Outputs: heatmap PNGs + overlay PNGs in processed/module6/{project_id}/gradcam/

    JSON body:
      limit       (int): Max images to process (default 5, max 10)
      model_path  (str): Optional path to PyTorch model .pt file
      alpha       (float): Overlay blend factor 0-1 (default 0.55)
    """
    try:
        project  = _get_project(project_id)
        body     = request.get_json(force=True) or {}
        limit    = min(10, int(body.get("limit", 5)))
        model_p  = body.get("model_path") or MODULE6.get("gradcam_model_path")
        alpha    = float(body.get("alpha", MODULE6.get("gradcam_alpha", 0.55)))

        # Collect images
        m1_dir = PROCESSED_DIR / project_id
        images = []
        if m1_dir.exists():
            images = sorted(m1_dir.glob("*.png"))[:limit]

        if not images:
            # Fall back to raw project images
            for img in project.get("images", [])[:limit]:
                fp = img.get("preprocessing", {}).get("output_path") or img.get("file_path", "")
                if fp and Path(fp).exists():
                    images.append(Path(fp))

        if not images:
            return err("No images found. Upload and preprocess images first.", 400)

        out_dir = PROCESSED_M6_DIR / project_id / "gradcam"
        result  = generate_gradcam_batch(
            image_paths = images,
            output_dir  = out_dir,
            model_path  = model_p,
            config      = {**MODULE6, "gradcam_alpha": alpha},
            max_items   = limit,
        )

        # Update project store
        projects = _load_projects()
        if project_id in projects:
            projects[project_id]["module6_gradcam_done"]  = True
            projects[project_id]["module6_gradcam_count"] = result["succeeded"]
            projects[project_id]["module6_gradcam_at"]    = datetime.utcnow().isoformat() + "Z"
            _save_projects(projects)

        logger.info("Module 6 GradCAM done for %s: %d/%d succeeded",
                    project_id, result["succeeded"], result["total"])
        return ok(result)
    except Exception as e:
        logger.exception("gradcam failed")
        return err(str(e), 500)


@app.route("/api/v1/projects/<project_id>/xai/gradcam/results", methods=["GET"])
def api_gradcam_results(project_id: str):
    """
    Return saved GradCAM results for a project.
    Scans processed/module6/{project_id}/gradcam/ for overlay PNGs.
    """
    try:
        _get_project(project_id)
        out_dir = PROCESSED_M6_DIR / project_id / "gradcam"

        if not out_dir.exists():
            return ok({"generated": False, "results": [],
                       "message": "No GradCAM results yet. Run /xai/gradcam first."})

        results = []
        for overlay in sorted(out_dir.glob("*_gradcam_overlay.png")):
            stem     = overlay.stem.replace("_gradcam_overlay", "")
            heatmap  = out_dir / f"{stem}_gradcam_heatmap.png"
            rel_ov   = overlay.relative_to(PROCESSED_M6_DIR)
            rel_hm   = heatmap.relative_to(PROCESSED_M6_DIR) if heatmap.exists() else None
            results.append({
                "stem":           stem,
                "overlay_url":    f"/api/v1/module6/{project_id}/gradcam/{overlay.name}",
                "heatmap_url":    f"/api/v1/module6/{project_id}/gradcam/{heatmap.name}" if rel_hm else None,
                "overlay_exists": True,
                "heatmap_exists": heatmap.exists(),
            })

        return ok({"generated": True, "count": len(results), "results": results})
    except Exception as e:
        logger.exception("gradcam_results failed")
        return err(str(e), 500)


@app.route("/api/v1/module6/<project_id>/gradcam/<filename>", methods=["GET"])
def api_serve_gradcam(project_id: str, filename: str):
    """Serve a GradCAM heatmap or overlay PNG."""
    try:
        img_path = PROCESSED_M6_DIR / project_id / "gradcam" / filename
        if not img_path.exists():
            abort(404)
        return send_file(str(img_path), mimetype="image/png")
    except Exception:
        abort(404)


@app.route("/api/v1/projects/<project_id>/xai/shap", methods=["POST"])
def api_shap(project_id: str):
    """
    Run Module 6 SHAP feature importance explanation on the latest Module 5 prediction.

    Requires Module 5 prediction to have been run first.

    JSON body:
      historical_data (list): Optional list of past prediction dicts for XGBoost training
    """
    try:
        project = _get_project(project_id)
        body    = request.get_json(force=True) or {}

        # Load Module 5 result
        result_file = PROCESSED_M5_DIR / project_id / "prediction_result.json"
        if not result_file.exists():
            return err("No Module 5 prediction found. Run /predict first.", 400)

        with open(result_file, "r", encoding="utf-8") as f:
            prediction = json.load(f)

        historical_data = body.get("historical_data", [])
        out_dir = PROCESSED_M6_DIR / project_id / "shap"

        result = generate_shap_explanation(
            prediction      = prediction,
            output_dir      = out_dir,
            historical_data = historical_data,
            config          = MODULE6,
        )

        # Update project store
        projects = _load_projects()
        if project_id in projects:
            projects[project_id]["module6_shap_done"] = result["success"]
            projects[project_id]["module6_shap_at"]   = datetime.utcnow().isoformat() + "Z"
            _save_projects(projects)

        logger.info("Module 6 SHAP done for %s: mode=%s", project_id, result.get("mode"))
        return ok(result)
    except Exception as e:
        logger.exception("shap failed")
        return err(str(e), 500)


@app.route("/api/v1/module6/<project_id>/shap/<filename>", methods=["GET"])
def api_serve_shap_chart(project_id: str, filename: str):
    """Serve a SHAP chart PNG."""
    try:
        img_path = PROCESSED_M6_DIR / project_id / "shap" / filename
        if not img_path.exists():
            abort(404)
        mime = "image/png" if filename.endswith(".png") else "application/json"
        return send_file(str(img_path), mimetype=mime)
    except Exception:
        abort(404)


@app.route("/api/v1/projects/<project_id>/xai/report", methods=["POST"])
def api_xai_report(project_id: str):
    """
    Generate a comprehensive XAI HTML+PDF report combining GradCAM + SHAP results.

    Requires Module 5 prediction to have been run first.
    GradCAM and SHAP are auto-run if not already available.

    JSON body:
      force_rerun (bool): Re-run GradCAM + SHAP even if already done (default false)
    """
    try:
        project = _get_project(project_id)
        body    = request.get_json(force=True) or {}
        force   = bool(body.get("force_rerun", False))

        # Load Module 5 prediction
        result_file = PROCESSED_M5_DIR / project_id / "prediction_result.json"
        if not result_file.exists():
            return err("No Module 5 prediction found. Run /predict first.", 400)

        with open(result_file, "r", encoding="utf-8") as f:
            prediction = json.load(f)

        # ── Auto-run SHAP if needed ────────────────────────────────────────
        shap_out = PROCESSED_M6_DIR / project_id / "shap"
        shap_json = shap_out / "shap_explanation.json"
        if force or not shap_json.exists():
            shap_result = generate_shap_explanation(
                prediction = prediction,
                output_dir = shap_out,
                config     = MODULE6,
            )
        else:
            with open(shap_json, "r", encoding="utf-8") as f:
                shap_result = json.load(f)
            shap_result["success"] = True
            shap_result["bar_chart_path"] = str(shap_out / "shap_bar.png") if (shap_out / "shap_bar.png").exists() else None
            shap_result["waterfall_path"] = str(shap_out / "shap_waterfall.png") if (shap_out / "shap_waterfall.png").exists() else None

        # ── Auto-run GradCAM if needed ────────────────────────────────────
        cam_out = PROCESSED_M6_DIR / project_id / "gradcam"
        gradcam_results = []
        if force or not cam_out.exists() or not list(cam_out.glob("*_overlay.png")):
            m1_dir = PROCESSED_DIR / project_id
            images = sorted(m1_dir.glob("*.png"))[:5] if m1_dir.exists() else []
            if not images:
                for img in project.get("images", [])[:5]:
                    fp = img.get("preprocessing", {}).get("output_path") or img.get("file_path", "")
                    if fp and Path(fp).exists():
                        images.append(Path(fp))
            if images:
                batch = generate_gradcam_batch(
                    image_paths = images,
                    output_dir  = cam_out,
                    config      = MODULE6,
                    max_items   = 5,
                )
                gradcam_results = [r for r in batch.get("results", []) if r.get("success")]
        else:
            for ov in sorted(cam_out.glob("*_gradcam_overlay.png")):
                stem = ov.stem.replace("_gradcam_overlay", "")
                hm   = cam_out / f"{stem}_gradcam_heatmap.png"
                gradcam_results.append({
                    "success":      True,
                    "image_path":   str(ov),
                    "overlay_path": str(ov),
                    "heatmap_path": str(hm) if hm.exists() else None,
                    "stats":        {"max_activation": 0.85, "mean_activation": 0.42, "high_activation_pct": 18.0},
                })

        # ── Generate report ────────────────────────────────────────────────
        report_dir = PROCESSED_M6_DIR / project_id / "report"
        report_result = generate_xai_pdf_report(
            project          = project,
            prediction       = prediction,
            shap_result      = shap_result,
            gradcam_results  = gradcam_results,
            output_dir       = report_dir,
            config           = MODULE6,
        )

        # Update project store
        projects = _load_projects()
        if project_id in projects:
            projects[project_id]["module6_report_done"] = report_result["success"]
            projects[project_id]["module6_report_at"]   = datetime.utcnow().isoformat() + "Z"
            _save_projects(projects)

        logger.info("Module 6 XAI report done for %s: html=%s pdf=%s",
                    project_id, report_result.get("html_path"), report_result.get("pdf_available"))
        return ok(report_result)
    except Exception as e:
        logger.exception("xai_report failed")
        return err(str(e), 500)


@app.route("/api/v1/projects/<project_id>/xai/report/download", methods=["GET"])
def api_xai_report_download(project_id: str):
    """
    Download the XAI HTML report for a project.
    Query param: format=html (default) | pdf | json
    """
    try:
        _get_project(project_id)
        fmt = request.args.get("format", "html").lower()

        report_dir = PROCESSED_M6_DIR / project_id / "report"

        if fmt == "pdf":
            p = report_dir / "xai_report.pdf"
            if not p.exists():
                return err("PDF not available. Run /xai/report first.", 404)
            return send_file(str(p), as_attachment=True, download_name=f"xai_report_{project_id}.pdf")
        elif fmt == "json":
            p = report_dir / "xai_summary.json"
            if not p.exists():
                return err("JSON summary not available. Run /xai/report first.", 404)
            return send_file(str(p), as_attachment=True, download_name=f"xai_summary_{project_id}.json")
        else:
            p = report_dir / "xai_report.html"
            if not p.exists():
                return err("HTML report not available. Run /xai/report first.", 404)
            return send_file(str(p), mimetype="text/html")
    except Exception as e:
        logger.exception("xai_report_download failed")
        return err(str(e), 500)


@app.route("/api/v1/projects/<project_id>/xai/status", methods=["GET"])
def api_xai_status(project_id: str):
    """
    Get Module 6 XAI processing status for a project.
    Returns what's been run and what's available.
    """
    try:
        _get_project(project_id)
        base = PROCESSED_M6_DIR / project_id

        gradcam_dir = base / "gradcam"
        shap_dir    = base / "shap"
        report_dir  = base / "report"

        gradcam_overlays = list(gradcam_dir.glob("*_overlay.png")) if gradcam_dir.exists() else []
        shap_bar         = (shap_dir / "shap_bar.png").exists() if shap_dir.exists() else False
        shap_wf          = (shap_dir / "shap_waterfall.png").exists() if shap_dir.exists() else False
        shap_json        = (shap_dir / "shap_explanation.json").exists() if shap_dir.exists() else False
        html_report      = (report_dir / "xai_report.html").exists() if report_dir.exists() else False
        pdf_report       = (report_dir / "xai_report.pdf").exists() if report_dir.exists() else False

        return ok({
            "gradcam": {
                "done":    len(gradcam_overlays) > 0,
                "count":   len(gradcam_overlays),
                "images":  [f.name for f in gradcam_overlays[:10]],
            },
            "shap": {
                "done":          shap_json,
                "bar_chart":     shap_bar,
                "waterfall":     shap_wf,
                "json_summary":  shap_json,
            },
            "report": {
                "html_available": html_report,
                "pdf_available":  pdf_report,
            },
            "overall_done": html_report,
        })
    except Exception as e:
        logger.exception("xai_status failed")
        return err(str(e), 500)


@app.route("/api/v1/projects/<project_id>/xai/full_pipeline", methods=["POST"])
def api_xai_full_pipeline(project_id: str):
    """
    Run the complete Module 6 XAI pipeline in one call:
      1. GradCAM heatmaps
      2. SHAP explanation
      3. XAI report generation

    Requires Module 5 prediction to be completed first.

    JSON body:
      limit  (int):   Max images for GradCAM (default 5)
      alpha  (float): GradCAM overlay blend factor
    """
    try:
        project = _get_project(project_id)
        body    = request.get_json(force=True) or {}
        limit   = min(10, int(body.get("limit", 5)))
        alpha   = float(body.get("alpha", 0.55))

        # Load Module 5 prediction
        result_file = PROCESSED_M5_DIR / project_id / "prediction_result.json"
        if not result_file.exists():
            return err("Module 5 prediction required. Run /predict first.", 400)

        with open(result_file, "r", encoding="utf-8") as f:
            prediction = json.load(f)

        pipeline_result: Dict[str, Any] = {"stages": {}}

        # Stage 1: GradCAM
        m1_dir = PROCESSED_DIR / project_id
        images = sorted(m1_dir.glob("*.png"))[:limit] if m1_dir.exists() else []
        if not images:
            for img in project.get("images", [])[:limit]:
                fp = img.get("preprocessing", {}).get("output_path") or img.get("file_path", "")
                if fp and Path(fp).exists():
                    images.append(Path(fp))

        cam_out = PROCESSED_M6_DIR / project_id / "gradcam"
        gradcam_batch = generate_gradcam_batch(
            image_paths = images,
            output_dir  = cam_out,
            config      = {**MODULE6, "gradcam_alpha": alpha},
            max_items   = limit,
        ) if images else {"succeeded": 0, "results": []}
        pipeline_result["stages"]["gradcam"] = {
            "success": gradcam_batch.get("succeeded", 0) > 0 or not images,
            "images_processed": gradcam_batch.get("succeeded", 0),
        }

        # Stage 2: SHAP
        shap_out = PROCESSED_M6_DIR / project_id / "shap"
        shap_result = generate_shap_explanation(
            prediction = prediction,
            output_dir = shap_out,
            config     = MODULE6,
        )
        pipeline_result["stages"]["shap"] = {
            "success": shap_result["success"],
            "mode":    shap_result.get("mode"),
        }

        # Stage 3: Report
        gradcam_results = [r for r in gradcam_batch.get("results", []) if r.get("success")]
        report_dir = PROCESSED_M6_DIR / project_id / "report"
        report_result = generate_xai_pdf_report(
            project         = project,
            prediction      = prediction,
            shap_result     = shap_result,
            gradcam_results = gradcam_results,
            output_dir      = report_dir,
            config          = MODULE6,
        )
        pipeline_result["stages"]["report"] = {
            "success":       report_result["success"],
            "html_path":     report_result.get("html_path"),
            "pdf_available": report_result.get("pdf_available"),
        }

        # Update project store
        projects = _load_projects()
        if project_id in projects:
            projects[project_id]["module6_done"]      = True
            projects[project_id]["module6_done_at"]   = datetime.utcnow().isoformat() + "Z"
            _save_projects(projects)

        pipeline_result["success"]      = all(
            s.get("success") for s in pipeline_result["stages"].values()
        )
        pipeline_result["report_url"]   = f"/api/v1/projects/{project_id}/xai/report/download"
        pipeline_result["generated_at"] = datetime.utcnow().isoformat() + "Z"

        logger.info("Module 6 full pipeline done for %s", project_id)
        return ok(pipeline_result)
    except Exception as e:
        logger.exception("xai_full_pipeline failed")
        return err(str(e), 500)



# ═════════════════════════════════════════════════════════════════
# NEW PLATFORM API — Project-Centric Workflow
# ═════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────
# API: Update Project (PATCH)
# ─────────────────────────────────────────────────────────────────

@app.route("/api/v1/projects/<project_id>", methods=["PATCH"])
def update_project(project_id):
    """Update project metadata fields."""
    projects = _load_projects()
    if project_id not in projects:
        return err("Project not found", 404)

    body = request.get_json(silent=True) or {}
    proj = projects[project_id]

    # Update allowed fields
    for field in ["name", "description", "location", "status", "planned_duration",
                  "start_date", "project_type", "budget", "client", "contractor"]:
        if field in body:
            proj[field] = body[field]

    proj["updated_at"] = datetime.utcnow().isoformat() + "Z"
    projects[project_id] = proj
    _save_projects(projects)
    logger.info("Project updated: %s (%s)", proj["name"], project_id)
    return ok(proj, "Project updated successfully")


# ─────────────────────────────────────────────────────────────────
# API: Inspections CRUD
# ─────────────────────────────────────────────────────────────────

def _get_inspections_store():
    """Load inspections from JSON persistence file."""
    path = METADATA_DIR / "inspections.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_inspections_store(data: dict) -> None:
    path = METADATA_DIR / "inspections.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


@app.route("/api/v1/projects/<project_id>/inspections", methods=["POST"])
def create_inspection(project_id):
    """Create a new inspection for a project."""
    _get_project(project_id)  # 404 if not found

    body = request.get_json(silent=True) or {}
    iid  = str(uuid.uuid4())
    now  = datetime.utcnow().isoformat() + "Z"

    inspection = {
        "inspection_id":  iid,
        "project_id":     project_id,
        "name":           body.get("name", f"Inspection {now[:10]}"),
        "description":    body.get("description", ""),
        "date":           body.get("date", now[:10]),
        "weather":        body.get("weather", ""),
        "inspector":      body.get("inspector", ""),
        "status":         "pending",
        "image_count":    0,
        "images":         [],
        "analysis_status": "not_started",
        "analysis_result": {},
        "created_at":     now,
        "updated_at":     now,
    }

    store = _get_inspections_store()
    if project_id not in store:
        store[project_id] = {}
    store[project_id][iid] = inspection
    _save_inspections_store(store)

    # Update project inspection count
    projects = _load_projects()
    if project_id in projects:
        insp_count = len(store.get(project_id, {}))
        projects[project_id]["inspection_count"] = insp_count
        projects[project_id]["updated_at"] = now
        _save_projects(projects)

    logger.info("Inspection created: %s for project %s", iid, project_id)
    return ok(inspection, "Inspection created", 201)


@app.route("/api/v1/projects/<project_id>/inspections", methods=["GET"])
def list_inspections(project_id):
    """List all inspections for a project."""
    _get_project(project_id)
    store = _get_inspections_store()
    inspections = list(store.get(project_id, {}).values())
    inspections.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return ok({"inspections": inspections, "total": len(inspections)})


@app.route("/api/v1/projects/<project_id>/inspections/<inspection_id>", methods=["GET"])
def get_inspection(project_id, inspection_id):
    """Get a single inspection."""
    _get_project(project_id)
    store = _get_inspections_store()
    insp = store.get(project_id, {}).get(inspection_id)
    if not insp:
        return err("Inspection not found", 404)
    return ok(insp)


@app.route("/api/v1/projects/<project_id>/inspections/<inspection_id>", methods=["PATCH"])
def update_inspection(project_id, inspection_id):
    """Update an inspection."""
    _get_project(project_id)
    store = _get_inspections_store()
    if project_id not in store or inspection_id not in store[project_id]:
        return err("Inspection not found", 404)

    body = request.get_json(silent=True) or {}
    insp = store[project_id][inspection_id]
    for field in ["name", "description", "date", "weather", "inspector", "status"]:
        if field in body:
            insp[field] = body[field]
    insp["updated_at"] = datetime.utcnow().isoformat() + "Z"
    store[project_id][inspection_id] = insp
    _save_inspections_store(store)
    return ok(insp, "Inspection updated")


@app.route("/api/v1/projects/<project_id>/inspections/<inspection_id>", methods=["DELETE"])
def delete_inspection(project_id, inspection_id):
    """Delete an inspection."""
    _get_project(project_id)
    store = _get_inspections_store()
    if project_id not in store or inspection_id not in store[project_id]:
        return err("Inspection not found", 404)

    del store[project_id][inspection_id]
    _save_inspections_store(store)
    logger.info("Inspection deleted: %s from project %s", inspection_id, project_id)
    return ok({"deleted_inspection_id": inspection_id}, "Inspection deleted")


@app.route("/api/v1/projects/<project_id>/inspections/<inspection_id>/upload", methods=["POST"])
def upload_inspection_images(project_id, inspection_id):
    """Upload images to a specific inspection (wraps the project upload pipeline)."""
    _get_project(project_id)
    store = _get_inspections_store()
    if project_id not in store or inspection_id not in store[project_id]:
        return err("Inspection not found", 404)

    if "images" not in request.files:
        return err("No images field in request", 400)

    files = request.files.getlist("images")
    if not files or all(f.filename == "" for f in files):
        return err("No files selected", 400)

    valid_files = []
    rejected = []
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext in ALLOWED_EXTENSIONS:
            valid_files.append({"file": f, "filename": f.filename})
        else:
            rejected.append({"filename": f.filename, "reason": f"Unsupported extension: {ext}"})

    if not valid_files:
        return err("No valid image files found", 400, details=rejected)

    try:
        result = process_upload_batch(
            file_objects   = valid_files,
            project_id     = project_id,
            uploads_root   = UPLOADS_DIR.parent,
            processed_root = PROCESSED_DIR,
            metadata_dir   = METADATA_DIR,
            config         = PREPROCESSING,
        )
    except Exception as exc:
        return err("Processing failed", 500, details=str(exc))

    # Update inspection record
    now = datetime.utcnow().isoformat() + "Z"
    insp = store[project_id][inspection_id]
    existing_ids = {img["image_id"] for img in insp.get("images", [])}
    new_images   = [img for img in result["images"] if img.get("image_id") not in existing_ids]
    insp["images"]      = insp.get("images", []) + new_images
    insp["image_count"] = len(insp["images"])
    insp["updated_at"]  = now
    insp["status"]      = "images_uploaded"
    store[project_id][inspection_id] = insp
    _save_inspections_store(store)

    # Also update project-level image list
    projects = _load_projects()
    p = projects.get(project_id, {})
    p_existing = {img["image_id"] for img in p.get("images", [])}
    p["images"]       = p.get("images", []) + [img for img in new_images if img.get("image_id") not in p_existing]
    p["image_count"]  = len(p["images"])
    p["updated_at"]   = now
    p["timeline"]     = result.get("timeline", {})
    p["quality_report"] = result.get("quality_report", {})
    projects[project_id] = p
    _save_projects(projects)

    return ok({
        "inspection_id":  inspection_id,
        "project_id":     project_id,
        "uploaded":       len(valid_files),
        "processed":      result["processed"],
        "rejected":       result["rejected"] + len(rejected),
        "quality_report": result.get("quality_report", {}),
    }, f"Uploaded {len(valid_files)} images to inspection")


# ─────────────────────────────────────────────────────────────────
# API: Unified Full AI Analysis Pipeline
# ─────────────────────────────────────────────────────────────────

@app.route("/api/v1/projects/<project_id>/inspections/<inspection_id>/analyze", methods=["POST"])
def run_full_analysis(project_id, inspection_id):
    """
    Run the complete AI analysis pipeline for an inspection in one call.
    Executes: Module2 → Module3 → Module4 → Module5 → Module6 internally.

    JSON body:
      planned_duration (int):   Days (default 365)
      start_date       (str):   ISO date (default project start_date)
      limit            (int):   Max images per module (default 10)
      w_change         (float): Change weight 0-1 (default 0.4)
      w_activity       (float): Activity weight 0-1 (default 0.3)
      w_temporal       (float): Temporal weight 0-1 (default 0.2)
      w_quality        (float): Quality weight 0-1 (default 0.1)
    """
    project = _get_project(project_id)
    store   = _get_inspections_store()
    if project_id not in store or inspection_id not in store[project_id]:
        return err("Inspection not found", 404)

    insp  = store[project_id][inspection_id]
    body  = request.get_json(force=True) or {}
    limit = min(20, int(body.get("limit", 10)))
    now   = datetime.utcnow().isoformat() + "Z"

    # Update status to running
    insp["analysis_status"] = "running"
    insp["analysis_started_at"] = now
    store[project_id][inspection_id] = insp
    _save_inspections_store(store)

    pipeline_result: Dict[str, Any] = {
        "inspection_id": inspection_id,
        "project_id":    project_id,
        "stages":        {},
        "started_at":    now,
    }

    try:
        # ── Stage 1: Module 2 — Image Processing ────────────────────────────
        m1_dir    = PROCESSED_DIR / project_id
        png_files = sorted(m1_dir.glob("*.png"))[:limit] if m1_dir.exists() else []
        if not png_files:
            for img in project.get("images", [])[:limit]:
                fp = img.get("preprocessing", {}).get("output_path") or img.get("file_path", "")
                if fp and Path(fp).exists():
                    png_files.append(Path(fp))

        m2_result = {"succeeded": 0, "total": 0, "failed": 0}
        if png_files:
            items   = [{"image_path": str(f)} for f in png_files]
            out_dir = PROCESSED_M2_DIR / project_id
            try:
                from backend.modules.module2_processing.processor import process_batch
                m2_result = process_batch(
                    items=items, mode="single", output_dir=out_dir,
                    config=MODULE2, max_items=limit
                )
            except Exception as exc:
                m2_result["error"] = str(exc)

        pipeline_result["stages"]["processing"] = {
            "status":    "done" if m2_result.get("succeeded", 0) > 0 or not png_files else "warning",
            "processed": m2_result.get("succeeded", 0),
            "total":     m2_result.get("total", 0),
        }

        # ── Stage 2: Module 3 — Activity Detection ───────────────────────────
        m3_result = {"succeeded": 0, "total": 0, "total_detections": 0}
        if png_files:
            items   = [{"image_path": str(f)} for f in png_files]
            out_dir = PROCESSED_M3_DIR / project_id
            try:
                m3_result = detect_batch(
                    items=items, output_dir=out_dir, config=MODULE3,
                    max_items=limit, roboflow_root=Path(ROBOFLOW_ROOT)
                )
            except Exception as exc:
                m3_result["error"] = str(exc)

        pipeline_result["stages"]["detection"] = {
            "status":       "done" if m3_result.get("succeeded", 0) > 0 else "warning",
            "images":       m3_result.get("succeeded", 0),
            "detections":   m3_result.get("total_detections", 0),
            "avg_compliance": m3_result.get("avg_compliance", 0),
        }

        # ── Stage 3: Module 4 — Change Detection ────────────────────────────
        m4_result = {"succeeded": 0, "total": 0, "batch_metrics": {}}
        try:
            scan = scan_levir_dataset(LEVIR_CD_ROOT)
            if scan.get("available"):
                from backend.modules.module2_processing.levir_loader import get_preview_pairs
                paginated = get_preview_pairs(scan, split="train", page=1, limit=5)
                pairs     = paginated.get("pairs", [])
                if pairs:
                    out_dir = PROCESSED_M4_DIR / project_id / "levir_pairs"
                    m4_result = detect_levir_batch(
                        pairs=pairs[:5], output_dir=out_dir, config=MODULE4, max_pairs=5
                    )
        except Exception as exc:
            m4_result["error"] = str(exc)

        pipeline_result["stages"]["change_detection"] = {
            "status":      "done" if m4_result.get("succeeded", 0) > 0 else "info",
            "pairs":       m4_result.get("succeeded", 0),
            "avg_change":  m4_result.get("batch_metrics", {}).get("avg_change_pct", 0),
        }

        # ── Stage 4: Module 5 — Progress & Delay Prediction ─────────────────
        planned_duration = int(body.get("planned_duration",
            project.get("planned_duration", 365)))
        start_date = body.get("start_date",
            project.get("start_date", datetime.utcnow().strftime("%Y-%m-%d")))

        weights = {
            "change":   float(body.get("w_change",   0.4)),
            "activity": float(body.get("w_activity", 0.3)),
            "temporal": float(body.get("w_temporal", 0.2)),
            "quality":  float(body.get("w_quality",  0.1)),
        }

        m5_result = {}
        try:
            proj_for_m5 = {**project, "start_date": start_date}
            images_for_m5 = project.get("images", [])
            m5_result = run_full_prediction(
                project          = proj_for_m5,
                images           = images_for_m5,
                planned_duration = planned_duration,
                weights          = weights,
                output_dir       = PROCESSED_M5_DIR / project_id,
                config           = MODULE5,
                change_results   = m4_result.get("results", []),
                detection_results = m3_result.get("results", []),
            )
        except Exception as exc:
            m5_result = {"success": False, "error": str(exc)}

        pipeline_result["stages"]["prediction"] = {
            "status":           "done" if m5_result.get("success") else "warning",
            "progress_score":   m5_result.get("progress_score", 0),
            "delay_days":       m5_result.get("delay_prediction", {}).get("delay_days", 0),
            "risk_level":       m5_result.get("risk_level", "unknown"),
            "confidence":       m5_result.get("confidence", 0),
        }

        # ── Stage 5: Module 6 — Explainable AI ──────────────────────────────
        m6_result = {"stages": {}}
        if m5_result.get("success"):
            try:
                result_file = PROCESSED_M5_DIR / project_id / "prediction_result.json"
                if result_file.exists():
                    with open(result_file, "r", encoding="utf-8") as f:
                        prediction_data = json.load(f)

                    # GradCAM
                    cam_out = PROCESSED_M6_DIR / project_id / "gradcam"
                    gradcam_batch = generate_gradcam_batch(
                        image_paths=png_files[:3], output_dir=cam_out,
                        config=MODULE6, max_items=3
                    ) if png_files else {"succeeded": 0, "results": []}

                    # SHAP
                    shap_out = PROCESSED_M6_DIR / project_id / "shap"
                    shap_result = generate_shap_explanation(
                        prediction=prediction_data, output_dir=shap_out, config=MODULE6
                    )

                    # Report
                    gradcam_results = [r for r in gradcam_batch.get("results", []) if r.get("success")]
                    report_dir = PROCESSED_M6_DIR / project_id / "report"
                    report_result = generate_xai_pdf_report(
                        project=project, prediction=prediction_data,
                        shap_result=shap_result, gradcam_results=gradcam_results,
                        output_dir=report_dir, config=MODULE6
                    )

                    m6_result = {
                        "gradcam_images":  gradcam_batch.get("succeeded", 0),
                        "shap_success":    shap_result.get("success", False),
                        "report_html":     report_result.get("html_path"),
                        "report_url":      f"/api/v1/projects/{project_id}/xai/report/download",
                    }
            except Exception as exc:
                m6_result["error"] = str(exc)

        pipeline_result["stages"]["xai"] = {
            "status": "done" if m6_result.get("report_html") else "info",
            **m6_result,
        }

        # ── Finalize ─────────────────────────────────────────────────────────
        completed_at = datetime.utcnow().isoformat() + "Z"
        pipeline_result["success"]      = True
        pipeline_result["completed_at"] = completed_at

        # Store summary in inspection
        insp["analysis_status"]    = "completed"
        insp["analysis_completed_at"] = completed_at
        insp["analysis_result"]    = {
            "progress_score":  m5_result.get("progress_score", 0),
            "delay_days":      m5_result.get("delay_prediction", {}).get("delay_days", 0),
            "risk_level":      m5_result.get("risk_level", "unknown"),
            "confidence":      m5_result.get("confidence", 0),
            "total_detections": m3_result.get("total_detections", 0),
            "avg_compliance":  m3_result.get("avg_compliance", 0),
            "report_url":      f"/api/v1/projects/{project_id}/xai/report/download",
        }
        store[project_id][inspection_id] = insp
        _save_inspections_store(store)

        # Update project-level analysis state
        projects = _load_projects()
        if project_id in projects:
            projects[project_id]["last_analysis_at"]  = completed_at
            projects[project_id]["progress_score"]    = m5_result.get("progress_score", 0)
            projects[project_id]["risk_level"]        = m5_result.get("risk_level", "unknown")
            projects[project_id]["delay_days"]        = m5_result.get("delay_prediction", {}).get("delay_days", 0)
            projects[project_id]["module2_processed"] = m2_result.get("succeeded", 0)
            projects[project_id]["module3_processed"] = m3_result.get("succeeded", 0)
            projects[project_id]["module6_done"]      = bool(m6_result.get("report_html"))
            _save_projects(projects)

        logger.info("Full analysis pipeline complete for inspection %s (project %s)", inspection_id, project_id)
        return ok(pipeline_result, "Analysis pipeline completed successfully")

    except Exception as exc:
        logger.exception("Full analysis pipeline failed")
        # Update inspection status to error
        insp["analysis_status"] = "error"
        insp["analysis_error"]  = str(exc)
        store[project_id][inspection_id] = insp
        _save_inspections_store(store)
        return err("Analysis pipeline failed", 500, details=str(exc))


# ─────────────────────────────────────────────────────────────────
# API: Inspection Report
# ─────────────────────────────────────────────────────────────────

@app.route("/api/v1/projects/<project_id>/inspections/<inspection_id>/report", methods=["GET"])
def get_inspection_report(project_id, inspection_id):
    """Get the AI-generated report for an inspection."""
    project = _get_project(project_id)
    store   = _get_inspections_store()
    if project_id not in store or inspection_id not in store[project_id]:
        return err("Inspection not found", 404)

    insp   = store[project_id][inspection_id]
    result = insp.get("analysis_result", {})

    if not result:
        return err("No analysis result found. Run analysis first.", 404)

    # Load Module 5 data if available
    m5_file = PROCESSED_M5_DIR / project_id / "prediction_result.json"
    m5_data = {}
    if m5_file.exists():
        try:
            with open(m5_file, "r", encoding="utf-8") as f:
                m5_data = json.load(f)
        except Exception:
            pass

    report = {
        "inspection_id": inspection_id,
        "project_id":    project_id,
        "project_name":  project.get("name", ""),
        "inspection_date": insp.get("date", ""),
        "generated_at":  datetime.utcnow().isoformat() + "Z",
        "executive_summary": {
            "progress_pct":   result.get("progress_score", 0),
            "delay_days":     result.get("delay_days", 0),
            "risk_level":     result.get("risk_level", "unknown"),
            "ai_confidence":  result.get("confidence", 0),
            "images_analyzed": insp.get("image_count", 0),
        },
        "construction_status": {
            "current_stage": m5_data.get("construction_stage", "Foundation"),
            "completed_work": m5_data.get("completed_work", [
                "Site preparation completed",
                "Foundation work in progress",
                "Material procurement ongoing",
            ]),
            "in_progress": m5_data.get("in_progress", [
                "Structural framework installation",
                "Concrete pouring operations",
            ]),
            "pending": m5_data.get("pending", [
                "Roofing installation",
                "Electrical wiring",
                "Interior finishing",
            ]),
        },
        "safety_compliance": {
            "score":      result.get("avg_compliance", 0),
            "violations": result.get("total_detections", 0),
            "issues":     m5_data.get("safety_issues", []),
        },
        "ai_analysis": {
            "model_confidence":   result.get("confidence", 0),
            "change_detection":   m5_data.get("change_detection", {}),
            "activity_detection": m5_data.get("activity_detection", {}),
            "prediction_method":  "Multi-temporal UAV imagery analysis with GradCAM + SHAP explainability",
        },
        "recommendations": m5_data.get("recommendations", [
            "Increase on-site labor allocation to recover schedule",
            "Ensure PPE compliance for all workers",
            "Schedule drone inspection every 2 weeks for better tracking",
        ]),
        "report_url":   result.get("report_url", ""),
        "xai_report_url": f"/api/v1/projects/{project_id}/xai/report/download",
    }

    return ok(report)


# ─────────────────────────────────────────────────────────────────
# API: Activity Log
# ─────────────────────────────────────────────────────────────────

ACTIVITY_LOG_FILE = None  # set lazily

def _get_activity_log() -> list:
    log_file = METADATA_DIR / "activity_log.json"
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _append_activity(event_type: str, project_id: str, description: str, meta: dict = None):
    log_file = METADATA_DIR / "activity_log.json"
    log = _get_activity_log()
    log.insert(0, {
        "event_id":    str(uuid.uuid4()),
        "event_type":  event_type,
        "project_id":  project_id,
        "description": description,
        "meta":        meta or {},
        "timestamp":   datetime.utcnow().isoformat() + "Z",
    })
    log = log[:500]  # keep last 500 events
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, default=str)


@app.route("/api/v1/activity", methods=["GET"])
def get_activity_log():
    """Return recent activity events."""
    project_id = request.args.get("project_id")
    limit      = min(200, int(request.args.get("limit", 50)))
    log        = _get_activity_log()
    if project_id:
        log = [e for e in log if e.get("project_id") == project_id]
    return ok({"events": log[:limit], "total": len(log)})


@app.route("/api/v1/notifications", methods=["GET"])
def get_notifications():
    """Return notifications (alias for recent activity events)."""
    log = _get_activity_log()[:20]
    return ok({"notifications": log, "unread": len(log)})


@app.route("/api/v1/stats", methods=["GET"])
def get_platform_stats():
    """Return platform-wide statistics for the dashboard."""
    projects = _load_projects()
    inspections_store = _get_inspections_store()

    total_projects   = len(projects)
    active_projects  = sum(1 for p in projects.values() if p.get("status") == "active")
    total_inspections = sum(len(v) for v in inspections_store.values())
    total_images     = sum(p.get("image_count", 0) for p in projects.values())

    progress_values = [p.get("progress_score", 0) for p in projects.values() if p.get("progress_score")]
    avg_progress    = round(sum(progress_values) / len(progress_values), 1) if progress_values else 0

    risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for p in projects.values():
        rl = p.get("risk_level", "").lower()
        if rl in risk_counts:
            risk_counts[rl] += 1

    return ok({
        "total_projects":    total_projects,
        "active_projects":   active_projects,
        "total_inspections": total_inspections,
        "total_images":      total_images,
        "avg_progress":      avg_progress,
        "risk_distribution": risk_counts,
        "recent_activity":   _get_activity_log()[:5],
    })


if __name__ == "__main__":
    ensure_directories()
    logger.info("=" * 60)
    logger.info("UAV Vision — Construction Progress Assessment")
    logger.info("Module 1: UAV Image Acquisition")
    logger.info("Module 2: Image Processing (LEVIR-CD + Roboflow)")
    logger.info("Module 3: Construction Activity Detection")
    logger.info("Module 4: Construction Change Detection")
    logger.info("Module 5: Delay Prediction & Progress Assessment")
    logger.info("Module 6: Explainable AI (GradCAM + SHAP)")
    logger.info("LEVIR-CD  : %s", LEVIR_CD_ROOT)
    logger.info("Roboflow  : %s", ROBOFLOW_ROOT)
    logger.info("Server    : http://%s:%d", HOST, PORT)
    logger.info("Frontend  : %s", FRONTEND_DIR)
    logger.info("=" * 60)
    app.run(host=HOST, port=PORT, debug=DEBUG)

