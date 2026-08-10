# Datasets Guide — Construction Progress Monitoring

This repository uses two benchmark datasets for image processing, change detection, and construction object detection. Due to size constraints and licensing, dataset files are kept **outside the repository** and configured via environment variables.

---

## 1. LEVIR-CD (Bi-Temporal Change Detection Dataset)

- **Official Source**: [LEVIR-CD Dataset Homepage](https://justchenhao.github.io/LEVIR/)
- **Description**: High-resolution building change detection dataset consisting of 637 VHR Google Earth image pairs (1024×1024 pixels) with 31,333 annotated building changes.
- **Used In**: Module 2 (`backend/modules/module2_processing/levir_loader.py`) & Module 4 (`backend/modules/module4_change/change_detector.py`).
- **Configure in `.env`**:
  ```env
  LEVIR_CD_PATH=/path/to/levir_cd
  ```
- **Expected Directory Structure**:
  ```
  levir_cd/
  ├── A/                  # Pre-change images (.png)
  ├── B/                  # Post-change images (.png)
  ├── label/              # Binary change masks (.png)
  ├── train.txt
  ├── val.txt
  └── test.txt
  ```

---

## 2. Roboflow Construction Safety & Equipment Dataset

- **Official Source**: [Roboflow Universe — Construction Site Safety](https://universe.roboflow.com/)
- **Description**: Annotations for construction equipment (excavators, cranes, trucks), workers, personal protective equipment (PPE: hard hats, safety vests), and structural components.
- **Used In**: Module 2 (`backend/modules/module2_processing/roboflow_loader.py`) & Module 3 (`backend/modules/module3_detection/detector.py`).
- **Configure in `.env`**:
  ```env
  ROBOFLOW_PATH=/path/to/roboflow_construction_dataset
  ```
- **Expected Directory Structure**:
  ```
  roboflow_construction_dataset/
  ├── train/
  │   ├── images/         # RGB images (.jpg / .png)
  │   └── labels/         # YOLO format bounding box txt files
  ├── valid/
  └── test/
  ```

---

## 3. Local Dataset Setup Instructions

1. Download the datasets from the official sources above.
2. Extract the files into your preferred local directory.
3. Update your local `.env` file with the actual paths (see `.env.example` for the template):
   ```env
   LEVIR_CD_PATH=/path/to/levir_cd
   ROBOFLOW_PATH=/path/to/roboflow_construction_dataset
   ```
4. Test the dataset connectivity by accessing:
   - `GET /api/v1/datasets/levir`
   - `GET /api/v1/datasets/roboflow`

> If datasets are not present, the system operates in **simulation mode** — all pipeline modules remain fully functional without real data.
