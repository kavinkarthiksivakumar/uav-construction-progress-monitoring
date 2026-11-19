"""
Central Configuration for UAV Vision
AI-Powered Construction Monitoring and Progress Assessment System

Dataset locations are configured via environment variables in .env:
  LEVIR_CD_PATH  : Path to LEVIR-CD+ bi-temporal change detection dataset
                   Structure: {train,test}/{A,B,label}/
  SYSU_CD_PATH   : Path to SYSU-CD bi-temporal change detection dataset
                   Structure: {train,val,test}/{time1,time2,label}/
  ROBOFLOW_PATH  : Path to Roboflow Construction Site Safety dataset
                   Structure: {train,valid,test}/{images,labels}/ + data.yaml
                   Classes (10): Hardhat, Mask, NO-Hardhat, NO-Mask,
                                 NO-Safety Vest, Person, Safety Cone,
                                 Safety Vest, machinery, vehicle

Paths may be relative (resolved from project root) or absolute.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ─────────────────────────────────────────────────────────────────
# Base Paths
# ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # project root

UPLOADS_DIR      = BASE_DIR / "uploads" / "raw"
PROCESSED_DIR    = BASE_DIR / "processed" / "module1"
PROCESSED_M2_DIR = BASE_DIR / "processed" / "module2"
PROCESSED_M3_DIR = BASE_DIR / "processed" / "module3"
PROCESSED_M4_DIR = BASE_DIR / "processed" / "module4"
PROCESSED_M5_DIR = BASE_DIR / "processed" / "module5"
PROCESSED_M6_DIR = BASE_DIR / "processed" / "module6"
PROCESSED_M7_DIR = BASE_DIR / "processed" / "module7_decision"
METADATA_DIR     = BASE_DIR / "metadata"
LOGS_DIR         = BASE_DIR / "logs"
REPORTS_DIR      = BASE_DIR / "reports"
DATASETS_DIR     = BASE_DIR / "datasets"
MODELS_DIR       = BASE_DIR / "models"
FRONTEND_DIR     = BASE_DIR / "frontend"


def _resolve_dataset_path(env_key: str, fallback: Path) -> Path:
    """
    Resolve a dataset path from an environment variable.
    Supports both absolute paths and relative paths (resolved from BASE_DIR).
    Falls back to ``fallback`` if the env var is not set or is empty.
    """
    raw = os.getenv(env_key, "").strip()
    if not raw:
        return fallback
    p = Path(raw)
    if p.is_absolute():
        return p
    # Relative path — resolve from project root
    return (BASE_DIR / p).resolve()


# ─────────────────────────────────────────────────────────────────
# External Dataset Paths (configured via environment variables)
# ─────────────────────────────────────────────────────────────────
LEVIR_CD_ROOT = _resolve_dataset_path(
    "LEVIR_CD_PATH",
    DATASETS_DIR / "levir" / "LEVIR-CD+" / "LEVIR-CD+",
)

SYSU_CD_ROOT = _resolve_dataset_path(
    "SYSU_CD_PATH",
    DATASETS_DIR / "sysu",
)

ROBOFLOW_ROOT = _resolve_dataset_path(
    "ROBOFLOW_PATH",
    DATASETS_DIR / "roboflow",
)

# Optional model weight paths
YOLO_MODEL_PATH            = os.getenv("YOLO_MODEL_PATH", "")
CHANGE_DETECTION_MODEL_PATH = os.getenv("CHANGE_DETECTION_MODEL_PATH", "")

# ─────────────────────────────────────────────────────────────────
# Flask Settings
# ─────────────────────────────────────────────────────────────────
SECRET_KEY          = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
DEBUG               = os.getenv("DEBUG", "false").lower() == "true"   # Default OFF for security
HOST                = os.getenv("HOST", "0.0.0.0")
PORT                = int(os.getenv("PORT", 5000))
MAX_CONTENT_LENGTH  = int(os.getenv("MAX_CONTENT_LENGTH", 500 * 1024 * 1024))  # 500 MB

# ─────────────────────────────────────────────────────────────────
# Upload Settings
# ─────────────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS  = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
MAX_FILE_SIZE_MB    = int(os.getenv("MAX_FILE_SIZE_MB", 100))  # 100 MB per file
MAX_FILES_PER_BATCH = int(os.getenv("MAX_FILES_PER_BATCH", 200))

# ─────────────────────────────────────────────────────────────────
# Image Quality Thresholds
# ─────────────────────────────────────────────────────────────────
QUALITY = {
    "blur_threshold":        100.0,   # Laplacian variance — below = blurry
    "brightness_min":        30,      # Too dark
    "brightness_max":        225,     # Too bright / overexposed
    "contrast_min":          20,      # Too low contrast
    "min_resolution_px":     100,     # Min width and height in pixels
    "accept_score_threshold": 60.0,   # Overall score to accept image
    "weights": {
        "blur":       0.35,
        "brightness": 0.25,
        "contrast":   0.25,
        "resolution": 0.15,
    }
}

# ─────────────────────────────────────────────────────────────────
# Preprocessing Settings
# ─────────────────────────────────────────────────────────────────
PREPROCESSING = {
    "target_size":        (1024, 1024),   # (width, height)
    "maintain_aspect":    True,
    "pad_color":          (0, 0, 0),      # Black padding
    "clahe_clip_limit":   2.0,
    "clahe_tile_grid":    (8, 8),
    "gaussian_kernel":    (3, 3),
    "gaussian_sigma":     0,
    "normalize":          True,
    "output_format":      "PNG",          # Lossless output
}

# ─────────────────────────────────────────────────────────────────
# Temporal Settings
# ─────────────────────────────────────────────────────────────────
TEMPORAL = {
    "exif_date_tag":   "EXIF DateTimeOriginal",
    "exif_date_fmt":   "%Y:%m:%d %H:%M:%S",
    "fallback_order":  "filename",  # filename | upload_order
}

# ─────────────────────────────────────────────────────────────────
# Dataset Paths Dictionary
# ─────────────────────────────────────────────────────────────────
DATASETS = {
    "roboflow": ROBOFLOW_ROOT,
    "levir":    LEVIR_CD_ROOT,
    "sysu":     SYSU_CD_ROOT,
}

# ─────────────────────────────────────────────────────────────────
# Roboflow Dataset — Actual 10 Classes (from data.yaml)
# ─────────────────────────────────────────────────────────────────
# Classes indexed 0–9 as declared in data.yaml:
#   0: Hardhat, 1: Mask, 2: NO-Hardhat, 3: NO-Mask, 4: NO-Safety Vest,
#   5: Person, 6: Safety Cone, 7: Safety Vest, 8: machinery, 9: vehicle
ROBOFLOW_CLASSES = [
    "Hardhat", "Mask", "NO-Hardhat", "NO-Mask", "NO-Safety Vest",
    "Person", "Safety Cone", "Safety Vest", "machinery", "vehicle",
]
ROBOFLOW_SAFE_CLASSES  = {"Hardhat", "Safety Vest", "Mask"}
ROBOFLOW_RISK_CLASSES  = {"NO-Hardhat", "NO-Mask", "NO-Safety Vest"}
ROBOFLOW_ACTIVITY_CLASSES = {"machinery", "vehicle", "Person", "Safety Cone"}

# ─────────────────────────────────────────────────────────────────
# Module 2 Processing Settings
# ─────────────────────────────────────────────────────────────────
MODULE2 = {
    "target_size":          (512, 512),    # Standard size for CD models
    "edge_canny_low":       50,
    "edge_canny_high":      150,
    "edge_sobel_ksize":     3,
    "gabor_frequencies":    [0.1, 0.25, 0.4],
    "gabor_thetas":         [0, 45, 90, 135],
    "lbp_radius":           3,
    "lbp_points":           24,
    "color_spaces":         ["RGB", "HSV", "LAB", "GRAY"],
    "change_threshold":     30,            # Pixel diff threshold for change map
    # LEVIR-CD structure: {split}/{A,B,label}/
    "levir_splits":         ["train", "test"],
    "levir_subdirs":        ["A", "B", "label"],
    # SYSU-CD structure: {split}/{time1,time2,label}/
    "sysu_splits":          ["train", "val", "test"],
    "sysu_subdirs":         ["time1", "time2", "label"],
    # Roboflow structure: {split}/{images,labels}/
    "roboflow_classes":     ROBOFLOW_CLASSES,
    "roboflow_splits":      ["train", "valid", "test"],
    "preview_limit":        20,            # Max pairs to load for UI preview
}

# ─────────────────────────────────────────────────────────────────
# Module 3 Processing Settings — 10-class Roboflow dataset
# ─────────────────────────────────────────────────────────────────
MODULE3 = {
    # Actual 10 classes from datasets/roboflow/data.yaml
    "classes":          ROBOFLOW_CLASSES,
    "safe_classes":     list(ROBOFLOW_SAFE_CLASSES),
    "risk_classes":     list(ROBOFLOW_RISK_CLASSES),
    "activity_classes": list(ROBOFLOW_ACTIVITY_CLASSES),
    "conf_threshold":   0.40,              # Minimum detection confidence
    "iou_threshold":    0.45,              # NMS IoU threshold
    # Set to .pt path to enable real YOLOv8 inference
    "model_path":       YOLO_MODEL_PATH if YOLO_MODEL_PATH else None,
    "save_viz":         True,              # Save annotated visualization PNG
    "max_batch_size":   50,               # Max images per batch call
    "compliance_threshold": 0.5,          # Site compliance fraction threshold
    "roboflow_splits":  ["train", "valid", "test"],
}

# ─────────────────────────────────────────────────────────────────
# Module 4 Change Detection Settings
# ─────────────────────────────────────────────────────────────────
MODULE4 = {
    "target_size":       (512, 512),       # Resize both images before differencing
    "threshold_method":  "otsu",           # 'otsu' | 'adaptive' | 'fixed'
    "fixed_threshold":   30,               # used only when method == 'fixed'
    "min_change_area":   100,              # min pixel area to count as a region
    "morph_kernel":      5,                # morphological closing kernel size
    "blur_sigma":        1.5,              # Gaussian blur sigma
    "save_overlay":      True,             # save annotated overlay PNG
    "save_mask":         True,             # save binary change mask PNG
    # Set to .onnx/.pth to use a trained deep change detection model
    "model_path":        CHANGE_DETECTION_MODEL_PATH if CHANGE_DETECTION_MODEL_PATH else None,
    "max_batch_size":    20,               # max pairs per API call
    # LEVIR-CD: train + test splits (no official val split)
    "levir_splits":      ["train", "test"],
    # SYSU-CD: train + val + test splits
    "sysu_splits":       ["train", "val", "test"],
    "evaluate_gt":       True,             # compute IoU/F1 against GT masks when available
}

# ─────────────────────────────────────────────────────────────────
# Module 5 Delay Prediction & Progress Assessment Settings
# ─────────────────────────────────────────────────────────────────
MODULE5 = {
    # Weights for composite progress score (must sum to 1.0)
    # Methodology: weighted linear combination of sub-scores derived
    # from Module 1–4 outputs. Each weight reflects the relative
    # evidential strength of that signal for construction progress.
    "weights": {
        "change":   0.40,   # Module 4 change detection contribution (strongest signal)
        "activity": 0.30,   # Module 3 activity detection contribution
        "temporal": 0.20,   # Module 1 temporal coverage contribution
        "quality":  0.10,   # Module 1 image quality contribution
    },
    # Default planned project duration when not specified by user
    "default_planned_duration_days": 365,
    # Risk level thresholds in delay days
    "risk_thresholds": {
        "at_risk":  10,
        "delayed":  20,
        "critical": 35,
    },
    # Progress status labels based on deviation %
    "status_thresholds": {
        "ahead":    10,    # deviation >= +10% → Ahead of Schedule
        "on_track": 0,     # deviation >= 0%  → On Schedule
        "at_risk":  -10,   # deviation >= -10% → At Risk
        # below -10% → Delayed
    },
}

# ─────────────────────────────────────────────────────────────────
# Module 6 Explainable AI Settings
# ─────────────────────────────────────────────────────────────────
MODULE6 = {
    "gradcam_alpha":        0.55,       # Blend factor for GradCAM overlay
    "gradcam_threshold":    0.60,       # Activation threshold for high-activity mask
    "gradcam_model_path":   None,       # Path to .pt PyTorch model (optional)
    "shap_mode":            "auto",     # 'xgboost' | 'simulation' | 'auto'
    "max_gradcam_images":   10,         # Max images for batch GradCAM
    "generate_pdf":         True,       # Attempt PDF generation
    "report_title":         "XAI Explainability Report — Construction Progress Assessment",
}

# ─────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────
LOGGING = {
    "log_dir":         str(LOGS_DIR),
    "max_bytes":       10 * 1024 * 1024,  # 10 MB
    "backup_count":    5,
    "console_level":   "INFO",
    "file_level":      "DEBUG",
}

# ─────────────────────────────────────────────────────────────────
# API Settings
# ─────────────────────────────────────────────────────────────────
API = {
    "prefix":   "/api/v1",
    "version":  "1.0.0",
    "title":    "UAV Construction Progress Assessment API",
}


def ensure_directories():
    """Create all required directories if they do not exist."""
    dirs = [
        UPLOADS_DIR, PROCESSED_DIR, PROCESSED_M2_DIR, PROCESSED_M3_DIR, PROCESSED_M4_DIR,
        PROCESSED_M5_DIR, PROCESSED_M6_DIR, PROCESSED_M7_DIR,
        METADATA_DIR, LOGS_DIR, REPORTS_DIR, MODELS_DIR,
        BASE_DIR / "modules",
        BASE_DIR / "tests",
        BASE_DIR / "utils",
        BASE_DIR / "config",
        BASE_DIR / "processed" / "module2",
        BASE_DIR / "processed" / "module3",
        BASE_DIR / "processed" / "module4",
        BASE_DIR / "processed" / "module5",
        BASE_DIR / "processed" / "module6",
        REPORTS_DIR / "evaluation",
        REPORTS_DIR / "project_summaries",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
