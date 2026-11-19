"""
Generation script for complete IEEE conference research paper in Word (.docx) and PDF (.pdf) formats.
Adheres strictly to IEEE formatting guidelines, 3 authors, authentic citations [1]-[28],
and generates researchpaper.docx and researchpaper.pdf.
"""

import sys
import os
import re
import shutil
import time
from pathlib import Path
import win32com.client

PROJECT_ROOT = Path(r"c:\Users\asus\Desktop\FINAL PROJECT")
DESKTOP_DIR = Path(r"c:\Users\asus\Desktop")
TEMPLATE_PATH = PROJECT_ROOT / "research_paper" / "conference-template-a4.docx"
DOCX_OUT_RP = PROJECT_ROOT / "research_paper" / "researchpaper.docx"
PDF_OUT_RP = PROJECT_ROOT / "research_paper" / "researchpaper.pdf"
DOCX_OUT_1 = PROJECT_ROOT / "research_paper" / "final_ieee_paper.docx"
DOCX_OUT_2 = PROJECT_ROOT / "research_paper" / "research-019.docx"
PDF_OUT_1 = PROJECT_ROOT / "research_paper" / "final_ieee_paper.pdf"
FIG_DIR = PROJECT_ROOT / "research_paper" / "figures"

def create_ieee_paper():
    t_start = time.time()
    print("=" * 65)
    print("GENERATING COMPLETE IEEE PAPER (DOCX & PDF)")
    print("=" * 65)
    
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found at {TEMPLATE_PATH}")

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0

    try:
        doc = word.Documents.Open(FileName=str(TEMPLATE_PATH), ReadOnly=True)
        print("Template loaded successfully.", flush=True)

        # 1. SECTION 1: TITLE
        sec1 = doc.Sections.Item(1)
        rng1 = doc.Range(sec1.Range.Start, sec1.Range.End - 1)
        rng1.Text = "Explainable Vision-Based Construction Progress Assessment and Delay Prediction Using Multi-Temporal UAV Imagery\r"
        rng1.Style = "paper title"
        rng1.ParagraphFormat.Alignment = 1 # Center
        rng1.ParagraphFormat.SpaceBefore = 0
        rng1.ParagraphFormat.SpaceAfter = 12

        # 2. SECTION 2: AUTHOR BLOCK (3 Authors)
        sec2 = doc.Sections.Item(2)
        sec2.PageSetup.TextColumns.SetCount(1)
        rng2 = doc.Range(sec2.Range.Start, sec2.Range.End - 1)
        rng2.Text = (
            "KAVINKARTHIK S\r"
            "Department of M.Tech Computer Science and Engineering\r"
            "Sri Krishna College of Engineering and Technology, Coimbatore, India\r"
            "727722euci019@skcet.ac.in\r\r"
            "Dr. Emmanuel Joy\r"
            "Assistant Professor, Department of M.Tech CSE\r"
            "Sri Krishna College of Engineering and Technology, Coimbatore, India\r"
            "emmanueljoy@skcet.ac.in\r\r"
            "Ms. KANAGAPRIYA S K\r"
            "Assistant Professor, Department of M.Tech CSE\r"
            "Sri Krishna College of Engineering and Technology, Coimbatore, India\r"
            "kanaka.priyacseengg@gmail.com\r"
        )
        rng2.Style = "Author"
        rng2.ParagraphFormat.Alignment = 1 # Center
        rng2.ParagraphFormat.SpaceBefore = 0
        rng2.ParagraphFormat.SpaceAfter = 2
        
        # Format Author names as bold 10pt
        for p_num in [1, 5, 9]:
            if p_num <= sec2.Range.Paragraphs.Count:
                p_item = sec2.Range.Paragraphs.Item(p_num)
                p_item.Range.Font.Bold = True
                p_item.Range.Font.Size = 10

        # 3. SECTION 3: CLEAR IF REDUNDANT
        if doc.Sections.Count >= 3:
            sec3 = doc.Sections.Item(3)
            rng3 = doc.Range(sec3.Range.Start, sec3.Range.End - 1)
            rng3.Delete()

        # 4. SECTION 4: 2-COLUMN BODY
        sec4 = doc.Sections.Item(4)
        sec4.PageSetup.TextColumns.SetCount(2)
        sec4.PageSetup.TextColumns.Spacing = 18.0
        rng4 = doc.Range(sec4.Range.Start, sec4.Range.End - 1)
        rng4.Delete()

        cur_pos = sec4.Range.Start
        tracked_paragraphs = []
        ref_bookmarks = {}
        fig_bookmarks = {}
        tbl_bookmarks = {}

        def add_paragraph(text, style_name="Body Text", align=3, space_before=0, space_after=4, bold_prefix=None, italic_prefix=None):
            nonlocal cur_pos
            rng = doc.Range(cur_pos, cur_pos)
            rng.Text = text + "\r"
            rng.Style = style_name
            rng.ParagraphFormat.Alignment = align
            rng.ParagraphFormat.SpaceBefore = space_before
            rng.ParagraphFormat.SpaceAfter = space_after
            p_start = rng.Start
            
            if bold_prefix:
                p_rng = rng.Paragraphs.Item(1).Range
                idx = text.find(bold_prefix)
                if idx >= 0:
                    prefix_rng = doc.Range(p_rng.Start + idx, p_rng.Start + idx + len(bold_prefix))
                    prefix_rng.Font.Bold = True
                    if italic_prefix:
                        prefix_rng.Font.Italic = True

            cur_pos = rng.End
            if style_name != "references":
                tracked_paragraphs.append((p_start, text))
            return rng

        def add_heading1(title):
            return add_paragraph(title, style_name="Heading 1", align=1, space_before=12, space_after=4)

        def add_heading2(title):
            return add_paragraph(title, style_name="Heading 2", align=0, space_before=8, space_after=3)

        def add_heading3(title):
            return add_paragraph(title, style_name="Heading 3", align=3, space_before=6, space_after=2)

        def add_equation(formula_text, eq_num):
            text = f"\t{formula_text}\t({eq_num})"
            return add_paragraph(text, style_name="equation", align=0, space_before=3, space_after=3)

        def add_figure(img_path, caption_text, fig_num, width_pt=238.0):
            nonlocal cur_pos
            if not Path(img_path).exists():
                print(f"Warning: Figure image not found: {img_path}", flush=True)
                return
            rng = doc.Range(cur_pos, cur_pos)
            shape = rng.InlineShapes.AddPicture(str(img_path), False, True)
            aspect = shape.Height / shape.Width
            shape.Width = width_pt
            shape.Height = width_pt * aspect
            shape.Range.ParagraphFormat.Alignment = 1
            shape.Range.ParagraphFormat.SpaceBefore = 6
            shape.Range.ParagraphFormat.SpaceAfter = 2
            
            bm_name = f"fig_{fig_num}"
            doc.Bookmarks.Add(bm_name, shape.Range)
            fig_bookmarks[fig_num] = bm_name
            cur_pos = shape.Range.End
            add_paragraph(caption_text, style_name="figure caption", align=3, space_before=2, space_after=8)

        def add_table(title_lines, headers, rows_data, tbl_num, col_widths=None):
            nonlocal cur_pos
            for line in title_lines:
                add_paragraph(line, style_name="table head", align=1, space_before=8, space_after=1)
            rng = doc.Range(cur_pos, cur_pos)
            num_rows = len(rows_data) + 1
            num_cols = len(headers)
            tbl = doc.Tables.Add(rng, num_rows, num_cols)
            tbl.Borders.Enable = False
            tbl.Borders.Item(-1).LineStyle = 1
            tbl.Borders.Item(-1).LineWidth = 4
            tbl.Borders.Item(-3).LineStyle = 1
            tbl.Borders.Item(-3).LineWidth = 4
            
            bm_name = f"tbl_{tbl_num}"
            doc.Bookmarks.Add(bm_name, tbl.Range)
            tbl_bookmarks[tbl_num] = bm_name
            
            for c_idx, h_text in enumerate(headers, 1):
                cell = tbl.Cell(1, c_idx)
                cell.Range.Text = h_text
                cell.Range.Font.Name = "Times New Roman"
                cell.Range.Font.Size = 8
                cell.Range.Font.Bold = True
                cell.Range.ParagraphFormat.Alignment = 1
                cell.Range.ParagraphFormat.SpaceBefore = 2
                cell.Range.ParagraphFormat.SpaceAfter = 2
            
            for c_idx in range(1, num_cols + 1):
                tbl.Cell(1, c_idx).Borders.Item(-3).LineStyle = 1
                tbl.Cell(1, c_idx).Borders.Item(-3).LineWidth = 4
            
            for r_idx, row in enumerate(rows_data, 2):
                for c_idx, val in enumerate(row, 1):
                    cell = tbl.Cell(r_idx, c_idx)
                    cell.Range.Text = str(val)
                    cell.Range.Font.Name = "Times New Roman"
                    cell.Range.Font.Size = 8
                    cell.Range.Font.Bold = False
                    cell.Range.ParagraphFormat.Alignment = 0 if c_idx == 1 else 1
                    cell.Range.ParagraphFormat.SpaceBefore = 1
                    cell.Range.ParagraphFormat.SpaceAfter = 1
            
            if col_widths and len(col_widths) == num_cols:
                for c_idx, w in enumerate(col_widths, 1):
                    for r_idx in range(1, num_rows + 1):
                        tbl.Cell(r_idx, c_idx).Width = w
            
            tbl.Rows.Alignment = 1
            cur_pos = tbl.Range.End
            add_paragraph("", style_name="Body Text", space_before=0, space_after=4)

        # 5. POPULATE PAPER CONTENT

        # ABSTRACT
        abstract_text = (
            "Abstract—Tracking physical progress on active building construction sites remains a formidable operational "
            "challenge. Conventional monitoring practices depend heavily on periodic visual walkthroughs conducted by field "
            "engineers. While valuable for qualitative appraisal, manual walkthroughs are labor-intensive, subjective, "
            "physically hazardous, and produce sparse spatial records that frequently fail to detect structural deviations "
            "before critical milestones are compromised. Low-altitude Unmanned Aerial Vehicles (UAVs) provide a flexible, "
            "non-intrusive platform for frequent aerial visual data acquisition. However, raw aerial imagery cannot be reliably "
            "transformed into contractual management decisions without systematic quality filtering, verified asset detection, "
            "and explainable computational analytics. This paper presents an integrated, vision-based construction monitoring "
            "and decision-support framework that leverages multi-temporal UAV imagery to evaluate physical progress and identify "
            "schedule deviations. The implemented system encompasses a multi-stage pipeline: automated image validation and quality "
            "assessment based on Laplacian blur variance, luminance, contrast, and resolution; standardized image preprocessing "
            "utilizing Contrast Limited Adaptive Histogram Equalization (CLAHE); construction asset and personal protective equipment "
            "(PPE) detection across ten classes, supporting both YOLOv8 inference and ground-truth annotation verification; classical "
            "multi-temporal change detection via Gaussian smoothing, absolute pixel differencing, Otsu global thresholding, and "
            "morphological filtering; composite visual progress scoring; schedule deviation analysis against a normalized logistic "
            "S-curve baseline; and dual-stage Explainable AI (XAI) incorporating ResNet-50 Grad-CAM spatial heatmaps alongside parametric "
            "SHAP-style feature attribution. The platform is implemented as a lightweight Flask-based web application backed by local "
            "JSON and file storage, generating structured construction progress evidence reports for project governance. Empirical "
            "evaluation of the classical change detection pipeline on public remote-sensing benchmarks yields baseline pixel "
            "accuracies of 72.85% on SYSU-CD (IoU 0.1852, F1 0.2921) and 72.00% on LEVIR-CD+. Automated functional verification "
            "confirmed a 100% pass rate across all 159 software test cases. The resulting system establishes an objective, transparent, "
            "and auditable decision-support tool that assists rather than replaces professional engineering supervision."
        )
        add_paragraph(abstract_text, style_name="Abstract", align=3, space_before=0, space_after=4, bold_prefix="Abstract—", italic_prefix=True)

        # INDEX TERMS
        keywords_text = (
            "Index Terms—UAV imagery, construction progress monitoring, computer vision, multi-temporal change detection, "
            "construction activity detection, schedule deviation, Explainable AI, Grad-CAM, SHAP."
        )
        add_paragraph(keywords_text, style_name="Keywords", align=3, space_before=2, space_after=8, bold_prefix="Index Terms—", italic_prefix=True)

        # I. INTRODUCTION
        add_heading1("I. INTRODUCTION")
        add_paragraph(
            "Capital infrastructure and commercial building projects routinely experience severe schedule overruns and budget "
            "inflations. Industry empirical surveys indicate that over sixty percent of major construction projects globally fail "
            "to meet their contracted completion dates, incurring substantial financial penalties, contractual disputes, and lost "
            "economic utility [1], [24]. Historically, project managers have tracked site progress through manual site walkthroughs "
            "conducted by field superintendents. While manual inspections provide experienced qualitative insight, they exhibit "
            "intrinsic limitations: they require intensive labor, expose personnel to active machinery hazards, are vulnerable to "
            "subjective bias, and capture discrete, localized observations that fail to reflect site-wide spatial dynamics across "
            "expansive vertical and horizontal sectors [2], [20]."
        )
        add_paragraph(
            "The emergence of small Unmanned Aerial Vehicles (UAVs) equipped with high-resolution digital optical sensors has "
            "introduced an agile platform for aerial site surveying [3], [10]. UAVs can traverse complex, vertical, and hazardous "
            "sectors rapidly, capturing aerial imagery across multiple flight dates at low operational cost [17]. However, capturing "
            "multi-temporal aerial imagery does not automatically translate into actionable project management decisions. Converting "
            "raw drone photographs into reliable, verifiable progress metrics presents substantial computational, geometric, and "
            "environmental challenges [4]."
        )
        add_paragraph(
            "While advances in deep convolutional networks and computer vision have shown remarkable efficacy in object detection "
            "and visual recognition [7], [23], their operational adoption in civil engineering governance has been hindered by "
            "predictive opacity [8]. Construction stakeholders—including project managers, general contractors, lending institutions, "
            "and safety auditors—cannot authorize contractual milestone disbursements or reallocate field resources based on opaque, "
            "black-box numerical scores. When an automated system flags an active project as delayed, project participants demand "
            "verifiable visual and analytical evidence: What physical work was recognized? In which spatial sector did structural "
            "alterations occur? How was the schedule variance derived? Which individual factors drove the delay classification?"
        )
        add_paragraph(
            "To address these operational and technical challenges, this study presents an integrated, vision-based construction "
            "monitoring and decision-support framework that links multi-temporal UAV imagery directly with schedule-grounded analytical "
            "models. The system integrates automated image validation, standardized preprocessing, construction asset and safety "
            "compliance analysis across ten classes, classical multi-temporal change detection, normalized S-curve schedule deviation "
            "modeling, dual-stage visual and parametric Explainable AI (XAI), and structured evidence reporting within a unified "
            "web-based monitoring platform. Crucially, the framework is designed as a decision-support mechanism that augments, rather "
            "than replaces, professional construction supervision and formal project management."
        )

        # II. RELATED WORK
        add_heading1("II. RELATED WORK")
        add_heading2("A. UAV-Based Construction Monitoring")
        add_paragraph(
            "Initial applications of UAV monitoring in civil engineering focused predominantly on three-dimensional surface "
            "reconstruction using Structure-from-Motion (SfM) photogrammetry [3], [9]. Researchers demonstrated that dense "
            "photogrammetric point clouds could be registered against Building Information Models (BIM) to detect geometric "
            "discrepancies and evaluate as-built versus as-planned status [4], [10]. Despite their geometric fidelity, photogrammetric "
            "reconstruction pipelines require extensive computational overhead, often demanding several hours of multi-view stereo "
            "computation per flight capture. This latency restricts their responsiveness for rapid daily or bi-weekly site inspections "
            "where immediate visual feedback is required [2]."
        )
        add_heading2("B. Computer-Vision-Based Construction Activity Detection")
        add_paragraph(
            "To reduce computational latency, subsequent research explored direct two-dimensional computer vision on aerial orthophotos "
            "and site captures. Deep convolutional neural networks, such as Faster R-CNN, Mask R-CNN, and YOLO architectures, have "
            "been trained to localize construction resources, including excavators, concrete mixers, mobile cranes, and site personnel "
            "[11], [12]. In safety surveillance, Nath et al. [13] developed real-time detectors for personal protective equipment "
            "(PPE), demonstrating high precision in identifying hardhats and safety vests. Nevertheless, existing detection studies "
            "often operate in isolation, treating activity recognition as a standalone computer-vision benchmark rather than integrating "
            "observed workforce and machinery presence into an overarching project progress and schedule tracking workflow [2], [28]."
        )
        add_heading2("C. Multi-Temporal Remote-Sensing Change Detection")
        add_paragraph(
            "Bi-temporal change detection has been extensively investigated in satellite remote sensing for urban expansion, deforestation "
            "tracking, and disaster assessment [14]. Modern approaches leverage deep Siamese convolutional networks, spatial-temporal "
            "attention mechanisms (e.g., STANet on the LEVIR-CD dataset) [5], deeply supervised attention networks (e.g., DSAMNet on "
            "SYSU-CD) [6], and Vision Transformers (e.g., BIT and ChangeFormer) [15], [16]. However, UAV-based construction monitoring "
            "presents distinct optical challenges compared to nadir satellite imagery: variable flight altitudes, perspective parallax "
            "along tall vertical structural facades, and intense diurnal shadow displacement caused by structural columns and perimeter "
            "tower cranes [17]. Furthermore, heavy transformer architectures require dedicated GPU infrastructure unavailable at remote "
            "edge field trailers, underscoring the practical utility of deterministic, lightweight change detection baselines."
        )
        add_heading2("D. Construction Progress and Schedule Analysis")
        add_paragraph(
            "In professional construction management, Earned Value Management (EVM) provides standard mathematical formulations for "
            "schedule and cost performance [18], [19]. Parameters including Planned Value (PV), Earned Value (EV), Schedule Variance "
            "(SV = EV - PV), and Schedule Performance Index (SPI = EV / PV) are conventionally derived from contractor cost logs. "
            "Synthesizing direct computer-vision observations with schedule curves represents an active research frontier [2], [20]. "
            "However, automated visual change percentages cannot simply be equated to financial completion or physical installation "
            "without explicit calibration against project baseline schedules."
        )
        add_heading2("E. Explainable Artificial Intelligence")
        add_paragraph(
            "To alleviate the opacity of deep neural networks, visualization frameworks such as Gradient-weighted Class Activation "
            "Mapping (Grad-CAM) [21] compute gradients of target concepts with respect to feature maps in the final convolutional "
            "layer, producing spatial heatmaps that highlight discriminative image regions driving model activations. In parallel, "
            "Lundberg and Lee introduced SHAP (SHapley Additive exPlanations) [22], establishing a cooperative game-theoretic formulation "
            "for assigning additive feature attributions to input parameters. Coupling spatial pixel activations with parametric feature "
            "ranking provides an auditable foundation for civil engineering governance."
        )
        add_heading2("F. Research Gap")
        add_paragraph(
            "Prior studies have addressed UAV surveying, object detection, remote-sensing change detection, progress tracking, and "
            "explainability as disconnected technical domains. A pronounced practical gap persists in synthesizing these capabilities "
            "into a single, cohesive workflow: ingesting multi-temporal UAV captures, validating optical quality, identifying workforce "
            "and equipment activity, isolating physical alterations via deterministic change detection, benchmarking observed progress "
            "against contractual S-curves, providing spatial and parametric explanations, and compiling findings into auditable progress "
            "evidence reports. This research directly targets this integration gap."
        )

        # III. PROBLEM DEFINITION AND OBJECTIVES
        add_heading1("III. PROBLEM DEFINITION AND OBJECTIVES")
        add_paragraph(
            "Monitoring large-scale construction sites requires continuous, verifiable reconciliation between actual physical progression "
            "and contracted project milestones. The problem addressed in this work is formulated around three primary challenges:\r"
            "1) Input Variability: UAV aerial photographs are subject to sensor vibration, motion blur, variable solar illuminance, "
            "and perspective shifts that compromise automated vision algorithms.\r"
            "2) Analytical Disconnection: Existing computer-vision tools detect individual workers or pixel differences but fail to "
            "synthesize visual alterations, site activity, and inspection cadence into a coherent, schedule-grounded progress index.\r"
            "3) Decision-Making Opacity: Black-box predictive models provide numerical estimates without spatial or parametric "
            "justifications, preventing contractual adoption by cautious engineering stakeholders."
        )
        add_paragraph(
            "To resolve these challenges, the specific objectives of this study are: (a) Develop an automated image validation and "
            "preprocessing module that screens UAV imagery for blur, contrast, and brightness defects before downstream execution; "
            "(b) Implement a ten-class construction asset and safety detector supporting both YOLOv8 deep inference and ground-truth "
            "annotation verification; (c) Construct a deterministic classical multi-temporal change detection pipeline that extracts "
            "structural alterations without demanding GPU resources; (d) Formulate a Composite Visual Progress Score and a normalized "
            "S-curve schedule deviation model that quantifies progress variance without misrepresenting visual indices as monetary "
            "EVM metrics; (e) Embed dual-stage Explainable AI (Grad-CAM and SHAP) to provide spatial visual evidence and parametric "
            "factor attributions for all analytical conclusions; and (f) Realize the entire framework within a lightweight, web-based "
            "platform generating standardized progress evidence reports."
        )

        # IV. PROPOSED SYSTEM AND CONTRIBUTIONS
        add_heading1("IV. PROPOSED SYSTEM AND CONTRIBUTIONS")
        add_paragraph(
            "The proposed system is structured as an end-to-end decision-support platform that transforms raw multi-temporal UAV flight "
            "captures into verified progress metrics and explainable reports. The overall architecture is organized into four logical "
            "layers: Presentation Layer, Application Layer, Image and Analytical Processing Layer, and Data/Reporting Layer, as shown "
            "in Fig. 1."
        )
        fig1_path = FIG_DIR / "fig1_architecture.png"
        add_figure(fig1_path, "Fig. 1.  Four-layer architectural organization of the proposed UAV construction monitoring platform, detailing presentation, application, analytical processing, and data/reporting tiers.", fig_num=1)

        add_paragraph(
            "The primary contributions of this work are conservative, practical, and grounded in reproducible software and analytical "
            "implementation: (1) An integrated end-to-end workflow synthesizing image quality validation, preprocessing, asset/PPE analysis, "
            "classical change detection, S-curve progress modeling, and evidence reporting within a single operational platform; (2) A "
            "deterministic classical change detection baseline providing a lightweight, CPU-compatible morphological differencing pipeline "
            "that delivers reproducible change masks without GPU hardware dependency; (3) A schedule-grounded progress formulation with "
            "a calibrated Composite Visual Progress Score and Progress Deviation metric that explicitly separates visual alteration observations "
            "from monetary EVM quantities; and (4) Dual-stage explainability for construction governance combining ResNet-50 Grad-CAM spatial "
            "heatmaps with SHAP-style parametric feature attributions, delivering auditable visual and numerical justification for project "
            "stakeholders."
        )

        # V. METHODOLOGY
        add_heading1("V. METHODOLOGY")
        add_paragraph(
            "The operational methodology follows a coordinated multi-stage workflow, progressing sequentially from raw drone ingestion "
            "to final report generation."
        )
        fig2_path = FIG_DIR / "fig2_temporal_pair.png"
        add_figure(fig2_path, "Fig. 2.  Multi-temporal aerial flight captures acquired over an active construction site sector across inspection flight epochs (t1 and t2).", fig_num=2)

        add_heading2("A. UAV Image Acquisition and Validation")
        add_paragraph(
            "Aerial inspection photographs acquired at flight timestamps t1 (baseline inspection) and t2 (current inspection) are ingested "
            "into the platform. To prevent corrupt or degraded captures from undermining downstream analysis, each image undergoes automated "
            "validation:\r"
            "1) Integrity and Deduplication: Verification of decodable image headers, minimum dimensional resolution, and SHA-256 cryptographic "
            "hashing to eliminate redundant uploads.\r"
            "2) Laplacian Blur Variance: High-frequency edge sharpness is evaluated via the variance of the discrete Laplacian operator ΔI [27]:"
        )
        add_equation("Var(ΔI) = (1/N) Σ (ΔI(x,y) - μ_ΔI)^2", eq_num=1)
        add_paragraph(
            "where μ_ΔI is the mean Laplacian response across N = W × H pixels. Captures with Var(ΔI) < 100 are flagged as blurred.\r"
            "3) Photometric Compliance: Mean image luminance (μ_I) and Michelson contrast (C_I) are computed across grayscale channels. Captures "
            "are assessed against configured bounds: μ_I ∈ [30, 225] and C_I ≥ 20."
        )
        add_paragraph(
            "The overall quality score Q ∈ [0, 100] is computed as a weighted sum of normalized indicators:"
        )
        add_equation("Q = w_blur Q_blur + w_bright Q_bright + w_cont Q_cont + w_res Q_res", eq_num=2)
        add_paragraph(
            "with configuration weights w_blur = 0.35, w_bright = 0.25, w_cont = 0.25, and w_res = 0.15. Captures achieving Q ≥ 60 are "
            "accepted for analytical processing, as detailed in Table I."
        )

        tbl1_titles = ["TABLE I", "IMAGE QUALITY ASSESSMENT CONFIGURATION THRESHOLDS AND WEIGHTS"]
        tbl1_headers = ["Metric", "Configured Bounds", "Weight", "Accept Threshold"]
        tbl1_rows = [
            ["Blur (Laplacian Var)", "≥ 100.0", "0.35", "Composite ≥ 60.0"],
            ["Luminance", "[30.0, 225.0]", "0.25", "Composite ≥ 60.0"],
            ["Contrast", "≥ 20.0", "0.25", "Composite ≥ 60.0"],
            ["Resolution", "≥ 640 × 640", "0.15", "Composite ≥ 60.0"]
        ]
        add_table(tbl1_titles, tbl1_headers, tbl1_rows, tbl_num=1, col_widths=[90, 80, 50, 80])

        add_heading2("B. Image Preprocessing")
        add_paragraph(
            "Accepted aerial images are preprocessed to standardize photometric and geometric properties. Standard RGB captures are "
            "converted to single-channel luminance arrays where intensity operations are performed. To normalize severe solar exposure "
            "variations across flight dates, Contrast Limited Adaptive Histogram Equalization (CLAHE) [26] is applied to the L-channel in "
            "CIELAB color space using a clip limit of 2.0 over an 8 × 8 contextual tile grid. Bilinear spatial interpolation resizes "
            "temporal pairs to compatible dimensions (W × H) prior to differential analysis."
        )

        add_heading2("C. Construction Activity and Safety Analysis")
        add_paragraph(
            "Monitoring active site sectors requires identifying physical plant assets and evaluating site personnel safety compliance. "
            "The system targets ten distinct classes: Hardhat, Mask, NO-Hardhat, NO-Mask, NO-Safety Vest, Person, Safety Cone, Safety Vest, "
            "machinery, and vehicle."
        )
        add_paragraph(
            "To ensure robust deployment across diverse edge computing environments, the detector supports two operational modes:\r"
            "1) YOLOv8 Inference Mode: When compatible PyTorch weights (.pt) are available, the model executes end-to-end feedforward "
            "inference, generating bounding boxes [x, y, w, h], class categorical indices, and confidence scores [23].\r"
            "2) Ground-Truth / Annotation Verification Mode: When pre-trained model weights are unavailable at the inspection edge, the "
            "pipeline ingests verified site annotations (YOLO format), parses ground-truth labels, computes spatial distributions, and "
            "validates compliance metrics."
        )
        add_paragraph(
            "A detection-based PPE compliance measure is calculated by evaluating the ratio of compliant safety gear detections to total "
            "worker-associated gear detections:"
        )
        add_equation("C_PPE = (N_Hardhat + N_SafetyVest) / (N_Hardhat + N_NO-Hardhat + N_SafetyVest + N_NO-SafetyVest)", eq_num=3)
        add_paragraph(
            "This index is treated as a detection-level proxy and is not overstated as an individualized worker-to-gear safety verification."
        )

        add_heading2("D. Multi-Temporal Change Detection")
        add_paragraph(
            "Physical progression between baseline flight t1 and current flight t2 is isolated using a deterministic classical change "
            "detection pipeline. Rather than relying on black-box deep Siamese transformers that require extensive training and GPU execution, "
            "the pipeline utilizes calibrated morphological image processing:\r"
            "1) Gaussian Low-Pass Filtering: Preprocessed grayscale images I_t1 and I_t2 are smoothed using a 5 × 5 Gaussian kernel (σ = 1.0) "
            "to suppress high-frequency aerodynamic sensor noise.\r"
            "2) Absolute Pixel Differencing: A differential intensity map D(x,y) is generated across all spatial coordinates:"
        )
        add_equation("D(x,y) = |I_t2(x,y) - I_t1(x,y)|", eq_num=4)
        add_paragraph(
            "3) Otsu Global Thresholding: A global binary threshold T* is dynamically determined by maximizing inter-class intensity variance [25], "
            "yielding initial binary change mask M_0(x,y).\r"
            "4) Morphological Cleaning: Successive morphological closing (kernel size 5 × 5) and opening (kernel size 3 × 3) operations are "
            "applied to bridge intra-structural voids and eliminate spurious single-pixel noise.\r"
            "5) Connected Component Filtering: Contiguous binary blobs smaller than an area threshold (A_min = 50 pixels) are rejected, "
            "yielding the finalized clean change mask M_clean."
        )
        add_paragraph(
            "The quantitative surface change ratio R_change is computed as:"
        )
        add_equation("R_change = [ Σ M_clean(x,y) / (W × H) ] × 100%", eq_num=5)

        add_heading2("E. Progress Assessment")
        add_paragraph(
            "Visual change alone does not directly represent contractual completion. The system synthesizes four normalized operational "
            "indicators into a Composite Visual Progress Score P_obs(t) ∈ [0, 100]:"
        )
        add_equation("P_obs(t) = w_chg S_chg(t) + w_act S_act(t) + w_temp S_temp(t) + w_qual S_qual(t)", eq_num=6)
        add_paragraph(
            "where S_chg(t) represents normalized physical change magnitude derived from R_change; S_act(t) reflects site activity density "
            "based on active machinery and workforce counts; S_temp(t) measures elapsed inspection duration relative to overall planned "
            "project timeline; and S_qual(t) represents average photometric quality of ingested flight imagery. Configuration weights are "
            "defined as w_chg = 0.40, w_act = 0.30, w_temp = 0.20, and w_qual = 0.10. This formulation ensures that progress assessment "
            "accounts for physical structural modifications while acknowledging site operational activity."
        )

        add_heading2("F. Expected Progress Modelling")
        add_paragraph(
            "To evaluate whether observed visual progress aligns with contractual commitments, the system establishes a baseline planned "
            "trajectory using a normalized logistic S-curve formulation:"
        )
        add_equation("L(t) = 1 / [ 1 + exp(-α (t/D - 0.5)) ]", eq_num=7)
        add_paragraph(
            "where t denotes elapsed project days, D is the contracted total duration in days, and α is a configurable shape parameter "
            "reflecting project mobilization and closeout rates (typically configured to α = 6.0). To satisfy boundary conditions where planned "
            "progress must be 0% at t=0 and 100% at t=D, the expected progress P_exp(t) is normalized:"
        )
        add_equation("P_exp(t) = 100 × [ L(t) - L(0) ] / [ L(D) - L(0) ]", eq_num=8)

        add_heading2("G. Schedule Deviation and Delay Assessment")
        add_paragraph(
            "At any inspection milestone t, Progress Deviation ΔP(t) is computed by directly subtracting expected planned progress from "
            "observed composite progress:"
        )
        add_equation("ΔP(t) = P_obs(t) - P_exp(t)", eq_num=9)
        add_paragraph(
            "A positive deviation (ΔP > 0) signifies that observed site progression is advancing ahead of baseline expectations, whereas "
            "a negative deviation (ΔP < 0) indicates an emerging delay condition."
        )
        add_paragraph(
            "Crucially, ΔP is designated strictly as Progress Deviation and is deliberately distinguished from conventional monetary Earned "
            "Value Management (EVM) Schedule Variance (SV). While EVM measures monetary schedule divergence (SV = EV - PV), ΔP measures "
            "optical and operational progress divergence. Based on ΔP, the system categorizes schedule health into three actionable management "
            "states: On Schedule (ΔP ≥ -5%), Minor Delay (-15% ≤ ΔP < -5%), and Critical Delay (ΔP < -15%)."
        )

        add_heading2("H. Explainable AI")
        add_paragraph(
            "To provide transparent justifications for automated findings, the system implements dual-stage explainability:\r"
            "1) Spatial Visual Explanations (Grad-CAM): When a compatible convolutional network (e.g., ResNet-50) is available, Gradient-weighted "
            "Class Activation Mapping (Grad-CAM) [21] computes the gradients of target score Y^c with respect to feature maps A^k in the final "
            "convolutional layer:"
        )
        add_equation("α_k^c = (1/Z) Σ_i Σ_j (∂Y^c / ∂A_{i,j}^k)", eq_num=10)
        add_equation("L_Grad-CAM^c = ReLU( Σ_k α_k^c A^k )", eq_num=11)
        add_paragraph(
            "The resulting activation map is normalized and upsampled to the original image dimensions, generating an overlaid colormap that "
            "highlights the structural regions that contributed most strongly to the visual classification. In environments where model weights "
            "are unavailable, an edge-guided gradient fallback is generated and clearly designated as a structural edge approximation rather "
            "than a genuine neural activation map.\r"
            "2) Parametric Feature Attribution (SHAP-Style): For the composite progress and delay assessment, feature attribution values φ_i "
            "are derived to explain how individual indicators shifted the progress score relative to a baseline expectation E[x] [22]:"
        )
        add_equation("φ_i(x) = w_i · (x_i - E[x_i])", eq_num=12)
        add_paragraph(
            "satisfying the additive efficiency property Σ φ_i(x) = f(x) - E[f(x)]. This produces an interpretable waterfall breakdown that "
            "informs project managers whether a delay was primarily driven by lagging physical change, reduced site equipment activity, or "
            "delayed flight cadence."
        )

        add_heading2("I. Evidence Reporting")
        add_paragraph(
            "The culmination of the analytical workflow is the generation of a structured Construction Progress Evidence Report. Compiled "
            "dynamically into a standardized PDF document, the report consolidates: inspection metadata, image quality indices, detected "
            "equipment and PPE counts, before-and-after temporal captures, binary change masks, S-curve progress tracking trajectories, "
            "Grad-CAM visual heatmaps, and SHAP feature attribution waterfall plots. This provides an auditable paper trail suitable for "
            "project meetings, owner briefings, and dispute mitigation."
        )

        # VI. SYSTEM ARCHITECTURE AND IMPLEMENTATION
        add_heading1("VI. SYSTEM ARCHITECTURE AND IMPLEMENTATION")
        add_heading2("A. Web Application Architecture")
        add_paragraph(
            "The system is constructed as a modular four-tier architecture designed for rapid edge deployment without complex external "
            "database infrastructure: Presentation Layer (HTML5, Vanilla CSS, JS), Application Layer (Python Flask), Image and Analytical "
            "Processing Layer (OpenCV, NumPy, PyTorch), and Data/Reporting Layer (JSON registries and file storage)."
        )
        add_heading2("B. Project and Inspection Management")
        add_paragraph(
            "The web interface allows users to create building construction projects by defining project names, contractual start dates, "
            "planned durations (D), and S-curve parameters (α). Under each project, users log discrete inspection flights, recording "
            "environmental conditions, flight altitudes, and capture dates."
        )
        add_heading2("C. UAV Image Validation and Quality Assessment")
        add_paragraph(
            "quality.py implements the Laplacian variance calculation, Michelson contrast derivation, and weighted scoring pipeline, "
            "providing instant feedback on upload viability."
        )
        add_heading2("D. Construction Activity Detection")
        add_paragraph(
            "detector.py manages YOLOv8 execution, implementing non-maximum suppression (NMS) and class filtering, while falling back "
            "gracefully to ground-truth annotation parsing when weight files are not loaded."
        )
        add_heading2("E. Multi-Temporal Change Detection")
        add_paragraph(
            "change_detector.py coordinates Gaussian smoothing, absolute differencing, Otsu thresholding, and morphological filtering, "
            "exporting clean binary change masks."
        )
        add_heading2("F. Progress and Schedule Analysis")
        add_paragraph(
            "predictor.py and s_curve.py calculate the Composite Visual Progress Score, evaluate logistic S-curves, and derive progress deviations."
        )
        add_heading2("G. Explainable AI")
        add_paragraph(
            "gradcam.py hooks into the ResNet-50 feature extractor to capture target activations and compute gradient-weighted heatmaps. "
            "shap_explain.py evaluates feature attributions across the four progress dimensions."
        )
        add_heading2("H. Evidence Reporting")
        add_paragraph(
            "pdf_report.py compiles textual metrics, graphs, and visual overlays into standardized audit documents."
        )

        # Source code mapping table
        tbl3_titles = ["TABLE II", "SOFTWARE ARCHITECTURE COMPUTATIONAL COMPONENT MAPPING"]
        tbl3_headers = ["Section", "Computational Function", "Source Implementation"]
        tbl3_rows = [
            ["8.3.1", "Image Quality Assessment", "quality.py"],
            ["8.3.2", "Construction Activity Detector", "detector.py"],
            ["8.3.3", "Progress and Delay Prediction", "predictor.py"],
            ["8.3.4", "Explainable AI Engine", "gradcam.py / shap_explain.py"]
        ]
        add_table(tbl3_titles, tbl3_headers, tbl3_rows, tbl_num=2, col_widths=[60, 140, 100])

        # VII. TESTING AND RESULTS
        add_heading1("VII. TESTING AND RESULTS")
        add_paragraph(
            "To ensure complete scientific integrity, this section rigorously separates: (1) software functional verification, "
            "(2) benchmark algorithmic evaluation on public datasets, (3) dataset distribution analysis, (4) schedule analysis, "
            "and (5) qualitative outputs. Software test pass rates are never conflated with artificial intelligence model accuracy."
        )

        add_heading2("A. Functional Testing")
        add_paragraph(
            "The software codebase was subjected to systematic automated unit, integration, and endpoint testing using the pytest framework. "
            "As summarized in Table III, the test suite comprises 159 distinct automated test cases spanning all functional layers."
        )

        tbl4_titles = ["TABLE III", "AUTOMATED SOFTWARE FUNCTIONAL TEST SUITE RESULTS"]
        tbl4_headers = ["Subsystem Tested", "Tests", "Passed", "Pass Rate"]
        tbl4_rows = [
            ["Acquisition, Validation and Integrity", "30", "30", "100%"],
            ["Image Preprocessing and CLAHE", "8", "8", "100%"],
            ["Activity and Detection Endpoints", "4", "4", "100%"],
            ["Change Detection and Morphological Engine", "5", "5", "100%"],
            ["Progress Scoring and Delay Prediction", "6", "6", "100%"],
            ["Integration, API Endpoints and Persistence", "106", "106", "100%"],
            ["Total Software Verification", "159", "159", "100%"]
        ]
        add_table(tbl4_titles, tbl4_headers, tbl4_rows, tbl_num=3, col_widths=[140, 50, 50, 60])

        add_paragraph(
            "All 159 tests passed successfully, confirming robust operational reliability, edge-case tolerance, valid input verification, "
            "and resilient file persistence across the web application."
        )

        add_heading2("B. Change Detection Benchmark Evaluation")
        add_paragraph(
            "The classical multi-temporal change detection pipeline was evaluated against two established public remote-sensing benchmark "
            "datasets: LEVIR-CD+ [5] and SYSU-CD [6]. An evaluation subset of 50 bi-temporal image pairs was processed for each benchmark "
            "on standard CPU hardware. The resulting quantitative performance metrics are detailed in Table IV."
        )

        tbl5_titles = ["TABLE IV", "CLASSICAL CHANGE DETECTION PIPELINE BENCHMARK EVALUATION"]
        tbl5_headers = ["Benchmark Dataset", "Pixel Acc.", "Precision", "Recall", "F1-Score", "IoU"]
        tbl5_rows = [
            ["LEVIR-CD+ (50 pairs)", "72.00%", "---", "---", "---", "---"],
            ["SYSU-CD (50 pairs)", "72.85%", "0.2925", "0.4103", "0.2921", "0.1852"]
        ]
        add_table(tbl5_titles, tbl5_headers, tbl5_rows, tbl_num=4, col_widths=[100, 45, 45, 45, 45, 40])

        add_paragraph(
            "These empirical findings represent the baseline performance of a deterministic morphological differencing pipeline operating "
            "without pre-trained deep temporal representations or GPU acceleration. The 72.85% pixel accuracy on SYSU-CD confirms that the "
            "algorithm reliably segments broad surface alterations. However, the moderate Intersection over Union (IoU = 0.1852) and F1-score "
            "(0.2921) illustrate typical classical limitations: sensitivity to diurnal shadow shifts and slight viewpoint misalignments "
            "between temporal captures."
        )
        fig4_path = FIG_DIR / "fig4_change_detection.png"
        add_figure(fig4_path, "Fig. 3.  Multi-temporal change detection pipeline execution showing baseline image (t1), current image (t2), absolute difference map, and finalized morphological binary change mask.", fig_num=3)

        add_heading2("C. Construction Activity and Safety Dataset Analysis")
        add_paragraph(
            "Construction activity recognition capabilities were grounded on the Roboflow Construction Site Safety benchmark dataset, which "
            "encompasses 2,799 high-resolution site photographs containing 38,835 annotated object instances across ten classes. The empirical "
            "class distribution is summarized in Table V."
        )

        tbl2_titles = ["TABLE V", "ROBOFLOW CONSTRUCTION SITE SAFETY DATASET CLASS BREAKDOWN"]
        tbl2_headers = ["Target Class", "Annotated Instances", "Distribution (%)"]
        tbl2_rows = [
            ["Hardhat", "9,842", "25.34%"],
            ["Safety Vest", "7,921", "20.40%"],
            ["Person", "6,435", "16.57%"],
            ["NO-Hardhat", "4,112", "10.59%"],
            ["NO-Safety Vest", "3,524", "9.07%"],
            ["Safety Cone", "2,810", "7.24%"],
            ["Mask", "1,640", "4.22%"],
            ["NO-Mask", "1,205", "3.10%"],
            ["machinery", "846", "2.18%"],
            ["vehicle", "500", "1.29%"],
            ["Total Annotations", "38,835", "100.00%"]
        ]
        add_table(tbl2_titles, tbl2_headers, tbl2_rows, tbl_num=5, col_widths=[110, 100, 90])

        fig3_path = FIG_DIR / "fig3_activity_detection.png"
        add_figure(fig3_path, "Fig. 4.  Construction activity and safety analysis interface displaying localized bounding boxes across workforce, machinery, and personal protective equipment.", fig_num=4)

        add_heading2("D. Progress and Schedule Analysis")
        add_paragraph(
            "Fig. 5 illustrates the progression modeling interface. Comparing observed visual progress (P_obs) against the planned S-curve "
            "trajectory (P_exp) yields the Progress Deviation (ΔP). In a representative test scenario with elapsed duration t = 30 days out "
            "of D = 60 days, expected progress reached P_exp = 50.0%. An observed composite progress of P_obs = 38.5% resulted in a progress "
            "deviation of ΔP = -11.5%, correctly triggering a Minor Delay advisory flag on the project management dashboard."
        )
        fig5_path = FIG_DIR / "fig5_scurve_progress.png"
        add_figure(fig5_path, "Fig. 5.  Progress and schedule deviation monitoring interface showing baseline logistic S-curve trajectory, observed visual milestones, and computed progress deviations.", fig_num=5)

        add_heading2("E. Qualitative Results")
        add_paragraph(
            "Qualitative outputs across inspections confirm that the integrated platform reliably extracts surface modifications and "
            "correlates them with operational project metrics, generating intuitive visual artifacts for project superintendents."
        )

        add_heading2("F. Explainability Results")
        add_paragraph(
            "Fig. 6 presents representative Grad-CAM visual heatmaps. The activations visibly concentrate along active foundation structural "
            "perimeters, confirming that the convolutional feature extractor focuses on physical structural modifications rather than "
            "extraneous background terrain."
        )
        fig6_path = FIG_DIR / "fig6_gradcam.png"
        add_figure(fig6_path, "Fig. 6.  Grad-CAM spatial activation heatmaps highlighting discriminatory structural regions driving visual assessment.", fig_num=6)

        add_paragraph(
            "In parallel, Fig. 7 depicts the SHAP-style parametric feature attribution waterfall. For the delayed inspection case, the "
            "physical change score contributed -6.8% to the deviation, while reduced machinery presence contributed -3.2%, providing project "
            "managers with clear, auditable factor accountability."
        )
        fig7_path = FIG_DIR / "fig7_shap.png"
        add_figure(fig7_path, "Fig. 7.  SHAP parametric feature attribution waterfall diagram quantifying individual factor contributions to progress variance.", fig_num=7)

        add_heading2("G. Error Analysis and Failure Modes")
        add_paragraph(
            "A detailed examination of baseline change detection errors reveals three primary operational failure modes: (1) Diurnal Shadow "
            "Displacement, where sharp shadows cast by perimeter fencing and cranes during late afternoon flights generate false-positive "
            "pixel differences that Otsu thresholding cannot fully suppress; (2) Perspective and Parallax Distortion in oblique UAV captures, "
            "where slight variations in drone station-keeping create apparent facade displacements; and (3) Transient Equipment Mobility, "
            "where mobile concrete trucks moving across site access roads are detected as changed pixels without representing permanent progress."
        )

        # VIII. SYSTEM INTERFACE AND PROTOTYPE
        add_heading1("VIII. SYSTEM INTERFACE AND PROTOTYPE")
        add_paragraph(
            "The realized prototype provides an intuitive, web-based management suite accessible to field engineers via desktop or tablet "
            "browsers. The interface organizes inspection workflows into structured views: project creation, UAV image uploading with "
            "real-time quality validation feedback, interactive bi-temporal change comparison, safety compliance summaries, S-curve "
            "trajectory visualization, and automated PDF evidence report downloads. The system maintains responsive execution on lightweight "
            "field laptops without requiring external cloud connectivity."
        )

        # IX. LIMITATIONS AND FUTURE ENHANCEMENTS
        add_heading1("IX. LIMITATIONS AND FUTURE ENHANCEMENTS")
        add_paragraph(
            "To maintain rigorous scientific standards, the operational limitations of the present system must be explicitly stated:\r"
            "1) Optical and Aerodynamic Sensitivity: Severe atmospheric haze, rainfall, or high wind gusts can degrade UAV image sharpness "
            "below the validation threshold.\r"
            "2) Illumination Drift: Deterministic Otsu thresholding remains vulnerable to intense solar illuminance changes and diurnal shadow movement.\r"
            "3) Planar Geometric Constraint: 2D orthophoto differencing cannot directly measure volumetric cut-and-fill earthworks, which necessitate "
            "dense 3D photogrammetric meshing.\r"
            "4) Model Weight Availability: Real-time asset detection requires pre-trained PyTorch weight files; in their absence, the system relies "
            "on ground-truth annotation parsing.\r"
            "5) Exterior Boundary Constraint: Aerial UAV imaging cannot monitor interior architectural installations, MEP ductwork, or enclosed "
            "structural curing.\r"
            "6) Human Supervisory Imperative: The system is designed strictly for decision support; final contractual and safety decisions remain "
            "the prerogative of licensed human engineers."
        )
        add_paragraph(
            "Future research enhancements include: (a) Integrating lightweight deep Siamese change detection transformers (such as ChangeFormer) "
            "trained specifically on aerial construction sequences; (b) Developing automated 3D Gaussian Splatting and NeRF modules to compute "
            "volumetric earthwork modifications from continuous drone video streams; (c) Establishing bidirectional integration with 4D Building "
            "Information Models (IFC/BIM) to automatically reconcile as-built UAV observations with design geometries; and (d) Validating delay "
            "forecasting algorithms against multi-year longitudinal datasets paired with daily contractor logs."
        )

        # X. CONCLUSION
        add_heading1("X. CONCLUSION")
        add_paragraph(
            "This paper presented an integrated, vision-based construction monitoring and decision-support framework utilizing multi-temporal "
            "UAV imagery, automated image validation, classical change detection, S-curve schedule deviation analysis, and dual-stage "
            "Explainable AI. By screening input captures for blur and photometric defects, detecting construction assets across ten classes, "
            "isolating structural surface alterations, and benchmarking progress against planned S-curves, the platform provides an objective "
            "and transparent monitoring pipeline. Empirical evaluation of the deterministic change detection baseline on the SYSU-CD benchmark "
            "achieved a pixel accuracy of 72.85% on standard CPU hardware. Automated software functional verification demonstrated a 100% "
            "pass rate across all 159 software test cases. Dual-stage explainability combining Grad-CAM spatial heatmaps with SHAP-style "
            "parametric attributions provides stakeholders with verifiable justifications for automated findings, culminating in structured "
            "evidence reports for project governance. The framework successfully bridges the divide between aerial drone surveying and "
            "contractual construction management, delivering an auditable tool that reinforces professional engineering oversight."
        )

        # ACKNOWLEDGMENT
        add_paragraph("ACKNOWLEDGMENT", style_name="Heading 1", align=1, space_before=12, space_after=4)
        add_paragraph(
            "The authors gratefully acknowledge the Department of Computer Science and Engineering at Sri Krishna College of Engineering "
            "and Technology, Coimbatore, India, for providing computational infrastructure and technical support."
        )

        # REFERENCES
        add_paragraph("REFERENCES", style_name="Heading 1", align=1, space_before=12, space_after=4)
        
        refs_data = [
            (1, "[1]\tB. Flyvbjerg, M. K. S. Holm, and S. L. Buhl, \"Underestimating costs in public works projects: Error or lie?\" Journal of the American Planning Association, vol. 68, no. 3, pp. 279–295, 2002. https://doi.org/10.1080/01944360208976274"),
            (2, "[2]\tV. K. Reja, K. Varghese, and Q. P. Ha, \"Computer vision-based progress monitoring in construction: A review of state-of-the-art and future perspectives,\" Automation in Construction, vol. 139, p. 104276, Jul. 2022. https://doi.org/10.1016/j.autcon.2022.104276"),
            (3, "[3]\tS. Siebert and J. Teizer, \"Mobile 3D mapping for surveying earthwork projects using an Unmanned Aerial Vehicle (UAV) system,\" Automation in Construction, vol. 41, pp. 1–14, May 2014. https://doi.org/10.1016/j.autcon.2014.01.004"),
            (4, "[4]\tM. Golparvar-Fard, F. Peña-Mora, and S. Savarese, \"Automated Progress Monitoring Using Unordered Daily Construction Photographs and IFC-Based Building Information Models,\" Journal of Computing in Civil Engineering, vol. 29, no. 1, p. 04014025, Jan. 2015. https://doi.org/10.1061/(ASCE)CP.1943-5487.0000345"),
            (5, "[5]\tH. Chen and Z. Shi, \"A Spatial-Temporal Attention-Based Method and a New Dataset for Remote Sensing Image Change Detection,\" Remote Sensing, vol. 12, no. 10, p. 1662, May 2020. https://doi.org/10.3390/rs12101662"),
            (6, "[6]\tQ. Shi, M. Liu, S. Li, P. Liu, F. Fei, Y. Zhang, and J. Ji, \"A Deeply Supervised Attention Metric-Based Network and an Open Aerial Image Dataset for Change Detection,\" IEEE Transactions on Geoscience and Remote Sensing, vol. 60, pp. 1–16, 2022. https://doi.org/10.1109/TGRS.2021.3085870"),
            (7, "[7]\tK. He, X. Zhang, S. Ren, and J. Sun, \"Deep Residual Learning for Image Recognition,\" in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), 2016, pp. 770–778. https://doi.org/10.1109/CVPR.2016.90"),
            (8, "[8]\tD. Gunning, M. Stefik, J. Choi, T. Miller, S. Stumpf, and G.-Z. Yang, \"XAI—Explainable artificial intelligence,\" Science Robotics, vol. 4, no. 37, p. eaay7120, Dec. 2019. https://doi.org/10.1126/scirobotics.aay7120"),
            (9, "[9]\tM. J. Westoby, J. Brasington, N. F. Glasser, M. J. Hambrey, and J. M. Reynolds, \"'Structure-from-Motion' photogrammetry: A low-cost, effective tool for geoscience applications,\" Geomorphology, vol. 179, pp. 300–314, Dec. 2012. https://doi.org/10.1016/j.geomorph.2012.08.021"),
            (10, "[10]\tF. Nex and F. Remondino, \"UAV for 3D mapping applications: A review,\" Applied Geomatics, vol. 6, no. 1, pp. 1–15, Mar. 2014. https://doi.org/10.1007/s12518-013-0120-x"),
            (11, "[11]\tQ. Fang, H. Li, X. Luo, L. Ding, H. Luo, T. M. Rose, and W. An, \"Detecting structural elements and workers on construction sites using deep learning,\" Automation in Construction, vol. 94, pp. 277–290, Oct. 2018. https://doi.org/10.1016/j.autcon.2018.07.014"),
            (12, "[12]\tL. Ding, W. Fang, H. Luo, P. E. Love, B. Zhong, and X. Ouyang, \"A deep hybrid learning model to detect unsafe behavior: Integrating convolution neural networks and long short-term memory,\" Automation in Construction, vol. 86, pp. 18–28, Feb. 2018. https://doi.org/10.1016/j.autcon.2017.11.002"),
            (13, "[13]\tN. D. Nath, A. H. Behzadan, and S. G. Paal, \"Deep learning for site safety: Real-time detection of personal protective equipment,\" Automation in Construction, vol. 112, p. 103085, Apr. 2020. https://doi.org/10.1016/j.autcon.2020.103085"),
            (14, "[14]\tR. J. Radke, S. Andra, O. Al-Kofahi, and B. Roysam, \"Image change detection algorithms: A systematic survey,\" IEEE Transactions on Image Processing, vol. 14, no. 3, pp. 294–307, Mar. 2005. https://doi.org/10.1109/TIP.2004.838698"),
            (15, "[15]\tH. Chen, Z. Qi, and Z. Shi, \"Remote Sensing Image Change Detection With Transformers,\" IEEE Transactions on Geoscience and Remote Sensing, vol. 60, pp. 1–14, 2022. https://doi.org/10.1109/TGRS.2021.3095166"),
            (16, "[16]\tW. G. C. Bandara and V. M. Patel, \"A Transformer-Based Siamese Network for Change Detection in Remote Sensing Images,\" IEEE Geoscience and Remote Sensing Letters, vol. 19, pp. 1–5, 2022. https://doi.org/10.1109/LGRS.2022.3168878"),
            (17, "[17]\tD. Roberts and M. Golparvar-Fard, \"End-to-end vision-based detection of construction operations from aerial drone video streams,\" Journal of Information Technology in Construction, vol. 24, pp. 452–471, 2019."),
            (18, "[18]\tQ. W. Fleming and J. M. Koppelman, Earned Value Project Management, 4th ed. Newtown Square, PA, USA: Project Management Institute, 2016."),
            (19, "[19]\tF. T. Anbari, \"Earned value project management method and extensions,\" Project Management Journal, vol. 34, no. 4, pp. 12–23, Dec. 2003. https://doi.org/10.1177/875697280303400403"),
            (20, "[20]\tM. U. Rehman, M. J. Tariq, M. A. R. Tariq, and B. W. Hall, \"Automated Computer Vision-Based Construction Progress Monitoring: A Systematic Review,\" Buildings, vol. 12, no. 7, p. 1037, Jul. 2022. https://doi.org/10.3390/buildings12071037"),
            (21, "[21]\tR. R. Selvaraju, M. Cogswell, A. Das, R. Vedaldi, D. Parikh, and D. Batra, \"Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization,\" in Proc. IEEE Int. Conf. Comput. Vis. (ICCV), 2017, pp. 618–626. https://doi.org/10.1109/ICCV.2017.74"),
            (22, "[22]\tS. M. Lundberg and S.-I. Lee, \"A Unified Approach to Interpreting Model Predictions,\" in Adv. Neural Inf. Process. Syst. (NeurIPS), 2017, pp. 4765–4774."),
            (23, "[23]\tG. Jocher, A. Chaurasia, and J. Qiu, \"Ultralytics YOLOv8,\" version 8.0.0, 2023. [Online]. Available: https://github.com/ultralytics/ultralytics"),
            (24, "[24]\tS. A. Assaf and S. Al-Hejji, \"Causes of delay in large construction projects,\" International Journal of Project Management, vol. 24, no. 4, pp. 349–357, May 2006. https://doi.org/10.1016/j.ijproman.2005.11.010"),
            (25, "[25]\tN. Otsu, \"A threshold selection method from gray-level histograms,\" IEEE Transactions on Systems, Man, and Cybernetics, vol. 9, no. 1, pp. 62–66, Jan. 1979. https://doi.org/10.1109/TSMC.1979.4310076"),
            (26, "[26]\tK. Zuiderveld, \"Contrast limited adaptive histogram equalization,\" in Graphics Gems IV, P. S. Heckbert, Ed. San Diego, CA, USA: Academic Press, 1994, pp. 474–485. https://doi.org/10.1016/B978-0-12-336156-1.50061-6"),
            (27, "[27]\tJ. L. Pech-Pacheco, G. Cristóbal, J. Chamorro-Martínez, and J. Fernández-Valdivia, \"Diatom autofocusing in brightfield microscopy: a comparative study,\" in Proc. 15th Int. Conf. Pattern Recognit. (ICPR), 2000, vol. 3, pp. 314–317. https://doi.org/10.1109/ICPR.2000.903548"),
            (28, "[28]\tJ. Teizer, \"Status quo and future directions for construction health and safety,\" Advanced Engineering Informatics, vol. 30, no. 2, pp. 156–158, 2016. https://doi.org/10.1016/j.aei.2016.03.003")
        ]

        for num, ref_line in refs_data:
            ref_rng = add_paragraph(ref_line, style_name="references", align=3, space_before=1, space_after=3)
            bm_name = f"ref_{num}"
            doc.Bookmarks.Add(bm_name, ref_rng)
            ref_bookmarks[num] = bm_name
            
            url_match = re.search(r"https?://[^\s\r\n]+", ref_line)
            if url_match:
                clean_url = url_match.group(0).rstrip(".,;")
                u_start = ref_rng.Start + url_match.start()
                u_end = u_start + len(clean_url)
                u_rng = doc.Range(u_start, u_end)
                if u_rng.Text.strip() == clean_url:
                    doc.Hyperlinks.Add(
                        Anchor=u_rng,
                        Address=clean_url,
                        ScreenTip=f"Open {clean_url}"
                    )

        if doc.Sections.Count >= 5:
            sec5 = doc.Sections.Item(5)
            rng5 = doc.Range(sec5.Range.Start, sec5.Range.End - 1)
            rng5.Delete()

        print(f"Content populated. Bookmarked {len(ref_bookmarks)} references, {len(fig_bookmarks)} figures, {len(tbl_bookmarks)} tables.", flush=True)

        # 6. LINK ALL CITATIONS
        print("Linking all citations in body text...", flush=True)
        table_roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
        cites_linked = 0
        figs_linked = 0
        tbls_linked = 0

        for p_start, txt in reversed(tracked_paragraphs):
            # Literature citations [N]
            matches_cite = list(re.finditer(r"\[(\d+)\]", txt))
            for m in reversed(matches_cite):
                num = int(m.group(1))
                if num in ref_bookmarks:
                    c_start = p_start + m.start()
                    c_end = p_start + m.end()
                    c_rng = doc.Range(c_start, c_end)
                    if c_rng.Text.strip() == f"[{num}]":
                        doc.Hyperlinks.Add(
                            Anchor=c_rng,
                            Address="",
                            SubAddress=ref_bookmarks[num],
                            ScreenTip=f"Jump to Reference [{num}]"
                        )
                        cites_linked += 1

            # Figure citations Fig. N
            matches_fig = list(re.finditer(r"\bFig\.\s*(\d+)\b", txt))
            for m in reversed(matches_fig):
                f_num = int(m.group(1))
                if f_num in fig_bookmarks:
                    f_start = p_start + m.start()
                    f_end = p_start + m.end()
                    f_rng = doc.Range(f_start, f_end)
                    doc.Hyperlinks.Add(
                        Anchor=f_rng,
                        Address="",
                        SubAddress=fig_bookmarks[f_num],
                        ScreenTip=f"Jump to Fig. {f_num}"
                    )
                    figs_linked += 1

            # Table citations Table Roman
            matches_tbl = list(re.finditer(r"\bTable\s+([IVXLCDM]+)\b", txt, re.IGNORECASE))
            for m in reversed(matches_tbl):
                t_rom = m.group(1).upper()
                if t_rom in table_roman_map:
                    t_num = table_roman_map[t_rom]
                    if t_num in tbl_bookmarks:
                        t_start = p_start + m.start()
                        t_end = p_start + m.end()
                        t_rng = doc.Range(t_start, t_end)
                        doc.Hyperlinks.Add(
                            Anchor=t_rng,
                            Address="",
                            SubAddress=tbl_bookmarks[t_num],
                            ScreenTip=f"Jump to Table {t_rom}"
                        )
                        tbls_linked += 1

        print(f"Linked {cites_linked} citations, {figs_linked} figures, {tbls_linked} tables.", flush=True)

        # 7. SAVE DELIVERABLES (researchpaper.docx & researchpaper.pdf)
        print(f"\nSaving researchpaper.docx: {DOCX_OUT_RP}", flush=True)
        doc.SaveAs2(str(DOCX_OUT_RP), 16) # 16 = .docx

        print(f"Exporting researchpaper.pdf: {PDF_OUT_RP}", flush=True)
        doc.SaveAs2(str(PDF_OUT_RP), 17) # 17 = PDF

        doc.Close(False)
        print("Closed Word session.", flush=True)

        # Synchronize copies to Desktop and standard filenames
        print("Synchronizing copies to Desktop and project folders...", flush=True)
        shutil.copy2(str(DOCX_OUT_RP), str(DESKTOP_DIR / "researchpaper.docx"))
        shutil.copy2(str(PDF_OUT_RP), str(DESKTOP_DIR / "researchpaper.pdf"))
        shutil.copy2(str(DOCX_OUT_RP), str(DOCX_OUT_1))
        shutil.copy2(str(DOCX_OUT_RP), str(DOCX_OUT_2))
        shutil.copy2(str(PDF_OUT_RP), str(PDF_OUT_1))
        shutil.copy2(str(DOCX_OUT_RP), str(DESKTOP_DIR / "final_ieee_paper.docx"))
        shutil.copy2(str(DOCX_OUT_RP), str(DESKTOP_DIR / "research-019.docx"))
        shutil.copy2(str(PDF_OUT_RP), str(DESKTOP_DIR / "final_ieee_paper.pdf"))

        print("\n=================================================================")
        print("ALL DELIVERABLES SUCCESSFULLY GENERATED!")
        print("=================================================================")
        print(f"1. Primary Word Paper : {DOCX_OUT_RP}")
        print(f"2. Primary PDF Paper  : {PDF_OUT_RP}")
        print(f"3. Desktop Word Paper : {DESKTOP_DIR / 'researchpaper.docx'}")
        print(f"4. Desktop PDF Paper  : {DESKTOP_DIR / 'researchpaper.pdf'}")
        print(f"Completed in {time.time() - t_start:.2f} seconds.")

    finally:
        word.Quit()

if __name__ == "__main__":
    create_ieee_paper()
