# Construction Progress Evidence Report — Technical Schema

**Document Type:** Technical Specification & Examiner Interface Standard  
**SIH Problem Statement ID:** SIH1726  
**System Title:** Explainable Vision-Based Construction Progress Assessment and Delay Prediction Using Multi-Temporal UAV Imagery  

---

## 1. Overview & Objective

The **Construction Progress Evidence Report** is the primary high-level research and demonstration deliverable of this system. It synthesizes intermediate and final outputs produced across Modules 1 through 6 into a single unified evidence document, enabling examiners, site project managers, and auditors to verify project state without needing to inspect low-level source code.

Strictly adhering to the project's core principle:
$$\text{User Input} \longrightarrow \text{Processing \& Progress} \longrightarrow \text{Output} \longrightarrow \text{Interpretation} \longrightarrow \text{Next Action}$$

Every section explicitly details:
1. **What was provided?** (Inputs and raw data)
2. **What did the system execute?** (Algorithm, model, or methodology)
3. **What did it observe?** (Concrete findings with quantitative metrics)
4. **What does the result mean?** (Human-readable interpretation)
5. **What limitations or boundaries apply?** (Ground-truth and model availability disclosures)

---

## 2. Nine-Section Structural Specification

```
CONSTRUCTION PROGRESS EVIDENCE REPORT
├── SECTION A: PROJECT & INSPECTION INFORMATION
├── SECTION B: UAV IMAGE VALIDATION
├── SECTION C: DETECTED CONSTRUCTION ACTIVITIES
├── SECTION D: MULTI-TEMPORAL CHANGE DETECTION
├── SECTION E: PROGRESS ASSESSMENT (EXPECTED VS. OBSERVED)
├── SECTION F: DELAY & SCHEDULE DEVIATION ANALYSIS
├── SECTION G: EXPLAINABLE AI (Grad-CAM & SHAP)
├── SECTION H: SYSTEM CONFIDENCE & DATA QUALITY DISCLOSURES
└── SECTION I: FINAL INTERPRETATION & DECISION-SUPPORT ANSWERS
```

---

### Section A: Project & Inspection Information
| Field | Type | Description |
| :--- | :--- | :--- |
| `project_name` | string | Official project moniker (e.g., *UAV Monitoring -- Site Alpha*) |
| `project_id` | UUID | Persistent project primary identifier |
| `location` | string | Geographical location or site zone |
| `project_type` | enum | `commercial`, `residential`, `infrastructure`, `industrial` |
| `project_manager` | string | Authoritative supervising authority / guide |
| `inspection_id` | UUID | Identifier for the specific inspection flight session |
| `inspection_name` | string | Inspection flight label |
| `inspection_date` | ISO Date | Timestamp of UAV flight mission |
| `earlier_inspection_date`| ISO Date | Baseline comparative date |
| `later_inspection_date`  | ISO Date | Comparative inspection flight date |
| `input_images_count` | int | Total UAV aerial orthophotos evaluated |
| `input_image_names` | list[str] | Explicit filenames of ingested drone imagery |

---

### Section B: UAV Image Validation
| Field | Type | Description |
| :--- | :--- | :--- |
| `validation_status` | enum | `VALID`, `REJECTED / ATTENTION REQUIRED`, `NOT AVAILABLE` |
| `quality_status` | enum | `HIGH / OPTIMAL`, `SUB-OPTIMAL`, `REJECTED` |
| `temporal_pair_status` | enum | `CONFIRMED_PAIR`, `SINGLE_IMAGE`, `NO_IMAGES` |
| `image_quality_details`| list[dict] | Per-frame breakdown: dimensions, resolution (MP), format, Laplacian blur status, illumination rating, issues list |

---

### Section C: Detected Construction Activities & Site Safety
| Field | Type | Description |
| :--- | :--- | :--- |
| `detection_mode` | enum | `Trained YOLOv8 Weights` or `Roboflow Ground-Truth Verification Mode` |
| `total_detected_objects`| int | Sum of physical objects and personnel detected |
| `site_compliance_rate` | string | Percentage of workers wearing compliant PPE (e.g., `92.5%`) |
| `active_activities` | list[dict] | Identified classes: Personnel, Machinery, Vehicles, Hardhats, Safety Vests, Cones with counts, confidence scores, and categorization |
| `model_availability_note`| string | Explicit disclosure regarding model weights file availability |

---

### Section D: Multi-Temporal Change Detection
| Field | Type | Description |
| :--- | :--- | :--- |
| `earlier_image_reference` | string | Baseline image reference |
| `later_image_reference` | string | Active inspection frame reference |
| `change_detection_method` | string | Differential CLAHE + Otsu Thresholding + Morphological Close |
| `quantitative_change_percentage` | string | Calculated percentage area of physical change (e.g., `14.80%`) |
| `change_severity` | enum | `LOW / MINIMAL`, `MODERATE`, `HIGH`, `CRITICAL` |
| `plain_language_summary` | string | Human-readable explanation of detected change extent |

---

### Section E: Progress Assessment
| Field | Type | Description |
| :--- | :--- | :--- |
| `current_observed_progress`| string | Composite CV progress estimate (e.g., `48.0%`) |
| `expected_progress` | string | S-Curve planned timeline progress (e.g., `65.0%`) |
| `progress_variance_percentage_points` | string | Observed minus Expected (e.g., `-17.0 points`) |
| `derivation_breakdown` | dict | Formula weights: $0.40(\text{Change}) + 0.30(\text{Activity}) + 0.20(\text{Temporal}) + 0.10(\text{Quality})$ |
| `completed_activities` | list[str] | Observable milestones verified by vision |
| `remaining_unobserved_activities` | list[str] | Unobserved or remaining tasks on project timeline |

---

### Section F: Delay & Schedule Deviation Analysis
| Field | Type | Description |
| :--- | :--- | :--- |
| `schedule_status` | enum | `ON TRACK`, `AHEAD OF SCHEDULE`, `MODERATE DELAY`, `HIGH DELAY RISK` |
| `schedule_deviation_points` | string | Deviation score |
| `estimated_delay_days` | int | Projected calendar days behind schedule |
| `basis_of_analysis` | string | Mathematical comparison methodology explanation |
| `risk_classification` | enum | `CONTROLLED`, `ELEVATED`, `CRITICAL` |

---

### Section G: Explainable AI (XAI)
| Sub-component | Details |
| :--- | :--- |
| **Grad-CAM** | Spatial heatmap overlay; target prediction zone; plain-language interpretation confirming whether network focused on structural components versus background artifacts. |
| **SHAP** | Feature attribution values; bar chart of contribution weights for Change, Activity, Timeline, and Image Quality. |

---

### Section H: System Confidence & Limitations
| Field | Details |
| :--- | :--- |
| `input_quality_rating` | Assessment of optical sharpness, ground sampling distance (GSD), and illumination consistency. |
| `model_availability_disclosure` | Transparent statement regarding whether inference utilized loaded deep learning weights or local benchmark ground-truth annotations. |
| `result_reliability_limitations` | Notes that UAV imagery is restricted to externally visible superstructure, earthworks, and machinery, and cannot assess subterranean or indoor MEP installations. |

---

### Section I: Final Interpretation & Reviewer Answers
Answers the six fundamental review questions:
1. **What was observed?** — Summary of active plant, personnel, and structural framing.
2. **What changed?** — Extent and localization of spatial modification between earlier and later flight dates.
3. **How much progress is indicated?** — Exact observed progress percentage derived from multi-modal evidence.
4. **Is there a schedule deviation?** — Explicit variance against planned S-Curve milestone.
5. **What evidence supports the result?** — Cross-validation between change masks, object counts, and XAI heatmaps.
6. **What limitations apply?** — Boundaries of aerial vision monitoring.

---

## 3. API Serving Endpoint

```http
GET /api/v1/projects/{project_id}/evidence_report
Content-Type: application/json
```
Accessible interactively via the web frontend under **Workspace Overview $\to$ Reports Tab $\to$ Construction Progress Evidence Report**.
