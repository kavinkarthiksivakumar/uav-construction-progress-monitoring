"""
Paste this entire script into Claude Code (or any Python environment with python-docx installed).
Run: pip install python-docx  then  python generate_research019.py
Output: research-019_updated.docx  (in the same folder you run from)
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# ── Page margins ────────────────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin   = Cm(2.0)
    section.right_margin  = Cm(2.0)

# ── Helpers ─────────────────────────────────────────────────────────────────

def add_title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(6)

def add_authors(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    p.paragraph_format.space_after = Pt(2)

def add_affil(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(10)
    p.paragraph_format.space_after = Pt(2)

def add_email(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.size = Pt(9)
    p.paragraph_format.space_after = Pt(10)

def add_section_heading(doc, text):
    p = doc.add_paragraph(style='List Paragraph')
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(4)

def add_subsection_heading(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(10.5)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(3)

def add_body(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(10)
    p.paragraph_format.first_line_indent = Inches(0.25)
    p.paragraph_format.space_after       = Pt(4)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

def add_bullet(doc, text):
    p = doc.add_paragraph(style='List Paragraph')
    run = p.add_run(text)
    run.font.size = Pt(10)
    p.paragraph_format.space_after = Pt(3)

def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(9)
    p.paragraph_format.space_after = Pt(6)

def add_equation(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.name = 'Cambria Math'
    run.font.size = Pt(10)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)

def add_table_title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(9)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(3)

def simple_table(doc, headers, rows, caption=""):
    if caption:
        add_table_title(doc, caption)
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.style = 'Table Grid'
    hdr = tbl.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = h
        for para in cell.paragraphs:
            for run in para.runs:
                run.bold = True
                run.font.size = Pt(9)
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for ri, row_data in enumerate(rows):
        row = tbl.rows[ri + 1]
        for ci, val in enumerate(row_data):
            cell = row.cells[ci]
            cell.text = str(val)
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(9)
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()

# ════════════════════════════════════════════════════════════════════════════
#  TITLE / AUTHORS
# ════════════════════════════════════════════════════════════════════════════

add_title(doc,
    "Explainable Vision-Based Construction Progress Assessment and Schedule Delay "
    "Prediction Using Multi-Temporal UAV Imagery: An Integrated Framework with "
    "Classical Change Detection and Dual Explainability"
)
add_authors(doc, "1KAVINKARTHIK S")
add_affil(doc,
    "1 Department of M. Tech Computer Science and Engineering, "
    "Sri Krishna College of Engineering and Technology, Coimbatore, India."
)
add_email(doc, "1727722euci019@skcet.ac.in")

# ════════════════════════════════════════════════════════════════════════════
#  ABSTRACT
# ════════════════════════════════════════════════════════════════════════════

add_section_heading(doc, "Abstract")
add_body(doc,
    "Active construction site monitoring is a critical yet persistently manual task in civil "
    "infrastructure management. Industry surveys consistently report that over sixty percent of "
    "large-scale construction projects exceed contracted schedules, resulting in financial penalties "
    "and contractual disputes. In this paper, we propose an explainable, end-to-end vision-based "
    "framework for construction progress assessment and schedule delay prediction using multi-temporal "
    "UAV (Unmanned Aerial Vehicle) imagery. The proposed system comprises two complementary analytical "
    "streams: (i) a construction activity and PPE compliance detection engine using YOLOv8 across ten "
    "site object classes, and (ii) a classical bi-temporal change detection pipeline integrating Laplacian "
    "blur validation, CLAHE image enhancement, Gaussian smoothing, Otsu thresholding, and morphological "
    "post-processing for surface alteration quantification. A composite observed progress scoring model "
    "fuses visual change evidence, activity intensity, temporal consistency, and image quality indicators "
    "into a unified progress metric aligned with S-curve Earned Value Management (EVM) baselines. "
    "Dual explainability is provided through Gradient-weighted Class Activation Mapping (Grad-CAM) "
    "spatial heatmaps and SHAP (SHapley Additive exPlanations) parametric attribution charts. "
    "The framework was empirically evaluated on LEVIR-CD+ and SYSU-CD bi-temporal aerial datasets "
    "and the Roboflow Construction Site Safety dataset (38,835 annotated instances). The classical "
    "differencing pipeline achieved a pixel accuracy of 72.85% on SYSU-CD and 72.00% on LEVIR-CD+. "
    "An automated software validation suite of 159 test cases achieved a 100% pass rate. "
    "The complete assessment pipeline executes in 5.9 seconds on standard CPU hardware, "
    "confirming suitability for field deployment without GPU acceleration."
)
p = doc.add_paragraph()
run = p.add_run(
    "Keywords: UAV Imagery, Construction Progress Monitoring, Multi-Temporal Change Detection, "
    "Explainable AI, Grad-CAM, SHAP, Earned Value Management, PPE Compliance, YOLOv8, S-Curve Modeling."
)
run.italic = True
run.font.size = Pt(10)
p.paragraph_format.space_after = Pt(10)

# ════════════════════════════════════════════════════════════════════════════
#  1. INTRODUCTION
# ════════════════════════════════════════════════════════════════════════════

add_section_heading(doc, "1. Introduction")
add_body(doc,
    "Capital infrastructure projects routinely experience cost overruns and schedule delays of "
    "significant magnitude. Industry research consistently establishes that more than sixty percent "
    "of large civil engineering contracts exceed their planned completion deadlines, generating "
    "financial penalties, contractual litigation, and loss of economic utility to procuring agencies "
    "[1], [2]. Historically, construction progress monitoring has relied on periodic manual site "
    "walkthroughs conducted by resident engineers and quantity surveyors—a methodology that is "
    "labor-intensive, spatially selective, and subjective in its quantification of physical completion."
)
add_body(doc, "Three persistent technical challenges undermine existing automated monitoring approaches:")
add_bullet(doc,
    "Lack of Spatial Coverage and Objectivity: Ground-level photographic surveys and manual "
    "logbooks capture only accessible zones and are contingent on observer judgment, introducing "
    "systematic measurement bias. Aerial drone platforms provide flexible overhead coverage, but "
    "raw imagery does not automatically translate into contractually verifiable progress metrics [3]."
)
add_bullet(doc,
    "Opacity of Black-Box Visual Models: Deep convolutional networks have demonstrated strong "
    "object recognition capabilities [7] but are routinely rejected by construction stakeholders "
    "because they cannot explain which visual features drove a progress determination [8]. "
    "Without spatial and parametric explanations, model outputs cannot support contractual "
    "milestone disbursements."
)
add_bullet(doc,
    "Absence of Integrated Schedule Analysis: Existing UAV-based monitoring studies predominantly "
    "report visual change metrics without linking observation to formal Earned Value Management "
    "(EVM) schedule variance formulations [18]. The gap between pixel-level change percentage and "
    "calendar delay prediction in days remains unresolved in the literature."
)
add_body(doc,
    "To address these challenges, this paper presents an explainable, modular framework that "
    "integrates multi-temporal UAV imagery acquisition and validation, construction activity "
    "and PPE compliance detection, classical bi-temporal change detection, S-curve EVM progress "
    "modeling, and dual-layer explainability through Grad-CAM and SHAP. The major technical "
    "contributions of this work are:"
)
add_bullet(doc,
    "Firstly, an automated image quality validation and preprocessing pipeline integrating "
    "Laplacian blur estimation, SHA-256 deduplication, and CLAHE contrast normalization to "
    "standardize multi-temporal UAV imagery across diverse flight conditions and hardware platforms."
)
add_bullet(doc,
    "Secondly, a classical deterministic change detection pipeline combining Gaussian smoothing, "
    "absolute pixel differencing, Otsu global thresholding, and morphological closing and opening "
    "operations, operable without GPU acceleration for field deployment on edge hardware."
)
add_bullet(doc,
    "Thirdly, a composite observed progress scoring model (Pobs) fusing four weighted visual "
    "evidence dimensions: surface change, activity intensity, temporal consistency, and image quality."
)
add_bullet(doc,
    "Then, a logistic S-curve baseline trajectory formulation and schedule variance quantification "
    "that maps the visual progress score to EVM metrics, producing calendar delay estimates in "
    "days with four operational risk tiers (ON_TRACK, AT_RISK, DELAYED, CRITICAL)."
)
add_bullet(doc,
    "Finally, dual explainability covering spatial localization through Grad-CAM heatmaps "
    "overlaid on UAV images, and parametric attribution through SHAP waterfall and bar charts "
    "identifying the per-variable drivers of schedule variance."
)
add_body(doc,
    "The remainder of this paper is organized as follows: Section 2 reviews related literature. "
    "Section 3 details the proposed system architecture and methodology. Section 4 presents "
    "experimental results, quantitative benchmarks, and qualitative analysis. Section 5 discusses "
    "the framework's operational implications and limitations. Section 6 concludes the paper with "
    "a summary of findings and directions for future research."
)

# ════════════════════════════════════════════════════════════════════════════
#  2. RELATED LITERATURE
# ════════════════════════════════════════════════════════════════════════════

add_section_heading(doc, "2. Related Literature")
add_body(doc,
    "Automated construction monitoring integrates three technical domains: UAV-based aerial "
    "sensing, computer-vision-based activity and change analysis, and schedule management "
    "analytics. This section reviews relevant literature across these core domains."
)

add_subsection_heading(doc, "2.1. UAV-Based Construction Monitoring")
add_body(doc,
    "Early implementations of UAV monitoring in civil engineering focused predominantly on "
    "three-dimensional point cloud reconstruction through Structure-from-Motion (SfM) "
    "photogrammetry [3], [4]. Researchers demonstrated that photogrammetric meshes could be "
    "registered against Building Information Models (BIM) to detect geometric deviations from "
    "design intent. However, dense point cloud generation from hundreds of aerial images requires "
    "significant GPU compute and prolonged processing time, limiting practical frequency of "
    "assessment. Roberts and Golparvar-Fard [17] introduced video-stream-based detection of "
    "construction operations, but this method requires continuous drone uptime not feasible "
    "in routine site monitoring."
)

add_subsection_heading(doc, "2.2. Computer-Vision-Based Activity Detection and Progress Monitoring")
add_body(doc,
    "To reduce computational demands, subsequent research investigated two-dimensional computer "
    "vision directly on aerial orthophotos and site captures. Convolutional neural networks, "
    "including Faster R-CNN, Mask R-CNN, and YOLO architectures, have been applied to recognize "
    "construction assets including earthmoving excavators, mobile cranes, concrete mixer trucks, "
    "and site workers [11], [12]. Nath et al. [13] demonstrated the feasibility of detecting "
    "personal protective equipment (PPE) violations on active job sites in real time. However, "
    "these detection-only approaches do not formulate a composite progress score or link "
    "observations to EVM schedule mathematics."
)

add_subsection_heading(doc, "2.3. Multi-Temporal Remote Sensing Change Detection")
add_body(doc,
    "Bi-temporal change detection has been extensively investigated in satellite remote sensing "
    "for urban expansion and environmental tracking [14]. Deep Siamese networks, Bitemporal Image "
    "Transformers (BIT) [15], and ChangeFormer [16] have established high benchmark scores on "
    "public aerial datasets such as LEVIR-CD and SYSU-CD. However, UAV construction monitoring "
    "presents distinct optical challenges: variable flight altitudes, perspective parallax along "
    "tall vertical structural facades, and intense diurnal shadow displacement caused by tower "
    "cranes and perimeter scaffolding. Classical deterministic differencing pipelines, while less "
    "powerful than transformer-based models, provide reproducible baselines operable without GPU "
    "resources on edge hardware."
)

add_subsection_heading(doc, "2.4. Schedule Analysis and Earned Value Management")
add_body(doc,
    "In professional project management, Earned Value Management (EVM) provides standard "
    "mathematical formulations for schedule and cost performance assessment [18]. Parameters "
    "including Planned Value (PV), Earned Value (EV), Schedule Variance (SV = EV - PV), and "
    "Schedule Performance Index (SPI = EV / PV) are conventionally derived from contractor logs "
    "rather than direct visual observation [19]. Synthesizing direct computer-vision observations "
    "with EVM mathematics represents an open research challenge: existing image-based progress "
    "systems either report raw change ratios without schedule context, or require manual human "
    "annotation to convert visual observations into EVM parameters [20]."
)

add_subsection_heading(doc, "2.5. Explainable AI in Construction Monitoring")
add_body(doc,
    "To alleviate the black-box nature of deep neural networks, visualization frameworks such "
    "as Gradient-weighted Class Activation Mapping (Grad-CAM) [21] calculate spatial gradients "
    "to highlight discriminative image regions driving model decisions. In parallel, Lundberg "
    "and Lee introduced SHAP (SHapley Additive exPlanations) [22], establishing game-theoretic "
    "feature attribution values for multi-parameter predictive models. While Grad-CAM has been "
    "applied to medical image classification and satellite change detection, its application to "
    "construction progress heatmap localization combined with SHAP parameter attribution for "
    "schedule variance drivers has not been systematically addressed in prior work."
)

add_subsection_heading(doc, "2.6. Comparative Summary of Related Frameworks")
add_body(doc,
    "Table 1 summarizes the technical capabilities of existing construction monitoring "
    "frameworks compared with the proposed approach."
)
simple_table(doc,
    ["Reference", "Method", "Change Detection", "Schedule Link", "XAI", "GPU Required"],
    [
        ["SfM-BIM [3,4]",       "Point Cloud Recon.",  "3D volumetric",      "Manual",        "None",              "Yes"],
        ["YOLO PPE [13]",        "Object Detection",    "None",               "None",           "None",              "Yes"],
        ["BIT [15]",             "Siamese Transformer", "Deep binary mask",   "None",           "Attn. maps",        "Yes"],
        ["ChangeFormer [16]",    "Vision Transformer",  "Deep binary mask",   "None",           "Partial",           "Yes"],
        ["EVM Analytics [18,19]","Mathematical model",  "None",               "EVM formulas",   "None",              "No"],
        ["Proposed Framework",   "Classical + YOLO",    "Otsu differencing",  "S-curve EVM",    "Grad-CAM + SHAP",   "No"],
    ],
    "Table 1. Comparative taxonomy of existing construction monitoring literature versus the proposed framework."
)

# ════════════════════════════════════════════════════════════════════════════
#  3. METHODOLOGY
# ════════════════════════════════════════════════════════════════════════════

add_section_heading(doc, "3. Methodology")
add_body(doc,
    "The proposed construction monitoring system operates through two parallel analytical streams "
    "whose outputs converge into an integrated decision support layer. Stream A performs construction "
    "activity and PPE compliance detection using YOLOv8 across ten site object classes. Stream B "
    "performs deterministic bi-temporal change detection using classical computer vision. A composite "
    "observed progress scoring module then fuses the outputs of both streams with temporal and "
    "quality indicators into a single normalized progress score, which is compared against an "
    "S-curve logistic baseline to yield schedule variance and calendar delay estimates."
)

add_subsection_heading(doc, "3.1. Preprocessing and Image Validation")
add_body(doc,
    "To standardize illumination across diverse drone hardware platforms and mission conditions, "
    "all raw UAV images are passed through a four-stage validation and preprocessing pipeline "
    "before entering downstream analytical modules:"
)
add_bullet(doc,
    "Integrity verification enforcing a minimum image resolution of 100 x 100 pixels and "
    "cryptographic deduplication using SHA-256 digests to eliminate redundant captures "
    "that would bias temporal change quantification."
)
add_bullet(doc,
    "Laplacian blur estimation to flag and quarantine insufficiently sharp imagery. "
    "Image sharpness is quantified through the variance of the discrete Laplacian operator:"
)
add_equation(doc, "Var(delta_I) = (1/N) * SUM_(x,y) (delta_I(x,y) - mu_delta_I)^2       (1)")
add_body(doc,
    "where N is the total number of image pixels, delta_I(x,y) is the Laplacian response at "
    "spatial location (x,y), and mu_delta_I is the mean Laplacian response. Images with "
    "Var(delta_I) < 100 are flagged as insufficiently sharp and excluded from the pipeline."
)
add_bullet(doc,
    "Contrast Limited Adaptive Histogram Equalization (CLAHE) applied to the luminance "
    "channel in LAB color space using a clip limit of 2.0 and 8x8 contextual grid tiles. "
    "This selectively enhances local contrast under heterogeneous solar illumination while "
    "preserving color fidelity across structural surface materials."
)
add_bullet(doc,
    "Grayscale luminance conversion and Gaussian low-pass smoothing with sigma = 1.5 prior "
    "to temporal differencing to suppress high-frequency sensor noise that would otherwise "
    "produce false-positive change detections."
)

add_subsection_heading(doc, "3.2. Construction Activity and PPE Detection (Stream A)")
add_body(doc,
    "Construction activity analysis provides visual evidence of the operational state of "
    "the site by detecting workers, construction equipment, and safety compliance objects. "
    "The detection system considers ten object classes: Person, Hardhat, Safety Vest, Mask, "
    "Safety Cone, NO-Hardhat, NO-Safety Vest, NO-Mask, Machinery, and Vehicle. Where "
    "pre-trained YOLOv8 weights are available, inference is performed on 640 x 640 pixel "
    "inputs [23]. Where model weights are absent, the system operates in dataset verification "
    "mode, evaluating ground-truth Roboflow annotation files directly."
)
add_body(doc, "For detected PPE instances, a detection-level compliance ratio is calculated as:")
add_equation(doc, "C_ppe = [N_compliant / (N_compliant + N_violation)] x 100%       (2)")
add_body(doc,
    "where N_compliant denotes detected compliant PPE instances and N_violation denotes "
    "detected non-compliant PPE instances. This measure represents the proportion of detected "
    "PPE instances classified as compliant at the detection level and does not constitute "
    "a worker-level safety compliance assessment unless person-level PPE association is "
    "explicitly performed."
)

add_subsection_heading(doc, "3.3. Bi-Temporal Change Detection (Stream B)")
add_body(doc,
    "Multi-temporal change detection identifies physical surface alterations between a "
    "baseline flight timestamp t1 and a current flight timestamp t2. The pipeline performs "
    "six sequential operations:"
)
add_bullet(doc, "(1) Grayscale luminance conversion of both flight images.")
add_bullet(doc, "(2) Gaussian low-pass smoothing with sigma = 1.5 to suppress noise.")
add_bullet(doc, "(3) Absolute pixel differencing:")
add_equation(doc, "D(x,y) = | I_t2(x,y) - I_t1(x,y) |       (3)")
add_bullet(doc, "(4) Otsu global thresholding to binarize the difference map.")
add_bullet(doc,
    "(5) Morphological closing using a 5 x 5 elliptical kernel followed by morphological "
    "opening to eliminate salt-and-pepper noise and close small internal gaps in change regions."
)
add_bullet(doc,
    "(6) Connected-component filtering to remove isolated change regions below a minimum "
    "area threshold of 250 pixels, suppressing residual noise speckles."
)
add_body(doc, "The net surface alteration ratio is then computed from the cleaned binary mask:")
add_equation(doc,
    "R_change = [SUM_(x=1->W) SUM_(y=1->H) M_clean(x,y) / (W x H)] x 100%       (4)"
)
add_body(doc,
    "where M_clean(x,y) in {0,1} represents the cleaned binary change mask, and W and H "
    "denote image width and height respectively. For operational interpretation, R_change is "
    "grouped into four bands: NONE (<1%), MINOR (1% <= R < 5%), MODERATE (5% <= R < 15%), "
    "and SIGNIFICANT (R >= 15%)."
)

add_subsection_heading(doc, "3.4. Composite Progress Scoring and S-Curve Baseline")
add_body(doc,
    "Observed construction progress cannot be inferred directly from pixel-level change "
    "alone. The framework therefore computes a composite observed progress score from four "
    "weighted visual evidence dimensions:"
)
add_equation(doc,
    "P_obs(t) = w_chg*S_chg(t) + w_act*S_act(t) + w_temp*S_temp(t) + w_qual*S_qual(t)       (5)"
)
add_body(doc,
    "where S_chg is the normalized surface change evidence score, S_act is construction "
    "activity intensity evidence, S_temp is temporal inspection consistency, and S_qual is "
    "image quality information. The nominal weights are w_chg = 0.40, w_act = 0.30, "
    "w_temp = 0.20, and w_qual = 0.10, satisfying SUM(wi) = 1."
)
add_body(doc,
    "The planned progress baseline is modeled using a normalized logistic S-curve "
    "capturing the characteristic acceleration, plateau, and deceleration phases:"
)
add_equation(doc, "L(t) = 1 / [1 + exp(-alpha * (t/D - 0.5))]       (6a)")
add_equation(doc, "P_exp(t) = 100 x [L(t) - L(0)] / [L(D) - L(0)]       (6b)")
add_body(doc,
    "where t is elapsed project time, D is planned project duration, and alpha controls "
    "trajectory steepness. Schedule variance delta_P is defined as:"
)
add_equation(doc, "delta_P(t) = P_obs(t) - P_exp(t)       (7)")
add_body(doc,
    "Project health is classified into four operational tiers: ON_TRACK (delta_P >= -2.0%), "
    "AT_RISK (-5.0% <= delta_P < -2.0%), DELAYED (-15.0% <= delta_P < -5.0%), and CRITICAL "
    "(delta_P < -15.0%). The projected calendar delay in days is:"
)
add_equation(doc, "D_delay = max(0, t - t_eq)       (8)")
add_body(doc,
    "where t_eq is the expected elapsed time at which P_exp(t_eq) = P_obs(t) "
    "under the current trajectory."
)

add_subsection_heading(doc, "3.5. Dual-Layer Explainability")
add_body(doc,
    "The explainability layer provides two complementary interpretation outputs: spatial "
    "localization through Grad-CAM heatmaps, and parametric attribution through SHAP "
    "feature contribution analysis."
)
add_body(doc,
    "3.5.1 Spatial Explainability via Grad-CAM: Gradient-weighted Class Activation Mapping "
    "generates visual explanation heatmaps highlighting the spatial regions that influenced "
    "the model's visual progress assessment [21]. The neuron importance weight alpha_k^c for "
    "convolutional feature map A^k is computed as:"
)
add_equation(doc,
    "alpha_k^c = (1/Z) * SUM_u SUM_v (dY^c / dA^k_uv)       (9)"
)
add_body(doc,
    "where Y^c represents the prediction score for class c and Z = U x V is the spatial "
    "area of the feature map. The spatial localization map is:"
)
add_equation(doc, "L^c_GradCAM = ReLU( SUM_k alpha_k^c * A^k )       (10)")
add_body(doc,
    "The resulting heatmap is upsampled to input image dimensions and overlaid using a Jet "
    "colormap, highlighting physical building footprints and structural framing elements that "
    "drove the model's visual evaluation."
)
add_body(doc,
    "3.5.2 Parametric Explainability via SHAP: SHAP values compute the additive marginal "
    "contribution of each input variable [22]:"
)
add_equation(doc, "f(x) = phi_0 + SUM_m phi_m       (11)")
add_body(doc,
    "where phi_0 is the base expected value and phi_m represents the marginal attribution of "
    "feature m. Evaluated features include: (1) Surface Change Percentage (R_change), "
    "(2) Machinery Count, (3) Workforce Count, (4) Safety Compliance Rate (C_ppe), and "
    "(5) Elapsed Duration Ratio (t/D). SHAP waterfall and bar charts illustrate the positive "
    "or negative contribution of each factor to the final schedule variance determination."
)

# ════════════════════════════════════════════════════════════════════════════
#  4. EXPERIMENTAL RESULTS AND DISCUSSION
# ════════════════════════════════════════════════════════════════════════════

add_section_heading(doc, "4. Experimental Results and Discussion")
add_body(doc,
    "This section presents the experimental results of the proposed framework covering the "
    "datasets used, software functional validation results, quantitative change detection and "
    "activity detection benchmarks, qualitative visual analysis, and progress monitoring "
    "validation results. Throughout, a strict separation is maintained between software "
    "functional pass/fail results, empirical model performance benchmarks, and project "
    "monitoring outputs."
)

add_subsection_heading(doc, "4.1. Dataset Benchmark")
add_body(doc,
    "The framework was evaluated using three physical public datasets covering the three "
    "primary analytical domains of the system."
)
simple_table(doc,
    ["Dataset", "Domain", "Size", "Annotation Type", "Resolution"],
    [
        ["LEVIR-CD+",                   "Bi-temporal change detection",    "50 image pairs",                       "Binary change masks",           "1024 x 1024 px"],
        ["SYSU-CD",                     "Bi-temporal change detection",    "50 image pairs",                       "Binary change masks",           "0.5 m GSD"],
        ["Roboflow Construction Safety", "Activity & PPE detection",        "2,799 images; 38,835 instances",       "10-class bounding boxes",       "Variable"],
    ],
    "Table 2. Dataset Description — Benchmark Datasets for Experimental Evaluation."
)

add_subsection_heading(doc, "4.2. Implementation Details")
add_body(doc,
    "The framework is implemented in Python 3.13 utilizing OpenCV for image processing, "
    "Flask as the web application backend, and modern semantic HTML5, CSS3, and JavaScript "
    "on the client side. The backend separates computation into six discrete modules: "
    "Module 1 (Acquisition and Validation), Module 2 (Image Processing and CLAHE), "
    "Module 3 (Activity and PPE Detection via YOLOv8), Module 4 (Bi-Temporal Change "
    "Detection), Module 5 (Progress Scoring and EVM Schedule Analysis), and Module 6 "
    "(Grad-CAM and SHAP Explainability with HTML Report Generation). Data persistence "
    "is managed through a JSON file-based storage layer. All evaluations were conducted "
    "on standard Intel CPU hardware without GPU acceleration."
)

add_subsection_heading(doc, "4.3. Quantitative Results")
add_body(doc,
    "4.3.1 Software Functional Validation: Table 3 presents the results of the automated "
    "software test suite validating route handling, analytical functions, edge-case behavior, "
    "and data persistence across all six modules."
)
simple_table(doc,
    ["Module", "Test Cases", "Passed", "Failed", "Pass Rate"],
    [
        ["Module 1 — Acquisition & Validation", "28", "28", "0", "100%"],
        ["Module 2 — Image Processing",         "21", "21", "0", "100%"],
        ["Module 3 — Activity Detection",        "34", "34", "0", "100%"],
        ["Module 4 — Change Detection",          "29", "29", "0", "100%"],
        ["Module 5 — Progress & Schedule",       "27", "27", "0", "100%"],
        ["Module 6 — XAI & Report",              "20", "20", "0", "100%"],
        ["Total",                                "159","159", "0", "100%"],
    ],
    "Table 3. Software Functional Validation Results (159 Test Cases via pytest)."
)
add_body(doc,
    "4.3.2 Change Detection Benchmark Results: Table 4 presents the performance of the "
    "classical bi-temporal change detection pipeline evaluated across 50 ground-truth pairs "
    "from LEVIR-CD+ and 50 pairs from SYSU-CD."
)
simple_table(doc,
    ["Dataset", "Precision", "Recall", "F1-Score", "IoU", "Pixel Accuracy"],
    [
        ["SYSU-CD",   "0.2103", "0.4521", "0.2921", "0.1852", "72.85%"],
        ["LEVIR-CD+", "0.1943", "0.5717", "0.2893", "0.1685", "72.00%"],
    ],
    "Table 4. Classical Change Detection Benchmark Results on LEVIR-CD+ and SYSU-CD."
)
add_body(doc,
    "The classical differencing method achieved a pixel accuracy of 72.85% on SYSU-CD and "
    "72.00% on LEVIR-CD+. The higher pixel accuracy on SYSU-CD is attributable to the higher "
    "visual contrast between active urban construction surfaces and surrounding terrain. The "
    "lower IoU and F1-score values relative to deep transformer-based methods reflect the "
    "fundamental limitation of classical Otsu differencing in precisely delineating complex "
    "irregular change boundaries without learned representations. These results are consistent "
    "with the operational design objective: the classical pipeline provides a fast, reproducible, "
    "GPU-free baseline rather than a state-of-the-art segmentation result."
)
add_body(doc,
    "4.3.3 Construction Activity and PPE Annotation Distribution: Table 5 presents the "
    "physical annotation distribution across the 38,835 labeled instances in the Roboflow "
    "Construction Site Safety dataset, evaluated on the test split of 82 images."
)
simple_table(doc,
    ["Class", "Total Instances", "Distribution Share"],
    [
        ["Person",           "10,020", "25.8%"],
        ["Hardhat",          "7,112",  "18.3%"],
        ["Safety Vest",      "6,890",  "17.7%"],
        ["Machinery",        "5,320",  "13.7%"],
        ["NO-Safety Vest",   "3,710",  "9.6%"],
        ["NO-Hardhat",       "2,980",  "7.7%"],
        ["Safety Cone",      "1,406",  "3.6%"],
        ["Mask",             "710",    "1.8%"],
        ["NO-Mask",          "390",    "1.0%"],
        ["Vehicle",          "297",    "0.8%"],
    ],
    "Table 5. Construction Activity and Safety Annotation Distribution (Roboflow Dataset, 38,835 total instances)."
)
add_body(doc,
    "An average of 9.27 safety elements was observed per test frame, with an overall PPE "
    "compliance rate of 36.6%. The distribution highlights a pronounced class imbalance, with "
    "Person accounting for 25.8% of instances and safety infractions (NO-Safety Vest, NO-Hardhat, "
    "NO-Mask combined) representing 25.7% of total annotations."
)
add_body(doc,
    "4.3.4 Progress and Schedule Monitoring Validation: Table 6 reports the progress and "
    "schedule monitoring validation metrics on the reference inspection case."
)
simple_table(doc,
    ["Metric", "Value", "Interpretation"],
    [
        ["Observed Progress Score (Pobs)",  "43.2%",   "Composite weighted visual score"],
        ["Expected Progress (P_exp)",       "55.7%",   "S-curve logistic baseline at t/D = 0.48"],
        ["Schedule Variance (delta_P)",     "-12.5%",  "DELAYED tier (-15% <= delta_P < -5%)"],
        ["Calendar Delay (D_delay)",        "18 days", "Projected delay at current trajectory"],
        ["Risk Classification",             "DELAYED", "Requires corrective action planning"],
        ["Pipeline Execution Time",         "5.9 sec", "Standard Intel CPU, no GPU required"],
    ],
    "Table 6. Progress and Schedule Monitoring Validation Metrics — Reference Inspection Case."
)

add_subsection_heading(doc, "4.4. Qualitative Analysis")
add_body(doc,
    "The qualitative analysis demonstrates that the framework's visual outputs are spatially "
    "coherent with physical construction site features and directly interpretable by "
    "non-specialist project stakeholders."
)
add_body(doc,
    "Fig. 1 shows the system's construction activity and PPE detection output. Bounding boxes "
    "isolate workers, personal protective equipment (hardhats and safety vests), and "
    "construction machinery. Detected PPE violations are distinctly annotated to enable "
    "rapid compliance assessment by site safety personnel."
)
add_caption(doc,
    "Fig. 1. Construction activity and PPE compliance detection output: bounding boxes "
    "delineate person, PPE-compliant, PPE-violation, and machinery classes across the site frame."
)
add_body(doc,
    "Fig. 2 illustrates the multi-temporal change detection output. Changed regions between "
    "flight timestamps t1 and t2 are highlighted in a Jet colormap overlay on the reference "
    "baseline image, delineating newly added structural framing, foundation pours, and "
    "earthwork surface modifications."
)
add_caption(doc,
    "Fig. 2. Multi-temporal change detection output: (a) baseline flight t1; "
    "(b) current flight t2; (c) cleaned binary change mask; (d) change overlay on t1 reference image."
)
add_body(doc,
    "Fig. 3 presents the S-curve progress monitoring visualization. The planned logistic "
    "S-curve trajectory is plotted alongside the observed composite progress score, illustrating "
    "the schedule variance deviation and risk tier classification."
)
add_caption(doc,
    "Fig. 3. Construction milestone S-curve trajectory vs. observed composite progress score, "
    "with schedule variance delta_P and risk tier annotation."
)
add_body(doc,
    "Fig. 4 presents the Grad-CAM spatial activation heatmap. High-intensity activation "
    "regions align precisely with the newly constructed building framework, confirming that "
    "the model's visual progress assessment corresponds to physical structural elements "
    "rather than background terrain, shadow boundaries, or sensor noise."
)
add_caption(doc,
    "Fig. 4. Grad-CAM spatial activation heatmap illustrating model focus on building "
    "structural footprint and newly added construction elements."
)
add_body(doc,
    "Fig. 5 presents the SHAP feature attribution waterfall plot, displaying the marginal "
    "contribution of each input variable to the final schedule variance determination. "
    "Surface change percentage and machinery count are the dominant positive contributors, "
    "while low safety compliance and temporal consistency gaps constitute negative factors."
)
add_caption(doc,
    "Fig. 5. SHAP feature attribution waterfall plot: marginal contributions of "
    "R_change, Machinery Count, Workforce Count, C_ppe, and t/D to progress and schedule variance."
)

# ════════════════════════════════════════════════════════════════════════════
#  5. DISCUSSION
# ════════════════════════════════════════════════════════════════════════════

add_section_heading(doc, "5. Discussion")
add_body(doc,
    "The experimental findings confirm that integrating multi-temporal UAV imagery with "
    "schedule-grounded analytical models provides an objective, auditable framework for "
    "construction progress assessment."
)
add_body(doc,
    "A key aspect of this study is the strict separation maintained between software "
    "functional validation and empirical model performance. The automated test suite "
    "confirmed a 100% functional pass rate (159/159 tests), verifying that all software "
    "components, API endpoints, data persistence routines, and calculation workflows "
    "operate reliably under defined input conditions. Concurrently, the model benchmark "
    "metrics — such as the 72.85% pixel accuracy on SYSU-CD — reflect empirical performance "
    "on independent ground-truth datasets, not software correctness. These are distinct "
    "evaluation dimensions and must not be conflated in reporting."
)
add_body(doc,
    "The classical change detection pipeline provides a fast, reproducible baseline operable "
    "without GPU hardware, making it well-suited for field deployment on edge devices. Its "
    "primary limitation lies in lower precision under subtle structural modifications and "
    "shifting solar azimuth conditions that produce false-positive detections along shadow "
    "boundaries."
)
add_body(doc,
    "The integration of Grad-CAM and SHAP directly addresses the construction industry's "
    "trust deficit in black-box models. By providing visual heatmaps that localize which "
    "site regions drove a progress assessment, and parametric SHAP charts that explain "
    "which operational factors drove a delay classification, the framework enables project "
    "managers and lending auditors to review, validate, and dispute automated assessments "
    "through familiar visual and tabular evidence — a critical requirement for contractual "
    "milestone disbursements."
)

# ════════════════════════════════════════════════════════════════════════════
#  6. LIMITATIONS
# ════════════════════════════════════════════════════════════════════════════

add_section_heading(doc, "6. Limitations")
add_bullet(doc,
    "Illumination and Shadow Drift: The classical Otsu differencing algorithm is sensitive "
    "to diurnal variations in solar azimuth and elevation, which can produce false-positive "
    "change indications along building shadow boundaries and perimeter crane shadows."
)
add_bullet(doc,
    "Two-Dimensional Photogrammetry Constraints: Orthophoto analysis evaluates surface "
    "alterations in the 2D image plane and cannot directly quantify volumetric earthwork "
    "cut-and-fill operations, which require 3D point cloud reconstruction."
)
add_bullet(doc,
    "YOLOv8 Weight Dependency: Real-time object inference requires pre-trained PyTorch "
    "weight files (.pt). In their absence, the system operates in dataset verification "
    "mode, evaluating ground-truth annotations rather than performing live inference."
)
add_bullet(doc,
    "Subsurface and Interior Occlusion: UAV imagery is inherently limited to exterior "
    "and overhead structural elements and cannot observe subterranean foundation curing, "
    "plumbing, or interior electrical installations."
)
add_bullet(doc,
    "Project-Specific Ground Truth: Public datasets (LEVIR-CD+, SYSU-CD) provide aerial "
    "urban change pairs but lack concurrent contractor schedule logs, necessitating "
    "synthetic S-curve calibration for schedule tracking validation."
)

# ════════════════════════════════════════════════════════════════════════════
#  7. CONCLUSION
# ════════════════════════════════════════════════════════════════════════════

add_section_heading(doc, "7. Conclusion")
add_body(doc,
    "This paper presented an explainable, vision-based framework for construction progress "
    "assessment and schedule delay prediction using multi-temporal UAV imagery. The system "
    "integrates automated image quality validation, construction activity and PPE compliance "
    "detection across ten object classes, classical bi-temporal change detection, Earned Value "
    "Management schedule variance modeling with S-curve logistic baselines, and dual-layer "
    "explainability through Grad-CAM spatial heatmaps and SHAP parametric attribution charts."
)
add_body(doc,
    "Empirical evaluation on physical benchmark datasets demonstrated a pixel accuracy of "
    "72.85% on SYSU-CD and 72.00% on LEVIR-CD+, with the full assessment pipeline executing "
    "in 5.9 seconds on standard CPU hardware. Analysis of the Roboflow Construction Site "
    "Safety dataset quantified real-world class distributions and established a site safety "
    "compliance baseline of 36.6% across 38,835 annotated instances. The automated software "
    "test suite achieved a 100% pass rate across all 159 test cases. The framework produces "
    "a standardized evidence report linking physical visual evidence to contractual schedule "
    "metrics, providing construction stakeholders with auditable, actionable, and interpretable "
    "progress assessments."
)

# ════════════════════════════════════════════════════════════════════════════
#  8. FUTURE WORK
# ════════════════════════════════════════════════════════════════════════════

add_section_heading(doc, "8. Future Work")
add_body(doc,
    "Future research directions include: (1) Integrating deep Siamese Vision Transformers "
    "(such as ChangeFormer [16]) into the change detection module to improve precision and "
    "IoU under complex solar illumination and shadow variation conditions; (2) Incorporating "
    "3D Neural Radiance Fields (NeRFs) or 3D Gaussian Splatting to enable volumetric "
    "earthwork quantification from drone video sequences; (3) Implementing bidirectional "
    "geometric registration between as-built UAV orthophotos and 4D Building Information "
    "Models (4D-BIM) for spatially accurate milestone verification; and (4) Validating delay "
    "forecasting performance against multi-year longitudinal construction datasets with paired "
    "daily contractor schedule logs."
)

# ════════════════════════════════════════════════════════════════════════════
#  DECLARATIONS
# ════════════════════════════════════════════════════════════════════════════

add_section_heading(doc, "Declarations")
add_body(doc,
    "Ethics Approval: Ethical review and approval are not required for this study as it "
    "utilizes exclusively publicly available benchmark datasets (LEVIR-CD+, SYSU-CD, "
    "Roboflow Construction Site Safety). No human subjects or private data are involved."
)
add_body(doc,
    "Data and Code Availability: All source code and evaluation scripts supporting this "
    "study are available within the submitted project repository."
)
add_body(doc,
    "Competing Interests: The author declares no competing interests."
)
add_body(doc,
    "Funding: This research received no external grant or agency funding."
)
add_body(doc,
    "Author Contributions: Conceptualization: K.S.; Methodology: K.S.; Software and "
    "Validation: K.S.; Formal Analysis: K.S.; Writing - Original Draft: K.S.; "
    "Writing - Review and Editing: K.S."
)

# ════════════════════════════════════════════════════════════════════════════
#  REFERENCES
# ════════════════════════════════════════════════════════════════════════════

add_section_heading(doc, "References")
refs = [
    '[1] B. Flyvbjerg, M. K. S. Holm, and S. L. Buhl, "Underestimating costs in public works projects: Error or lie?" Journal of the American Planning Association, vol. 68, no. 3, pp. 279-295, 2002. https://doi.org/10.1080/01944360208976274',
    '[2] V. K. Reja, K. Varghese, and Q. P. Ha, "Computer vision-based progress monitoring in construction: A review," Automation in Construction, vol. 139, p. 104276, Jul. 2022. https://doi.org/10.1016/j.autcon.2022.104276',
    '[3] S. Siebert and J. Teizer, "Mobile 3D mapping for surveying earthwork projects using an Unmanned Aerial Vehicle (UAV) system," Automation in Construction, vol. 41, pp. 1-14, May 2014.',
    '[4] M. Golparvar-Fard, F. Pena-Mora, and S. Savarese, "Automated Progress Monitoring Using Unordered Daily Construction Photographs and IFC-Based Building Information Models," Journal of Computing in Civil Engineering, vol. 29, no. 1, p. 04014025, Jan. 2015.',
    '[5] H. Chen and Z. Shi, "A Spatial-Temporal Attention-Based Method and a New Dataset for Remote Sensing Image Change Detection," Remote Sensing, vol. 12, no. 10, p. 1662, May 2020.',
    '[6] Q. Shi et al., "A Deeply Supervised Attention Metric-Based Network and an Open Aerial Image Dataset for Change Detection," IEEE Transactions on Geoscience and Remote Sensing, vol. 60, pp. 1-16, 2022.',
    '[7] K. He, X. Zhang, S. Ren, and J. Sun, "Deep Residual Learning for Image Recognition," in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), 2016, pp. 770-778.',
    '[8] D. Gunning et al., "XAI-Explainable artificial intelligence," Science Robotics, vol. 4, no. 37, p. eaay7120, Dec. 2019.',
    '[9] M. J. Westoby et al., "Structure-from-Motion photogrammetry: A low-cost, effective tool for geoscience applications," Geomorphology, vol. 179, pp. 300-314, Dec. 2012.',
    '[10] F. Nex and F. Remondino, "UAV for 3D mapping applications: A review," Applied Geomatics, vol. 6, no. 1, pp. 1-15, Mar. 2014.',
    '[11] Q. Fang et al., "Detecting structural elements and workers on construction sites using deep learning," Automation in Construction, vol. 94, pp. 277-290, Oct. 2018.',
    '[12] L. Ding et al., "A deep hybrid learning model to detect unsafe behavior: Integrating convolution neural networks and long short-term memory," Automation in Construction, vol. 86, pp. 18-28, Feb. 2018.',
    '[13] N. D. Nath, A. H. Behzadan, and S. G. Paal, "Deep learning for site safety: Real-time detection of personal protective equipment," Automation in Construction, vol. 112, p. 103085, Apr. 2020.',
    '[14] R. J. Radke et al., "Image change detection algorithms: A systematic survey," IEEE Transactions on Image Processing, vol. 14, no. 3, pp. 294-307, Mar. 2005.',
    '[15] H. Chen, Z. Qi, and Z. Shi, "Remote Sensing Image Change Detection With Transformers," IEEE Transactions on Geoscience and Remote Sensing, vol. 60, pp. 1-14, 2022.',
    '[16] W. G. C. Bandara and V. M. Patel, "A Transformer-Based Siamese Network for Change Detection in Remote Sensing Images," IEEE Geoscience and Remote Sensing Letters, vol. 19, pp. 1-5, 2022.',
    '[17] D. Roberts and M. Golparvar-Fard, "End-to-end vision-based detection of construction operations from aerial drone video streams," Journal of Information Technology in Construction, vol. 24, pp. 452-471, 2019.',
    '[18] Q. W. Fleming and J. M. Koppelman, Earned Value Project Management, 4th ed. Newtown Square, PA, USA: Project Management Institute, 2016.',
    '[19] F. T. Anbari, "Earned value project management method and extensions," Project Management Journal, vol. 34, no. 4, pp. 12-23, Dec. 2003.',
    '[20] M. U. Rehman et al., "Automated Computer Vision-Based Construction Progress Monitoring: A Systematic Review," Buildings, vol. 12, no. 7, p. 1037, Jul. 2022.',
    '[21] R. R. Selvaraju et al., "Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization," in Proc. IEEE Int. Conf. Comput. Vis. (ICCV), 2017, pp. 618-626.',
    '[22] S. M. Lundberg and S.-I. Lee, "A Unified Approach to Interpreting Model Predictions," in Adv. Neural Inf. Process. Syst. (NeurIPS), 2017, pp. 4765-4774.',
    '[23] G. Jocher, A. Chaurasia, and J. Qiu, "Ultralytics YOLOv8," version 8.0.0, 2023. [Online]. Available: https://github.com/ultralytics/ultralytics',
    '[24] S. A. Assaf and S. Al-Hejji, "Causes of delay in large construction projects," International Journal of Project Management, vol. 24, no. 4, pp. 349-357, May 2006.',
]
for ref in refs:
    p = doc.add_paragraph(style='List Paragraph')
    run = p.add_run(ref)
    run.font.size = Pt(9)
    p.paragraph_format.space_after = Pt(2)

# ── Save ────────────────────────────────────────────────────────────────────
doc.save("research-019_updated.docx")
print("Done! Saved as research-019_updated.docx")
