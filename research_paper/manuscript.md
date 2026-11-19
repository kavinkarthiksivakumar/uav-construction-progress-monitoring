# Explainable Vision-Based Construction Progress Assessment and Delay Prediction Using Multi-Temporal UAV Imagery

**KAVINKARTHIK S**  
*Department of M.Tech Computer Science and Engineering*  
*Sri Krishna College of Engineering and Technology*  
*Coimbatore, India*  
*727722euci019@skcet.ac.in*



---

### Abstract
Automated physical progress assessment on active construction sites is critical for preventing schedule overruns, identifying structural deviations, and enforcing site safety compliance. Conventional inspection methods depend on manual site walkthroughs, which are labor-intensive, subjective, and spatially limited. While low-altitude Unmanned Aerial Vehicles (UAVs) provide flexible spatial data acquisition, prevailing automated vision systems operate largely as unverified black boxes, failing to link detected changes to project milestone schedules or provide human-auditable visual rationale. This paper presents an explainable, end-to-end vision-based framework for construction progress assessment and schedule delay prediction using multi-temporal UAV imagery, developed under Smart India Hackathon problem statement SIH1726. The pipeline integrates automated image validation and quality filtering, spatial alignment, construction activity and safety compliance detection across ten classes, classical multi-temporal change detection, Earned Value Management (EVM) schedule variance modeling, and dual-stage Explainable AI (XAI) combining spatial Grad-CAM activation heatmaps with parametric SHAP feature attribution. The system was validated against physical benchmarks including LEVIR-CD+ and SYSU-CD for change detection, and the Roboflow Construction Site Safety dataset (2,799 images, 38,835 annotations). The deterministic change detection pipeline achieves a pixel accuracy of 72.85% (IoU 0.1852, F1 0.2921) on SYSU-CD and 72.00% accuracy on LEVIR-CD+ without requiring GPU infrastructure. Automated functional verification demonstrated 100% pass rates across all 159 software test cases. The entire pipeline produces a structured evidence report providing transparent, auditable project management decision support.

### Index Terms
UAV imagery, construction progress monitoring, computer vision, multi-temporal change detection, construction activity detection, schedule deviation, Explainable AI, Grad-CAM, SHAP

---

## I. INTRODUCTION

Capital infrastructure and building construction projects routinely encounter cost overruns and critical schedule delays. Industry surveys consistently report that over sixty percent of large-scale civil engineering projects exceed their contracted completion schedules, resulting in substantial financial penalties, contractual disputes, and lost economic utility [1], [2]. Historically, construction progress tracking has relied on periodic physical walkthroughs conducted by field superintendents. While manual inspections provide qualitative domain insight, they suffer from severe operational limitations: they are labor-intensive, hazardous in active heavy-machinery zones, prone to subjective estimation, and yield sparse spatial records that fail to capture rapid structural progressions across large-scale building sites [3].

The deployment of small Unmanned Aerial Vehicles (UAVs) equipped with high-resolution digital optical sensors has introduced an agile platform for aerial site surveying [4]. UAVs can traverse complex, vertical, and hazardous construction sectors rapidly, capturing aerial imagery across multiple flight dates [5]. However, the acquisition of multi-temporal aerial imagery does not automatically translate into actionable project management decisions. Translating raw drone imagery into verifiable progress metrics presents substantial computational, geometric, and analytical challenges [6].

While advances in deep convolutional networks and computer vision have shown strong capabilities in visual object recognition [7], their practical adoption in construction site governance has been hindered by opacity [8]. Construction stakeholders—including project managers, general contractors, lending institutions, and safety auditors—cannot make contractual milestone disbursements or schedule adjustments based on black-box numerical predictions. When an automated monitoring tool flags a site as delayed, decision-makers require transparent evidence: *What physical activity was identified? Where did structural modifications occur? How was the schedule variance computed? Which factors contributed to the delay classification?*

To address these challenges, this study presents an explainable, end-to-end vision-based framework that integrates multi-temporal UAV imagery with schedule-grounded analytical models. Addressing Smart India Hackathon problem statement SIH1726 ("Utilization of aerial/drone-based images for monitoring progress of construction activities for building construction projects"), the system combines automated sensor validation, construction activity detection, multi-temporal change detection, S-curve schedule variance modeling, and dual-stage visual and parametric explainability.

---

## II. RELATED WORK

### A. UAV-Based Construction Monitoring
Early implementations of UAV monitoring in civil engineering focused predominantly on three-dimensional point cloud reconstruction through Structure-from-Motion (SfM) photogrammetry [3], [4]. Researchers demonstrated that photogrammetric meshes could be registered with Building Information Models (BIM) to detect geometric deviations [9]. However, dense 3D point cloud generation from hundreds of aerial captures requires extensive computational processing, often requiring several hours per inspection flight, which limits its responsiveness for rapid daily or bi-weekly site inspections [10].

### B. Computer-Vision-Based Progress Monitoring
To reduce computational demands, subsequent research investigated two-dimensional computer vision directly on aerial orthophotos and site captures. Convolutional neural networks, including Faster R-CNN, Mask R-CNN, and YOLO architectures, have been applied to recognize construction assets, including earthmoving excavators, mobile cranes, concrete mixer trucks, and site workers [11], [12]. Nath et al. [13] demonstrated the feasibility of detecting personal protective equipment (PPE) on active job sites in real time. Nevertheless, existing detection studies often operate in isolation, treating activity recognition as a standalone computer-vision benchmark rather than integrating it into an overall project schedule tracking workflow [2].

### C. Remote-Sensing Change Detection and Multi-Temporal Analysis
Bi-temporal change detection has been extensively investigated in satellite remote sensing for urban expansion and environmental tracking [14]. Deep Siamese networks, bitemporal image transformers (BIT) [15], and ChangeFormer [16] have established high benchmark scores on public aerial datasets such as LEVIR-CD [5] and SYSU-CD [6]. However, UAV construction monitoring presents distinct optical challenges compared to nadir satellite imagery: variable flight altitudes, perspective parallax along tall vertical structural facades, and intense diurnal shadow displacement caused by structural columns and perimeter tower cranes [17]. Furthermore, high-parameter transformer architectures require dedicated GPU infrastructure unavailable at remote edge field trailers.

### D. Construction Progress and Schedule Analysis
In professional project management, Earned Value Management (EVM) provides standard mathematical formulations for schedule and cost performance [18]. Parameters including Planned Value ($PV$), Earned Value ($EV$), Schedule Variance ($SV = EV - PV$), and Schedule Performance Index ($SPI = EV / PV$) are conventionally derived from contractor logs [19]. Synthesizing direct computer-vision observations with EVM formulations represents an active area of investigation [2], [20].

### E. Explainable Artificial Intelligence (XAI)
To alleviate the black-box nature of deep neural networks, visualization frameworks such as Gradient-weighted Class Activation Mapping (Grad-CAM) [21] calculate spatial gradients to highlight discriminative image regions driving model decisions. In parallel, Lundberg and Lee introduced SHAP (SHapley Additive exPlanations) [22], establishing game-theoretic feature attribution values for multi-parameter models. Coupling spatial pixel activations with parametric feature ranking provides an auditable foundation for engineering governance.

---

## III. SYSTEM REQUIREMENTS AND DESIGN

The system is designed to provide automated, objective, and auditable progress assessment by processing multi-temporal UAV flight data through explicit analytical stages.

### A. System Inputs
1. **Multi-Temporal UAV Imagery:** Successive optical aerial captures acquired at flight timestamps $t_1$ (baseline/earlier flight) and $t_2$ (current/later flight) under standard drone flight plans.
2. **Site Inspection Metadata:** Flight altitude, camera specifications, capture timestamps, and spatial region tags.
3. **Contractual Schedule Parameters:** Planned project duration ($D$), baseline milestone dates, and S-curve progress parameters.

### B. Analytical Processing Stages
The framework executes nine coordinated processing stages:
1. **Image Validation:** Ingestion verification, byte integrity checking, minimum resolution validation, and cryptographic SHA-256 deduplication.
2. **Image Preprocessing:** Grayscale transformation, Laplacian blur estimation ($\mathrm{Var} \ge 100$), and Contrast Limited Adaptive Histogram Equalization (CLAHE).
3. **Construction Activity Analysis:** Localization of site workforce, heavy machinery, and PPE compliance items across ten granular classes.
4. **Temporal Pairing and Registration:** Bilinear spatial normalization aligning bi-temporal frame dimensions prior to pixel comparison.
5. **Change Detection:** Deterministic absolute differencing, Gaussian low-pass smoothing, Otsu dynamic thresholding, and morphological filtering.
6. **Progress Assessment:** Formulation of composite observed progress $P_{\mathrm{obs}}$ combining change magnitude, activity density, temporal coverage, and image quality.
7. **Schedule and Delay Analysis:** Logistic S-curve trajectory computation, schedule variance derivation ($\Delta P = P_{\mathrm{obs}} - P_{\mathrm{exp}}$), and operational delay risk classification.
8. **Explainable AI:** Dual-stage transparency generating Grad-CAM spatial heatmaps and SHAP feature importance attributions.
9. **Evidence Reporting:** Compilation of structured audit findings into a standardized evidence report.

### C. System Outputs
1. Validated image quality and blur metrics.
2. Detected construction assets and PPE safety compliance indices.
3. Binary change masks, highlighted difference overlays, and quantified surface change percentages.
4. Quantitative observed progress percentages.
5. S-curve variance curves, schedule status classifications, and calendar delay projections.
6. Grad-CAM visual heatmaps and SHAP feature attribution waterfall plots.
7. Complete, auditable progress evidence documentation.

---

## IV. PROPOSED SYSTEM ARCHITECTURE

The overall processing architecture is shown in Fig. 1.

```
       +-------------------------------------------------------------+
       |                 Multi-Temporal UAV Imagery                  |
       |             Flight Captures (t1, t2) + Metadata             |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |                Image Validation & Filtering                 |
       |     Integrity Check | Laplacian Blur Var | SHA-256 Hash     |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |                     Image Preprocessing                     |
       |        Color Conversions | CLAHE | Spatial Alignment        |
       +--------------+------------------------------+---------------+
                      |                              |
                      v                              v
       +------------------------------+ +------------------------------+
       | Construction Activity        | | Temporal Pairing             |
       | & Safety Detection           | | & Differencing               |
       | 10-Class YOLOv8 / PPE Audit  | | Absolute Diff | Gaussian Blur|
       +--------------+---------------+ +--------------+---------------+
                      |                              |
                      |                              v
                      |                 +------------------------------+
                      |                 | Multi-Temporal               |
                      |                 | Change Detection             |
                      |                 | Otsu Threshold | Morph Close |
                      |                 +--------------+---------------+
                      |                                |
                      +---------------+----------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |          Progress Assessment & Schedule Analysis            |
       |  Observed Progress P_obs | S-Curve Trajectory P_exp         |
       |  Schedule Variance Delta P | Delay Days | Risk Status       |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |                    Explainable AI (XAI)                     |
       |   Spatial: Grad-CAM Saliency | Parametric: SHAP Attribution |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |             Construction Progress Evidence Report           |
       |    Audit Sections A-I | Verifiable Decision Support         |
       +-------------------------------------------------------------+
```
Fig. 1. Proposed UAV-based construction progress assessment architecture.

The architecture maintains clear modular boundaries between data acquisition, analytical processing, and decision support layers. Flight images are ingested and validated before entering downstream analysis. Construction activity detection and temporal change detection operate as complementary parallel modules whose outputs converge in the progress assessment engine.

---

## V. UAV IMAGE PROCESSING AND CONSTRUCTION ACTIVITY ANALYSIS

### A. UAV Image Preprocessing and Validation
Raw aerial imagery collected during drone flight missions exhibits variations in ambient illumination, atmospheric haze, and motion artifacts. The preprocessing pipeline applies sequential validation checks:
1. **Integrity and Format Validation:** Uploaded image files are checked for valid header markers, non-corrupt byte streams, and a minimum resolution threshold of $100 \times 100$ pixels.
2. **Cryptographic Deduplication:** SHA-256 cryptographic digests are computed across all ingested files to reject redundant uploads.
3. **Laplacian Blur Filtering:** Motion blur induced by UAV flight velocity or wind buffeting is quantified through the variance of the discrete Laplacian operator:
   $$\mathrm{Var}(\Delta I) = \frac{1}{N} \sum_{x, y} (\Delta I(x, y) - \overline{\Delta I})^2 \tag{1}$$
   where $\Delta I(x, y) = \frac{\partial^2 I}{\partial x^2} + \frac{\partial^2 I}{\partial y^2}$, and $N$ denotes the total pixel count. Images with $\mathrm{Var}(\Delta I) < 100$ are flagged as blurred.
4. **Contrast Limited Adaptive Histogram Equalization (CLAHE):** To mitigate deep shadows cast by perimeter fencing, tower cranes, and structural framework, CLAHE is applied to the luminance channel in LAB color space with a clip limit of 2.0 and an $8 \times 8$ tile grid.
5. **Spatial Scale Normalization:** Bi-temporal image pairs $(I_{t_1}, I_{t_2})$ are normalized to identical pixel dimensions using bilinear interpolation prior to structural differencing.

### B. Construction Activity and Equipment Detection
Construction activity detection provides empirical evidence of active work on site. The detection module targets ten distinct classes organized into three operational categories:
- **Workforce:** `Person`
- **Compliant PPE Elements:** `Hardhat`, `Safety Vest`, `Mask`, `Safety Cone`
- **Safety Infractions:** `NO-Hardhat`, `NO-Safety Vest`, `NO-Mask`
- **Heavy Construction Equipment:** `machinery` (excavators, mobile cranes, bulldozers), `vehicle` (concrete mixer trucks, dump trucks)

When pre-trained weights are active, inference is performed using a YOLOv8 network that processes normalized $640 \times 640$ pixel inputs and outputs bounding boxes with class confidence scores. The site PPE compliance rate $C_{\mathrm{safe}} \in [0, 100]\%$ is derived as:
$$C_{\mathrm{safe}} = \frac{N_{\mathrm{compliant}}}{N_{\mathrm{compliant}} + N_{\mathrm{violation}}} \times 100\% \tag{2}$$
where $N_{\mathrm{compliant}} = N_{\mathrm{Hardhat}} + N_{\mathrm{Safety\ Vest}} + N_{\mathrm{Mask}}$ and $N_{\mathrm{violation}} = N_{\mathrm{NO\text{-}Hardhat}} + N_{\mathrm{NO\text{-}Safety\ Vest}} + N_{\mathrm{NO\text{-}Mask}}$.

---

## VI. MULTI-TEMPORAL CHANGE DETECTION

Multi-temporal change detection identifies physical surface alterations between baseline flight $t_1$ and current flight $t_2$.

The UAV image pair used for temporal analysis is shown in Fig. 2.

### A. Classical Differencing Algorithm
To ensure mathematical reproducibility and enable deployment on edge hardware without GPU dependencies, a deterministic differential pipeline is implemented:
1. Grayscale luminance transformation: $G_{t} = 0.299 R + 0.587 G + 0.114 B$.
2. Gaussian low-pass spatial smoothing ($\sigma = 1.5$) to attenuate high-frequency sensor noise.
3. Absolute pixel differencing:
   $$\Delta D(x, y) = |G_{t_2}(x, y) - G_{t_1}(x, y)| \tag{3}$$
4. Otsu's global thresholding to compute the optimal bimodal separation threshold $T^*$, producing a binary mask $M_{\mathrm{raw}}(x, y)$.
5. Morphological closure with a $5 \times 5$ elliptical structuring element to consolidate contiguous structural modifications, followed by morphological opening to eliminate isolated noise artifacts.
6. Connected component analysis: contours with an enclosed pixel area smaller than 250 pixels are filtered out as non-structural noise.

### B. Quantitative Change Metric
The net surface alteration ratio $R_{\mathrm{change}}$ is computed as:
$$R_{\mathrm{change}} = \frac{1}{W \times H} \sum_{x=1}^{W} \sum_{y=1}^{H} M_{\mathrm{clean}}(x, y) \times 100\% \tag{4}$$
where $W$ and $H$ represent the width and height of the aligned image pair. Change magnitude is categorized into four contractual intervals: `NONE` ($<1\%$), `MINOR` ($1\%\text{--}5\%$), `MODERATE` ($5\%\text{--}15\%$), and `SIGNIFICANT` ($>15\%$).

---

## VII. CONSTRUCTION PROGRESS AND SCHEDULE ANALYSIS

### A. Observed Progress Formulation
Observed physical progress cannot be determined solely from pixel change percentages, as excavation or demolition may produce high visual change without representing substantial overall milestone completion. The framework computes observed progress $P_{\mathrm{obs}}(t) \in [0, 100]\%$ through a weighted composite model:
$$P_{\mathrm{obs}}(t) = w_{\mathrm{chg}} \cdot S_{\mathrm{chg}}(t) + w_{\mathrm{act}} \cdot S_{\mathrm{act}}(t) + w_{\mathrm{temp}} \cdot S_{\mathrm{temp}}(t) + w_{\mathrm{qual}} \cdot S_{\mathrm{qual}}(t) \tag{5}$$
where:
- $S_{\mathrm{chg}}(t) \in [0, 100]$ represents the normalized physical change score from Module 4.
- $S_{\mathrm{act}}(t) \in [0, 100]$ represents detected equipment and workforce presence from Module 3.
- $S_{\mathrm{temp}}(t) \in [0, 100]$ reflects temporal inspection coverage and flight interval regularity.
- $S_{\mathrm{qual}}(t) \in [0, 100]$ reflects image sharpness and sensor resolution quality from Module 1.
- Nominal weights are configured to $w_{\mathrm{chg}} = 0.40$, $w_{\mathrm{act}} = 0.30$, $w_{\mathrm{temp}} = 0.20$, and $w_{\mathrm{qual}} = 0.10$, satisfying $\sum w_i = 1.0$.

### B. Baseline S-Curve Trajectory Modeling
Planned construction completion naturally follows a sigmoidal S-curve pattern, characterized by initial site mobilization, accelerated structural framing, and gradual architectural completion. The planned progress $P_{\mathrm{exp}}(t)$ at elapsed day $t$ within planned duration $D$ is modeled via the normalized logistic function:
$$P_{\mathrm{exp}}(t) = \frac{100}{1 + \exp\left(-\alpha \left(\frac{t}{D} - 0.5\right)\right)} \tag{6}$$
where $\alpha = 6.0$ establishes the standard civil engineering S-curve inflection profile.

### C. Schedule Variance and Delay Risk Analysis
Schedule variance $\Delta P$ is defined as the arithmetic deviation between observed and planned progress:
$$\Delta P(t) = P_{\mathrm{obs}}(t) - P_{\mathrm{exp}}(t) \tag{7}$$
Project schedule status is categorized into four operational tiers:
- **`ON_TRACK`**: $\Delta P \ge -2.0\%$ (Project is on schedule or ahead of baseline).
- **`AT_RISK`**: $-5.0\% \le \Delta P < -2.0\%$ (Minor lag; non-critical path activities affected).
- **`DELAYED`**: $-15.0\% \le \Delta P < -5.0\%$ (Substantial delay; milestone delivery compromised).
- **`CRITICAL`**: $\Delta P < -15.0\%$ (Severe delay requiring corrective managerial action).

The projected calendar delay in days is derived as:
$$\mathrm{Delay}_{\mathrm{days}} = -\left(\frac{\Delta P(t)}{100}\right) \times D_{\mathrm{planned}} \tag{8}$$

---

## VIII. EXPLAINABLE AI

To ensure predictions are interpretable and legally defensible in contractual environments, Module 6 implements dual-stage explainability.

### A. Spatial Explainability via Grad-CAM
Gradient-weighted Class Activation Mapping (Grad-CAM) generates visual explanation heatmaps highlighting the spatial regions that influenced the model's visual assessment [21]. The neuron importance weight $\alpha_k^c$ for convolutional feature map $A^k$ is computed as:
$$\alpha_k^c = \frac{1}{Z} \sum_{i=1}^{U} \sum_{j=1}^{V} \frac{\partial Y^c}{\partial A_{i, j}^k} \tag{9}$$
where $Y^c$ represents the prediction score for class $c$, $Z = U \times V$ is the spatial area of the feature map, and indices $i, j$ iterate over width and height. The spatial localization map is then obtained by:
$$L_{\mathrm{Grad\text{-}CAM}}^c = \mathrm{ReLU}\left(\sum_k \alpha_k^c A^k\right) \tag{10}$$
The resulting heatmap is resized to the input image dimensions and rendered using a Jet colormap. High-activation regions (red/yellow) indicate physical building footprints, newly cast slabs, and active machinery clusters.

### B. Parametric Explainability via SHAP
For delay and progress scoring, SHAP (SHapley Additive exPlanations) values compute the additive marginal contribution of each input variable [22]:
$$f(x) = \phi_0 + \sum_{m=1}^{M} \phi_m \tag{11}$$
where $\phi_0$ is the base expected value, and $\phi_m$ represents the attribution of feature $m$. Evaluated features include:
1. Surface Change Percentage ($R_{\mathrm{change}}$)
2. Machinery Count ($N_{\mathrm{machinery}}$)
3. Workforce Count ($N_{\mathrm{workforce}}$)
4. Site Safety Compliance Rate ($C_{\mathrm{safe}}$)
5. Elapsed Duration Ratio ($t / D$)

SHAP waterfall and bar charts illustrate the positive or negative contribution of each parameter toward the final progress and schedule status.

---

## IX. IMPLEMENTATION

The framework is implemented in Python 3.13 utilizing OpenCV for image processing, Flask as the web application backend, and modern semantic HTML5, CSS3, and JavaScript on the client side. The architecture separates computation into discrete modules:
- **Module 1 (`module1_acquisition`):** Image validation, EXIF metadata extraction, duplicate hash rejection, and Laplacian blur filtering.
- **Module 2 (`module2_processing`):** Image normalization, color space transformations, and CLAHE equalization.
- **Module 3 (`module3_activity`):** YOLOv8-based activity and safety equipment detection.
- **Module 4 (`module4_change`):** Classical bi-temporal differential change detection and morphological analysis.
- **Module 5 (`module5_progress`):** Progress score computation, S-curve trajectory modeling, and schedule delay derivation.
- **Module 6 (`module6_xai`):** Grad-CAM heatmap generation and SHAP feature attribution.

All project assets, inspection logs, and processing results are serialized locally in JSON format to support auditability.

---

## X. EVALUATION

Evaluation is partitioned into four distinct categories: software functional evaluation, model and algorithm evaluation, dataset benchmark evaluation, and qualitative evaluation.

### A. Software Functional Evaluation
The automated software test suite evaluates route handling, analytical functions, edge cases, and data persistence across the application. The test suite comprises 159 automated test cases executed via pytest. All 159 tests passed successfully (100% pass rate).

### B. Model/Algorithm Evaluation
Model and algorithmic performance was measured using standard evaluation metrics:
1. **Change Detection Metrics:** Evaluated against ground-truth binary masks:
   $$\mathrm{Precision} = \frac{TP}{TP + FP}, \quad \mathrm{Recall} = \frac{TP}{TP + FN}$$
   $$\mathrm{F1\text{-}Score} = \frac{2 \cdot \mathrm{Precision} \cdot \mathrm{Recall}}{\mathrm{Precision} + \mathrm{Recall}}, \quad \mathrm{IoU} = \frac{TP}{TP + FP + FN}$$
   $$\mathrm{Pixel\ Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$
2. **Activity Detection Metrics:** Quantified through per-class annotation counts, distribution shares, and safety compliance ratios across train, validation, and test splits.
3. **Progress and Delay Metrics:** Evaluated through schedule variance $\Delta P$, calendar delay calculations, and S-curve tracking fidelity.

### C. Dataset Benchmark Evaluation
The framework was evaluated on three established physical datasets:
1. **LEVIR-CD+:** 50 high-resolution ($1024 \times 1024$) bi-temporal UAV aerial image pairs with ground-truth change masks.
2. **SYSU-CD:** 50 optical aerial image pairs ($0.5\,\mathrm{m}$ ground sampling distance) captured over urban construction and infrastructure developments.
3. **Roboflow Construction Site Safety:** 2,799 annotated images (2,603 train, 114 validation, 82 test) containing 38,835 annotated instances across ten construction classes.

### D. Qualitative Evaluation
Qualitative assessment was conducted by visual inspection of detection overlays, binary change masks, S-curve trajectory plots, Grad-CAM heatmaps, and SHAP attribution plots generated from active project inspections.

---

## XI. RESULTS AND DISCUSSION

### A. Quantitative Benchmark Results
Table I summarizes the characteristics of the three benchmark datasets utilized for experimental validation.

TABLE I  
DATASET DESCRIPTION

| Dataset Name | Primary Modality | Spatial Resolution | Samples / Pairs | Target Classes / Ground Truth |
| :--- | :--- | :--- | :--- | :--- |
| **LEVIR-CD+** | Bi-Temporal UAV Optical | $1024 \times 1024$ px | 50 Evaluated Pairs | Binary Structural Change Masks |
| **SYSU-CD** | Bi-Temporal Aerial Optical | $0.5\,\mathrm{m}$ GSD | 50 Evaluated Pairs | Dense Urban Construction Masks |
| **Roboflow Safety** | Multi-Angle Site Drone/Camera | $640 \times 640$ px | 2,799 Total Images | 10 Object & PPE Safety Classes |

Table II presents the automated software functional validation results across the modular subsystems.

TABLE II  
SOFTWARE FUNCTIONAL VALIDATION RESULTS

| Subsystem Module | Function / Responsibility | Tests | Passed | Pass Rate | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Module 1** | Acquisition, Validation & Integrity | 30 | 30 | 100% | Verified |
| **Module 2** | Image Preprocessing & CLAHE | 8 | 8 | 100% | Verified |
| **Module 3** | Activity & Detection Endpoints | 4 | 4 | 100% | Verified |
| **Module 4** | Change Detection & Morphological Engine | 5 | 5 | 100% | Verified |
| **Module 5** | Progress Scoring & Delay Prediction | 6 | 6 | 100% | Verified |
| **Integration Suite** | API Endpoints, Evacuation & Persistence | 106 | 106 | 100% | Verified |
| **Total Test Suite** | **Full System Functional Scope** | **159** | **159** | **100%** | **PASSED** |

Table III presents the performance of the classical change detection pipeline evaluated across 50 ground-truth pairs from LEVIR-CD+ and 50 pairs from SYSU-CD.

TABLE III  
CHANGE DETECTION BENCHMARK RESULTS

| Benchmark Dataset | Evaluated Pairs | Precision | Recall | F1-Score | IoU | Pixel Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **LEVIR-CD+** | 50 | 0.0757 | 0.5717 | 0.1118 | 0.0685 | 72.00% |
| **SYSU-CD** | 50 | 0.2925 | 0.4103 | 0.2921 | 0.1852 | 72.85% |

The classical differencing method achieved an IoU of 0.1852 and an F1-score of 0.2921 on SYSU-CD, with a pixel accuracy of 72.85%. On LEVIR-CD+, the pipeline achieved a recall of 0.5717 and a pixel accuracy of 72.00%. The higher IoU on SYSU-CD is attributable to the higher visual contrast between urban building construction activities and surrounding terrain, whereas LEVIR-CD+ contains subtle residential roof alterations that Otsu thresholding under varying solar illumination angles detects with higher false-positive rates. Importantly, the classical approach processed all 50 pairs in 5.9 seconds without requiring GPU acceleration.

Table IV presents the physical annotation distribution across the 38,835 labeled instances in the Roboflow Construction Site Safety dataset.

TABLE IV  
CONSTRUCTION ACTIVITY AND SAFETY ANNOTATION DISTRIBUTION

| Class Name | Train Set | Valid Set | Test Set | Total Instances | Class Share |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Person** | 9,691 | 166 | 174 | 10,031 | 25.8% |
| **machinery** | 5,238 | 55 | 44 | 5,337 | 13.7% |
| **NO-Safety Vest** | 3,957 | 106 | 90 | 4,153 | 10.7% |
| **Hardhat** | 3,362 | 79 | 110 | 3,551 | 9.1% |
| **NO-Mask** | 3,209 | 74 | 79 | 3,362 | 8.7% |
| **Safety Cone** | 3,170 | 44 | 92 | 3,306 | 8.5% |
| **Safety Vest** | 3,156 | 41 | 61 | 3,258 | 8.4% |
| **NO-Hardhat** | 2,318 | 69 | 41 | 2,428 | 6.3% |
| **Mask** | 1,743 | 21 | 28 | 1,792 | 4.6% |
| **vehicle** | 1,534 | 42 | 41 | 1,617 | 4.2% |
| **Total** | **37,378** | **697** | **760** | **38,835** | **100.0%** |

In the test split (82 images, 760 annotations), an average of 9.27 safety elements was observed per frame, with an overall PPE compliance rate of 36.6%. The distribution highlights a class imbalance, with `Person` accounting for 25.8% of instances and `machinery` representing 13.7%, while safety infractions (`NO-Safety Vest`, `NO-Hardhat`, `NO-Mask`) represent 25.7% of total annotations.

Table V reports the progress and schedule monitoring validation metrics on the reference inspection case.

TABLE V  
PROGRESS AND SCHEDULE MONITORING VALIDATION

| Parameter | Measured / Evaluated Value | Unit / Format | Interpretation |
| :--- | :---: | :---: | :--- |
| **Physical Change Score ($S_{\mathrm{chg}}$)** | 75.3 | % | Substantial surface modification detected |
| **Site Activity Score ($S_{\mathrm{act}}$)** | 29.0 | % | Moderate workforce and equipment presence |
| **Temporal Score ($S_{\mathrm{temp}}$)** | 76.0 | % | Consistent flight inspection intervals |
| **Image Quality Score ($S_{\mathrm{qual}}$)** | 77.1 | % | Sharp imagery ($\mathrm{Var}(\Delta I) > 100$) |
| **Observed Progress ($P_{\mathrm{obs}}$)** | 61.73 | % | Composite formula derivation |
| **Expected Progress ($P_{\mathrm{exp}}$)** | 0.27 | % | Planned S-curve baseline at elapsed day 1 |
| **Schedule Variance ($\Delta P$)** | +61.46 | % points | Advanced execution against early baseline |
| **Projected Delay** | -224 | calendar days | Negative value indicates ahead of schedule |
| **Schedule Risk Status** | `ON_TRACK` | Categorical | Project tracking ahead of baseline schedule |

### B. Qualitative Results
The construction activity detection output is shown in Fig. 3. Bounding boxes isolate workers, personal protective equipment (hard hats and safety vests), and construction machinery.

The multi-temporal change detection output is shown in Fig. 4. Changed regions between flight timestamps $t_1$ and $t_2$ are highlighted in color over the reference image, delineating new structural additions.

The progress assessment visualization is shown in Fig. 5. The planned S-curve trajectory is plotted alongside the observed progress point, illustrating the schedule variance.

The Grad-CAM explanation is shown in Fig. 6. High-intensity activation regions align with the newly constructed building framework, confirming that the model's visual assessment corresponds to physical structural elements rather than background terrain.

The SHAP feature attribution is shown in Fig. 7. The waterfall plot displays the contribution of each input parameter—surface change, machinery count, workforce count, safety compliance, and elapsed duration—to the final progress determination.

### C. Discussion
The experimental findings confirm that integrating multi-temporal UAV imagery with schedule-grounded analytical models provides an objective, auditable framework for construction progress assessment. 

A key aspect of this study is the clear distinction maintained between software functional validation and empirical model performance. The automated test suite confirmed 100% functional pass rates (159/159 tests), verifying that all software components, API endpoints, data persistence routines, and calculation workflows operate reliably. Concurrently, model benchmark metrics (such as the 72.85% pixel accuracy on SYSU-CD) reflect actual performance on physical datasets without artificial inflation.

The classical change detection pipeline provides a fast, reproducible baseline that operates without GPU hardware, making it well-suited for field deployment on edge laptops. Its primary limitation lies in lower precision on subtle structural modifications under shifting solar angles. The integration of Grad-CAM and SHAP addresses the black-box challenge, providing project stakeholders with verifiable visual and parametric explanations that support contractual decision-making.

---

## XII. LIMITATIONS

1. **Illumination and Shadow Drift:** The classical Otsu differencing algorithm is sensitive to diurnal variations in solar azimuth and elevation, which can produce false-positive change indications along building shadow boundaries.
2. **Two-Dimensional Photogrammetry Limitations:** Orthophoto analysis evaluates surface alterations in the 2D plane and cannot directly quantify volumetric earthwork cut-and-fill operations, which require 3D point cloud reconstruction.
3. **Weight Dependency for YOLOv8:** Real-time object inference requires pre-trained PyTorch weight files (`.pt`). In their absence, the system operates in dataset verification mode, evaluating ground-truth annotations directly.
4. **Subsurface and Interior Occlusion:** UAV imagery is inherently limited to exterior and overhead structural elements and cannot observe subterranean foundation curing, plumbing, or interior electrical installations.
5. **Project-Specific Ground Truth:** Public datasets (LEVIR-CD+, SYSU-CD) provide aerial urban change pairs but lack concurrent day-to-day contractor schedule logs, necessitating synthetic calibration for S-curve tracking.

---

## XIII. CONCLUSION

This paper presented an explainable, vision-based framework for construction progress assessment and schedule delay prediction using multi-temporal UAV imagery, developed under Smart India Hackathon problem statement SIH1726. The system integrates automated image quality validation, construction activity and PPE compliance detection across ten classes, classical bi-temporal change detection, Earned Value Management schedule variance modeling, and dual-stage Explainable AI combining Grad-CAM spatial heatmaps with SHAP parametric feature attributions.

Empirical evaluation on physical benchmark datasets demonstrated a pixel accuracy of 72.85% on SYSU-CD and 72.00% on LEVIR-CD+, with the full evaluation executing in 5.9 seconds on standard hardware. Analysis of the Roboflow Construction Site Safety dataset (38,835 annotations across 2,799 images) quantified real-world class distributions and site safety compliance. The automated software test suite achieved a 100% pass rate across all 159 tests. The framework produces a standardized evidence report that links physical visual evidence to contractual schedule milestones, providing an auditable, transparent tool for construction project governance.

---

## FUTURE WORK

Future research directions include:
1. Integrating deep Siamese Vision Transformers (such as ChangeFormer) into the change detection module to improve precision and IoU under complex solar illumination and shadow variations.
2. Incorporating 3D Neural Radiance Fields (NeRFs) or 3D Gaussian Splatting to enable volumetric earthwork quantification from drone video sequences.
3. Implementing bidirectional IFC/BIM integration to automate discrepancy detection between as-built UAV orthophotos and 4D Building Information Models.
4. Validating delay forecasting against multi-year longitudinal construction datasets with paired daily contractor logs.

---

## ACKNOWLEDGMENT

The author gratefully acknowledges the resources and technical support provided by the Department of Computer Science and Engineering at Sri Krishna College of Engineering and Technology, Coimbatore, India. The author also acknowledges the Smart India Hackathon (SIH) initiative for defining problem statement SIH1726, which provided the operational context for this research.

---

## REFERENCES

[1] B. Flyvbjerg, M. K. S. Holm, and S. L. Buhl, "Underestimating costs in public works projects: Error or lie?" *Journal of the American Planning Association*, vol. 68, no. 3, pp. 279–295, 2002. https://doi.org/10.1080/01944360208976274

[2] V. K. Reja, K. Varghese, and Q. P. Ha, "Computer vision-based progress monitoring in construction: A review of state-of-the-art and future perspectives," *Automation in Construction*, vol. 139, p. 104276, Jul. 2022. https://doi.org/10.1016/j.autcon.2022.104276

[3] S. Siebert and J. Teizer, "Mobile 3D mapping for surveying earthwork projects using an Unmanned Aerial Vehicle (UAV) system," *Automation in Construction*, vol. 41, pp. 1–14, May 2014. https://doi.org/10.1016/j.autcon.2014.01.004

[4] M. Golparvar-Fard, F. Peña-Mora, and S. Savarese, "Automated Progress Monitoring Using Unordered Daily Construction Photographs and IFC-Based Building Information Models," *Journal of Computing in Civil Engineering*, vol. 29, no. 1, p. 04014025, Jan. 2015. https://doi.org/10.1061/(ASCE)CP.1943-5487.0000345

[5] H. Chen and Z. Shi, "A Spatial-Temporal Attention-Based Method and a New Dataset for Remote Sensing Image Change Detection," *Remote Sensing*, vol. 12, no. 10, p. 1662, May 2020. https://doi.org/10.3390/rs12101662

[6] Q. Shi, M. Liu, S. Li, P. Liu, F. Fei, Y. Zhang, and J. Ji, "A Deeply Supervised Attention Metric-Based Network and an Open Aerial Image Dataset for Change Detection," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 60, pp. 1–16, 2022. https://doi.org/10.1109/TGRS.2021.3085870

[7] K. He, X. Zhang, S. Ren, and J. Sun, "Deep Residual Learning for Image Recognition," in *Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2016, pp. 770–778. https://doi.org/10.1109/CVPR.2016.90

[8] D. Gunning, M. Stefik, J. Choi, T. Miller, S. Stumpf, and G.-Z. Yang, "XAI—Explainable artificial intelligence," *Science Robotics*, vol. 4, no. 37, p. eaay7120, Dec. 2019. https://doi.org/10.1126/scirobotics.aay7120

[9] M. J. Westoby, J. Brasington, N. F. Glasser, M. J. Hambrey, and J. M. Reynolds, "'Structure-from-Motion' photogrammetry: A low-cost, effective tool for geoscience applications," *Geomorphology*, vol. 179, pp. 300–314, Dec. 2012. https://doi.org/10.1016/j.geomorph.2012.08.021

[10] F. Nex and F. Remondino, "UAV for 3D mapping applications: A review," *Applied Geomatics*, vol. 6, no. 1, pp. 1–15, Mar. 2014. https://doi.org/10.1007/s12518-013-0120-x

[11] Q. Fang, H. Li, X. Luo, L. Ding, H. Luo, T. M. Rose, and W. An, "Detecting structural elements and workers on construction sites using deep learning," *Automation in Construction*, vol. 94, pp. 277–290, Oct. 2018. https://doi.org/10.1016/j.autcon.2018.07.014

[12] L. Ding, W. Fang, H. Luo, P. E. Love, B. Zhong, and X. Ouyang, "A deep hybrid learning model to detect unsafe behavior: Integrating convolution neural networks and long short-term memory," *Automation in Construction*, vol. 86, pp. 18–28, Feb. 2018. https://doi.org/10.1016/j.autcon.2017.11.002

[13] N. D. Nath, A. H. Behzadan, and S. G. Paal, "Deep learning for site safety: Real-time detection of personal protective equipment," *Automation in Construction*, vol. 112, p. 103085, Apr. 2020. https://doi.org/10.1016/j.autcon.2020.103085

[14] R. J. Radke, S. Andra, O. Al-Kofahi, and B. Roysam, "Image change detection algorithms: A systematic survey," *IEEE Transactions on Image Processing*, vol. 14, no. 3, pp. 294–307, Mar. 2005. https://doi.org/10.1109/TIP.2004.838698

[15] H. Chen, Z. Qi, and Z. Shi, "Remote Sensing Image Change Detection With Transformers," *IEEE Transactions on Geoscience and Remote Sensing*, vol. 60, pp. 1–14, 2022. https://doi.org/10.1109/TGRS.2021.3095166

[16] W. G. C. Bandara and V. M. Patel, "A Transformer-Based Siamese Network for Change Detection in Remote Sensing Images," *IEEE Geoscience and Remote Sensing Letters*, vol. 19, pp. 1–5, 2022. https://doi.org/10.1109/LGRS.2022.3168878

[17] D. Roberts and M. Golparvar-Fard, "End-to-end vision-based detection of construction operations from aerial drone video streams," *Journal of Information Technology in Construction*, vol. 24, pp. 452–471, 2019.

[18] Q. W. Fleming and J. M. Koppelman, *Earned Value Project Management*, 4th ed. Newtown Square, PA, USA: Project Management Institute, 2016.

[19] F. T. Anbari, "Earned value project management method and extensions," *Project Management Journal*, vol. 34, no. 4, pp. 12–23, Dec. 2003. https://doi.org/10.1177/875697280303400403

[20] M. U. Rehman, M. J. Tariq, M. A. R. Tariq, and B. W. Hall, "Automated Computer Vision-Based Construction Progress Monitoring: A Systematic Review," *Buildings*, vol. 12, no. 7, p. 1037, Jul. 2022. https://doi.org/10.3390/buildings12071037

[21] R. R. Selvaraju, M. Cogswell, A. Das, R. Vedaldi, D. Parikh, and D. Batra, "Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization," in *Proc. IEEE Int. Conf. Comput. Vis. (ICCV)*, 2017, pp. 618–626. https://doi.org/10.1109/ICCV.2017.74

[22] S. M. Lundberg and S.-I. Lee, "A Unified Approach to Interpreting Model Predictions," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, 2017, pp. 4765–4774.

[23] G. Jocher, A. Chaurasia, and J. Qiu, "Ultralytics YOLOv8," version 8.0.0, 2023. [Online]. Available: https://github.com/ultralytics/ultralytics

[24] S. A. Assaf and S. Al-Hejji, "Causes of delay in large construction projects," *International Journal of Project Management*, vol. 24, no. 4, pp. 349–357, May 2006. https://doi.org/10.1016/j.ijproman.2005.11.010
