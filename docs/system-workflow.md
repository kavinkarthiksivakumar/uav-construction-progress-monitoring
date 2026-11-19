# Unified System Workflow — End-to-End Construction Monitoring

This document describes the complete lifecycle the system implements, connecting
project management, UAV data acquisition, AI analysis, explainability, and
decision support into one coherent workflow.

```
PROJECT CREATION
        ↓
PROJECT PLAN AND TIMELINE SETUP          (start date, estimated completion, manager)
        ↓
UAV / SITE IMAGE UPLOAD                  (Module 1 — per project or per inspection)
        ↓
IMAGE VALIDATION                         (format, resolution, duplicates)
        ↓
IMAGE QUALITY INSPECTION                 (blur, brightness, contrast, quality score)
        ↓
PREPROCESSING                            (resize, normalise, CLAHE, denoise)
        ↓
CONSTRUCTION ACTIVITY DETECTION          (Module 3 — person / machinery / vehicle)
        ↓
SAFETY COMPLIANCE ANALYSIS               (Module 3 — PPE classes vs NO-* violations)
        ↓
MULTI-TEMPORAL CHANGE DETECTION          (Module 4 — before/after pairs, masks, overlays)
        ↓
INSPECTION FINDING GENERATION            (structured findings from stored evidence)
        ↓
PHYSICAL PROGRESS ESTIMATION             (Module 5 — weighted composite score)
        ↓
TIMELINE PROGRESS CALCULATION            (elapsed days / planned days × 100)
        ↓
SCHEDULE VARIANCE ANALYSIS               (physical − timeline; delay band classification)
        ↓
PROJECT HEALTH ASSESSMENT                (transparent weighted 0–100 score)
        ↓
EXPLAINABLE AI ANALYSIS                  (Module 6 — Grad-CAM + SHAP + report)
        ↓
QUALITATIVE RESULT GENERATION            (visual evidence chain with interpretations)
        ↓
QUANTITATIVE RESULT GENERATION           (3 separated metric groups, no fabrication)
        ↓
FINAL INSPECTION REPORT                  (key findings + recommended actions)
        ↓
DASHBOARD AND MANAGEMENT DECISION        (Results Center · Health & XAI Center)
```

## Timeline Progress vs Physical Progress

The system deliberately distinguishes two independent measures:

| Measure | Source | Meaning |
|---|---|---|
| **Timeline Progress** | Project start/end dates | The share of the planned schedule that has elapsed. |
| **Physical Progress** | Module 5 composite of Modules 1–4 outputs | The share of construction work the imagery suggests is complete. |

**Schedule Variance = Physical Progress − Timeline Progress** (percentage points)

Classification bands (configurable in `backend/modules/decision_support/health_score.py`):

| Variance | Band |
|---|---|
| ≥ 0 | ON TRACK |
| −1 to −10 | MINOR DELAY RISK |
| −11 to −20 | MODERATE DELAY |
| < −20 | HIGH DELAY RISK |

## Project Health Score

```
HEALTH = 0.35 × Progress Score
       + 0.25 × Schedule Score
       + 0.20 × Safety Score
       + 0.10 × Inspection Confidence
       + 0.10 × Activity Score
```

- Weights are configurable (`?w_progress=…` query params on `/health_score`).
- When a component lacks data its weight is renormalised over available components,
  and the breakdown discloses this.
- Classifications: **80–100 HEALTHY** · **60–79 STABLE** · **40–59 AT RISK** · **0–39 CRITICAL**.
- Every score is returned with an interpretation paragraph explaining *why*.

## Structured Explainable AI Queries

`GET /api/v1/projects/<id>/xai/query?query=<name>` answers:

| Query | Question answered |
|---|---|
| `what_changed` | What changed on the construction site? |
| `progress_status` | What is the current construction progress? |
| `why_delayed` | Why is the project delayed? |
| `safety_concerns` | What are the main safety concerns? |
| `region_attention` | Which region requires attention? |
| `evidence` | What evidence supports these results? |
| `limitations` | What are the limitations of this analysis? |

Every answer contains: **finding · location · why · confidence (with basis) ·
evidence · visual artifacts · limitations · recommendation**, all derived from
stored module outputs.

## Data Integrity Rules Enforced

1. Dataset/model evaluation results are served from real saved evaluation files
   (`reports/evaluation/*.json`) and are clearly labelled as
   **"Classical Change Detection Baseline Evaluation"** — never presented as
   trained deep-learning performance.
2. Roboflow statistics are labelled as **"Detection Dataset Annotation Analysis"**
   (label-file reads), explicitly not mAP/precision/recall of a trained detector.
3. Live project inspection metrics are computed only from actual uploaded images
   and executed pipeline stages; missing inputs degrade to explicit "not available"
   reasons rather than fabricated numbers.
4. Every final recommendation is traceable to measurable evidence recorded in the
   activity log.

## Activity Trail Event Types

`PROJECT_CREATED`, `PROJECT_UPDATED`, `PROJECT_INSPECTION_STARTED`,
`UAV_IMAGES_UPLOADED`, `IMAGE_QUALITY_CHECK_COMPLETED`, `PREPROCESSING_COMPLETED`,
`ACTIVITY_DETECTION_COMPLETED`, `SAFETY_DETECTION_COMPLETED`,
`CHANGE_DETECTION_COMPLETED`, `PROGRESS_ASSESSMENT_COMPLETED`,
`DELAY_ANALYSIS_COMPLETED`, `XAI_ANALYSIS_COMPLETED`,
`QUANTITATIVE_EVALUATION_COMPLETED`, `QUALITATIVE_EVALUATION_COMPLETED`,
`XAI_QUERY_ANSWERED`, `FINAL_REPORT_GENERATED`, `ASSESSMENT_STARTED`,
`ASSESSMENT_COMPLETED`.

Entries carry `timestamp · project_id · inspection_id · event_type · module ·
status · summary` and are rendered as a readable timeline in the dashboard.
