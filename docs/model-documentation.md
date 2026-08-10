# AI / ML Model Architecture Documentation

This document details the neural network architectures, algorithms, and explainability frameworks integrated into the system.

---

## 1. Overview of System AI Architecture

```
UAV Image Inputs (T1, T2)
        │
        ├──► Module 1: Preprocessor & Quality Assessor (backend/modules/module1_acquisition)
        │
        ├──► Module 2: Bi-Temporal Feature Alignment   (backend/modules/module2_processing)
        │
        ├──► Module 3: YOLOv8 Construction Detector    (backend/modules/module3_detection)
        │
        ├──► Module 4: Bi-Temporal Change Detection    (backend/modules/module4_change)
        │
        ├──► Module 5: Progress Score & Delay Forecast (backend/modules/module5_prediction)
        │
        └──► Module 6: Explainable AI (Grad-CAM+SHAP)  (backend/modules/module6_xai)
```

---

## 2. Module Specifications

### Module 3: Activity & Equipment Detection (`backend/modules/module3_detection/detector.py`)
- **Architecture**: YOLOv8 (You Only Look Once v8).
- **Backbone**: Modified CSPDarknet53 with PANet neck.
- **Detections**: Construction machinery, worker presence, PPE compliance (hardhats, safety vests), scaffolding, material stockpiles.
- **Output**: Bounding box coordinates, confidence scores, classified label, and rendered overlays.

### Module 4: Bi-Temporal Change Detection (`backend/modules/module4_change/change_detector.py`)
- **Method**: Feature-level bi-temporal subtraction combined with intensity change thresholding.
- **Metrics Calculated** (`backend/modules/module4_change/metrics.py`):
  - **IoU (Intersection over Union)**: Overlap between detected and actual structural changes.
  - **Precision & Recall**: Accuracy of positive structural change identification.
  - **Change Percentage**: Proportion of modified area relative to total site area.

### Module 5: Progress Prediction & S-Curve (`backend/modules/module5_prediction/`)
- **Predictor** (`predictor.py`): Computes overall project progress score ($0-100\%$) based on detected structural components vs. scheduled milestones.
- **S-Curve Analyzer** (`s_curve.py`): Fits a sigmoidal cumulative progress curve against planned schedule baselines to quantify delay variance (ahead/behind schedule).
- **Delay Risk Model**: Evaluates risk factors (weather impact, material shortages, labor activity) to predict estimated completion date.

### Module 6: Explainable AI — XAI (`backend/modules/module6_xai/`)
- **Grad-CAM (`gradcam.py`)**: Gradient-weighted Class Activation Mapping generating spatial heatmaps to visually explain which regions of the UAV imagery influenced the change detection and progress models.
- **SHAP Explainer (`shap_explain.py`)**: SHAP (SHapley Additive exPlanations) values quantifying feature attribution for delay predictions (e.g. impact of worker count, equipment active hours, change square meters).
- **PDF Report (`pdf_report.py`)**: Generates an automated PDF executive report incorporating Grad-CAM heatmaps, SHAP summary charts, and progress tables.
