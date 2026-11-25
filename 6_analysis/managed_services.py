# Reperage des services geres (variable moderatrice H1b) -- v2 (2026-11-12)
# Inclusion : expressions designant une offre de services geres / impartition.
# Exclusion (fenetre de 120 caracteres) : conseil SUR l'impartition, clients impartiteurs, contenus editoriaux.
import pandas as pd, re, sys
INC = r"managed services?|\boutsourc\w*|as[- ]a[- ]service|\bBPO\b|business process (outsourcing|services)|application (management|maintenance) services|infogérance|externalisation|services gérés"
EXC = r"sourcing advis\w*|outsourcing advis\w*|advis\w* on (outsourcing|sourcing)|whether (or not )?to outsource|should (you )?outsource|reasons? (why )?(you should )?outsource|outsourcing strategy|vendor (selection|management)|outsourcers? as (our )?clients|(our )?clients? (include|are) \w* ?outsourc|read (more|the article)|white ?paper|webinar|blog|podcast|survey|report\b"
inc, exc = re.compile(INC, re.I), re.compile(EXC, re.I)
def occurrences(txt):
    out = []
    for m in inc.finditer(txt):
        w = txt[max(0, m.start()-120): m.end()+120]
        out.append((m.group(0), bool(exc.search(w)), txt[max(0, m.start()-200): m.end()+200]))
    return out
if __name__ == "__main__":
    t = pd.read_csv("3_cleaning_panel/cleaned_texts.csv")
    d = pd.read_csv("4_temporal_markers/horizon_index_v4.csv")[["id","annee"]]
    t = t[t.source=="principale"].merge(d, on=["id","annee"])
    rows, page = [], []
    for r in t.itertuples():
        occ = occurrences(str(r.texte_nettoye))
        kept = [o for o in occ if not o[1]]
        page.append((r.id, r.annee, len(occ), len(kept), int(len(kept) > 0)))
        rows += [(r.id, r.nom, r.annee, o[0], o[1], o[2]) for o in occ]
    pd.DataFrame(page, columns=["id","annee","sg_brut","sg_retenu","services_geres"]).to_csv("6_analysis/managed_services_page.csv", index=False)
    pd.DataFrame(rows, columns=["id","nom","annee","terme","exclu","contexte"]).to_csv("6_analysis/managed_services_occurrences.csv", index=False)
