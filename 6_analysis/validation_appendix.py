# Table: validation of the temporal marker dictionary (English, Times New Roman)
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()
st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(10)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
sec = doc.sections[0]
for m in ("left_margin", "right_margin"): setattr(sec, m, Cm(2.2))

def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), color); tcPr.append(s)

def table(title, hdr, rows, widths, note):
    p = doc.add_paragraph(); r = p.add_run(title); r.bold = True
    t = doc.add_table(rows=1, cols=len(hdr)); t.style = "Table Grid"; t.autofit = False
    for i, h in enumerate(hdr):
        c = t.rows[0].cells[i]; c.text = ""; rr = c.paragraphs[0].add_run(h); rr.bold = True; shade(c, "D9D9D9")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = str(v)
            if i > 0: cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths): gc.set(qn("w:w"), str(int(w.twips)))
    for r_ in t.rows:
        for i, w in enumerate(widths): r_.cells[i].width = w
    pn = doc.add_paragraph(); rn = pn.add_run(note); rn.italic = True; rn.font.size = Pt(8.5)

p = doc.add_paragraph(); r = p.add_run("Table 2. Validation of the temporal marker dictionary"); r.bold = True; r.font.size = Pt(11)

table("Panel A. Precision of the dictionary (manual coding, 240 occurrences)",
      ["Dictionary category", "n", "Temporal orientation present (%)", "Direction consistent (%)", "Coded ambiguous (%)"],
      [["Explicit, long term", 60, "93.3", "98.0", "12.5"],
       ["Explicit, short term", 60, "93.3", "100.0", "0.0"],
       ["Implicit, long term", 60, "100.0", "87.0", "23.3"],
       ["Implicit, short term", 60, "38.3", "100.0", "0.0"],
       ["All markers", 240, "81.2", "—", "10.8"]],
      [Cm(4.6), Cm(1.4), Cm(3.6), Cm(3.4), Cm(3.4)],
      "Note. Occurrences (60 per category) were drawn at random and coded blind to the dictionary category, using the version tested before revision. "
      "Temporal orientation present: share of occurrences coded as expressing a temporal orientation (Q1). Direction consistent: among those, share whose "
      "short- or long-term direction (Q2) matches the dictionary category, excluding occurrences coded ambiguous. Coded ambiguous: share of Q1-positive "
      "occurrences coded as ambiguous. The dictionary was revised on this basis (Table A1, panel D); precision is not recomputed on the revised version, "
      "which was derived from this sample.")

table("Panel B. Inter-coder agreement (second coder, 100 occurrences)",
      ["Subset and question", "n", "Agreement (%)", "Cohen's κ", "Gwet's AC1"],
      [["All markers", "", "", "", ""],
       ["   Q1 Temporal orientation present", 100, "57.0", "0.18", "0.21"],
       ["   Q2 Short / long / ambiguous", 43, "88.4", "0.79", "0.84"],
       ["   Q3 Attachment", 43, "65.1", "0.48", "0.55"],
       ["Explicit markers (final dictionary)", "", "", "", ""],
       ["   Q1 Temporal orientation present", 36, "91.7", "—ᵃ", "0.91"],
       ["   Q2 Short / long / ambiguous", 33, "87.9", "0.77", "0.84"],
       ["Implicit markers", "", "", "", ""],
       ["   Q1 Temporal orientation present", 50, "40.0", "0.10", "−0.17"]],
      [Cm(6.4), Cm(1.4), Cm(2.8), Cm(2.4), Cm(2.4)],
      "Note. Q2 and Q3 are computed on occurrences that both coders coded as expressing a temporal orientation (Q1 = yes). Q3 uses the first coder's codes "
      "before reconciliation. ᵃ Cohen's κ is not informative when almost all occurrences fall in one category (prevalence paradox); Gwet's AC1 is reported "
      "for this reason. Agreement on implicit markers is low because the second coder read them as activity domains rather than temporal orientations; "
      "they are therefore analysed separately (exploratory). Interpretation follows Landis and Koch (1977).")
doc.save("table_validation.docx"); print("ok")
