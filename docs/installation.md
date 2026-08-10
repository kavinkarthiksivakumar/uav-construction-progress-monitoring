# Installation Guide

## Explainable AI-Powered Construction Progress Assessment
### Using Multi-Temporal UAV Imagery

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11 (64-bit) |
| Python | 3.10, 3.11, 3.12, or 3.13 |
| RAM | 8 GB minimum (16 GB recommended) |
| Disk | 5 GB free (for datasets + outputs) |
| GPU | Optional (CPU-mode supported) |
| Network | Required for first-time pip install |

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/your-username/uav-construction-progress-monitoring.git
cd uav-construction-progress-monitoring
```

Confirm directory contains:
```
backend/  frontend/  requirements.txt  .env.example  README.md
```

---

## Step 2 — Install Python (if needed)

Download Python 3.12 from https://python.org/downloads/  
**Important:** Check "Add Python to PATH" during installation.

Verify:
```bash
python --version   # Should show 3.10 / 3.11 / 3.12 / 3.13
pip --version
```

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Core packages installed:
- **Flask 3.0.3** — Web server
- **OpenCV** — Image processing
- **NumPy / SciPy** — Numerical computation
- **Pillow** — Image I/O
- **PyTorch 2.3.1** — Deep learning (Module 3 YOLO, Module 6 GradCAM)
- **XGBoost 2.0.3** — Delay prediction (Module 5/6)
- **SHAP 0.45.1** — Feature importance (Module 6)
- **fpdf2 2.7.9** — PDF report generation (Module 6)
- **Matplotlib** — Chart generation
- **pandas** — Data processing
- **pytest** — Testing

> ⚠️ **PyTorch** is a large package (~2 GB). The system works in CPU-only mode (no CUDA required).

---

## Step 4 — Configure Environment Variables

Copy the example template to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and update dataset paths to match your local setup:

```env
# Dataset locations (update to your actual local paths)
LEVIR_CD_PATH=/path/to/levir_cd
ROBOFLOW_PATH=/path/to/roboflow_construction_dataset

# Server settings
PORT=5000
HOST=0.0.0.0
DEBUG=true
SECRET_KEY=your_secret_key_here
MAX_CONTENT_LENGTH=524288000
```

### Dataset Directory Structure Expected:

**LEVIR-CD** (`LEVIR_CD_PATH`):
```
levir_cd/
├── train/
│   ├── A/          ← Before images (.png)
│   ├── B/          ← After images (.png)
│   └── label/      ← Ground truth masks (.png)
├── val/
│   ├── A/, B/, label/
└── test/
    ├── A/, B/, label/
```

**Roboflow Construction Dataset** (`ROBOFLOW_PATH`):
```
roboflow_construction_dataset/
├── train/
│   ├── images/     ← .jpg images
│   └── labels/     ← YOLO .txt annotation files
├── valid/
│   ├── images/, labels/
└── test/
    ├── images/, labels/
```

> If datasets are NOT present, the system operates in **simulation mode** — fully functional without real data.

---

## Step 5 — Start the Server

### Option A — Batch File (Recommended, Windows only)
```bash
run_server.bat
```

### Option B — Direct Python
```bash
python backend/app.py
```

### Option C — Module invocation
```bash
python -m backend.app
```

**Expected server startup output:**
```
============================================================
UAV Vision — Construction Progress Assessment
Module 1: UAV Image Acquisition
Module 2: Image Processing (LEVIR-CD + Roboflow)
Module 3: Construction Activity Detection
Module 4: Construction Change Detection
Module 5: Delay Prediction & Progress Assessment
Module 6: Explainable AI (GradCAM + SHAP)
Server    : http://0.0.0.0:5000
============================================================
* Running on http://0.0.0.0:5000
```

---

## Step 6 — Open Dashboard

Open a browser and navigate to:
```
http://localhost:5000
```

---

## Step 7 — Verify Installation

### Quick Health Check:
```bash
curl http://localhost:5000/api/v1/health
```

Expected:
```json
{
  "success": true,
  "data": { "status": "healthy", "version": "1.0.0" }
}
```

### Run Automated Test Suite:
```bash
python -m pytest tests/ -v
```

Or use the convenience runner:
```bash
python validate_all.py
```

---

## Troubleshooting

### ❌ `ModuleNotFoundError: No module named 'flask'`
```bash
pip install flask flask-cors
```

### ❌ `ModuleNotFoundError: No module named 'cv2'`
```bash
pip install opencv-python-headless
```

### ❌ Port 5000 already in use
Edit `.env`: set `PORT=5001`  
Or: `$env:PORT=5001; python backend/app.py`

### ❌ Dataset not found error
This is **non-critical**. The system runs in simulation mode.  
Check `LEVIR_CD_PATH` and `ROBOFLOW_PATH` in `.env`.

### ❌ PyTorch not available — GradCAM uses synthetic mode
This is **expected** if no GPU/PyTorch model is present.  
Synthetic GradCAM produces realistic heatmaps for demonstration.

---

## Optional — Install GPU Support (NVIDIA)

For real YOLOv8 inference with CUDA:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install ultralytics
```

Then add the model path in `.env`:
```env
YOLO_MODEL_PATH=models/yolov8n.pt
```

---

## Directory Permissions

Ensure write access to:
- `uploads/` — Image upload storage
- `processed/` — Pipeline output
- `metadata/` — Project JSON
- `logs/` — Application logs
- `reports/` — Generated reports

These directories are **created automatically** on first run.
