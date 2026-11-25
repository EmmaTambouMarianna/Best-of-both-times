# Analyse principale : evolution de l'horizon temporel (pages services, 93 firmes, lexique v4 du 2026-10-26)
# Mesure principale = marqueurs EXPLICITES ; marqueurs implicites = analyse exploratoire (kappa insuffisant)
# Usage : python3 main_analysis.py <dossier wayback> <fichier de sortie .xlsx>
import sys, numpy as np, pandas as pd, pyfixest as pf, statsmodels.api as sm
from pathlib import Path
B = Path(sys.argv[1]); OUT = sys.argv[2]
ix = pd.read_csv(B / "4_temporal_markers/horizon_index_v4.csv")
ct = pd.read_csv(B / "5_controls/controls_firm_year.csv")
d = ix.merge(ct.drop(columns=["nom", "n_mots"]), on=["id", "annee"], how="left")

def idx(l, c): return np.where((l + c) > 0, (l - c) / (l + c).replace(0, np.nan), np.nan)
d["n_expl"] = d.long_explicite + d.court_explicite
d["n_impl"] = d.long_implicite + d.court_implicite
d["expl_ambig_long"] = idx(d.long_explicite + d.ambigu, d.court_explicite)
d["expl_ambig_court"] = idx(d.long_explicite, d.court_explicite + d.ambigu)
d["part_ambigu"] = np.where(d.n_expl + d.ambigu > 0, d.ambigu / (d.n_expl + d.ambigu).replace(0, np.nan), np.nan)
d["a_expl"] = (d.n_expl > 0).astype(int)
d["log_mots"] = np.log(d.n_mots.clip(lower=1))
d["page_industrie"] = (d.type_page == "industrie").astype(int)
d["t"] = d.annee - 2010                       # pente exprimee par an, centree sur 2010
d["periode"] = pd.cut(d.annee, [1995, 2004, 2009, 2014, 2019, 2025],
                      labels=["1996-2004", "2005-2009", "2010-2014", "2015-2019", "2020-2025"]).astype(str)
nyrs = d.groupby("id").annee.transform("size")
SERV = [c for c in ct.columns if c.startswith("serv_") and c.endswith("_1000")]

rows = []
def keep(name, groupe, fit, var="t", note=""):
    co, se, p = fit.coef()[var], fit.se()[var], fit.pvalue()[var]
    n = fit._N; firms = int(fit._data["id"].nunique()) if "id" in fit._data else np.nan
    rows.append(dict(groupe=groupe, modele=name, coef_par_an=co, erreur_type=se, p=p,
                     ic95_bas=co - 1.96 * se, ic95_haut=co + 1.96 * se, n_pages=n, n_firmes=firms, note=note))
CL = {"CRV1": "id"}
E = d[d.n_expl > 0]

# --- 1. Modele principal ---------------------------------------------------------------
m1 = pf.feols("indice_explicite ~ t | id", data=E, weights="n_expl", vcov=CL)
keep("M1 Principal : indice explicite, EF firme, pondere par nb de marqueurs", "1. Principal", m1)

# --- 2. Robustesse ----------------------------------------------------------------------
keep("R1 Non pondere", "2. Robustesse", pf.feols("indice_explicite ~ t | id", data=E, vcov=CL))
keep("R2 + controles (log mots, page industrie)", "2. Robustesse",
     pf.feols("indice_explicite ~ t + log_mots + page_industrie | id", data=E, weights="n_expl", vcov=CL))
keep("R3 + composition des services (dictionnaire non encore valide)", "2. Robustesse",
     pf.feols("indice_explicite ~ t + log_mots + page_industrie + " + " + ".join(SERV) + " | id", data=E, weights="n_expl", vcov=CL),
     note="controles provisoires")
keep("R4 Poisson : nb marqueurs LONG explicites (exposition = mots)", "2. Robustesse",
     pf.fepois("long_explicite ~ t | id", data=d, offset="log_mots", vcov=CL), note="coef = variation log du taux par an")
keep("R5 Poisson : nb marqueurs COURT explicites (exposition = mots)", "2. Robustesse",
     pf.fepois("court_explicite ~ t | id", data=d, offset="log_mots", vcov=CL), note="coef = variation log du taux par an")
keep("R6 Borne haute : ambigus comptes long terme", "2. Robustesse",
     pf.feols("expl_ambig_long ~ t | id", data=d[d.n_expl + d.ambigu > 0], weights=None, vcov=CL))
keep("R7 Borne basse : ambigus comptes court terme", "2. Robustesse",
     pf.feols("expl_ambig_court ~ t | id", data=d[d.n_expl + d.ambigu > 0], vcov=CL))
keep("R8 Controle : part des termes ambigus", "2. Robustesse",
     pf.feols("indice_explicite ~ t + part_ambigu | id", data=E, weights="n_expl", vcov=CL))
keep("R9 Firmes avec >= 14 annees", "2. Robustesse",
     pf.feols("indice_explicite ~ t | id", data=E[nyrs[E.index] >= 14], weights="n_expl", vcov=CL))
keep("R10 Annees 2000 et suivantes", "2. Robustesse",
     pf.feols("indice_explicite ~ t | id", data=E[E.annee >= 2000], weights="n_expl", vcov=CL))
keep("R11 Pages services generales seulement", "2. Robustesse",
     pf.feols("indice_explicite ~ t | id", data=E[E.page_industrie == 0], weights="n_expl", vcov=CL))
keep("R12 Presence d'au moins un marqueur explicite (MPL)", "2. Robustesse",
     pf.feols("a_expl ~ t + log_mots | id", data=d, vcov=CL), note="tendance a parler d'horizon, pas sa direction")
# logit fractionnaire groupe (sans EF firme, controles de taille), part de long terme
F = E.assign(part_long=E.long_explicite / E.n_expl)
X = sm.add_constant(F[["t", "log_mots", "page_industrie"]])
fl = sm.GLM(F.part_long, X, family=sm.families.Binomial(), freq_weights=F.n_expl).fit(cov_type="cluster", cov_kwds={"groups": F.id})
rows.append(dict(groupe="2. Robustesse", modele="R13 Logit fractionnaire (part long terme), groupe", coef_par_an=fl.params.t,
                 erreur_type=fl.bse.t, p=fl.pvalues.t, ic95_bas=fl.conf_int().loc["t", 0], ic95_haut=fl.conf_int().loc["t", 1],
                 n_pages=len(F), n_firmes=F.id.nunique(), note="coef en log-odds ; sans EF firme"))

# --- 3. Exploratoire : implicite ----------------------------------------------------------
I = d[d.n_impl > 0]
keep("X1 Indice implicite, EF firme, pondere", "3. Exploratoire (implicite)", pf.feols("indice_implicite ~ t | id", data=I, weights="n_impl", vcov=CL))
keep("X2 Poisson : nb marqueurs LONG implicites", "3. Exploratoire (implicite)", pf.fepois("long_implicite ~ t | id", data=d, offset="log_mots", vcov=CL))
keep("X3 Poisson : nb marqueurs COURT implicites", "3. Exploratoire (implicite)", pf.fepois("court_implicite ~ t | id", data=d, offset="log_mots", vcov=CL))
keep("X4 Indice global (explicite + implicite)", "3. Exploratoire (implicite)",
     pf.feols("indice_global ~ t | id", data=d[d.n_expl + d.n_impl > 0], weights=None, vcov=CL))
keep("X5 Poisson : termes ambigus", "3. Exploratoire (implicite)", pf.fepois("ambigu ~ t | id", data=d, offset="log_mots", vcov=CL))

res = pd.DataFrame(rows)
for c in ["coef_par_an", "erreur_type", "ic95_bas", "ic95_haut"]: res[c] = res[c].round(4)
res["p"] = res.p.round(4)
res["sig"] = np.select([res.p < .001, res.p < .01, res.p < .05, res.p < .1], ["***", "**", "*", "."], "")

# forme de la tendance : periodes (reference 1996-2004)
mp = pf.feols("indice_explicite ~ C(periode, Treatment('1996-2004')) | id", data=E, weights="n_expl", vcov=CL)
per = pd.DataFrame({"coef": mp.coef(), "erreur_type": mp.se(), "p": mp.pvalue()}).round(4)
per.index = [i.split("T.")[-1].rstrip("]") for i in per.index]
desc = d.groupby("periode").agg(pages=("id", "size"), firmes=("id", "nunique"), pct_pages_avec_explicite=("a_expl", "mean"),
                                 long_expl_1000=("long_explicite_1000", "mean"), court_expl_1000=("court_explicite_1000", "mean"),
                                 indice_explicite_moyen=("indice_explicite", "mean")).round(3)
with pd.ExcelWriter(OUT) as w:
    res.to_excel(w, "Resultats", index=False); per.to_excel(w, "Periodes (ref 1996-2004)"); desc.to_excel(w, "Descriptifs")
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
print(res[["modele", "coef_par_an", "erreur_type", "p", "sig", "n_pages", "n_firmes"]].to_string(index=False))
print(per.to_string()); print(desc.to_string())
