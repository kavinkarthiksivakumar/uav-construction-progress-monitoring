# API Documentation

## Explainable Vision-Based Construction Progress Assessment
### REST API Reference — v1.0.0

**Base URL:** `http://localhost:5000/api/v1`  
**Content-Type:** `application/json`  
**CORS:** Enabled for all origins on `/api/*`

---

## Response Envelope

All API responses use a uniform envelope:

```json
{
  "success": true,
  "message": "Success",
  "data": { ... },
  "timestamp": "2026-07-16T14:00:00Z"
}
```

Error responses:
```json
{
  "success": false,
  "message": "Error description",
  "details": "...",
  "timestamp": "2026-07-16T14:00:00Z"
}
```

---

## Health Check

### `GET /api/v1/health`
Returns server health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "module": "Module 1: UAV Image Acquisition",
  "uptime": "2026-07-16T14:00:00Z"
}
```

---

## Module 1 — UAV Image Acquisition

### `POST /api/v1/projects`
Create a new UAV imagery project.

**Body:**
```json
{
  "name": "Highway Bridge Project",
  "description": "Monitoring Phase 2",
  "location": "Chennai, Tamil Nadu"
}
```

**Response:** `201 Created` with project object.

---

### `GET /api/v1/projects`
List all projects with summary statistics.

**Response:**
```json
{
  "projects": [
    {
      "project_id": "uuid",
      "name": "...",
      "image_count": 12,
      "created_at": "...",
      "status": "active"
    }
  ],
  "total": 1
}
```

---

### `GET /api/v1/projects/{project_id}`
Get full project details.

---

### `DELETE /api/v1/projects/{project_id}`
Delete project and all associated files.

---

### `POST /api/v1/projects/{project_id}/upload`
Upload UAV images (multipart/form-data).

**Form field:** `images` (multiple files allowed)  
**Supported formats:** `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`

**Response:**
```json
{
  "uploaded": 5,
  "processed": 5,
  "rejected": 0,
  "timeline": { ... },
  "quality_report": { ... }
}
```

---

### `GET /api/v1/projects/{project_id}/images`
List project images (paginated).

**Query params:** `page`, `limit` (default: 50)

---

### `GET /api/v1/projects/{project_id}/timeline`
Return temporal timeline sorted by capture date.

---

### `GET /api/v1/projects/{project_id}/quality`
Return image quality report (blur, brightness, contrast, resolution scores).

---

### `POST /api/v1/projects/{project_id}/preprocess`
Re-run preprocessing (CLAHE, resize, normalize) on project images.

---

### `GET /api/v1/projects/{project_id}/export`
Download project metadata as JSON.

---

### `GET /api/v1/images/{project_id}/{image_id}/preview`
Serve processed image preview (PNG).

---

## Module 2 — Image Processing

### `GET /api/v1/datasets/levir`
Scan LEVIR-CD dataset inventory.

### `GET /api/v1/datasets/levir/pairs`
List LEVIR-CD image pairs (paginated).

**Query params:** `split` (train/val/test), `page`, `limit`

### `POST /api/v1/datasets/levir/process`
Process a batch of LEVIR-CD pairs through Module 2 pipeline.

**Body:**
```json
{ "split": "train", "page": 1, "limit": 5 }
```

### `GET /api/v1/datasets/roboflow`
Scan Roboflow construction dataset.

### `GET /api/v1/datasets/roboflow/images`
List Roboflow images (paginated).

### `POST /api/v1/projects/{project_id}/process_module2`
Process project's preprocessed images through Module 2.

**Body:** `{ "limit": 20 }`

### `GET /api/v1/projects/{project_id}/process_module2/status`
Get Module 2 processing status.

---

## Module 3 — Construction Activity Detection

### `POST /api/v1/projects/{project_id}/detect`
Run YOLO/simulation detection on project images.

**Body:** `{ "limit": 20 }`

**Response:**
```json
{
  "total": 10,
  "succeeded": 10,
  "total_detections": 47,
  "results": [...]
}
```

### `GET /api/v1/projects/{project_id}/detect/results`
Return saved detection results.

**Response includes:**
- Per-image detection lists
- Class counts (helmet, no-helmet, vest, no-vest, person)
- Compliance rate
- Visualization URLs

### `POST /api/v1/datasets/roboflow/detect`
Detect on Roboflow dataset split.

**Body:** `{ "split": "train", "limit": 10 }`

---

## Module 4 — Change Detection

### `POST /api/v1/projects/{project_id}/change`
Run temporal change detection between project image pairs.

**Body:**
```json
{
  "limit": 5,
  "method": "otsu",
  "pairs": [
    { "image_a": "/path/before.png", "image_b": "/path/after.png" }
  ]
}
```

**Available methods:** `otsu` | `adaptive` | `fixed`

### `GET /api/v1/projects/{project_id}/change/results`
Return change detection results with severity classification.

**Severity levels:** `low` | `moderate` | `high` | `extreme`

### `GET /api/v1/projects/{project_id}/change/report`
Download change detection report as JSON.

### `POST /api/v1/datasets/levir/change`
Run change detection on LEVIR-CD dataset.

---

## Module 5 — Progress Assessment & Delay Prediction

### `POST /api/v1/projects/{project_id}/predict`
Run full Module 5 prediction pipeline.

**Body:**
```json
{
  "planned_duration_days": 365,
  "planned_start_date": "2026-01-01",
  "weights": {
    "change": 0.40,
    "activity": 0.30,
    "temporal": 0.20,
    "quality": 0.10
  }
}
```

**Response:**
```json
{
  "progress": {
    "progress_score": 62.4,
    "expected_progress": 55.0
  },
  "delay": {
    "delay_days": -11,
    "status": "ahead of schedule"
  },
  "risk": {
    "risk_level": "on_track",
    "risk_color": "#22c55e"
  },
  "sub_scores": {
    "change_score": 70.0,
    "activity_score": 60.0,
    "temporal_score": 55.0,
    "quality_score": 80.0
  },
  "s_curve": { ... },
  "milestones": [ ... ]
}
```

### `GET /api/v1/projects/{project_id}/predict/results`
Get saved prediction results.

### `GET /api/v1/projects/{project_id}/predict/s_curve`
Get planned vs actual S-curve data.

### `GET /api/v1/projects/{project_id}/predict/report`
Download progress report as JSON.

---

## Module 6 — Explainable AI (XAI)

### `POST /api/v1/projects/{project_id}/xai/gradcam`
Generate GradCAM heatmap overlays for project images.

**Body:**
```json
{
  "limit": 5,
  "alpha": 0.55,
  "model_path": null
}
```

**Response:**
```json
{
  "total": 5,
  "succeeded": 5,
  "results": [
    {
      "success": true,
      "mode": "synthetic",
      "overlay_path": "...",
      "heatmap_path": "...",
      "top_regions": [...],
      "stats": {
        "max_activation": 0.95,
        "mean_activation": 0.42,
        "high_activation_pct": 18.5
      }
    }
  ]
}
```

---

### `GET /api/v1/projects/{project_id}/xai/gradcam/results`
Return saved GradCAM results with image URLs.

---

### `POST /api/v1/projects/{project_id}/xai/shap`
Run SHAP feature importance analysis on Module 5 prediction.

**Body:** `{ "historical_data": [] }` (optional)

**Response:**
```json
{
  "success": true,
  "mode": "simulation",
  "features": {
    "change_score": 70.0,
    "activity_score": 60.0,
    "temporal_score": 55.0,
    "quality_score": 80.0
  },
  "shap_values": {
    "change_score": 8.0,
    "activity_score": 3.0,
    "temporal_score": 1.0,
    "quality_score": 3.0
  },
  "base_value": 50.0,
  "predicted_value": 62.4,
  "feature_importance": [...],
  "narrative": "The strongest positive driver is Change Detection (M4)..."
}
```

---

### `POST /api/v1/projects/{project_id}/xai/report`
Generate comprehensive XAI HTML + PDF report.

**Body:** `{ "force_rerun": false }`

**Auto-runs:** GradCAM + SHAP if not already available.

**Response:**
```json
{
  "success": true,
  "html_path": "processed/module6/{id}/report/xai_report.html",
  "pdf_path": "...",
  "pdf_available": true,
  "summary_path": "..."
}
```

---

### `GET /api/v1/projects/{project_id}/xai/report/download`
Download XAI report.

**Query param:** `format=html` (default) | `pdf` | `json`

---

### `GET /api/v1/projects/{project_id}/xai/status`
Check Module 6 processing status.

**Response:**
```json
{
  "gradcam": { "done": true, "count": 5 },
  "shap": { "done": true, "bar_chart": true, "waterfall": true },
  "report": { "html_available": true, "pdf_available": true },
  "overall_done": true
}
```

---

### `POST /api/v1/projects/{project_id}/xai/full_pipeline`
Run complete Module 6 pipeline in one call (GradCAM → SHAP → Report).

**Body:** `{ "limit": 5, "alpha": 0.55 }`

**Response:**
```json
{
  "success": true,
  "stages": {
    "gradcam": { "success": true, "images_processed": 5 },
    "shap":    { "success": true, "mode": "simulation" },
    "report":  { "success": true, "html_path": "...", "pdf_available": true }
  },
  "report_url": "/api/v1/projects/{id}/xai/report/download"
}
```

---

## Static File Serving

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/images/{pid}/{img_id}/preview` | Module 1 processed image |
| `GET /api/v1/images/{pid}/{img_id}/raw` | Module 1 raw image |
| `GET /api/v1/module2/{pid}/{stem}/{file}` | Module 2 feature map |
| `GET /api/v1/module2/levir/{split}/{pair_id}/{file}` | LEVIR-CD feature map |
| `GET /api/v1/module3/{pid}/{filepath}` | Module 3 detection viz |
| `GET /api/v1/module4/overlay/{pid}/{filepath}` | Module 4 change overlay |
| `GET /api/v1/module6/{pid}/gradcam/{file}` | Module 6 GradCAM image |
| `GET /api/v1/module6/{pid}/shap/{file}` | Module 6 SHAP chart |

---

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (missing params / no data) |
| 404 | Project / resource not found |
| 413 | File too large (max 500 MB) |
| 500 | Internal server error |

---

## Error Handling

All errors follow the standard envelope. Common errors:

| Message | Cause | Fix |
|---------|-------|-----|
| `No images field in request` | Missing `images` form field | Include `images` in multipart POST |
| `No Module 5 prediction found` | Module 5 not run | Call `/predict` first |
| `Dataset unavailable` | LEVIR/Roboflow path invalid | Check `.env` dataset paths |
| `No image pairs found` | < 2 images in project | Upload at least 2 images |
