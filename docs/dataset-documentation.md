# Dataset Integration & Pipeline Documentation

This document describes how raw aerial datasets (LEVIR-CD and Roboflow Construction) are parsed, validated, and processed within the UAV Construction Progress Monitoring system.

---

## 1. Supported Datasets

### A. LEVIR-CD Dataset
- **Format**: PNG Image pairs (`A/` and `B/`) + Binary label masks (`label/`).
- **Resolution**: 1024 × 1024 pixels.
- **Loader Module**: `backend/modules/module2_processing/levir_loader.py`.
- **API Endpoints**:
  - `GET /api/v1/datasets/levir` — Scans dataset folder structure and counts total pairs.
  - `GET /api/v1/datasets/levir/pairs` — Paginated list of image pairs with preview paths.
  - `POST /api/v1/datasets/levir/process` — Runs feature extraction and change detection on a batch of LEVIR pairs.

### B. Roboflow Site Safety & Equipment Dataset
- **Format**: RGB images + YOLO annotation text files (`labels/*.txt` format `class_id x_center y_center width height`).
- **Loader Module**: `backend/modules/module2_processing/roboflow_loader.py`.
- **Classes Supported**:
  - `0`: Worker
  - `1`: Hardhat
  - `2`: Safety Vest
  - `3`: Excavator
  - `4`: Crane
  - `5`: Concrete Truck
  - `6`: Scaffolding
  - `7`: Raw Materials
- **API Endpoints**:
  - `GET /api/v1/datasets/roboflow` — Scans train/val/test splits and class distribution.
  - `GET /api/v1/datasets/roboflow/images` — Paginated image list with class labels.

---

## 2. UAV Image Upload & Preprocessing Pipeline

When raw UAV images are uploaded via `POST /api/v1/projects/<id>/upload`:

1. **Validation (`backend/modules/module1_acquisition/validator.py`)**:
   - Format check (`.png`, `.jpg`, `.jpeg`, `.tiff`).
   - File size validation (Max 100 MB per file, Max 500 MB per batch).
   - Duplicate detection via MD5 checksum hashing.
2. **Metadata Extraction (`backend/modules/module1_acquisition/metadata.py`)**:
   - EXIF parsing for `DateTimeOriginal`, Camera Make/Model, Focal Length, ISO.
   - GPS coordinate extraction (Latitude, Longitude, Altitude).
3. **Quality Assessment (`backend/modules/module1_acquisition/quality.py`)**:
   - Blur detection using Laplacian variance (threshold > 100.0).
   - Exposure evaluation (brightness range 30–225).
   - Contrast calculation.
4. **Preprocessing (`backend/modules/module1_acquisition/preprocessor.py`)**:
   - CLAHE (Contrast Limited Adaptive Histogram Equalization) contrast enhancement.
   - Standardized resizing to 1024 × 1024 pixels with aspect ratio preservation and black padding.
   - Gaussian denoising and normalization.
5. **Temporal Sorting (`backend/modules/module1_acquisition/temporal.py`)**:
   - Flight timeline sequencing ordered chronologically by EXIF timestamp.
