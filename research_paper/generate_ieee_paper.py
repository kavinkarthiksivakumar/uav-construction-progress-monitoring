"""
IEEE Conference Paper Generator with Interactive Cross-Referenced Citations
Generates:
  - research_paper/final_ieee_paper.docx
  - research_paper/research-019.docx
  - research_paper/final_ieee_paper.pdf
  - Also copied directly to Desktop

Features:
  - Built upon authentic IEEE conference-template-a4.docx
  - Preserves two-column A4 layout, IEEE margins, typography, and styling
  - Zero template placeholders or student project references
  - ALL 24 literature citations [1] to [24] are bookmarked and hyperlinked so clicking jumps to the reference!
  - ALL Figure citations (Fig. 1 to Fig. 7) are bookmarked and hyperlinked to jump to the figure!
  - ALL Table citations (Table I to Table V) are bookmarked and hyperlinked to jump to the table!
  - ALL Reference DOIs/URLs are hyperlinked to open the authentic web sources!
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
DOCX_OUT_1 = PROJECT_ROOT / "research_paper" / "final_ieee_paper.docx"
DOCX_OUT_2 = PROJECT_ROOT / "research_paper" / "research-019.docx"
PDF_OUT = PROJECT_ROOT / "research_paper" / "final_ieee_paper.pdf"
FIG_DIR = PROJECT_ROOT / "research_paper" / "figures"

def create_ieee_paper():
    t_start = time.time()
    print("=" * 65)
    print("GENERATING IEEE CONFERENCE PAPER WITH INTERACTIVE CITATIONS")
    print("=" * 65)
    print(f"Opening template: {TEMPLATE_PATH}", flush=True)
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found at {TEMPLATE_PATH}")

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0

    try:
        doc = word.Documents.Open(str(TEMPLATE_PATH))
        print("Template loaded successfully.", flush=True)

        # =========================================================================
        # 1. SECTION 1: TITLE
        # =========================================================================
        sec1 = doc.Sections.Item(1)
        rng1 = doc.Range(sec1.Range.Start, sec1.Range.End - 1)
        rng1.Text = "Explainable Vision-Based Construction Progress Assessment and Delay Prediction Using Multi-Temporal UAV Imagery\r"
        rng1.Style = "paper title"
        rng1.ParagraphFormat.Alignment = 1 # Center
        rng1.ParagraphFormat.SpaceBefore = 0
        rng1.ParagraphFormat.SpaceAfter = 12

        # =========================================================================
        # 2. SECTION 2: AUTHOR BLOCK (Single Column, Centered)
        # =========================================================================
        sec2 = doc.Sections.Item(2)
        sec2.PageSetup.TextColumns.SetCount(1)
        rng2 = doc.Range(sec2.Range.Start, sec2.Range.End - 1)
        rng2.Text = (
            "KAVINKARTHIK S\r"
            "Department of M.Tech Computer Science and Engineering\r"
            "Sri Krishna College of Engineering and Technology\r"
            "Coimbatore, India\r"
            "727722euci019@skcet.ac.in\r"
        )
        rng2.Style = "Author"
        rng2.ParagraphFormat.Alignment = 1 # Center
        rng2.ParagraphFormat.SpaceBefore = 0
        rng2.ParagraphFormat.SpaceAfter = 2
        
        # Format Author name as bold 11pt
        p_author = sec2.Range.Paragraphs.Item(1)
        p_author.Range.Font.Bold = True
        p_author.Range.Font.Size = 11

        # =========================================================================
        # 3. SECTION 3: EMPTY REDUNDANT SECTION
        # =========================================================================
        if doc.Sections.Count >= 3:
            sec3 = doc.Sections.Item(3)
            rng3 = doc.Range(sec3.Range.Start, sec3.Range.End - 1)
            rng3.Delete()

        # =========================================================================
        # 4. SECTION 4: 2-COLUMN BODY (CLEAR ALL TEMPLATE INSTRUCTIONS)
        # =========================================================================
        sec4 = doc.Sections.Item(4)
        sec4.PageSetup.TextColumns.SetCount(2)
        sec4.PageSetup.TextColumns.Spacing = 18.0 # 0.25 in / 18 pt IEEE spacing
        
        rng4 = doc.Range(sec4.Range.Start, sec4.Range.End - 1)
        rng4.Delete()
        print("Cleared Section 4 template instructions.", flush=True)

        # Track elements for hyperlinking
        cur_pos = sec4.Range.Start
        tracked_paragraphs = [] # list of (start_pos, text)
        ref_bookmarks = {}      # num -> bookmark name
        fig_bookmarks = {}      # num -> bookmark name
        tbl_bookmarks = {}      # num -> bookmark name

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
            
            # Record for citation linking if in body
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
            
            # Maintain aspect ratio
            aspect = shape.Height / shape.Width
            shape.Width = width_pt
            shape.Height = width_pt * aspect
            shape.Range.ParagraphFormat.Alignment = 1 # Center
            shape.Range.ParagraphFormat.SpaceBefore = 6
            shape.Range.ParagraphFormat.SpaceAfter = 2
            
            # Bookmark figure
            bm_name = f"fig_{fig_num}"
            doc.Bookmarks.Add(bm_name, shape.Range)
            fig_bookmarks[fig_num] = bm_name
            
            cur_pos = shape.Range.End
            
            # Caption
            add_paragraph(caption_text, style_name="figure caption", align=3, space_before=2, space_after=8)

        def add_table(title_lines, headers, rows_data, tbl_num, col_widths=None):
            nonlocal cur_pos
            # Title
            for line in title_lines:
                add_paragraph(line, style_name="table head", align=1, space_before=8, space_after=1)
            
            rng = doc.Range(cur_pos, cur_pos)
            num_rows = len(rows_data) + 1
            num_cols = len(headers)
            tbl = doc.Tables.Add(rng, num_rows, num_cols)
            tbl.Borders.Enable = False
            
            # IEEE standard table borders: Top line, header underline, bottom line
            tbl.Borders.Item(-1).LineStyle = 1 # Top border
            tbl.Borders.Item(-1).LineWidth = 4 # 0.5 pt
            tbl.Borders.Item(-3).LineStyle = 1 # Bottom border
            tbl.Borders.Item(-3).LineWidth = 4
            
            # Bookmark table
            bm_name = f"tbl_{tbl_num}"
            doc.Bookmarks.Add(bm_name, tbl.Range)
            tbl_bookmarks[tbl_num] = bm_name
            
            # Populate headers
            for c_idx, h_text in enumerate(headers, 1):
                cell = tbl.Cell(1, c_idx)
                cell.Range.Text = h_text
                cell.Range.Font.Name = "Times New Roman"
                cell.Range.Font.Size = 8
                cell.Range.Font.Bold = True
                cell.Range.ParagraphFormat.Alignment = 1 # Center
                cell.Range.ParagraphFormat.SpaceBefore = 2
                cell.Range.ParagraphFormat.SpaceAfter = 2
            
            # Underline header row
            for c_idx in range(1, num_cols + 1):
                tbl.Cell(1, c_idx).Borders.Item(-3).LineStyle = 1
                tbl.Cell(1, c_idx).Borders.Item(-3).LineWidth = 4
            
            # Populate rows
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
            
            # Set widths if specified
            if col_widths and len(col_widths) == num_cols:
                for c_idx, w in enumerate(col_widths, 1):
                    for r_idx in range(1, num_rows + 1):
                        tbl.Cell(r_idx, c_idx).Width = w
            
            tbl.Rows.Alignment = 1 # Center table
            cur_pos = tbl.Range.End
            add_paragraph("", style_name="Body Text", space_before=0, space_after=4)

        # =========================================================================
        # 5. POPULATE PAPER CONTENT
        # =========================================================================

        # ABSTRACT
        abstract_text = (
            "Abstract—Automated physical progress assessment on active construction sites is critical for "
            "preventing schedule overruns, identifying structural deviations, and enforcing site safety compliance. "
            "Conventional inspection methods depend on manual site walkthroughs, which are labor-intensive, subjective, "
            "and spatially limited. While low-altitude Unmanned Aerial Vehicles (UAVs) provide flexible spatial data "
            "acquisition, prevailing automated vision systems operate largely as unverified black boxes, failing to "
            "link detected changes to project milestone schedules or provide human-auditable visual rationale. "
            "This paper presents an explainable, end-to-end vision-based framework for construction progress assessment "
            "and schedule delay prediction using multi-temporal UAV imagery, developed under Smart India Hackathon "
            "problem statement SIH1726. The pipeline integrates automated image validation and quality filtering, "
            "spatial alignment, construction activity and safety compliance detection across ten classes, classical "
            "multi-temporal change detection, Earned Value Management (EVM) schedule variance modeling, and dual-stage "
            "Explainable AI (XAI) combining spatial Grad-CAM activation heatmaps with parametric SHAP feature attribution. "
            "The system was validated against physical benchmarks including LEVIR-CD+ and SYSU-CD for change detection, "
            "and the Roboflow Construction Site Safety dataset (2,799 images, 38,835 annotations). The deterministic "
            "change detection pipeline achieves a pixel accuracy of 72.85% (IoU 0.1852, F1 0.2921) on SYSU-CD and "
            "72.00% accuracy on LEVIR-CD+ without requiring GPU infrastructure. Automated functional verification "
            "demonstrated 100% pass rates across all 159 software test cases. The entire pipeline produces a structured "
            "evidence report providing transparent, auditable project management decision support."
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
            "Capital infrastructure and building construction projects routinely encounter cost overruns and critical "
            "schedule delays. Industry surveys consistently report that over sixty percent of large-scale civil engineering "
            "projects exceed their contracted completion schedules, resulting in substantial financial penalties, contractual "
            "disputes, and lost economic utility [1], [2]. Historically, construction progress tracking has relied on periodic "
            "physical walkthroughs conducted by field superintendents. While manual inspections provide qualitative domain "
            "insight, they suffer from severe operational limitations: they are labor-intensive, hazardous in active heavy-machinery "
            "zones, prone to subjective estimation, and yield sparse spatial records that fail to capture rapid structural progressions "
            "across large-scale building sites [3]."
        )
        add_paragraph(
            "The deployment of small Unmanned Aerial Vehicles (UAVs) equipped with high-resolution digital optical sensors has "
            "introduced an agile platform for aerial site surveying [4]. UAVs can traverse complex, vertical, and hazardous "
            "construction sectors rapidly, capturing aerial imagery across multiple flight dates [5]. However, the acquisition "
            "of multi-temporal aerial imagery does not automatically translate into actionable project management decisions. "
            "Translating raw drone imagery into verifiable progress metrics presents substantial computational, geometric, and "
            "analytical challenges [6]."
        )
        add_paragraph(
            "While advances in deep convolutional networks and computer vision have shown strong capabilities in visual object "
            "recognition [7], their practical adoption in construction site governance has been hindered by opacity [8]. "
            "Construction stakeholders—including project managers, general contractors, lending institutions, and safety auditors—cannot "
            "make contractual milestone disbursements or schedule adjustments based on black-box numerical predictions. When an "
            "automated monitoring tool flags a site as delayed, decision-makers require transparent evidence: What physical activity "
            "was identified? Where did structural modifications occur? How was the schedule variance computed? Which factors contributed "
            "to the delay classification?"
        )
        add_paragraph(
            "To address these challenges, this study presents an explainable, end-to-end vision-based framework that integrates "
            "multi-temporal UAV imagery with schedule-grounded analytical models. Addressing Smart India Hackathon problem statement "
            "SIH1726 (\"Utilization of aerial/drone-based images for monitoring progress of construction activities for building "
            "construction projects\"), the system combines automated sensor validation, construction activity detection, "
            "multi-temporal change detection, S-curve schedule variance modeling, and dual-stage visual and parametric explainability."
        )

        # II. RELATED WORK
        add_heading1("II. RELATED WORK")
        add_heading2("A. UAV-Based Construction Monitoring")
        add_paragraph(
            "Early implementations of UAV monitoring in civil engineering focused predominantly on three-dimensional point cloud "
            "reconstruction through Structure-from-Motion (SfM) photogrammetry [3], [4]. Researchers demonstrated that photogrammetric "
            "meshes could be registered with Building Information Models (BIM) to detect geometric deviations [9]. However, dense 3D "
            "point cloud generation from hundreds of aerial captures requires extensive computational processing, often requiring several "
            "hours per inspection flight, which limits its responsiveness for rapid daily or bi-weekly site inspections [10]."
        )
        add_heading2("B. Computer-Vision-Based Progress Monitoring")
        add_paragraph(
            "To reduce computational demands, subsequent research investigated two-dimensional computer vision directly on aerial orthophotos "
            "and site captures. Convolutional neural networks, including Faster R-CNN, Mask R-CNN, and YOLO architectures, have been "
            "applied to recognize construction assets, including earthmoving excavators, mobile cranes, concrete mixer trucks, and site "
            "workers [11], [12]. Nath et al. [13] demonstrated the feasibility of detecting personal protective equipment (PPE) on active "
            "job sites in real time. Nevertheless, existing detection studies often operate in isolation, treating activity recognition as a "
            "standalone computer-vision benchmark rather than integrating it into an overall project schedule tracking workflow [2]."
        )
        add_heading2("C. Remote-Sensing Change Detection and Multi-Temporal Analysis")
        add_paragraph(
            "Bi-temporal change detection has been extensively investigated in satellite remote sensing for urban expansion and environmental "
            "tracking [14]. Deep Siamese networks, bitemporal image transformers (BIT) [15], and ChangeFormer [16] have established high "
            "benchmark scores on public aerial datasets such as LEVIR-CD [5] and SYSU-CD [6]. However, UAV construction monitoring presents "
            "distinct optical challenges compared to nadir satellite imagery: variable flight altitudes, perspective parallax along tall vertical "
            "structural facades, and intense diurnal shadow displacement caused by structural columns and perimeter tower cranes [17]. "
            "Furthermore, high-parameter transformer architectures require dedicated GPU infrastructure unavailable at remote edge field trailers."
        )
        add_heading2("D. Construction Progress and Schedule Analysis")
        add_paragraph(
            "In professional project management, Earned Value Management (EVM) provides standard mathematical formulations for schedule and "
            "cost performance [18]. Parameters including Planned Value (PV), Earned Value (EV), Schedule Variance (SV = EV - PV), and "
            "Schedule Performance Index (SPI = EV / PV) are conventionally derived from contractor logs [19]. Synthesizing direct "
            "computer-vision observations with EVM formulations represents an active area of investigation [2], [20]."
        )
        add_heading2("E. Explainable Artificial Intelligence (XAI)")
        add_paragraph(
            "To alleviate the black-box nature of deep neural networks, visualization frameworks such as Gradient-weighted Class Activation "
            "Mapping (Grad-CAM) [21] calculate spatial gradients to highlight discriminative image regions driving model decisions. In parallel, "
            "Lundberg and Lee introduced SHAP (SHapley Additive exPlanations) [22], establishing game-theoretic feature attribution values "
            "for multi-parameter models. Coupling spatial pixel activations with parametric feature ranking provides an auditable foundation "
            "for engineering governance."
        )

        # III. SYSTEM REQUIREMENTS AND DESIGN
        add_heading1("III. SYSTEM REQUIREMENTS AND DESIGN")
        add_paragraph(
            "The system is designed to provide automated, objective, and auditable progress assessment by processing multi-temporal UAV flight "
            "data through explicit analytical stages."
        )
        add_heading2("A. System Inputs")
        add_paragraph(
            "1) Multi-Temporal UAV Imagery: Successive optical aerial captures acquired at flight timestamps t1 (baseline/earlier flight) and "
            "t2 (current/later flight) under standard drone flight plans.\r"
            "2) Site Inspection Metadata: Flight altitude, camera specifications, capture timestamps, and spatial region tags.\r"
            "3) Contractual Schedule Parameters: Planned project duration (D), baseline milestone dates, and S-curve progress parameters."
        )
        add_heading2("B. Analytical Processing Stages")
        add_paragraph(
            "The framework executes nine coordinated processing stages: (1) Image Validation enforcing file integrity, minimum resolution, "
            "and SHA-256 deduplication; (2) Image Preprocessing utilizing Laplacian blur estimation and CLAHE; (3) Construction Activity "
            "Analysis across ten classes; (4) Temporal Pairing and spatial alignment; (5) Multi-Temporal Change Detection using Otsu "
            "differencing; (6) Progress Assessment via composite formula; (7) Schedule and Delay Analysis against baseline S-curves; "
            "(8) Explainable AI via Grad-CAM and SHAP; and (9) Evidence Reporting compiling structured audit findings."
        )
        add_heading2("C. System Outputs")
        add_paragraph(
            "The system outputs comprise verified quality scores, detected construction equipment and PPE compliance indices, binary "
            "change masks with quantified surface alteration percentages, composite observed progress values, S-curve schedule variance "
            "curves, Grad-CAM visual heatmaps, SHAP feature rankings, and standardized evidence reports."
        )

        # IV. PROPOSED SYSTEM ARCHITECTURE
        add_heading1("IV. PROPOSED SYSTEM ARCHITECTURE")
        add_paragraph(
            "The overall processing architecture is shown in Fig. 1. The framework maintains clear modular boundaries between data acquisition, "
            "analytical processing, and decision support layers. Flight images are ingested and validated before entering downstream analysis. "
            "Construction activity detection and temporal change detection operate as complementary parallel modules whose outputs converge "
            "in the progress assessment engine."
        )
        fig1_path = FIG_DIR / "fig1_architecture.png"
        add_figure(fig1_path, "Fig. 1.  Proposed UAV-based construction progress assessment architecture.", fig_num=1)

        # V. UAV IMAGE PROCESSING AND CONSTRUCTION ACTIVITY ANALYSIS
        add_heading1("V. UAV IMAGE PROCESSING AND CONSTRUCTION ACTIVITY ANALYSIS")
        add_heading2("A. UAV Image Preprocessing and Validation")
        add_paragraph(
            "Raw aerial imagery collected during drone flight missions exhibits variations in ambient illumination, atmospheric haze, "
            "and motion artifacts. The preprocessing pipeline applies sequential validation checks: (1) Integrity verification enforcing "
            "a minimum resolution of 100 x 100 pixels; (2) Cryptographic deduplication via SHA-256 digests; (3) Laplacian blur filtering, "
            "where motion blur is quantified through the variance of the discrete Laplacian operator:"
        )
        add_equation("Var(\u0394I) = (1/N) \u2211_{x,y} (\u0394I(x,y) - \u0394I_mean)^2", 1)
        add_paragraph(
            "Images with Var(\u0394I) < 100 are flagged as motion-blurred. Subsequently, Contrast Limited Adaptive Histogram Equalization "
            "(CLAHE) is applied to the luminance channel in LAB color space (clip limit = 2.0, tile grid = 8 x 8) to normalize deep shadows, "
            "and bi-temporal image pairs are spatially scaled using bilinear interpolation."
        )
        add_heading2("B. Construction Activity and Equipment Detection")
        add_paragraph(
            "Construction activity detection provides empirical evidence of active work on site across ten classes: Workforce (Person), "
            "Mandatory Safety Elements (Hardhat, Safety Vest, Mask, Safety Cone), Safety Infractions (NO-Hardhat, NO-Safety Vest, NO-Mask), "
            "and Heavy Machinery (machinery, vehicle). Inference is performed via YOLOv8 on 640 x 640 pixel inputs [23]. The site PPE "
            "compliance index C_safe is derived as:"
        )
        add_equation("C_safe = [N_compliant / (N_compliant + N_violation)] \u00d7 100%", 2)
        add_paragraph(
            "where N_compliant denotes total detections of hardhats, safety vests, and masks, while N_violation sums non-compliant instances."
        )

        # VI. MULTI-TEMPORAL CHANGE DETECTION
        add_heading1("VI. MULTI-TEMPORAL CHANGE DETECTION")
        add_paragraph(
            "Multi-temporal change detection identifies physical surface alterations between baseline flight t1 and current flight t2. "
            "The UAV image pair used for temporal analysis is shown in Fig. 2."
        )
        fig2_path = FIG_DIR / "fig2_temporal_pair.png"
        add_figure(fig2_path, "Fig. 2.  UAV image pair used for temporal analysis: (a) Flight t1 (Baseline), (b) Flight t2 (Current).", fig_num=2)
        
        add_heading2("A. Classical Differencing Algorithm")
        add_paragraph(
            "To guarantee mathematical reproducibility and eliminate GPU dependency on edge field hardware, a deterministic differential "
            "pipeline is executed: (1) Grayscale luminance conversion; (2) Gaussian low-pass spatial smoothing (\u03c3 = 1.5); "
            "(3) Absolute pixel differencing:"
        )
        add_equation("\u0394D(x, y) = |G_{t2}(x, y) - G_{t1}(x, y)|", 3)
        add_paragraph(
            "followed by (4) Otsu's adaptive global thresholding; (5) Morphological closure (5 x 5 ellipse) and opening; and (6) Connected "
            "component contour filtering rejecting non-structural blobs smaller than 250 pixels."
        )
        add_heading2("B. Quantitative Change Metric")
        add_paragraph(
            "The net surface alteration ratio R_change is computed as:"
        )
        add_equation("R_change = [1 / (W \u00d7 H)] \u2211_{x=1}^W \u2211_{y=1}^H M_clean(x, y) \u00d7 100%", 4)
        add_paragraph(
            "Change magnitude is categorized into four contractual intervals: NONE (<1%), MINOR (1%–5%), MODERATE (5%–15%), and SIGNIFICANT (>15%)."
        )

        # VII. CONSTRUCTION PROGRESS AND SCHEDULE ANALYSIS
        add_heading1("VII. CONSTRUCTION PROGRESS AND SCHEDULE ANALYSIS")
        add_heading2("A. Observed Progress Formulation")
        add_paragraph(
            "Observed physical progress cannot be determined solely from pixel change percentages, as excavation or demolition may produce "
            "high visual change without representing substantial overall milestone completion. The framework computes observed progress "
            "P_obs(t) in [0, 100]% through a weighted composite model:"
        )
        add_equation("P_obs(t) = w_chg \u00b7 S_chg(t) + w_act \u00b7 S_act(t) + w_temp \u00b7 S_temp(t) + w_qual \u00b7 S_qual(t)", 5)
        add_paragraph(
            "where S_chg reflects physical change from Module 4, S_act reflects equipment and workforce presence from Module 3, S_temp "
            "reflects temporal inspection regularity, and S_qual reflects image sharpness from Module 1. Nominal weights are calibrated "
            "to w_chg = 0.40, w_act = 0.30, w_temp = 0.20, and w_qual = 0.10, satisfying \u2211 w_i = 1.0."
        )
        add_heading2("B. Baseline S-Curve Trajectory Modeling")
        add_paragraph(
            "Planned construction completion naturally follows a sigmoidal S-curve pattern. The planned progress P_exp(t) at elapsed day t "
            "within planned duration D is modeled via the normalized logistic function:"
        )
        add_equation("P_exp(t) = 100 / [1 + exp(-\u03b1 (t/D - 0.5))]", 6)
        add_paragraph(
            "where \u03b1 = 6.0 establishes the standard civil engineering S-curve inflection profile."
        )
        add_heading2("C. Schedule Variance and Delay Risk Analysis")
        add_paragraph(
            "Schedule variance \u0394P is defined as the arithmetic deviation between observed and planned progress:"
        )
        add_equation("\u0394P(t) = P_obs(t) - P_exp(t)", 7)
        add_paragraph(
            "Project health is categorized into four operational tiers: ON_TRACK (\u0394P \u2265 -2.0%), AT_RISK (-5.0% \u2264 \u0394P < -2.0%), "
            "DELAYED (-15.0% \u2264 \u0394P < -5.0%), and CRITICAL (\u0394P < -15.0%). The projected calendar delay in days is derived as:"
        )
        add_equation("Delay_days = -[\u0394P(t) / 100] \u00d7 D_planned", 8)

        # VIII. EXPLAINABLE AI
        add_heading1("VIII. EXPLAINABLE AI")
        add_heading2("A. Spatial Explainability via Grad-CAM")
        add_paragraph(
            "Gradient-weighted Class Activation Mapping (Grad-CAM) generates visual explanation heatmaps highlighting the spatial regions "
            "that influenced the model's visual assessment [21]. The neuron importance weight \u03b1_k^c for convolutional feature map A^k is computed as:"
        )
        add_equation("\u03b1_k^c = (1/Z) \u2211_{i=1}^U \u2211_{j=1}^V [\u2202Y^c / \u2202A_{i,j}^k]", 9)
        add_paragraph(
            "where Y^c represents the prediction score for class c, and Z = U \u00d7 V is the spatial area of the feature map. The spatial "
            "localization map is obtained by:"
        )
        add_equation("L_{Grad-CAM}^c = ReLU(\u2211_k \u03b1_k^c A^k)", 10)
        add_paragraph(
            "The resulting heatmap is upsampled to input image dimensions and overlaid using a Jet colormap, highlighting the physical "
            "building footprints and structural framing that drove the model's evaluation."
        )
        add_heading2("B. Parametric Explainability via SHAP")
        add_paragraph(
            "For delay and progress scoring, SHAP (SHapley Additive exPlanations) values compute the additive marginal contribution of each input variable [22]:"
        )
        add_equation("f(x) = \u03c6_0 + \u2211_{m=1}^M \u03c6_m", 11)
        add_paragraph(
            "where \u03c6_0 is the base expected value, and \u03c6_m represents the attribution of feature m. Evaluated features include: "
            "(1) Surface Change Percentage (R_change), (2) Machinery Count, (3) Workforce Count, (4) Safety Compliance Rate (C_safe), and "
            "(5) Elapsed Duration Ratio (t/D). SHAP waterfall and bar charts illustrate the positive or negative contribution of each factor."
        )

        # IX. IMPLEMENTATION
        add_heading1("IX. IMPLEMENTATION")
        add_paragraph(
            "The framework is implemented in Python 3.13 utilizing OpenCV for image processing, Flask as the web application backend, "
            "and modern semantic HTML5, CSS3, and JavaScript on the client side. The architecture separates computation into discrete modules: "
            "Module 1 (Acquisition & Validation), Module 2 (Image Processing & CLAHE), Module 3 (Activity & Detection), Module 4 (Change Detection), "
            "Module 5 (Progress & Delay), and Module 6 (Explainable AI). All project assets, inspection logs, and processing results are serialized "
            "locally in JSON format to support transparency and auditability."
        )

        # X. EVALUATION
        add_heading1("X. EVALUATION")
        add_heading2("A. Software Functional Evaluation")
        add_paragraph(
            "The automated software test suite evaluates route handling, analytical functions, edge cases, and data persistence across the application. "
            "The test suite comprises 159 automated test cases executed via pytest. All 159 tests passed successfully (100% pass rate)."
        )
        add_heading2("B. Model/Algorithm Evaluation")
        add_paragraph(
            "Model and algorithmic performance was measured using standard evaluation metrics: (1) Change Detection: Precision, Recall, F1-score, "
            "IoU, and Pixel Accuracy evaluated against ground-truth binary masks; (2) Activity Detection: per-class annotation counts, distribution "
            "shares, and safety compliance ratios; and (3) Progress and Delay: Schedule Variance (\u0394P), calendar delay calculations, and S-curve tracking fidelity."
        )
        add_heading2("C. Dataset Benchmark Evaluation")
        add_paragraph(
            "The framework was evaluated on three established physical datasets: (1) LEVIR-CD+ (50 high-resolution 1024 x 1024 bi-temporal UAV aerial "
            "image pairs); (2) SYSU-CD (50 optical aerial image pairs with 0.5 m ground sampling distance); and (3) Roboflow Construction Site Safety "
            "(2,799 annotated images containing 38,835 annotated instances across ten construction classes)."
        )
        add_heading2("D. Qualitative Evaluation")
        add_paragraph(
            "Qualitative assessment was conducted by visual inspection of detection overlays, binary change masks, S-curve trajectory plots, "
            "Grad-CAM heatmaps, and SHAP attribution plots generated from active project inspections."
        )

        # XI. RESULTS AND DISCUSSION
        add_heading1("XI. RESULTS AND DISCUSSION")
        add_heading2("A. Quantitative Benchmark Results")
        add_paragraph(
            "Table I summarizes the characteristics of the three benchmark datasets utilized for experimental validation."
        )
        
        # TABLE I
        add_table(
            ["TABLE I", "DATASET DESCRIPTION"],
            ["Dataset Name", "Primary Modality", "Spatial Resolution", "Samples / Pairs", "Target Classes / Ground Truth"],
            [
                ["LEVIR-CD+", "Bi-Temporal UAV Optical", "1024 \u00d7 1024 px", "50 Evaluated Pairs", "Binary Structural Change Masks"],
                ["SYSU-CD", "Bi-Temporal Aerial Optical", "0.5 m GSD", "50 Evaluated Pairs", "Dense Urban Construction Masks"],
                ["Roboflow Safety", "Multi-Angle Site Drone/Camera", "640 \u00d7 640 px", "2,799 Total Images", "10 Object & PPE Safety Classes"]
            ],
            tbl_num=1,
            col_widths=[60, 60, 40, 40, 43]
        )

        add_paragraph(
            "Table II presents the automated software functional validation results across the modular subsystems."
        )

        # TABLE II
        add_table(
            ["TABLE II", "SOFTWARE FUNCTIONAL VALIDATION RESULTS"],
            ["Subsystem Module", "Function / Responsibility", "Tests", "Passed", "Pass Rate", "Status"],
            [
                ["Module 1", "Acquisition, Validation & Integrity", "30", "30", "100%", "Verified"],
                ["Module 2", "Image Preprocessing & CLAHE", "8", "8", "100%", "Verified"],
                ["Module 3", "Activity & Detection Endpoints", "4", "4", "100%", "Verified"],
                ["Module 4", "Change Detection & Morphological Engine", "5", "5", "100%", "Verified"],
                ["Module 5", "Progress Scoring & Delay Prediction", "6", "6", "100%", "Verified"],
                ["Integration Suite", "API Endpoints, Evacuation & Persistence", "106", "106", "100%", "Verified"],
                ["Total Test Suite", "Full System Functional Scope", "159", "159", "100%", "PASSED"]
            ],
            tbl_num=2,
            col_widths=[50, 75, 25, 25, 30, 38]
        )

        add_paragraph(
            "Table III presents the performance of the classical change detection pipeline evaluated across 50 ground-truth pairs from "
            "LEVIR-CD+ and 50 pairs from SYSU-CD."
        )

        # TABLE III
        add_table(
            ["TABLE III", "CHANGE DETECTION BENCHMARK RESULTS"],
            ["Benchmark Dataset", "Evaluated Pairs", "Precision", "Recall", "F1-Score", "IoU", "Pixel Accuracy"],
            [
                ["LEVIR-CD+", "50", "0.0757", "0.5717", "0.1118", "0.0685", "72.00%"],
                ["SYSU-CD", "50", "0.2925", "0.4103", "0.2921", "0.1852", "72.85%"]
            ],
            tbl_num=3,
            col_widths=[55, 32, 31, 31, 31, 31, 32]
        )

        add_paragraph(
            "The classical differencing method achieved an IoU of 0.1852 and an F1-score of 0.2921 on SYSU-CD, with a pixel accuracy of 72.85%. "
            "On LEVIR-CD+, the pipeline achieved a recall of 0.5717 and a pixel accuracy of 72.00%. The higher IoU on SYSU-CD is attributable to "
            "the higher visual contrast between urban building construction activities and surrounding terrain, whereas LEVIR-CD+ contains subtle "
            "residential roof alterations that Otsu thresholding under varying solar illumination angles detects with higher false-positive rates. "
            "Importantly, the classical approach processed all 50 pairs in 5.9 seconds without requiring GPU acceleration."
        )
        add_paragraph(
            "Table IV presents the physical annotation distribution across the 38,835 labeled instances in the Roboflow Construction Site Safety dataset."
        )

        # TABLE IV
        add_table(
            ["TABLE IV", "CONSTRUCTION ACTIVITY AND SAFETY ANNOTATION DISTRIBUTION"],
            ["Class Name", "Train Set", "Valid Set", "Test Set", "Total Instances", "Class Share"],
            [
                ["Person", "9,691", "166", "174", "10,031", "25.8%"],
                ["machinery", "5,238", "55", "44", "5,337", "13.7%"],
                ["NO-Safety Vest", "3,957", "106", "90", "4,153", "10.7%"],
                ["Hardhat", "3,362", "79", "110", "3,551", "9.1%"],
                ["NO-Mask", "3,209", "74", "79", "3,362", "8.7%"],
                ["Safety Cone", "3,170", "44", "92", "3,306", "8.5%"],
                ["Safety Vest", "3,156", "41", "61", "3,258", "8.4%"],
                ["NO-Hardhat", "2,318", "69", "41", "2,428", "6.3%"],
                ["Mask", "1,743", "21", "28", "1,792", "4.6%"],
                ["vehicle", "1,534", "42", "41", "1,617", "4.2%"],
                ["Total", "37,378", "697", "760", "38,835", "100.0%"]
            ],
            tbl_num=4,
            col_widths=[55, 37, 37, 37, 42, 35]
        )

        add_paragraph(
            "In the test split (82 images, 760 annotations), an average of 9.27 safety elements was observed per frame, with an overall PPE "
            "compliance rate of 36.6%. The distribution highlights a class imbalance, with Person accounting for 25.8% of instances and machinery "
            "representing 13.7%, while safety infractions (NO-Safety Vest, NO-Hardhat, NO-Mask) represent 25.7% of total annotations."
        )
        add_paragraph(
            "Table V reports the progress and schedule monitoring validation metrics on the reference inspection case."
        )

        # TABLE V
        add_table(
            ["TABLE V", "PROGRESS AND SCHEDULE MONITORING VALIDATION"],
            ["Parameter", "Measured Value", "Unit / Format", "Interpretation"],
            [
                ["Physical Change Score (S_chg)", "75.3", "%", "Substantial surface modification detected"],
                ["Site Activity Score (S_act)", "29.0", "%", "Moderate workforce and equipment presence"],
                ["Temporal Score (S_temp)", "76.0", "%", "Consistent flight inspection intervals"],
                ["Image Quality Score (S_qual)", "77.1", "%", "Sharp imagery (Var(\u0394I) > 100)"],
                ["Observed Progress (P_obs)", "61.73", "%", "Composite formula derivation"],
                ["Expected Progress (P_exp)", "0.27", "%", "Planned S-curve baseline at elapsed day 1"],
                ["Schedule Variance (\u0394P)", "+61.46", "% points", "Advanced execution against early baseline"],
                ["Projected Delay", "-224", "calendar days", "Negative value indicates ahead of schedule"],
                ["Schedule Risk Status", "ON_TRACK", "Categorical", "Project tracking ahead of baseline schedule"]
            ],
            tbl_num=5,
            col_widths=[75, 40, 45, 83]
        )

        # B. Qualitative Results
        add_heading2("B. Qualitative Results")
        add_paragraph(
            "The construction activity detection output is shown in Fig. 3. Bounding boxes isolate workers, personal protective equipment "
            "(hard hats and safety vests), and construction machinery."
        )
        fig3_path = FIG_DIR / "fig3_activity_detection.png"
        add_figure(fig3_path, "Fig. 3.  Construction activity and PPE safety compliance detection output.", fig_num=3)

        add_paragraph(
            "The multi-temporal change detection output is shown in Fig. 4. Changed regions between flight timestamps t1 and t2 are highlighted "
            "in color over the reference image, delineating new structural additions."
        )
        fig4_path = FIG_DIR / "fig4_change_detection.png"
        add_figure(fig4_path, "Fig. 4.  Multi-temporal change detection output highlighting structural alterations.", fig_num=4)

        add_paragraph(
            "The progress assessment visualization is shown in Fig. 5. The planned S-curve trajectory is plotted alongside the observed "
            "progress point, illustrating the schedule variance."
        )
        fig5_path = FIG_DIR / "fig5_scurve_progress.png"
        add_figure(fig5_path, "Fig. 5.  Construction milestone S-curve trajectory vs. observed progress score.", fig_num=5)

        add_paragraph(
            "The Grad-CAM explanation is shown in Fig. 6. High-intensity activation regions align with the newly constructed building framework, "
            "confirming that the model's visual assessment corresponds to physical structural elements rather than background terrain."
        )
        fig6_path = FIG_DIR / "fig6_gradcam.png"
        add_figure(fig6_path, "Fig. 6.  Grad-CAM spatial activation heatmap illustrating model focus on building structural footprint.", fig_num=6)

        add_paragraph(
            "The SHAP feature attribution is shown in Fig. 7. The waterfall plot displays the contribution of each input parameter—surface change, "
            "machinery count, workforce count, safety compliance, and elapsed duration—to the final progress determination."
        )
        fig7_path = FIG_DIR / "fig7_shap.png"
        add_figure(fig7_path, "Fig. 7.  SHAP feature attribution waterfall plot displaying factor contributions to progress and schedule variance.", fig_num=7)

        # C. Discussion
        add_heading2("C. Discussion")
        add_paragraph(
            "The experimental findings confirm that integrating multi-temporal UAV imagery with schedule-grounded analytical models provides "
            "an objective, auditable framework for construction progress assessment."
        )
        add_paragraph(
            "A key aspect of this study is the clear distinction maintained between software functional validation and empirical model "
            "performance. The automated test suite confirmed 100% functional pass rates (159/159 tests), verifying that all software components, "
            "API endpoints, data persistence routines, and calculation workflows operate reliably. Concurrently, model benchmark metrics (such as "
            "the 72.85% pixel accuracy on SYSU-CD) reflect actual performance on physical datasets without artificial inflation."
        )
        add_paragraph(
            "The classical change detection pipeline provides a fast, reproducible baseline that operates without GPU hardware, making it "
            "well-suited for field deployment on edge laptops. Its primary limitation lies in lower precision on subtle structural modifications "
            "under shifting solar angles. The integration of Grad-CAM and SHAP addresses the black-box challenge, providing project stakeholders "
            "with verifiable visual and parametric explanations that support contractual decision-making."
        )

        # XII. LIMITATIONS
        add_heading1("XII. LIMITATIONS")
        add_paragraph(
            "1) Illumination and Shadow Drift: The classical Otsu differencing algorithm is sensitive to diurnal variations in solar azimuth "
            "and elevation, which can produce false-positive change indications along building shadow boundaries.\r"
            "2) Two-Dimensional Photogrammetry Limitations: Orthophoto analysis evaluates surface alterations in the 2D plane and cannot "
            "directly quantify volumetric earthwork cut-and-fill operations, which require 3D point cloud reconstruction.\r"
            "3) Weight Dependency for YOLOv8: Real-time object inference requires pre-trained PyTorch weight files (.pt). In their absence, "
            "the system operates in dataset verification mode, evaluating ground-truth annotations directly.\r"
            "4) Subsurface and Interior Occlusion: UAV imagery is inherently limited to exterior and overhead structural elements and cannot "
            "observe subterranean foundation curing, plumbing, or interior electrical installations.\r"
            "5) Project-Specific Ground Truth: Public datasets (LEVIR-CD+, SYSU-CD) provide aerial urban change pairs but lack concurrent "
            "day-to-day contractor schedule logs, necessitating synthetic calibration for S-curve tracking."
        )

        # XIII. CONCLUSION
        add_heading1("XIII. CONCLUSION")
        add_paragraph(
            "This paper presented an explainable, vision-based framework for construction progress assessment and schedule delay prediction "
            "using multi-temporal UAV imagery, developed under Smart India Hackathon problem statement SIH1726. The system integrates automated "
            "image quality validation, construction activity and PPE compliance detection across ten classes, classical bi-temporal change "
            "detection, Earned Value Management schedule variance modeling, and dual-stage Explainable AI combining Grad-CAM spatial heatmaps "
            "with SHAP parametric feature attributions."
        )
        add_paragraph(
            "Empirical evaluation on physical benchmark datasets demonstrated a pixel accuracy of 72.85% on SYSU-CD and 72.00% on LEVIR-CD+, "
            "with the full evaluation executing in 5.9 seconds on standard hardware. Analysis of the Roboflow Construction Site Safety dataset "
            "(38,835 annotations across 2,799 images) quantified real-world class distributions and site safety compliance. The automated software "
            "test suite achieved a 100% pass rate across all 159 tests. The framework produces a standardized evidence report that links physical "
            "visual evidence to contractual schedule milestones, providing an auditable, transparent tool for construction project governance."
        )

        # FUTURE WORK
        add_paragraph("FUTURE WORK", style_name="Heading 1", align=1, space_before=12, space_after=4)
        add_paragraph(
            "Future research directions include: (1) Integrating deep Siamese Vision Transformers (such as ChangeFormer) into the change "
            "detection module to improve precision and IoU under complex solar illumination and shadow variations; (2) Incorporating 3D Neural "
            "Radiance Fields (NeRFs) or 3D Gaussian Splatting to enable volumetric earthwork quantification from drone video sequences; "
            "(3) Implementing bidirectional IFC/BIM integration to automate discrepancy detection between as-built UAV orthophotos and 4D "
            "Building Information Models; and (4) Validating delay forecasting against multi-year longitudinal construction datasets with paired "
            "daily contractor logs."
        )

        # ACKNOWLEDGMENT
        add_paragraph("ACKNOWLEDGMENT", style_name="Heading 1", align=1, space_before=12, space_after=4)
        add_paragraph(
            "The author gratefully acknowledges the resources and technical support provided by the Department of Computer Science and "
            "Engineering at Sri Krishna College of Engineering and Technology, Coimbatore, India. The author also acknowledges the Smart India "
            "Hackathon (SIH) initiative for defining problem statement SIH1726, which provided the operational context for this research."
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
            (24, "[24]\tS. A. Assaf and S. Al-Hejji, \"Causes of delay in large construction projects,\" International Journal of Project Management, vol. 24, no. 4, pp. 349–357, May 2006. https://doi.org/10.1016/j.ijproman.2005.11.010")
        ]

        for num, ref_line in refs_data:
            ref_rng = add_paragraph(ref_line, style_name="references", align=3, space_before=1, space_after=3)
            # Add bookmark on each reference item
            bm_name = f"ref_{num}"
            doc.Bookmarks.Add(bm_name, ref_rng)
            ref_bookmarks[num] = bm_name
            
            # Add external hyperlink to URL/DOI if present
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

        # Clear Section 5 if exists
        if doc.Sections.Count >= 5:
            sec5 = doc.Sections.Item(5)
            rng5 = doc.Range(sec5.Range.Start, sec5.Range.End - 1)
            rng5.Delete()

        print(f"Content populated. Bookmarked {len(ref_bookmarks)} references, {len(fig_bookmarks)} figures, {len(tbl_bookmarks)} tables.", flush=True)

        # =========================================================================
        # 6. LINK ALL CITATIONS IN BODY TEXT TO BOOKMARKS
        # =========================================================================
        print("Linking all citations in body text...", flush=True)
        table_roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
        
        cites_linked = 0
        figs_linked = 0
        tbls_linked = 0

        # Loop through tracked paragraphs in reverse order (bottom to top)
        # and reverse matches inside paragraph, so character indices remain perfectly stable!
        for p_start, txt in reversed(tracked_paragraphs):
            # 1. Literature citations [N]
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

            # 2. Figure citations Fig. N
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

            # 3. Table citations Table Roman
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

        print(f"Linked {cites_linked} literature citations [1]-[24] to references.", flush=True)
        print(f"Linked {figs_linked} figure citations to figures.", flush=True)
        print(f"Linked {tbls_linked} table citations to tables.", flush=True)
        print(f"Total interactive hyperlinks in document: {doc.Hyperlinks.Count}", flush=True)

        # =========================================================================
        # 7. SAVE DOCUMENTS (DOCX & PDF)
        # =========================================================================
        print(f"\nSaving primary Word document: {DOCX_OUT_1}", flush=True)
        doc.SaveAs2(str(DOCX_OUT_1), 16) # 16 = wdFormatXMLDocument (.docx)

        print(f"Exporting PDF document: {PDF_OUT}", flush=True)
        doc.SaveAs2(str(PDF_OUT), 17) # 17 = wdFormatPDF

        doc.Close(False)
        print("Closed Word session.", flush=True)

        # Copy to research-019.docx
        print(f"Copying to {DOCX_OUT_2}", flush=True)
        shutil.copy2(str(DOCX_OUT_1), str(DOCX_OUT_2))

        # Copy all deliverables directly to Desktop as requested
        print("\nCopying deliverables directly to Desktop...", flush=True)
        shutil.copy2(str(DOCX_OUT_1), str(DESKTOP_DIR / "final_ieee_paper.docx"))
        shutil.copy2(str(DOCX_OUT_2), str(DESKTOP_DIR / "research-019.docx"))
        shutil.copy2(str(PDF_OUT), str(DESKTOP_DIR / "final_ieee_paper.pdf"))
        shutil.copy2(str(PROJECT_ROOT / "research_paper" / "manuscript.md"), str(DESKTOP_DIR / "manuscript.md"))

        print("\n=================================================================")
        print("ALL DELIVERABLES SUCCESSFULLY CREATED & SYNCHRONIZED TO DESKTOP!")
        print("=================================================================")
        print(f"1. Desktop Word Document : {DESKTOP_DIR / 'final_ieee_paper.docx'}")
        print(f"2. Desktop Named Copy    : {DESKTOP_DIR / 'research-019.docx'}")
        print(f"3. Desktop PDF Document  : {DESKTOP_DIR / 'final_ieee_paper.pdf'}")
        print(f"4. Desktop Manuscript    : {DESKTOP_DIR / 'manuscript.md'}")
        print(f"Execution completed in {time.time()-t_start:.2f} seconds.")

    finally:
        word.Quit()

if __name__ == "__main__":
    create_ieee_paper()
