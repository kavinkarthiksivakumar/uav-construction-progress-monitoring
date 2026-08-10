# System Architecture Specification

This document presents the system architecture of the **UAV Construction Progress Monitoring & Decision-Support System**.

---

## 🏛️ System Architecture Overview

The system is structured as a decoupled, multi-tier Decision-Support Architecture comprising a Single-Page Web Frontend, a Flask REST API Gateway, an Automated Computer Vision Processing Pipeline, and a Metadata Storage Engine.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Single-Page Web Dashboard                       │
│             (HTML5 / Vanilla CSS3 / Modern JavaScript ES6+)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP REST Requests
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Flask REST API Gateway                          │
│                           (backend/app.py)                             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
┌──────────────┐             ┌──────────────┐             ┌──────────────┐
│  Module 1:   │             │  Module 2:   │             │  Module 3:   │
│ Image Ingest │             │ Image Align  │             │ YOLOv8 Site  │
│  & Validation│             │ & Loaders    │             │ Stage Detect │
└──────┬───────┘             └──────┬───────┘             └──────┬───────┘
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
┌──────────────┐             ┌──────────────┐             ┌──────────────┐
│  Module 4:   │             │  Module 5:   │             │  Module 6:   │
│ Multi-Temp   │             │ Progress &   │             │ Explainable  │
│ Change Detect│             │ Delay Model  │             │ AI (GradCAM) │
└──────┬───────┘             └──────┬───────┘             └──────┬───────┘
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        JSON Metadata Database                          │
│                 (metadata/projects.json, inspections.json)             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Pipeline Components

### 1. Ingestion & Quality Control Subsystem (`backend/modules/module1_acquisition/`)
- Handles UAV flight upload batches.
- Performs EXIF timestamp & GPS extraction (`metadata.py`).
- Evaluates blur variance (Laplacian method) and exposure levels (`quality.py`).
- Normalizes and resizes imagery to 1024×1024 (`preprocessor.py`).

### 2. Deep Learning Detection Subsystem (`backend/modules/module3_detection/`)
- Deploys YOLOv8 real-time object detection model.
- Detects site machinery (excavators, cranes, trucks), workers, scaffolding, and PPE compliance.
- Renders bounding box visualizations (`visualizer.py`).

### 3. Multi-Temporal Change Detection Subsystem (`backend/modules/module4_change/`)
- Subtracts bi-temporal feature maps from time T1 and time T2 survey flights.
- Calculates Intersection over Union (IoU) and change percentage metrics (`metrics.py`).

### 4. Progress Estimation & Delay Forecasting Subsystem (`backend/modules/module5_prediction/`)
- Calculates quantitative completion scores ($0-100\%$).
- Fits S-Curves (`s_curve.py`) against project milestone schedules.
- Forecasts completion delay days and risk tiers (`predictor.py`).

### 5. Explainable AI Subsystem (`backend/modules/module6_xai/`)
- Generates spatial Grad-CAM activation heatmaps (`gradcam.py`) for vision models.
- Computes SHAP feature importance values (`shap_explain.py`) for delay prediction factors.
- Produces automated PDF reports (`pdf_report.py`) with embedded visual evidence and recommendations.
