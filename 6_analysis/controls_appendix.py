# Appendix table: dictionary of service categories (control variables), English, Times New Roman, landscape.
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
# category, English terms, French terms, pages, firms, precision, recall
R = [
 ("Strategy and growth", "strategy, strategic, growth strategy, market entry, corporate development, portfolio strategy, business planning", "stratégie, stratégique, croissance externe, plan d'affaires", 993, 92, 69, 82),
 ("Operations and supply chain", "operation(s), operational excellence, supply chain, procurement, sourcing, lean, logistics, manufacturing excellence, process improvement", "opération(s), excellence opérationnelle, chaîne d'approvisionnement, achat(s), logistique, lean", 787, 85, 41, 88),
 ("Technology, digital and data", "digital, technolog*, cloud, data, analytics, artificial intelligence, AI, IT, software, automation, ERP, SAP", "numérique, digital*, technolog*, données, intelligence artificielle, IA, systèmes d'information, logiciel", 1168, 93, 55, 90),
 ("Risk, compliance and cybersecurity", "risk(s), compliance, regulatory, cyber*, security, internal audit, fraud, resilience", "risque(s), conformité, réglementa*, cyber*, sécurité, audit interne, fraude, résilience", 838, 87, 48, 55),
 ("Finance, transactions and M&A", "M&A, merger(s), acquisition(s), due diligence, transaction*, valuation(s), corporate finance, private equity, capital markets, deal", "fusion(s), acquisition(s), due diligence, transaction*, évaluation d'entreprise, finance d'entreprise, capital-investissement", 751, 86, 53, 52),
 ("Performance, costs and restructuring", "performance improvement, cost(s), restructur*, turnaround, profitability, efficiency, productivity, insolvenc*", "performance, coût(s), restructur*, redressement, rentabilité, efficacité, productivité", 723, 86, 75, 68),
 ("Human capital, organisation and change", "human capital, HR, human resources, talent, workforce, people strategy/advisory/analytics, leadership development, organisational design/effectiveness/change, change management, culture, compensation, executive search", "ressources humaines, RH, talent(s), capital humain, conduite/gestion du changement, organisation, rémunération, leadership", 635, 85, 41, 35),
 ("Marketing, customers and sales", "marketing, customer*, brand*, pricing, sales, commercial excellence, consumer insight(s), customer experience", "marketing, client(s), marque(s), tarification, prix, vente(s), expérience client", 760, 85, 34, 67),
 ("Sustainability, climate and ESG", "sustainab*, ESG, climate, net zero, decarboni*, energy transition, circular economy, environmental", "durabilité, développement durable, ESG, climat*, décarbon*, transition énergétique, environnement*", 542, 83, 55, 80),
 ("Innovation, R&D and design", "innovation, R&D, research and development, product development, design thinking, ventur*, new product", "innovation, R&D, recherche et développement, développement de produit(s), design", 547, 81, 26, 50),
 ("Engineering, infrastructure and projects", "engineering, infrastructure, construction, project management, capital projects, asset management, architecture", "ingénierie, infrastructure(s), construction, gestion de projet(s), architecture", 650, 86, 40, 83),
 ("Public policy and development", "public policy, policy advisory, government advisory, economic development, international development, public affairs, advocacy", "politique(s) publique(s), développement économique, développement international, affaires publiques", 114, 22, 22, 33),
 ("Litigation, economic expertise and forensics", "litigation, dispute(s), forensic, expert witness, antitrust, competition economics, economic consulting, arbitration", "litige(s), contentieux, expertise judiciaire, forensique, concurrence, arbitrage", 185, 31, 82, 90),
]
doc = Document()
st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(9)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
sec = doc.sections[0]; sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = sec.page_height, sec.page_width
for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, m, Cm(1.8))
p = doc.add_paragraph(); r = p.add_run("Table A2. Dictionary of service categories (control variables)"); r.bold = True; r.font.size = Pt(11)
hdr = ["Service category", "English terms", "French terms", "Pages", "Firms", "Precision (%)", "Recall (%)"]
W = [Cm(4.2), Cm(8.2), Cm(6.2), Cm(1.4), Cm(1.3), Cm(2.1), Cm(1.6)]
t = doc.add_table(rows=1, cols=7); t.style = "Table Grid"; t.autofit = False
def shade(c, col):
    tcPr = c._tc.get_or_add_tcPr(); s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), col); tcPr.append(s)
for i, h in enumerate(hdr):
    c = t.rows[0].cells[i]; c.text = ""; rr = c.paragraphs[0].add_run(h); rr.bold = True; shade(c, "D9D9D9")
for row in R:
    cells = t.add_row().cells
    for i, v in enumerate(row):
        cells[i].text = f"{v:,}" if isinstance(v, int) else v
        if i >= 3: cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if row[0].startswith("Sustainability"):
        for c in cells: 
            for rr in c.paragraphs[0].runs: rr.bold = True
for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), W): gc.set(qn("w:w"), str(int(w.twips)))
for r_ in t.rows:
    for i, w in enumerate(W): r_.cells[i].width = w
note = ("Note. Each category is coded 1 if at least one term appears on the page. Pages and Firms: number of firm-years (out of 1,374) and firms (out of 93) "
        "in which the category is detected. Precision and recall are computed against the manual coding of 160 randomly drawn passages, in which the coder could "
        "assign at most three categories per passage; precision is therefore a lower bound (overall: 51%; 62% when categories in passages flagged by the coder as "
        "involving additional services are counted as valid; overall recall: 70%). Matching is case-insensitive; * denotes any word ending. The sustainability "
        "category (in bold) is the main control for H2; the full set of 13 categories is used in a robustness check.")
pn = doc.add_paragraph(); rn = pn.add_run(note); rn.italic = True; rn.font.size = Pt(8.5)
doc.save("tableA2_service_categories.docx"); print("ok")
