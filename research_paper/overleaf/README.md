# Explainable Vision-Based Construction Progress Assessment and Delay Prediction Using Multi-Temporal UAV Imagery

## Overleaf / IEEE LaTeX Project Package

This repository package contains the complete, publication-quality IEEE conference research paper formatted for submission and compilation in **Overleaf** using the standard `IEEEtran` document class.

---

### Authors
1. **KAVINKARTHIK S**  
   *Department of M.Tech Computer Science and Engineering, Sri Krishna College of Engineering and Technology, Coimbatore, India*  
   Email: `727722euci019@skcet.ac.in`

2. **Dr. Emmanuel Joy**  
   *Assistant Professor, Department of M.Tech CSE, Sri Krishna College of Engineering and Technology, Coimbatore, India*  
   Email: `emmanueljoy@skcet.ac.in`

3. **Ms. KANAGAPRIYA S K**  
   *Assistant Professor, Department of M.Tech CSE, Sri Krishna College of Engineering and Technology, Coimbatore, India*  
   Email: `kanaka.priyacseengg@gmail.com`

---

### Project File Structure

```text
├── main.tex                 # Primary IEEEtran LaTeX document containing the full paper
├── references.bib           # 28 fully verified, authentic peer-reviewed references
├── README.md                # Project documentation and Overleaf instructions
└── figures/                 # High-resolution figures embedded in the manuscript
    ├── architecture.png     # Fig. 1: Four-layer proposed system architecture
    ├── workflow.png         # Fig. 2: End-to-end twelve-stage monitoring workflow
    ├── dashboard.png        # Fig. 3: Construction activity & safety analysis interface
    ├── change_detection.png # Fig. 4: Multi-temporal change detection pipeline execution
    ├── progress_methodology.png # Fig. 5: S-curve progress tracking & deviation interface
    ├── gradcam.png          # Fig. 6: Grad-CAM spatial activation heatmaps
    ├── shap.png             # Fig. 7: SHAP parametric feature attribution waterfall
    └── database.png         # Fig. 8: Logical data design & persistence architecture
```

---

### How to Compile in Overleaf

1. **Upload Files:**
   - Log into [Overleaf](https://www.overleaf.com/).
   - Click **New Project** $\rightarrow$ **Upload Project**.
   - Upload either the entire zipped folder or individually upload:
     - `main.tex`
     - `references.bib`
     - The `figures/` folder containing all 8 PNG images.

2. **Set Compiler Settings:**
   - Click **Menu** (top-left corner in Overleaf).
   - Set **Compiler** to `pdfLaTeX` (default).
   - Set **TeX Live Version** to `2023` or `2024`.
   - Set **Main document** to `main.tex`.

3. **Compile:**
   - Click the green **Recompile** button.
   - The compiled IEEE two-column PDF will be generated immediately without warnings or missing reference errors.

---

### Research Paper Key Technical Specifications

- **Document Class:** `\documentclass[conference]{IEEEtran}`
- **Evaluation Datasets:**
  - *LEVIR-CD+*: 50 evaluated image pairs, Pixel Accuracy = 72.00%
  - *SYSU-CD*: 50 evaluated image pairs, Pixel Accuracy = 72.85%, Precision = 0.2925, Recall = 0.4103, F1 = 0.2921, IoU = 0.1852
  - *Roboflow Construction Site Safety*: 2,799 images, 38,835 annotated instances across 10 classes
- **Software Functional Verification:**
  - 159 total automated tests executed via `pytest`
  - 159 tests passed (100% functional pass rate across 6 distinct subsystems)
  - Explicitly separated from algorithmic AI metrics
- **Explainable AI Mechanisms:**
  - *Spatial Explanations:* ResNet-50 Grad-CAM feature activation maps
  - *Parametric Attributions:* SHAP-style additive feature attributions across four progress dimensions
