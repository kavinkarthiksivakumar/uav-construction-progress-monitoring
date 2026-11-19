"""
Compiles research_paper/manuscript.md into research_paper/plagiarism/paper_final_for_checking.docx
Using python-docx for authentic submission and plagiarism-checking preparation.
"""

import sys
import re
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT_MD = PROJECT_ROOT / "research_paper" / "manuscript.md"
PLAGIARISM_DIR = PROJECT_ROOT / "research_paper" / "plagiarism"
OUTPUT_DOCX = PLAGIARISM_DIR / "paper_final_for_checking.docx"

def compile_markdown_to_docx():
    print(f"Reading markdown from: {MANUSCRIPT_MD}")
    if not MANUSCRIPT_MD.exists():
        raise FileNotFoundError(f"Manuscript not found at {MANUSCRIPT_MD}")
    
    with open(MANUSCRIPT_MD, "r", encoding="utf-8") as f:
        md_text = f.read()

    doc = docx.Document()

    # Page Margins: 1 inch standard
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Style definitions
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)

    lines = md_text.split("\n")
    i = 0
    in_code_block = False
    code_lines = []
    
    while i < len(lines):
        line = lines[i]

        # Handle Code / ASCII Blocks
        if line.startswith("```"):
            if in_code_block:
                # Flush code block
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.4)
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(4)
                run = p.add_run("\n".join(code_lines))
                run.font.name = 'Courier New'
                run.font.size = Pt(9.5)
                run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Handle Markdown Tables
        if line.startswith("|") and i + 1 < len(lines) and "|---" in lines[i + 1]:
            table_lines = [line]
            i += 2  # skip header separator
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            
            # Create Table in Docx
            header_cells = [c.strip() for c in table_lines[0].strip("|").split("|")]
            table = doc.add_table(rows=len(table_lines), cols=len(header_cells))
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = True

            # Populate header
            for col_idx, cell_text in enumerate(header_cells):
                hdr_cell = table.cell(0, col_idx)
                # Strip bold formatting markdown
                clean_hdr = re.sub(r"\*\*(.*?)\*\*", r"\1", cell_text)
                p = hdr_cell.paragraphs[0]
                p.paragraph_format.space_after = Pt(2)
                run = p.add_run(clean_hdr)
                run.bold = True
                run.font.name = 'Times New Roman'
                run.font.size = Pt(10)

            # Populate rows
            for row_idx, row_line in enumerate(table_lines[1:], start=1):
                row_cells = [c.strip() for c in row_line.strip("|").split("|")]
                for col_idx in range(len(header_cells)):
                    val = row_cells[col_idx] if col_idx < len(row_cells) else ""
                    cell = table.cell(row_idx, col_idx)
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_after = Pt(2)
                    clean_val = re.sub(r"\*\*(.*?)\*\*", r"\1", val)
                    clean_val = clean_val.replace("\\ge", "≥").replace("\\le", "≤")
                    run = p.add_run(clean_val)
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(9.5)
            
            p_spacer = doc.add_paragraph()
            p_spacer.paragraph_format.space_after = Pt(4)
            continue

        # Headings
        if line.startswith("# "):
            title_text = line[2:].strip()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(12)
            run = p.add_run(title_text)
            run.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(18)
            run.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
        elif line.startswith("## "):
            h2_text = line[3:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(h2_text)
            run.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(13)
            run.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
        elif line.startswith("### "):
            h3_text = line[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(h3_text)
            run.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11.5)
        elif line.startswith("> "):
            # Blockquote
            quote_text = line[2:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.right_indent = Inches(0.3)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(quote_text)
            run.italic = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
        elif line.strip() == "---":
            # Horizontal rule
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
        elif line.startswith("- ") or line.startswith("* "):
            # Bullet list
            item_text = line[2:].strip()
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_after = Pt(2)
            _add_formatted_runs(p, item_text)
        elif re.match(r"^\d+\.\s", line):
            # Numbered list
            m = re.match(r"^(\d+\.\s)(.*)", line)
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_after = Pt(2)
            _add_formatted_runs(p, m.group(2))
        elif line.strip():
            # Standard paragraph
            p = doc.add_paragraph()
            _add_formatted_runs(p, line.strip())

        i += 1

    PLAGIARISM_DIR.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT_DOCX))
    print(f"Successfully compiled paper docx to:\n  {OUTPUT_DOCX}")
    return OUTPUT_DOCX

def _add_formatted_runs(paragraph, text):
    """Parses basic inline markdown (**bold**, *italic*, `code`) into docx runs."""
    tokens = re.split(r"(\*\*.*?\*\*|\*.*?\*|`.*?`)", text)
    for token in tokens:
        if not token:
            continue
        if token.startswith("**") and token.endswith("**"):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        elif token.startswith("*") and token.endswith("*"):
            run = paragraph.add_run(token[1:-1])
            run.italic = True
        elif token.startswith("`") and token.endswith("`"):
            run = paragraph.add_run(token[1:-1])
            run.font.name = 'Courier New'
            run.font.size = Pt(10)
        else:
            paragraph.add_run(token)

if __name__ == "__main__":
    compile_markdown_to_docx()
