# End-to-End Technical Workflow Specification

This document details the step-by-step automated analysis pipeline implemented in the **UAV Construction Progress Monitoring & Decision-Support System**.

---

## 🏗️ Technical Pipeline Overview

```
UAV Images
    ↓
Image Validation
    ↓
Preprocessing
    ↓
Feature Extraction
    ↓
Construction Activity / Stage Detection
    ↓
Multi-Temporal Change Detection
    ↓
Progress Estimation
    ↓
Delay Prediction
    ↓
Explainable AI
    ↓
Construction Monitoring Results
    ↓
Reports & Recommendations
```

---

## 📋 Step-by-Step Pipeline Specifications

### 1. UAV Images Ingestion
- Ingests raw aerial survey images (`.jpg`, `.jpeg`, `.png`, `.tiff`) captured by drone survey flights.
- API Endpoint: `POST /api/v1/projects/<id>/upload`.

### 2. Image Validation (`backend/modules/module1_acquisition/validator.py`)
- Verifies format validity, batch size caps, and individual file size limits.
- Performs MD5 checksum hashing for duplicate file detection.
- Extracts EXIF tags (`DateTimeOriginal`, Focal Length, Camera Model) and GPS coordinates (Latitude, Longitude, Altitude).
- Assesses image quality using Laplacian blur variance and exposure/contrast scoring.

### 3. Preprocessing (`backend/modules/module1_acquisition/preprocessor.py`)
- Applies Contrast Limited Adaptive Histogram Equalization (CLAHE) to balance lighting.
- Resizes imagery to a uniform 1024 × 1024 resolution while preserving aspect ratio with padding.
- Performs Gaussian smoothing and color space normalization.

### 4. Feature Extraction & Alignment (`backend/modules/module2_processing/processor.py`)
- Aligns bi-temporal flight surveys (Time T1 and Time T2).
- Extracts deep spatial feature representations using a Siamese feature extractor network.
- Integrates LEVIR-CD and Roboflow benchmark datasets.

### 5. Construction Activity & Stage Detection (`backend/modules/module3_detection/detector.py`)
- Runs YOLOv8 deep learning model to detect construction site machinery (excavators, cranes, concrete trucks), workers, scaffolding, and safety PPE (hardhats, safety vests).
- Classifies the active construction stage based on detected component densities.
- Generates labeled bounding box overlays.

### 6. Multi-Temporal Change Detection (`backend/modules/module4_change/change_detector.py`)
- Calculates bi-temporal change masks comparing pre-construction (T1) and post-construction (T2) visual features.
- Computes quantitative change metrics: Intersection over Union (IoU), Precision, Recall, and Change Surface Area Percentage.

### 7. Progress Estimation (`backend/modules/module5_prediction/predictor.py`)
- Computes overall construction progress score ($0-100\%$) based on detected structural progress vs baseline schedule milestones.
- Fits sigmoidal cumulative progress S-Curves (`s_curve.py`) to quantify schedule deviation.

### 8. Delay Prediction (`backend/modules/module5_prediction/predictor.py`)
- Evaluates progress velocity, labor activity, and site change rates to forecast project completion date delays.
- Assigns delay risk classifications (Low, Medium, High Risk).

### 9. Explainable AI (`backend/modules/module6_xai/`)
- Generates Grad-CAM spatial activation heatmaps (`gradcam.py`) highlighting the exact visual image regions that influenced model decisions.
- Computes SHAP feature attribution values (`shap_explain.py`) quantifying the impact of each progress metric on delay predictions.

### 10. Construction Monitoring Results
- Consolidates progress scores, change maps, detection visualizers, delay risk forecasts, and XAI heatmaps into the Web Dashboard interface.

### 11. Reports & Recommendations (`backend/modules/module6_xai/pdf_report.py`)
- Generates automated executive PDF reports embedding Grad-CAM heatmaps, SHAP summary plots, and component progress tables.
- Provides actionable recommendations for site management.
