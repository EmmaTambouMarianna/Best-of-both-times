# =====================================================================
# Construction du panel firme x annee et selection des firmes eligibles
# Reconstitue a partir de la session du 2026-10-07 (version finale : anglais + francais).
# Entree : 3_cleaning_panel/cleaned_texts.csv, pivot_verdicts.csv ; 2_collection/services_metadata.csv
# Sortie : 3_cleaning_panel/panel_firm_year.csv, eligible_firms_final.csv
# Lancer depuis le dossier wayback :  python3 3_cleaning_panel/panel.py [dossier_sortie]
#
# Une page-annee est valide si : (1) sa page pivot n'a pas ete exclue a la verification manuelle,
# (2) elle compte au moins 50 mots apres nettoyage, (3) sa langue detectee est l'anglais ou le
# francais (langdetect, probabilite >= 0,85, sur au moins 20 mots). Une firme est eligible si elle
# compte au moins 10 annees valides.
# =====================================================================
import pandas as pd, re, sys
from langdetect import detect_langs, DetectorFactory
DetectorFactory.seed = 0
N = "3_cleaning_panel/"
OUT = sys.argv[1] if len(sys.argv) > 1 else N

meta = pd.read_csv("2_collection/services_metadata.csv", sep=None, engine="python", encoding="utf-8-sig")
t = pd.read_csv(N + "cleaned_texts.csv"); p = t[t.source == "principale"].copy()
v = pd.read_csv(N + "pivot_verdicts.csv", sep=None, engine="python", encoding="utf-8-sig")
ex = set(zip(v[v.pivot_exclu == 1].id, v[v.pivot_exclu == 1].annee))

m = meta[meta.statut == "ok services"][["id", "nom", "annee", "url_services_capture", "langue"]].merge(
    p[["id", "annee", "n_mots_avant", "n_mots_apres", "texte_nettoye"]], on=["id", "annee"], how="left")
m["pivot_exclu"] = [int((i, a) in ex) for i, a in zip(m.id, m.annee)]
url = m.url_services_capture.fillna("").str.lower()
m["type_page"] = ["industrie" if re.search(r"industr|sector-focus|financial-services|banking-financial", u) else "generale" for u in url]

def lang(x):
    x = str(x)
    if len(x.split()) < 20: return "na"
    try:
        r = detect_langs(x[:3000])[0]; return r.lang if r.prob >= 0.85 else "incertain"
    except Exception: return "na"
m["langue_nett"] = m.texte_nettoye.apply(lang)
m["f_exclu"] = m.pivot_exclu == 1
m["f_mots"] = m.n_mots_apres < 50
m["f_lang"] = ~m.langue_nett.isin(["en", "fr"])
m["valide"] = ~(m.f_exclu | m.f_mots | m.f_lang)

ids = meta.id.unique()
c = m[m.valide].groupby("id").size().reindex(ids, fill_value=0)
print("pages ok services", len(m), "| pivots exclus", m.f_exclu.sum(), "| <50 mots", (~m.f_exclu & m.f_mots).sum(),
      "| langue", (~m.f_exclu & ~m.f_mots & m.f_lang).sum(), "| valides", m.valide.sum())
print("firmes eligibles (>= 10 annees valides):", (c >= 10).sum(), "| pages:", m[m.valide & m.id.isin(c[c >= 10].index)].shape[0])
m.drop(columns=["texte_nettoye"]).to_csv(OUT + "panel_firm_year.csv", index=False, encoding="utf-8-sig")
pd.DataFrame({"id": c.index, "nom": [meta[meta.id == i].nom.iloc[0] for i in c.index],
              "annees_valides": c.values, "eligible": (c.values >= 10).astype(int)}).to_csv(OUT + "eligible_firms_final.csv", index=False, encoding="utf-8-sig")
