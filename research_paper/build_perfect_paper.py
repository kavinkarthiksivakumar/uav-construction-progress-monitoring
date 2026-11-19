"""
Build the publication-quality IEEE research paper matching the exact visual layout,
3-author header table, 7 figures, 5 tables, and clean typography.
"""

import os
import shutil
import time
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls
import win32com.client

PROJECT_ROOT = Path(r"c:\Users\asus\Desktop\FINAL PROJECT")
DESKTOP_DIR = Path(r"c:\Users\asus\Desktop")
SRC_DOCX = PROJECT_ROOT / "research_paper" / "final_ieee_paper.docx"

DOCX_OUT_RP = PROJECT_ROOT / "research_paper" / "researchpaper.docx"
PDF_OUT_RP = PROJECT_ROOT / "research_paper" / "researchpaper.pdf"
DOCX_OUT_019 = PROJECT_ROOT / "research_paper" / "research-019.docx"

def set_cell_margins(cell, top=50, bottom=50, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def build_paper():
    print("Loading base document:", SRC_DOCX)
    doc = docx.Document(str(SRC_DOCX))

    # 1. Title formatting (P[0])
    p0 = doc.paragraphs[0]
    p0.text = "Explainable Vision-Based Construction Progress Assessment and Delay Prediction Using Multi-Temporal UAV Imagery"
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p0.paragraph_format.space_before = Pt(0)
    p0.paragraph_format.space_after = Pt(12)
    for r in p0.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(24)

    # 2. Build 3-Author Table (Matching IEEE template screenshot exactly)
    # 3 equal columns: each ~2.33 inches across 7.0 inch page width
    tbl = doc.add_table(rows=1, cols=3)
    tbl.autofit = False
    tbl.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER

    # Remove all borders from author table
    tblPr = tbl._tbl.tblPr
    borders_xml = parse_xml(
        '<w:tblBorders %s>'
        '<w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/>'
        '<w:insideH w:val="none"/><w:insideV w:val="none"/>'
        '</w:tblBorders>' % nsdecls('w')
    )
    tblPr.append(borders_xml)

    authors_data = [
        (
            "KAVINKARTHIK S",
            "Dept. of M.Tech Computer Science and Eng.",
            "Sri Krishna College of Eng. and Technology",
            "Coimbatore, India",
            "727722euci019@skcet.ac.in"
        ),
        (
            "Dr. Emmanuel Joy",
            "Assistant Professor, Dept. of M.Tech CSE",
            "Sri Krishna College of Eng. and Technology",
            "Coimbatore, India",
            "emmanueljoy@skcet.ac.in"
        ),
        (
            "Ms. KANAGAPRIYA S K",
            "Assistant Professor, Dept. of M.Tech CSE",
            "Sri Krishna College of Eng. and Technology",
            "Coimbatore, India",
            "kanaka.priyacseengg@gmail.com"
        )
    ]

    col_w = Inches(2.32)
    for idx, (name, dept, org, loc, email) in enumerate(authors_data):
        cell = tbl.cell(0, idx)
        cell.width = col_w
        set_cell_margins(cell, top=0, bottom=60, left=40, right=40)
        
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.05

        # Line 1: Name (bold 10pt)
        r_name = p.add_run(name + "\n")
        r_name.font.name = "Times New Roman"
        r_name.font.size = Pt(10)
        r_name.font.bold = True

        # Line 2: Dept (italic 8.5pt)
        r_dept = p.add_run(dept + "\n")
        r_dept.font.name = "Times New Roman"
        r_dept.font.size = Pt(8.5)
        r_dept.font.italic = True

        # Line 3: Organization (italic 8.5pt)
        r_org = p.add_run(org + "\n")
        r_org.font.name = "Times New Roman"
        r_org.font.size = Pt(8.5)
        r_org.font.italic = True

        # Line 4: City, Country (8.5pt)
        r_loc = p.add_run(loc + "\n")
        r_loc.font.name = "Times New Roman"
        r_loc.font.size = Pt(8.5)

        # Line 5: Email (8.5pt)
        r_email = p.add_run(email)
        r_email.font.name = "Times New Roman"
        r_email.font.size = Pt(8.5)

    # Move table before P[2]
    doc.paragraphs[2]._p.addprevious(tbl._tbl)

    # Clear paragraphs 2-8
    for i in range(2, 9):
        doc.paragraphs[i].text = ""
        doc.paragraphs[i].paragraph_format.space_before = Pt(0)
        doc.paragraphs[i].paragraph_format.space_after = Pt(0)

    # 3. Update Abstract (P[9]) - Humanized, complete, clean
    p9 = doc.paragraphs[9]
    p9.text = (
        "Abstract—Tracking physical progress on active building construction sites remains a formidable operational "
        "challenge. Conventional monitoring practices depend heavily on periodic visual walkthroughs conducted by field "
        "engineers. While valuable for qualitative appraisal, manual walkthroughs are labor-intensive, subjective, "
        "physically hazardous, and produce sparse spatial records that frequently fail to detect structural deviations "
        "before critical milestones are compromised. Low-altitude Unmanned Aerial Vehicles (UAVs) provide a flexible, "
        "non-intrusive platform for frequent aerial visual data acquisition. However, raw aerial imagery cannot be reliably "
        "transformed into contractual management decisions without systematic quality filtering, verified asset detection, "
        "and explainable computational analytics. This paper presents an explainable, end-to-end vision-based framework for "
        "construction progress assessment and schedule delay prediction using multi-temporal UAV imagery. The pipeline "
        "integrates automated image validation and quality filtering, spatial alignment, construction activity and safety "
        "compliance detection across ten classes, classical multi-temporal change detection, schedule deviation modeling, "
        "and dual-stage Explainable AI (XAI) combining spatial Grad-CAM activation heatmaps with parametric SHAP feature "
        "attribution. The system was validated against physical benchmarks including LEVIR-CD+ and SYSU-CD for change detection, "
        "and the Roboflow Construction Site Safety dataset (2,799 images, 38,835 annotations). The deterministic change detection "
        "pipeline achieves a pixel accuracy of 72.85% (IoU 0.1852, F1 0.2921) on SYSU-CD and 72.00% accuracy on LEVIR-CD+ without "
        "requiring GPU infrastructure. Automated functional verification demonstrated 100% pass rates across all 159 software test "
        "cases. The entire pipeline produces a structured evidence report providing transparent, auditable project management "
        "decision support."
    )
    p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p9.paragraph_format.space_before = Pt(0)
    p9.paragraph_format.space_after = Pt(4)

    # Format Abstract bold-italic prefix
    for r in p9.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.italic = False

    # 4. Update Index Terms (P[10])
    p10 = doc.paragraphs[10]
    p10.text = "Index Terms—UAV imagery, construction progress monitoring, computer vision, multi-temporal change detection, construction activity detection, schedule deviation, Explainable AI, Grad-CAM, SHAP."
    p10.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p10.paragraph_format.space_before = Pt(2)
    p10.paragraph_format.space_after = Pt(6)
    for r in p10.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.italic = True

    # 5. Update Introduction ending paragraph (P[15])
    p15 = doc.paragraphs[15]
    p15.text = (
        "To address these operational and technical challenges, this study presents an explainable, end-to-end "
        "vision-based framework that integrates multi-temporal UAV imagery with schedule-grounded analytical models. "
        "The system combines automated sensor validation, construction activity detection across ten classes, "
        "classical multi-temporal change detection, S-curve progress deviation modeling, and dual-stage visual and "
        "parametric explainability within an auditable monitoring architecture."
    )
    p15.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for r in p15.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)

    # 6. Fix Equation formatting so no box/corrupted glyphs appear in PDF
    equations_map = {
        43: "Var(ΔI) = (1/N) Σ_{x,y} (ΔI(x,y) - μ_ΔI)²\t(1)",
        47: "C_safe = [N_compliant / (N_compliant + N_violation)] × 100%\t(2)",
        54: "ΔD(x, y) = |G_{t2}(x, y) - G_{t1}(x, y)|\t(3)",
        58: "R_change = [1 / (W × H)] Σ_{x=1}^W Σ_{y=1}^H M_clean(x, y) × 100%\t(4)",
        63: "P_obs(t) = w_chg · S_chg(t) + w_act · S_act(t) + w_temp · S_temp(t) + w_qual · S_qual(t)\t(5)",
        67: "P_exp(t) = 100 / [1 + exp(-α (t/D - 0.5))]\t(6)",
        71: "ΔP(t) = P_obs(t) - P_exp(t)\t(7)",
        73: "Delay_days = -[ΔP(t) / 100] × D_planned\t(8)",
        77: "α_k^c = (1/Z) Σ_{i=1}^U Σ_{j=1}^V [∂Y^c / ∂A_{i,j}^k]\t(9)",
        79: "L_{Grad-CAM}^c = ReLU(Σ_k α_k^c A^k)\t(10)",
        83: "f(x) = φ_0 + Σ_{m=1}^M φ_m\t(11)"
    }

    for p_idx, eq_text in equations_map.items():
        if p_idx < len(doc.paragraphs):
            p_eq = doc.paragraphs[p_idx]
            p_eq.text = "\t" + eq_text
            p_eq.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_eq.paragraph_format.space_before = Pt(3)
            p_eq.paragraph_format.space_after = Pt(3)
            for r in p_eq.runs:
                r.font.name = "Cambria Math"
                r.font.size = Pt(9.5)
                r.font.italic = False

    # 7. Check and fix Headings / Conclusion / Acknowledgment
    for idx, p in enumerate(doc.paragraphs):
        t = p.text
        if "XII. LIMITATIONS" in t:
            p.text = "XII. LIMITATIONS"
        elif "XII. CONCLUSION" in t:
            p.text = "XIII. CONCLUSION"
        elif "XII. FUTURE WORK" in t or "FUTURE WORK" == t.strip():
            p.text = "FUTURE WORK"
        elif "XII. ACKNOWLEDGMENT" in t or "ACKNOWLEDGMENT" in t:
            p.text = "ACKNOWLEDGMENT"
        elif "XII. REFERENCES" in t or "REFERENCES" in t:
            p.text = "REFERENCES"
        
        # Remove any lingering SIH mention
        if "Smart India Hackathon" in t or "SIH1726" in t:
            if idx == 142 or "This paper presented an explainable" in t:
                p.text = (
                    "This paper presented an explainable, vision-based framework for construction progress assessment and "
                    "schedule delay prediction using multi-temporal UAV imagery. The system integrates automated image quality "
                    "validation, construction activity and PPE compliance detection across ten classes, classical bi-temporal change "
                    "detection, S-curve schedule deviation modeling, and dual-stage Explainable AI combining Grad-CAM spatial "
                    "heatmaps with SHAP parametric feature attributions."
                )
            elif idx == 147 or "acknowledged the Smart India Hackathon" in t:
                p.text = (
                    "The authors gratefully acknowledge the Department of Computer Science and Engineering at Sri Krishna College "
                    "of Engineering and Technology, Coimbatore, India, for providing computational infrastructure and technical support."
                )

    # Save Word document
    print("Saving updated document to:", DOCX_OUT_RP)
    doc.save(str(DOCX_OUT_RP))
    doc.save(str(DOCX_OUT_019))
    shutil.copy2(str(DOCX_OUT_RP), str(DESKTOP_DIR / "researchpaper.docx"))
    shutil.copy2(str(DOCX_OUT_RP), str(DESKTOP_DIR / "research-019.docx"))
    print("Saved Word documents successfully!")

def export_pdf():
    print("Exporting PDF via Word COM...")
    os.system("taskkill /f /im WINWORD.EXE >nul 2>&1")
    time.sleep(1)

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0

    try:
        doc = word.Documents.Open(str(DOCX_OUT_RP))
        doc.SaveAs2(str(PDF_OUT_RP), 17) # 17 = wdFormatPDF
        doc.Close(False)
        print("Saved PDF to:", PDF_OUT_RP)

        shutil.copy2(str(PDF_OUT_RP), str(DESKTOP_DIR / "researchpaper.pdf"))
        shutil.copy2(str(PDF_OUT_RP), str(DESKTOP_DIR / "research-019.pdf"))
        print("Synchronized PDF to Desktop successfully!")
    finally:
        word.Quit()

if __name__ == "__main__":
    build_paper()
    export_pdf()
    print("=" * 60)
    print("PERFECT PAPER GENERATION COMPLETE!")
    print("=" * 60)
