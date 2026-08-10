# Model Checkpoints & Weights Guide

This folder contains references and configuration specifications for the deep learning models used across the UAV Construction Progress Monitoring pipeline. Heavy model weights are excluded from Git storage.

---

## 1. Overview of AI Models Used

| Module | Model Name / Architecture | Task / Purpose | Checkpoint Location |
| :--- | :--- | :--- | :--- |
| **Module 3: Activity Detection** | YOLOv8 (`yolov8n.pt` / `yolov8s.pt` / `yolov8m.pt`) | Object detection for workers, hard hats, safety vests, excavators, scaffolding, concrete mixer trucks. | Dynamically downloaded / cached in `models/yolov8n.pt` |
| **Module 4: Change Detection** | Deep Siamese Feature Extractor (ResNet-50 / Custom CNN) | Bi-temporal image feature comparison & change mask computation. | Synthesized / loaded in `backend/modules/module4_change/change_detector.py` |
| **Module 5: Progress Prediction** | Random Forest / Gradient Boosting Regressor | Predicts overall completion percentage, delay risk, and milestone variance. | Loaded in `backend/modules/module5_prediction/predictor.py` |
| **Module 6: Explainable AI** | Grad-CAM & SHAP Explainer | Spatial activation heatmap overlay & tabular feature attribution for progress scores. | Loaded in `backend/modules/module6_xai/gradcam.py` & `shap_explain.py` |

---

## 2. Model Weights & Cache Location

- Model weight files (`.pt`, `.pth`, `.joblib`, `.onnx`) are automatically downloaded or generated upon first run and cached locally in `models/` or PyTorch cache directory (`~/.cache/torch/hub/checkpoints/`).
- Do **not** commit large binary `.pt` or `.pth` files (>100MB) directly to GitHub.

---

## 3. How to Train or Download Custom Weights

1. **YOLOv8 Construction Detection**:
   - Ultralytics pretrained weights are automatically downloaded when initializing `YOLO('yolov8n.pt')`.
   - To use custom fine-tuned weights trained on Roboflow site safety dataset, place your `best.pt` inside `models/`:
     ```
     models/
     └── best.pt
     ```
2. **Environment Variable Overrides**:
   - Set custom model path in `.env` if stored in a non-default location:
     ```env
     YOLO_MODEL_PATH=models/best.pt
     ```
