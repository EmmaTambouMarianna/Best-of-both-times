# Marqueurs temporels : explicite vs implicite (long / court terme)
# Corpus : pages services du panel (source "principale", firmes eligibles, annees valides)
# Lancer depuis le dossier wayback :  python3 4_temporal_markers/markers_explicit_implicit.py
import pandas as pd, numpy as np, re
from pathlib import Path

B = Path(__file__).resolve().parents[1]
N = B / "3_cleaning_panel"; O = B / "4_temporal_markers"

panel = pd.read_csv(N / "panel_firm_year.csv")
elig = pd.read_csv(N / "eligible_firms_final.csv")
E_ids = set(elig[elig.eligible == 1].id)
t = pd.read_csv(N / "cleaned_texts.csv")
d = t[t.source == "principale"].merge(panel[panel.valide][["id", "annee", "type_page", "langue_nett"]], on=["id", "annee"])
d = d[d.id.isin(E_ids)].copy()
d["lg"] = ["fr" if l == "fr" else "en" for l in d.langue_nett]

def phrases(txt):
    txt = re.sub(r"\s*\|\s*", " . ", str(txt))
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9«“\"(])", txt) if s.strip()]

# ---------------------------------------------------------------------------
# LEXIQUE v3 : (categorie, etiquette, regex en, regex fr)
#   long_explicite  : expression qui nomme un horizon futur eloigne
#   court_explicite : expression qui nomme un horizon immediat
#   long_implicite  : objet de service dont l'horizon est long par nature (durabilite, climat...)
#   court_implicite : objet de service dont l'horizon est immediat par nature (crise, redressement...)
#   a_trancher      : compte a part, NON inclus dans les indices (ambigu ou non temporel)
# ---------------------------------------------------------------------------
LEX = [
 ("long_explicite","long term",        r"long[- ]term|longer[- ]term",                      r"long terme|plus long terme"),
 ("long_explicite","future",           r"\bfutures?\b(?![- ]proof)",                        r"\bavenir\b|\bfutur(e|s|es)?\b"),
 ("long_explicite","tomorrow",         r"\btomorrow\b",                                     r"\bdemain\b"),
 ("long_explicite","years ahead",      r"years ahead|coming years|years to come|next \d+ years|(next|coming) decades?", r"prochaines ann[ée]es|ann[ée]es [àa] venir|prochaines d[ée]cennies"),
 ("long_explicite","date 2030+",       r"\b20[3-9]\d\b",                                    r"\b20[3-9]\d\b"),
 ("court_explicite","short term",      r"short[- ]term|near[- ]term",                       r"court terme"),
 ("court_explicite","immediate",       r"\bimmediate(ly)?\b",                               r"\bimm[ée]diat\w*"),
 ("court_explicite","urgent",          r"\burgen(t|cy)\w*",                                 r"\burgen\w*"),
 ("court_explicite","within days",     r"\bwithin (hours|days|weeks|months)\b",             r"\ben quelques (heures|jours|semaines)\b"),
 ("court_explicite","day-to-day",      r"\bday[- ]to[- ]day\b",                             r"\bau quotidien\b"),
 ("court_explicite","quick wins",      r"quick[- ]wins?",                                   r"gains rapides"),
 ("long_implicite","sustainability",   r"sustainab\w*",                                     r"d[ée]veloppement durable|durabilit[ée]"),
 ("long_implicite","net zero / decarbonisation", r"net[- ]zero|decarboni[sz]\w*|carbon[- ]neutral\w*|low[- ]carbon", r"carboneutr\w*|d[ée]carbon\w*|bas carbone"),
 ("long_implicite","climate",          r"\bclimate\b",                                      r"\bclimat(ique)?s?\b"),
 ("long_implicite","ESG",              r"\bESG\b",                                          r"\bESG\b"),
 ("long_implicite","energy transition / circular economy", r"energy transition|circular economy", r"transition [ée]nerg\w*|[ée]conomie circulaire"),
 ("long_implicite","succession planning", r"succession planning",                           r"planification de la rel[èe]ve"),
 ("court_implicite","crisis management", r"crisis (management|response|communications?)",   r"gestion de crise"),
 ("court_implicite","turnaround / restructuring", r"\bturn[- ]?arounds?\b|\brestructur\w*", r"\bredressement\b|\brestructur\w*"),
 ("court_implicite","cost reduction",  r"cost (reduction|cutting|savings?|containment)",    r"r[ée]duction des co[uû]ts"),
 ("court_implicite","cash / liquidity",r"cash management|\bliquidity\b|working capital",    r"tr[ée]sorerie|liquidit[ée]s|fonds de roulement"),
 ("court_implicite","interim management", r"interim (management|managers?|executives?|leadership|CFO|CEO)", r"management de transition|gestion int[ée]rimaire"),
 ("court_implicite","insolvency / distress", r"insolvenc\w*|bankruptc\w*|financial distress", r"insolvabilit[ée]|faillite"),
 ("a_trancher","decades (souvent retrospectif)", r"(?<!next )(?<!coming )\bdecades?\b", r"d[ée]cennies?"),
 ("a_trancher","today / now (rhetorique)", r"\btoday\b|\bnow\b",                            r"aujourd.hui|maintenant"),
 ("a_trancher","vitesse (quick, rapid, fast)", r"\bquick(ly)?\b(?![- ]wins?)|\brapid(ly)?\b|\bfast(er)?\b", r"\brapide\w*"),
 ("a_trancher","agile",                r"\bagil\w*",                                        r"\bagil\w*"),
 ("a_trancher","future-proof",         r"future[- ]proof\w*",                               r"p[ée]renn\w*"),
 ("a_trancher","next generation",      r"next generation|\bnext[- ]gen\b",                  r"nouvelle g[ée]n[ée]ration"),
 ("a_trancher","beyond",               r"\bbeyond\b",                                       r"\bau[- ]del[àa]\b"),
 ("a_trancher","quarter (souvent finance)", r"\bquarter(ly)?\b",                            r"\btrimestr\w*"),
 ("a_trancher","transformation",       r"\btransform\w*",                                   r"\btransform\w*"),
 ("a_trancher","litigation (retrospectif)", r"\blitigation\b",                              r"\blitiges?\b|contentieux"),
]
CATS = ["long_explicite","court_explicite","long_implicite","court_implicite","a_trancher"]
RX = [(c, e, {"en": re.compile(en, re.I), "fr": re.compile(fr, re.I)}) for c, e, en, fr in LEX]

def idx(l, c):
    return (l - c) / (l + c) if (l + c) > 0 else np.nan

rows, terms = [], []
for _, r in d.iterrows():
    txt = " ".join(phrases(r.texte_nettoye)); nm = len(txt.split())
    cnt = dict.fromkeys(CATS, 0)
    for c, e, rx in RX:
        k = len(rx[r.lg].findall(txt))
        cnt[c] += k
        if k: terms.append((c, e, r.id, r.annee, k))
    rows.append(dict(id=r.id, nom=r.nom, annee=r.annee, type_page=r.type_page, langue=r.lg, n_mots=nm, **cnt))

ix = pd.DataFrame(rows)
ix["indice_explicite"] = [idx(a, b) for a, b in zip(ix.long_explicite, ix.court_explicite)]
ix["indice_implicite"] = [idx(a, b) for a, b in zip(ix.long_implicite, ix.court_implicite)]
ix["indice_global"] = [idx(a + b, c + e) for a, b, c, e in zip(ix.long_explicite, ix.long_implicite, ix.court_explicite, ix.court_implicite)]
for c in CATS: ix[c + "_1000"] = 1000 * ix[c] / ix.n_mots
ix.to_csv(O / "horizon_index_explicit_implicit.csv", index=False, encoding="utf-8-sig")

# lexique documente
tm = pd.DataFrame(terms, columns=["categorie","etiquette","id","annee","n"])
lexdoc = pd.DataFrame(LEX, columns=["categorie","etiquette","regex_en","regex_fr"])
f = tm.groupby(["categorie","etiquette"]).agg(occurrences=("n","sum"), pages=("n","size"), firmes=("id","nunique")).reset_index()
lexdoc = lexdoc.merge(f, on=["categorie","etiquette"], how="left").fillna({"occurrences":0,"pages":0,"firmes":0})
lexdoc.to_csv(O / "dictionary_temporal_v3.csv", index=False, encoding="utf-8-sig")

# tendances par periode
ix["periode"] = pd.cut(ix.annee, [1995,2004,2009,2014,2019,2025], labels=["1996-2004","2005-2009","2010-2014","2015-2019","2020-2025"])
g = ix.groupby("periode", observed=True)
tend = pd.DataFrame({
  "pages": g.size(), "firmes": g.id.nunique(),
  **{c + "_1000": g[c].sum() / g.n_mots.sum() * 1000 for c in CATS},
  "indice_explicite": g.indice_explicite.mean(), "indice_implicite": g.indice_implicite.mean(), "indice_global": g.indice_global.mean(),
  "pct_pages_explicite": g.apply(lambda x: ((x.long_explicite + x.court_explicite) > 0).mean() * 100),
  "pct_pages_implicite": g.apply(lambda x: ((x.long_implicite + x.court_implicite) > 0).mean() * 100),
}).round(2)
tend.to_csv(O / "trends_explicit_implicit.csv", encoding="utf-8-sig")

# pente annuelle intra-firme (effets fixes firme, par demeaning)
def pente(col):
    s = ix[["id","annee",col]].dropna()
    s = s[s.groupby("id")[col].transform("size") >= 3]
    y = s[col] - s.groupby("id")[col].transform("mean"); x = s.annee - s.groupby("id").annee.transform("mean")
    b = (x * y).sum() / (x * x).sum()
    res = y - b * x; n, k = len(s), s.id.nunique() + 1
    # erreur-type groupee par firme
    sc = (x * res).groupby(s.id).sum()
    se = np.sqrt((sc ** 2).sum()) / (x * x).sum() * np.sqrt(k / (k - 1))
    return dict(indice=col, pente_par_an=round(b, 4), erreur_type=round(se, 4), t=round(b / se, 2), pages=n, firmes=s.id.nunique())
pentes = pd.DataFrame([pente(c) for c in ["indice_explicite","indice_implicite","indice_global"]] +
                      [pente(c + "_1000") for c in CATS[:4]])
pentes.to_csv(O / "within_firm_slopes.csv", index=False, encoding="utf-8-sig")

# co-occurrence : implicite vs explicite dans une fenetre phrase +-1
def win_has(cat, lg, ctx): return any(rx[lg].search(ctx) for c, e, rx in RX if c == cat)
co = []
for _, r in d.iterrows():
    ph = phrases(r.texte_nettoye)
    for i in range(len(ph)):
        ctx = " ".join(ph[max(0, i - 1): i + 2]); s = ph[i]
        co.append(dict(LI=win_has("long_implicite", r.lg, s), CI=win_has("court_implicite", r.lg, s),
                       LE=win_has("long_explicite", r.lg, ctx), CE=win_has("court_explicite", r.lg, ctx)))
co = pd.DataFrame(co)
coo = pd.DataFrame({
  "phrases": [len(co), co.LI.sum(), co.CI.sum()],
  "pct_avec_long_explicite": [co.LE.mean()*100, co[co.LI].LE.mean()*100, co[co.CI].LE.mean()*100],
  "pct_avec_court_explicite": [co.CE.mean()*100, co[co.LI].CE.mean()*100, co[co.CI].CE.mean()*100],
}, index=["toutes les phrases (base)","phrases avec implicite LONG","phrases avec implicite COURT"]).round(2)
coo.to_csv(O / "cooccurrence_implicit_explicit.csv", encoding="utf-8-sig")

print("pages", len(ix), "firmes", ix.id.nunique())
print(lexdoc[["categorie","etiquette","occurrences","pages","firmes"]].to_string(index=False))
print(tend.T.to_string()); print(pentes.to_string(index=False)); print(coo.to_string())
