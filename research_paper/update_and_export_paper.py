"""
Update manuscript in DOCX and export to PDF with all 3 authors,
humanized abstract, and strict prompt compliance.
"""

import os
import shutil
import time
from pathlib import Path
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import win32com.client

PROJECT_ROOT = Path(r"c:\Users\asus\Desktop\FINAL PROJECT")
DESKTOP_DIR = Path(r"c:\Users\asus\Desktop")
SRC_DOCX = PROJECT_ROOT / "research_paper" / "final_ieee_paper.docx"

DOCX_RP = PROJECT_ROOT / "research_paper" / "researchpaper.docx"
PDF_RP = PROJECT_ROOT / "research_paper" / "researchpaper.pdf"

DOCX_FINAL = PROJECT_ROOT / "research_paper" / "final_ieee_paper.docx"
DOCX_019 = PROJECT_ROOT / "research_paper" / "research-019.docx"
PDF_FINAL = PROJECT_ROOT / "research_paper" / "final_ieee_paper.pdf"

def update_docx_content():
    print("Loading source DOCX:", SRC_DOCX)
    doc = docx.Document(str(SRC_DOCX))

    # 1. Update Title
    doc.paragraphs[0].text = "Explainable Vision-Based Construction Progress Assessment and Delay Prediction Using Multi-Temporal UAV Imagery"
    doc.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 2. Update Authors in paragraphs 2-6
    # Author block: 3 authors centered
    authors_text = (
        "KAVINKARTHIK S\n"
        "Department of M.Tech Computer Science and Engineering\n"
        "Sri Krishna College of Engineering and Technology, Coimbatore, India\n"
        "727722euci019@skcet.ac.in\n\n"
        "Dr. Emmanuel Joy\n"
        "Assistant Professor, Department of M.Tech CSE\n"
        "Sri Krishna College of Engineering and Technology, Coimbatore, India\n"
        "emmanueljoy@skcet.ac.in\n\n"
        "Ms. KANAGAPRIYA S K\n"
        "Assistant Professor, Department of M.Tech CSE\n"
        "Sri Krishna College of Engineering and Technology, Coimbatore, India\n"
        "kanaka.priyacseengg@gmail.com"
    )
    
    # We clear p2 to p6 and put the authors cleanly
    doc.paragraphs[2].text = authors_text
    doc.paragraphs[2].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[3].text = ""
    doc.paragraphs[4].text = ""
    doc.paragraphs[5].text = ""
    doc.paragraphs[6].text = ""

    # Format author paragraph
    p2 = doc.paragraphs[2]
    p2.paragraph_format.space_before = Pt(4)
    p2.paragraph_format.space_after = Pt(10)
    for run in p2.runs:
        run.font.name = "Times New Roman"
        run.font.size = Pt(9.5)

    # 3. Update Abstract (p9)
    humanized_abstract = (
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
    doc.paragraphs[9].text = humanized_abstract
    doc.paragraphs[9].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # 4. Check and remove any SIH occurrences across all paragraphs
    for idx, p in enumerate(doc.paragraphs):
        t = p.text
        if "SIH" in t or "Smart India Hackathon" in t:
            print(f"Sanitizing SIH mention at P[{idx}]: {t[:60]}...")
            if idx == 15:
                p.text = (
                    "To address these operational and technical challenges, this study presents an integrated, "
                    "vision-based construction monitoring and decision-support framework that links multi-temporal UAV imagery "
                    "directly with schedule-grounded analytical models. The system combines automated sensor validation, "
                    "construction activity detection across ten classes, classical multi-temporal change detection, S-curve "
                    "progress deviation modeling, and dual-stage visual and parametric explainability within an auditable monitoring architecture."
                )
            elif idx == 142 or "This paper presented an explainable" in t:
                p.text = (
                    "This paper presented an explainable, vision-based construction monitoring and decision-support framework "
                    "using multi-temporal UAV imagery. The system integrates automated image quality validation, construction "
                    "activity and PPE compliance detection across ten classes, classical bi-temporal change detection, S-curve "
                    "schedule deviation modeling, and dual-stage Explainable AI combining Grad-CAM spatial heatmaps with SHAP "
                    "parametric feature attributions."
                )
            elif idx == 147 or "acknowledged the Smart India Hackathon" in t or "Department of Computer Science" in t:
                p.text = (
                    "The authors gratefully acknowledge the Department of Computer Science and Engineering at Sri Krishna College "
                    "of Engineering and Technology, Coimbatore, India, for providing computational infrastructure and technical support."
                )
            else:
                p.text = t.replace("under Smart India Hackathon problem statement SIH1726", "") \
                          .replace("Smart India Hackathon problem statement SIH1726", "") \
                          .replace("under Smart India Hackathon", "") \
                          .replace("SIH1726", "")

    # Save to researchpaper.docx
    print("Saving updated DOCX to:", DOCX_RP)
    doc.save(str(DOCX_RP))

    # Also update final_ieee_paper.docx and research-019.docx
    doc.save(str(DOCX_FINAL))
    doc.save(str(DOCX_019))
    shutil.copy2(str(DOCX_RP), str(DESKTOP_DIR / "researchpaper.docx"))
    print("DOCX files updated successfully!")

def export_to_pdf():
    print("Exporting PDF using Word COM automation...")
    os.system("taskkill /f /im WINWORD.EXE >nul 2>&1")
    time.sleep(1)

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0

    try:
        doc = word.Documents.Open(str(DOCX_RP))
        print("Opened DOCX in Word successfully.")
        
        # Save as researchpaper.pdf
        doc.SaveAs2(str(PDF_RP), 17)
        print("Saved PDF to:", PDF_RP)
        
        # Save as final_ieee_paper.pdf
        doc.SaveAs2(str(PDF_FINAL), 17)
        print("Saved PDF to:", PDF_FINAL)

        doc.Close(False)
        
        # Copy to Desktop
        shutil.copy2(str(PDF_RP), str(DESKTOP_DIR / "researchpaper.pdf"))
        shutil.copy2(str(PDF_RP), str(DESKTOP_DIR / "final_ieee_paper.pdf"))
        print("Synchronized PDF files to Desktop successfully!")
    finally:
        word.Quit()

if __name__ == "__main__":
    update_docx_content()
    export_to_pdf()
    print("=" * 60)
    print("DELIVERABLES GENERATION COMPLETE!")
    print("=" * 60)
