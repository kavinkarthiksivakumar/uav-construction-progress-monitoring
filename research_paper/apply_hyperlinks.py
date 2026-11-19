"""
Apply Interactive Cross-Referenced Hyperlinks to IEEE Research Paper
===================================================================
This script opens the finalized IEEE paper document, creates Word bookmarks
for all references, figures, and tables, and converts all citation mentions
into active hyperlinks that redirect to the exact referenced location.

Target Deliverables:
  - research_paper/final_ieee_paper.docx
  - research_paper/research-019.docx
  - research_paper/final_ieee_paper.pdf
  - c:\\Users\\asus\\Desktop\\final_ieee_paper.docx
  - c:\\Users\\asus\\Desktop\\research-019.docx
  - c:\\Users\\asus\\Desktop\\final_ieee_paper.pdf
"""

import os
import re
import sys
import time
import shutil
from pathlib import Path
import win32com.client

PROJECT_ROOT = Path(r"c:\Users\asus\Desktop\FINAL PROJECT")
DESKTOP_DIR = Path(r"c:\Users\asus\Desktop")
DOCX_SRC = PROJECT_ROOT / "research_paper" / "final_ieee_paper.docx"

DOCX_OUT_1 = PROJECT_ROOT / "research_paper" / "final_ieee_paper.docx"
DOCX_OUT_2 = PROJECT_ROOT / "research_paper" / "research-019.docx"
PDF_OUT = PROJECT_ROOT / "research_paper" / "final_ieee_paper.pdf"

DESKTOP_DOCX_1 = DESKTOP_DIR / "final_ieee_paper.docx"
DESKTOP_DOCX_2 = DESKTOP_DIR / "research-019.docx"
DESKTOP_PDF = DESKTOP_DIR / "final_ieee_paper.pdf"


def clean_lock_files():
    """Remove stale Word lock files (~$*) if Word is not running."""
    for folder in [PROJECT_ROOT / "research_paper", DESKTOP_DIR]:
        for lock in folder.glob("~$*.docx"):
            try:
                lock.unlink()
                print(f"Removed stale lock file: {lock.name}")
            except Exception:
                pass


def apply_citations_and_hyperlinks():
    t_start = time.time()
    print("=" * 70)
    print("APPLYING CITATION REDIRECTIONS & INTERACTIVE HYPERLINKS")
    print("=" * 70)

    clean_lock_files()

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0

    try:
        print(f"Opening document: {DOCX_SRC} ...", flush=True)
        doc = word.Documents.Open(str(DOCX_SRC))
        print("Document opened successfully.", flush=True)

        # ---------------------------------------------------------
        # Step 1: Ensure [24] is cited in the Introduction paragraph
        # ---------------------------------------------------------
        intro_updated = False
        for p in doc.Paragraphs:
            txt = p.Range.Text
            if "[1], [2], [3]" in txt and "[24]" not in txt:
                rng = p.Range
                if rng.Find.Execute("[1], [2], [3]", False, False, False, False, False, True, 0, False):
                    rng.Text = "[1], [2], [3], [24]"
                    intro_updated = True
                    print("Updated Introduction citation to include [24].")
                    break

        # ---------------------------------------------------------
        # Step 2: Bookmark all 24 reference items in REFERENCES section
        # ---------------------------------------------------------
        ref_bms = {}
        for p in doc.Paragraphs:
            if p.Style.NameLocal.lower() == "references":
                txt = p.Range.Text.strip()
                m = re.match(r"^\[(\d+)\]", txt)
                if m:
                    num = int(m.group(1))
                    bm_name = f"ref_{num}"
                    doc.Bookmarks.Add(bm_name, p.Range)
                    ref_bms[num] = bm_name

        print(f"Bookmarked {len(ref_bms)} references: ref_1 to ref_{max(ref_bms.keys())}")

        # ---------------------------------------------------------
        # Step 3: Bookmark all Figure Captions (Fig. 1 to Fig. 7)
        # ---------------------------------------------------------
        fig_bms = {}
        for p in doc.Paragraphs:
            if "caption" in p.Style.NameLocal.lower():
                txt = p.Range.Text.strip()
                m = re.search(r"Fig\.\s*(\d+)\.", txt)
                if m:
                    f_num = int(m.group(1))
                    bm_name = f"fig_{f_num}"
                    doc.Bookmarks.Add(bm_name, p.Range)
                    fig_bms[f_num] = bm_name

        print(f"Bookmarked {len(fig_bms)} figures: {sorted(fig_bms.keys())}")

        # ---------------------------------------------------------
        # Step 4: Bookmark all Table Headings (TABLE I to TABLE V)
        # ---------------------------------------------------------
        tbl_bms = {}
        roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
        for p in doc.Paragraphs:
            txt = p.Range.Text.strip()
            m = re.search(r"^TABLE\s+([IVXLCDM]+)$", txt, re.IGNORECASE)
            if m:
                r_str = m.group(1).upper()
                if r_str in roman_map:
                    t_num = roman_map[r_str]
                    bm_name = f"tbl_{t_num}"
                    doc.Bookmarks.Add(bm_name, p.Range)
                    tbl_bms[t_num] = bm_name

        print(f"Bookmarked {len(tbl_bms)} tables: {sorted(tbl_bms.keys())}")

        # ---------------------------------------------------------
        # Step 5: Convert Body Citations to Internal Hyperlinks
        # ---------------------------------------------------------
        citations_linked = 0
        figs_linked = 0
        tbls_linked = 0

        # Sort Roman numerals by length descending so Table III is processed before Table I
        sorted_romans = sorted(roman_map.keys(), key=lambda r: len(r), reverse=True)

        for p in doc.Paragraphs:
            p_style = p.Style.NameLocal.lower()
            if p_style == "references":
                continue

            txt = p.Range.Text

            # 5a. Literature Citations [num]
            cites = re.findall(r"\[(\d+)\]", txt)
            for c in set(cites):
                num = int(c)
                if num in ref_bms:
                    rng = p.Range
                    target = f"[{num}]"
                    if rng.Find.Execute(target, False, False, False, False, False, True, 0, False):
                        doc.Hyperlinks.Add(
                            Anchor=rng,
                            Address="",
                            SubAddress=ref_bms[num],
                            ScreenTip=f"Jump to Reference [{num}]"
                        )
                        citations_linked += 1

            # 5b. Figure Citations Fig. N
            if "caption" not in p_style:
                fig_matches = re.findall(r"\bFig\.\s*(\d+)\b", txt)
                for f_str in set(fig_matches):
                    f_num = int(f_str)
                    if f_num in fig_bms:
                        rng = p.Range
                        target = f"Fig. {f_num}"
                        if rng.Find.Execute(target, False, False, False, False, False, True, 0, False):
                            doc.Hyperlinks.Add(
                                Anchor=rng,
                                Address="",
                                SubAddress=fig_bms[f_num],
                                ScreenTip=f"Jump to Fig. {f_num}"
                            )
                            figs_linked += 1

            # 5c. Table Citations Table Roman
            if p_style != "table head":
                for r_str in sorted_romans:
                    pattern = rf"\bTable\s+{r_str}\b"
                    if re.search(pattern, txt):
                        t_num = roman_map[r_str]
                        if t_num in tbl_bms:
                            rng = p.Range
                            target = f"Table {r_str}"
                            if rng.Find.Execute(target, False, False, False, False, False, True, 0, False):
                                doc.Hyperlinks.Add(
                                    Anchor=rng,
                                    Address="",
                                    SubAddress=tbl_bms[t_num],
                                    ScreenTip=f"Jump to Table {r_str}"
                                )
                                tbls_linked += 1

        print(f"Linked {citations_linked} literature citations ([1] - [24]).")
        print(f"Linked {figs_linked} figure citations (Fig. 1 - Fig. 7).")
        print(f"Linked {tbls_linked} table citations (Table I - Table V).")

        # ---------------------------------------------------------
        # Step 6: Convert DOIs and URLs in References to External Links
        # ---------------------------------------------------------
        urls_linked = 0
        for p in doc.Paragraphs:
            if p.Style.NameLocal.lower() == "references":
                txt = p.Range.Text
                urls = re.findall(r"https?://[^\s\r\n]+", txt)
                for u in urls:
                    clean_u = u.rstrip(".,;)")
                    rng = p.Range
                    if rng.Find.Execute(clean_u, False, False, False, False, False, True, 0, False):
                        doc.Hyperlinks.Add(
                            Anchor=rng,
                            Address=clean_u,
                            ScreenTip=f"Open {clean_u}"
                        )
                        urls_linked += 1

        print(f"Linked {urls_linked} external reference URLs/DOIs.")
        total_links = doc.Hyperlinks.Count
        print(f"Total interactive hyperlinks in document: {total_links}")

        # ---------------------------------------------------------
        # Step 7: Save to Target Deliverables & Export PDF
        # ---------------------------------------------------------
        print("Saving final document deliverables ...", flush=True)
        doc.Save()
        print(f"  -> Saved: {DOCX_OUT_1}")

        # Save copy as research-019.docx
        doc.SaveAs2(str(DOCX_OUT_2), 16)
        print(f"  -> Saved: {DOCX_OUT_2}")

        # Export PDF with native bookmarks and hyperlinks
        # 17 = wdExportFormatPDF
        doc.ExportAsFixedFormat(
            OutputFileName=str(PDF_OUT),
            ExportFormat=17,
            OpenAfterExport=False,
            OptimizeFor=0,           # wdExportOptimizeForPrint
            Range=0,                 # wdExportAllDocument
            IncludeDocProps=True,
            KeepIRM=True,
            CreateBookmarks=1,       # wdExportCreateHeadingBookmarks / Word Bookmarks
            DocStructureTags=True,
            BitmapMissingFonts=True,
            UseISO19005_1=False
        )
        print(f"  -> Exported PDF: {PDF_OUT}")

        doc.Close(False)

        # ---------------------------------------------------------
        # Step 8: Copy Deliverables to Desktop
        # ---------------------------------------------------------
        print("Synchronizing deliverables to Desktop ...", flush=True)
        shutil.copy2(DOCX_OUT_1, DESKTOP_DOCX_1)
        print(f"  -> Desktop: {DESKTOP_DOCX_1}")

        shutil.copy2(DOCX_OUT_2, DESKTOP_DOCX_2)
        print(f"  -> Desktop: {DESKTOP_DOCX_2}")

        shutil.copy2(PDF_OUT, DESKTOP_PDF)
        print(f"  -> Desktop: {DESKTOP_PDF}")

        elapsed = time.time() - t_start
        print(f"ALL DELIVERABLES SUCCESSFULLY UPDATED in {elapsed:.2f}s!")
        print("=" * 70)

        return {
            "ref_bms": len(ref_bms),
            "fig_bms": len(fig_bms),
            "tbl_bms": len(tbl_bms),
            "citations_linked": citations_linked,
            "figs_linked": figs_linked,
            "tbls_linked": tbls_linked,
            "urls_linked": urls_linked,
            "total_links": total_links,
            "elapsed": elapsed
        }

    finally:
        word.Quit()


if __name__ == "__main__":
    apply_citations_and_hyperlinks()
