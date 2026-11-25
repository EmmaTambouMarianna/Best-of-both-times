# Appendix table: final temporal marker dictionary (v4), English, Times New Roman, landscape.
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

rows = [
 ("A. Explicit markers — main measure", None),
 ("Long term", "Long term", "long-term, longer-term", "long terme, plus long terme", 219, 167, 47),
 ("", "Future", "future(s) (excl. future-proof)", "avenir, futur(e)(s)", 1068, 415, 75),
 ("", "Years ahead", "years ahead, coming years, years to come, next n years, next/coming decade(s)", "prochaines années, années à venir, prochaines décennies", 30, 26, 14),
 ("", "Dates 2030+", "2030–2069 (excl. standards, e.g. PAS 2080)", "2030–2069", 47, 30, 15),
 ("Short term", "Short term", "short-term, near-term", "court terme", 29, 25, 13),
 ("", "Immediate", "immediate(ly)", "immédiat(e)(ment)", 56, 42, 21),
 ("", "Urgent", "urgent, urgency", "urgent(e), urgence", 24, 20, 12),
 ("", "Within days", "within hours/days/weeks/months", "en quelques heures/jours/semaines", 0, 0, 0),
 ("", "Quick wins", "quick win(s)", "gains rapides", 13, 13, 6),
 ("", "Speed", "rapid(ly), quickly, fast-paced, faster, fast-track", "rapide(s), rapidement", 614, 317, 72),
 ("B. Implicit markers — exploratory analysis", None),
 ("Long term", "Sustainability", "sustainab*", "développement durable, durabilité", 1375, 423, 72),
 ("", "Net zero / decarbonisation", "net zero, decarbonis(z)*, carbon neutral*, low carbon", "carboneutr*, décarbon*, bas carbone", 275, 59, 21),
 ("", "Climate", "climate (excl. economic/business climate)", "climat(ique)(s)", 448, 157, 39),
 ("Short term", "Crisis management", "crisis management/response/communication(s)", "gestion de crise", 34, 20, 8),
 ("", "Turnaround", "turnaround(s)", "redressement", 89, 60, 12),
 ("", "Cash / liquidity", "cash management, liquidity, working capital", "trésorerie, liquidités, fonds de roulement", 102, 54, 19),
 ("", "Interim management", "interim management/manager(s)/executive(s)/leadership/CFO/CEO", "management de transition, gestion intérimaire", 43, 31, 6),
 ("C. Ambiguous markers — sensitivity analyses only", None),
 ("Undetermined", "Tomorrow", "tomorrow", "demain", 123, 89, 25),
 ("", "ESG", "ESG", "ESG", 150, 63, 28),
 ("", "Energy transition / circular economy", "energy transition, circular economy", "transition énergétique, économie circulaire", 32, 21, 9),
 ("", "Succession planning", "succession planning", "planification de la relève", 16, 16, 4),
 ("D. Terms excluded from the dictionary", None),
 ("Non-temporal (coding)", "Restructuring", "restructur*", "restructur*", 236, 146, 28),
 ("", "Cost reduction", "cost reduction/cutting/savings/containment", "réduction des coûts", 268, 89, 24),
 ("", "Insolvency / distress", "insolvenc*, bankruptc*, financial distress", "insolvabilité, faillite", 118, 34, 6),
 ("Non-temporal (second coder)", "Agile", "agil*", "agil*", 368, 172, 47),
 ("", "Day-to-day", "day-to-day", "au quotidien", 27, 24, 13),
 ("Set aside before coding", "Decades (alone)", "decade(s) (mostly retrospective)", "décennie(s)", 133, 105, 36),
 ("", "Today / now", "today, now", "aujourd'hui, maintenant", 907, 465, 78),
 ("", "Quick / fast (alone)", "quick, fast (often navigation)", "—", 217, 170, 48),
 ("", "Future-proof", "future-proof*", "pérenn*", 29, 22, 10),
 ("", "Next generation", "next generation, next-gen", "nouvelle génération", 131, 72, 28),
 ("", "Beyond", "beyond", "au-delà", 197, 147, 47),
 ("", "Quarter", "quarter(ly) (mostly financial reporting)", "trimestr*", 56, 38, 20),
 ("", "Transformation", "transform* (describes change, not a horizon)", "transform*", 2131, 515, 78),
 ("", "Litigation", "litigation (mostly retrospective)", "litige(s), contentieux", 474, 112, 20),
]

doc = Document()
st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(9)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
sec = doc.sections[0]; sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = sec.page_height, sec.page_width
for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, m, Cm(1.8))

p = doc.add_paragraph(); r = p.add_run("Table A1. Final dictionary of temporal markers (version 4)"); r.bold = True; r.font.size = Pt(11)
hdr = ["Category", "Marker", "English terms", "French terms", "Occ.", "Pages", "Firms"]
widths = [Cm(3.6), Cm(3.6), Cm(7.6), Cm(5.8), Cm(1.4), Cm(1.4), Cm(1.4)]
t = doc.add_table(rows=1, cols=7); t.style = "Table Grid"
def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), color); tcPr.append(s)
for i, h in enumerate(hdr):
    c = t.rows[0].cells[i]; c.text = ""; rr = c.paragraphs[0].add_run(h); rr.bold = True; shade(c, "D9D9D9")
for row in rows:
    cells = t.add_row().cells
    if row[1] is None:
        m = cells[0].merge(cells[6]); m.text = ""; rr = m.paragraphs[0].add_run(row[0]); rr.bold = True; rr.italic = True; shade(m, "F2F2F2")
        continue
    for i, v in enumerate(row):
        cells[i].text = f"{v:,}" if isinstance(v, int) else v
        if i >= 4: cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
for r_ in t.rows:
    for i, w in enumerate(widths): r_.cells[i].width = w
note = ("Note. Counts are computed on the 1,374 services pages of the final panel (Occ. = occurrences; Pages and Firms = number of pages and firms "
        "with at least one occurrence). Matching is case-insensitive; * denotes any word ending. The main measure uses explicit markers only (panel A). "
        "Implicit markers (B) are analysed separately because of low inter-coder agreement; ambiguous markers (C) are used only in sensitivity analyses. "
        "Terms in panel D were removed after manual coding (non-temporal in context), after the second coder's review, or set aside during the review "
        "of occurrences in context before coding. Elements of site navigation (e.g. “quick links”, “fast filter”) are excluded.")
pn = doc.add_paragraph(); rn = pn.add_run(note); rn.font.size = Pt(8.5); rn.italic = True
doc.save("tableA1_dictionary.docx"); print("ok")
