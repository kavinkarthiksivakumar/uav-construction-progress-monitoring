import docx

doc = docx.Document('research_paper/final_ieee_paper.docx')
with open('research_paper/equations_list.txt', 'w', encoding='utf-8') as f:
    for i, p in enumerate(doc.paragraphs):
        txt = p.text
        if p.style.name.lower() == 'equation' or any(f'({num})' in txt for num in range(1, 13)):
            f.write(f"P[{i}] (style={p.style.name}): {repr(txt)}\n")

print("Wrote equations_list.txt")
