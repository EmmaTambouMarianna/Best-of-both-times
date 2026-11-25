# =====================================================================
# Nettoyage des textes collectes (pages services + sous-pages)
# Reconstitue a partir de la session du 2026-10-07 (version finale).
# Entree : 2_collection/services_metadata.csv, services_texts.csv, subpages_texts.csv
# Sortie : 3_cleaning_panel/cleaned_texts.csv
# Lancer depuis le dossier wayback :  python3 3_cleaning_panel/cleaning.py [fichier_sortie]
#
# Regles (fenetres de K = 8 mots consecutifs) :
#  1. Gabarit evident : fenetre presente sur >= 50 % des pages d'une meme firme-annee
#     (pivot + sous-pages, au moins 4 pages) -> retiree.
#  2. Gabarit tres stable : fenetre presente sur >= 80 % des pages de la firme,
#     toutes annees confondues (au moins 6 pages) -> retiree.
#  3. Repetition : fenetre deja vue sur une page precedente de la meme firme-annee
#     -> retiree des pages suivantes, gardee sur la premiere (pivot d'abord).
#  4. Passages communs a plusieurs firmes : fenetre presente dans >= 25 pages
#     et >= 6 firmes differentes (cookies, droits d'auteur) -> retiree.
#  + mentions de droits d'auteur (« (c) ... all rights reserved ») retirees.
#  Les sous-pages perdant plus de 80 % de leur texte sont signalees (replique = 1).
# =====================================================================
import pandas as pd, re, sys
from collections import defaultdict
C = "2_collection/"
SORTIE = sys.argv[1] if len(sys.argv) > 1 else "3_cleaning_panel/cleaned_texts.csv"
K = 8; SEUIL_GLOBAL_DOCS = 25; SEUIL_GLOBAL_FIRMES = 6

meta = pd.read_csv(C + "services_metadata.csv", sep=None, engine="python", encoding="utf-8-sig")
nom = dict(zip(meta.id, meta.nom))
a = pd.read_csv(C + "services_texts.csv", sep=None, engine="python", encoding="utf-8-sig")
a = a.rename(columns={"texte_services": "texte"}); a["source"] = "principale"; a["url"] = ""
b = pd.read_csv(C + "subpages_texts.csv", encoding="utf-8-sig")
b = b.drop_duplicates(subset=["id", "annee", "url_sous_page"], keep="last").rename(columns={"url_sous_page": "url"}); b["source"] = "profondeur"
d = pd.concat([a[["source", "id", "annee", "url", "texte"]], b[["source", "id", "annee", "url", "texte"]]], ignore_index=True)
d["texte"] = d.texte.fillna("").astype(str); d["nom"] = d.id.map(nom)
toks = [t.split() for t in d.texte]
low = [[w.lower() for w in t] for t in toks]

# fenetres par document
wins = [[hash(tuple(l[j:j + K])) for j in range(len(l) - K + 1)] for l in low]
wset = [set(w) for w in wins]
glob_docs = defaultdict(int); glob_firms = defaultdict(set)
for fid, ws in zip(d.id, wset):
    for h in ws: glob_docs[h] += 1; glob_firms[h].add(fid)
idx = defaultdict(list)
for i, (fid, an) in enumerate(zip(d.id, d.annee)): idx[fid].append((i, an))

res = []
for i, (fid, an) in enumerate(zip(d.id, d.annee)):
    nb = [j for j, a2 in idx[fid] if a2 == an]          # meme firme, meme annee (pivot + sous-pages, dans l'ordre)
    allf = [j for j, _ in idx[fid]]
    avant = [j for j in nb if j < i]                     # pages deja vues cette annee (pivot d'abord)
    n = len(low[i]); mark = [False] * n
    for j, h in enumerate(wins[i]):
        f = False
        if len(nb) >= 4 and sum(1 for k in nb if h in wset[k]) >= 0.5 * len(nb): f = True            # regle 1
        if not f and len(allf) >= 6 and sum(1 for k in allf if h in wset[k]) >= 0.8 * len(allf): f = True   # regle 2
        if not f and any(h in wset[k] for k in avant): f = True                                        # regle 3
        g = (glob_docs[h] >= SEUIL_GLOBAL_DOCS and len(glob_firms[h]) >= SEUIL_GLOBAL_FIRMES)          # regle 4
        if f or g:
            for x in range(j, j + K): mark[x] = True
    keep = [w for w, m in zip(toks[i], mark) if not m]
    t = " ".join(keep)
    t = re.sub(r"(?i)(©|copyright)[^.]{0,120}(all rights reserved\.?)?", "", t)
    res.append(t)

d["texte_nettoye"] = res
d["n_mots_avant"] = [len(t) for t in toks]; d["n_mots_apres"] = [len(t.split()) for t in res]
d["replique"] = 0
d["prop_retiree"] = (1 - d.n_mots_apres / d.n_mots_avant.clip(lower=1)).round(3)
d.loc[(d.source == "profondeur") & (d.prop_retiree > 0.8), "replique"] = 1
d[["source", "id", "nom", "annee", "url", "n_mots_avant", "n_mots_apres", "prop_retiree", "replique", "texte_nettoye"]].to_csv(SORTIE, index=False, encoding="utf-8-sig")
print(len(d), d.groupby("source").size().to_dict())
print(d.groupby("source")[["n_mots_avant", "n_mots_apres", "prop_retiree"]].median())
