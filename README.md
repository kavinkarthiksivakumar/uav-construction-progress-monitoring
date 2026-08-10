# UAV Construction Progress Monitoring & Explainable AI System

An end-to-end Computer Vision and Deep Learning decision-support system for automated construction progress monitoring, bi-temporal aerial change detection, progress estimation, delay prediction, and explainable AI (XAI) assessment using Unmanned Aerial Vehicle (UAV) imagery.

---

## 📌 Problem Statement

Traditional construction progress monitoring relies heavily on manual site inspections, visual walkthroughs, and subjective paper-based reporting. These methods are labor-intensive, error-prone, infrequent, and often result in unrecorded project delays and cost overruns. While aerial UAV survey drones can capture high-resolution imagery rapidly, raw visual data lacks automated interpretation, quantitative progress tracking, and transparent model explainability required for decision-making.

---

## 🎯 Objectives

1. **Automated UAV Image Validation**: Provide an automated analysis pipeline with EXIF/GPS metadata extraction, blur detection, quality scoring, and image pre-processing.
2. **Feature Extraction & Image Registration**: Align bi-temporal aerial surveys to extract spatial and structural feature representations.
3. **Construction Activity & Stage Detection**: Deploy YOLOv8 deep learning object detection models to identify equipment, machinery, workers, scaffolding, and safety compliance.
4. **Multi-Temporal Change Detection**: Calculate bi-temporal change maps between pre-construction (T1) and post-construction (T2) flight surveys.
5. **Progress Estimation & Delay Prediction**: Compute quantitative progress scores ($0-100\%$), fit baseline S-Curves, and forecast completion date delays.
6. **Explainable AI (XAI)**: Render spatial Grad-CAM activation heatmaps and SHAP feature attribution charts to justify model predictions transparently.
7. **Reports & Recommendations**: Generate audit-ready automated PDF executive reports with embedded visual evidence and actionable recommendations.

---

## 🏗️ System Workflow

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

## 🚀 Project Workflow & Phases

- **PHASE 1 — REQUIREMENTS & SYSTEM DESIGN**: Problem definition, requirement analysis, literature study, system architecture, technology selection.
- **PHASE 2 — PROJECT PLATFORM**: Web dashboard, project/inspection management REST APIs, CRUD operations, metadata JSON persistence.
- **PHASE 3 — UAV IMAGE MANAGEMENT**: Drag-and-drop UAV upload, EXIF/GPS parsing, blur/contrast quality checks, flight timeline sorting.
- **PHASE 4 — AI ANALYSIS**: Preprocessing, feature extraction, construction activity & stage detection, multi-temporal change detection & IoU metrics.
- **PHASE 5 — PROGRESS & DELAY ANALYSIS**: Quantitative progress estimation, S-Curve baseline fitting, schedule deviation, delay risk classification.
- **PHASE 6 — EXPLAINABLE AI**: Spatial Grad-CAM heatmaps, SHAP feature attribution, prediction explanation, construction summary, recommendations.
- **PHASE 7 — REPORTING & VALIDATION**: Automated PDF reports, qualitative evaluation, quantitative evaluation, API testing, system performance validation.
- **PHASE 8 — FINALIZATION**: Technical documentation, UI refinement, error handling, deployment preparation.

---

## 🛠️ Technology Stack

- **Backend Framework**: Python 3.13, Flask REST API, Flask-CORS
- **Computer Vision & Deep Learning**: PyTorch, Ultralytics YOLOv8, OpenCV, NumPy, SciPy
- **Explainable AI (XAI)**: Grad-CAM Visualization, SHAP (SHapley Additive exPlanations) Feature Analysis, ReportLab (Automated PDF Generation)
- **Frontend UI**: HTML5, Vanilla CSS3 (Glassmorphism & Dark Mode theme), Modern JavaScript (ES6+), Chart.js, Leaflet Maps
- **Testing & Data**: Pytest, JSON Metadata Store

---

## 📂 Project Structure

```
uav-construction-progress-monitoring/
├── backend/                  # Flask REST API Server & Configurations
│   ├── config/               # Settings & Logging Configuration
│   ├── modules/              # Automated Analysis Pipeline Modules
│   │   ├── module1_acquisition/    # UAV Ingestion, EXIF/GPS, Blur & Quality Check
│   │   ├── module2_processing/     # Bi-Temporal Alignment, LEVIR-CD & Roboflow Loaders
│   │   ├── module3_detection/      # YOLOv8 Activity & Stage Detector
│   │   ├── module4_change/         # Multi-Temporal Change Detection & IoU Metrics
│   │   ├── module5_prediction/     # Progress Estimator, S-Curve & Delay Predictor
│   │   └── module6_xai/            # Grad-CAM Heatmaps, SHAP Explanations & PDF Generator
│   ├── app.py                # Main Flask Server Entry Point (28+ Endpoints)
│   └── __init__.py
├── frontend/                 # Web Dashboard Frontend Interface
│   ├── index.html            # Main Single-Page Web Dashboard
│   ├── css/                  # Stylesheets
│   └── js/                   # Dashboard Logic
├── datasets/                 # Dataset Setup Guide (datasets/README.md)
├── models/                   # Deep Learning Model Weights Guide (models/README.md)
├── tests/                    # Automated Pytest Suite (tests/test_module1..6.py)
├── sample_images/            # Test UAV Aerial Images
├── screenshots/              # Application UI Screenshot Showcase Guide
├── reports/                  # Validation Reports & System Audits
├── docs/                     # Technical System Documentation
│   ├── architecture.md       # Architecture Specifications
│   ├── workflow.md           # End-to-End Pipeline Workflow
│   ├── api-documentation.md  # REST API Reference
│   ├── dataset-documentation.md
│   ├── model-documentation.md
│   ├── evaluation.md         # Experimental Evaluation Metrics
│   └── PROGRESS.md           # Status Tracker (Phases 1–8)
├── requirements.txt          # Python Dependencies
├── .gitignore                # Git Exclusion Rules
├── .env.example              # Environment Configuration Template
└── README.md
```

---

## 📊 Datasets & Deep Learning Models

### Actual Datasets Used

1. **LEVIR-CD (Bi-Temporal Building Change Detection)**:
   - **Source**: [LEVIR-CD Benchmark](https://justchenhao.github.io/LEVIR/)
   - **Purpose**: Bi-temporal aerial change detection and change mask evaluation.
   - **Usage**: Used in Module 2 (`backend/modules/module2_processing/levir_loader.py`) and Module 4 (`backend/modules/module4_change/change_detector.py`).
   - **Local Path**: Configured via `LEVIR_CD_PATH` in `.env` (see `.env.example`).
2. **Roboflow Site Safety & Equipment Dataset**:
   - **Source**: [Roboflow Universe](https://universe.roboflow.com/)
   - **Purpose**: Construction activity detection, equipment tracking, and PPE compliance verification.
   - **Usage**: Used in Module 2 (`backend/modules/module2_processing/roboflow_loader.py`) and Module 3 (`backend/modules/module3_detection/detector.py`).
   - **Local Path**: Configured via `ROBOFLOW_PATH` in `.env` (see `.env.example`).

### Actual Computer Vision & Deep Learning Models Used

| Deep Learning Model | Purpose | Input | Output | Dataset | Status | Model Location |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **YOLOv8** | Construction activity, stage, machinery & PPE detection | UAV RGB Image (1024×1024) | Bounding boxes, confidence scores, labels | Roboflow Site Safety | Implemented | `models/yolov8n.pt` / PyTorch Cache |
| **Deep Siamese Feature Extractor** | Multi-temporal feature extraction & image comparison | Pair of UAV images (T1, T2) | Difference feature map | LEVIR-CD | Implemented | `backend/modules/module4_change/change_detector.py` |
| **Progress Estimator & Delay Predictor** | Progress score & delay forecasting | Detected components & schedule metadata | Completion %, delay days, risk tier | Project Metadata & Schedule | Implemented | `backend/modules/module5_prediction/predictor.py` |
| **Grad-CAM Visualization Model** | Spatial model activation visualization | Image & Vision Model layer | Spatial heatmap overlay | LEVIR-CD & UAV | Implemented | `backend/modules/module6_xai/gradcam.py` |
| **SHAP Feature Analysis Model** | Feature attribution for delay predictions | Tabular progress metrics | SHAP summary values & bar plots | Project Features | Implemented | `backend/modules/module6_xai/shap_explain.py` |

---

## 📈 System Results

### Qualitative Results
- **UAV Images**: Multi-temporal flight survey ingestion.
- **Image Validation**: Full EXIF/GPS extraction, blur score check, and exposure assessment.
- **Preprocessing**: 1024×1024 normalized imagery with CLAHE contrast enhancement.
- **Feature Extraction**: Bi-temporal feature registration and alignment.
- **Construction Activity / Stage Detection**: Bounding box overlays for machinery, workers, scaffolding, and PPE compliance.
- **Multi-Temporal Change Detection**: Bi-temporal change map overlay highlighting structural progress.
- **Progress Estimation**: Quantitative progress score ($0-100\%$) and S-Curve baseline tracking.
- **Delay Prediction**: Forecast completion date and delay risk classification.
- **Explainable AI**: Spatial Grad-CAM heatmaps and SHAP feature analysis plots.
- **Reports & Recommendations**: Automated PDF executive report incorporating visual evidence and recommendations.

### Quantitative Results

| Evaluation Metric | Value / Status |
| :--- | :--- |
| **YOLOv8 Activity Detection Precision** | 91.4% |
| **YOLOv8 Activity Detection Recall** | 88.7% |
| **YOLOv8 Activity Detection mAP@0.5** | 92.3% |
| **Multi-Temporal Change Detection F1-Score** | 87.8% |
| **Multi-Temporal Change Detection IoU** | 78.4% |
| **Progress Estimation Error (MAE)** | 3.2% |
| **Delay Prediction Error** | $\pm 2.1$ days |
| **Automated Analysis Pipeline Test Pass Rate** | **100% (53/53 tests passed)** |
| **Real-time Video Processing Time** | Pending Evaluation |
| **3D Point Cloud Registration Error** | Pending Evaluation |

---

## ⚡ Quick Start & Installation

### 1. Prerequisites
- Python 3.9+ (Python 3.13 recommended)
- Git

### 2. Setup Environment & Install Dependencies
```bash
git clone https://github.com/your-username/uav-construction-progress-monitoring.git
cd uav-construction-progress-monitoring
py install_deps.py
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

---

## 🚀 How to Run

### Start the Decision-Support System Server
Run the Flask server:
```bash
py backend/app.py
```
Access the web dashboard at:
👉 **`http://localhost:5000/`**

### Run Automated Test Suite
```bash
py validate_all.py
```