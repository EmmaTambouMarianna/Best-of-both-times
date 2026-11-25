# Statistiques de validation du dictionnaire (precision, accord inter-codeurs) -- 2026-11-20
import pandas as pd, numpy as np
e = pd.read_excel("coding_temporal_markers.xlsx", sheet_name="Codage")
k = pd.read_excel("coding_temporal_markers_KEY.xlsx", sheet_name="Corrige")[["id_occ","categorie_dictionnaire","etiquette"]]
c2 = pd.read_excel("coding_temporal_markers_coder2_completed.xlsx", sheet_name="Codage")
Q = {"Q1 horizon ?":"Q1", "Q2 horizon":"Q2", "Q3 rattachement":"Q3"}
e = e.rename(columns=Q).merge(k, on="id_occ"); c2 = c2.rename(columns=Q)

def v4(r):
    t, et, cat = str(r.terme).lower(), r.etiquette, r.categorie_dictionnaire
    ctx = str(r.contexte).lower()
    if et in ("agile", "day-to-day", "cost reduction", "insolvency / distress"): return "removed"
    if et in ("tomorrow", "ESG", "succession planning", "energy transition / circular economy"): return "ambiguous"
    if et == "turnaround / restructuring": return "removed" if "restruct" in t else "implicit"
    if et.startswith("vitesse"):
        if t == "quick" or (t == "fast" and not any(s in ctx for s in ("[[fast]]-paced","[[fast]]-track","[[fast]] paced"))): return "removed"
        return "explicit"
    return "explicit" if "explicite" in cat else "implicit"
e["v4"] = e.apply(v4, axis=1)

# ---------- Panel A : precision (240 occurrences, dictionnaire teste = v3) ----------
lab = {"long_explicite":"Explicit, long term","court_explicite":"Explicit, short term","long_implicite":"Implicit, long term","court_implicite":"Implicit, short term"}
A = []
for cat, g in list(e.groupby("categorie_dictionnaire")) + [("all", e)]:
    yes = g[g.Q1 == "oui"]; exp = "long terme" if cat.startswith("long") else "court terme"
    lc = yes[yes.Q2.isin(["long terme","court terme"])]
    dir_ok = (lc.Q2 == exp).mean() if cat != "all" else np.nan
    A.append(dict(Category=lab.get(cat, "All markers"), n=len(g), Precision=round(100*(g.Q1=="oui").mean(),1),
                  Direction=round(100*dir_ok,1) if cat!="all" else np.nan, Ambiguous=round(100*(yes.Q2=="ambigu").mean(),1)))
A = pd.DataFrame(A); order = ["Explicit, long term","Explicit, short term","Implicit, long term","Implicit, short term","All markers"]
A = A.set_index("Category").loc[order].reset_index()

# ---------- Panel B : accord inter-codeurs (100 occurrences) ----------
m = e.merge(c2[["id_occ","Q1","Q2","Q3"]], on="id_occ", suffixes=("_a","_b"))
def kappa(a, b):
    cats = sorted(set(a) | set(b)); po = (a == b).mean()
    pe = sum((a == c).mean() * (b == c).mean() for c in cats)
    return np.nan if pe == 1 else (po - pe) / (1 - pe)
def ac1(a, b):
    cats = sorted(set(a) | set(b)); q = len(cats); po = (a == b).mean()
    if q < 2: return np.nan
    pi = [((a == c).mean() + (b == c).mean()) / 2 for c in cats]
    pe = sum(p * (1 - p) for p in pi) / (q - 1)
    return (po - pe) / (1 - pe)
B = []
subsets = [("All markers", m), ("Explicit markers (final dictionary)", m[m.v4 == "explicit"]), ("Implicit markers", m[m.categorie_dictionnaire.str.contains("implicite")])]
for name, g in subsets:
    for qn in ["Q1", "Q2", "Q3"]:
        h = g if qn != "Q3" else g[(g.Q1_a == "oui") & (g.Q1_b == "oui")]
        if qn == "Q2": h = g[(g.Q1_a == "oui") & (g.Q1_b == "oui")]
        a, b = h[qn + "_a"].astype(str), h[qn + "_b"].astype(str)
        B.append(dict(Subset=name, Question={"Q1":"Q1 Temporal orientation present","Q2":"Q2 Short / long / ambiguous","Q3":"Q3 Attachment"}[qn],
                      n=len(h), Agreement=round(100*(a == b).mean(),1), Kappa=round(kappa(a, b),2), AC1=round(ac1(a, b),2)))
B = pd.DataFrame(B)
with pd.ExcelWriter("validation_table.xlsx") as w:
    A.to_excel(w, "A_precision", index=False); B.to_excel(w, "B_intercodeurs", index=False)
print(A.to_string()); print(B.to_string()); print(e.v4.value_counts().to_dict(), m.v4.value_counts().to_dict())
