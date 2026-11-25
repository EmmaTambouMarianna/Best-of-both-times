# Tests H1 (co-occurrence court/long terme) et H2 (hausse du long terme) -- 2026-11-13
# Donnees : 4_temporal_markers/horizon_index_v4.csv (marqueurs explicites, lexique v4) + 5_controls/controls_firm_year.csv
import pandas as pd, numpy as np, warnings; warnings.filterwarnings("ignore")
import statsmodels.api as sm
from statsmodels.discrete.conditional_models import ConditionalLogit
import pyfixest as pf
d = pd.read_csv("4_temporal_markers/horizon_index_v4.csv")
c = pd.read_csv("5_controls/controls_firm_year.csv").drop(columns=["nom","n_mots"])
d = d.merge(c, on=["id","annee"])
d["L"] = (d.long_explicite > 0).astype(int); d["C"] = (d.court_explicite > 0).astype(int)
d["log_mots"] = np.log(d.n_mots); d["annee_c"] = d.annee - 2010
SERV = [x for x in d.columns if x.startswith("serv_") and not x.endswith("_1000")]
IND  = [x for x in d.columns if x.startswith("ind_") and not x.endswith("_1000")]
for v in SERV + IND: d[v+"_b"] = (d[v] > 0).astype(int)
CTRL = [v+"_b" for v in SERV + IND]
out = []
def add(model, hyp, terme, est, se, p, n, note=""):
    out.append(dict(hypothese=hyp, modele=model, terme=terme, coef=round(est,4), rc_ou_irr=round(np.exp(est),3), se=round(se,4), p=round(p,4), n=n, note=note))

# ---------- Descriptif H1 : co-occurrence observee vs attendue ----------
d["periode"] = pd.cut(d.annee, [1995,2005,2010,2015,2020,2025], labels=["1996-2005","2006-2010","2011-2015","2016-2020","2021-2025"])
desc = d.groupby("periode", observed=True).apply(lambda g: pd.Series(dict(pages=len(g), part_L=g.L.mean(), part_C=g.C.mean(),
        cooc_observee=(g.L*g.C).mean(), cooc_attendue=g.L.mean()*g.C.mean())))
tot = pd.Series(dict(pages=len(d), part_L=d.L.mean(), part_C=d.C.mean(), cooc_observee=(d.L*d.C).mean(), cooc_attendue=d.L.mean()*d.C.mean()), name="Total")
desc = pd.concat([desc, tot.to_frame().T]); desc["ratio_obs_att"] = desc.cooc_observee/desc.cooc_attendue
desc = desc.round(3)

# ---------- H1 : logit conditionnel (effets fixes firme) ----------
def clogit(y, X, hyp, name, note=""):
    m = ConditionalLogit(d[y], d[X], groups=d["id"]).fit(disp=0)
    v = d.groupby("id")[y].transform("nunique").gt(1); nf = d.loc[v,"id"].nunique()
    add(name, hyp, X[0], m.params.iloc[0], m.bse.iloc[0], m.pvalues.iloc[0], int(v.sum()), note or f"{nf} firmes informatives")
    return m
clogit("C", ["L","log_mots","annee_c"], "H1", "Logit conditionnel (EF firme)")
clogit("C", ["L","log_mots","annee_c"]+CTRL, "H1", "Logit conditionnel + controles services/industries")
clogit("L", ["C","log_mots","annee_c"], "H1 (robustesse)", "Logit conditionnel inverse (L ~ C)")
m = pf.feols("C ~ L + log_mots + annee_c | id", data=d, vcov={"CRV1":"id"}); t=m.tidy().loc["L"]
add("Probabilite lineaire (EF firme, ET groupees)", "H1 (robustesse)", "L", t.Estimate, t["Std. Error"], t["Pr(>|t|)"], len(d), "coef = difference de probabilite, pas un log-RC")
lg = sm.Logit(d.C, sm.add_constant(d[["L","log_mots","annee_c"]])).fit(disp=0, cov_type="cluster", cov_kwds={"groups": d.id})
add("Logit sans EF (ET groupees par firme)", "H1 (robustesse)", "L", lg.params["L"], lg.bse["L"], lg.pvalues["L"], len(d))
# Exploratoire : evolution de la co-occurrence
d["L_x_annee"] = d.L*d.annee_c
mi = ConditionalLogit(d["C"], d[["L","L_x_annee","log_mots","annee_c"]], groups=d["id"]).fit(disp=0)
add("Logit conditionnel + interaction", "Exploratoire", "L x annee", mi.params["L_x_annee"], mi.bse["L_x_annee"], mi.pvalues["L_x_annee"], int(d.groupby("id")["C"].transform("nunique").gt(1).sum()))

# ---------- H2 : Poisson a effets fixes firme, exposition = log(mots) ----------
def pois(y, rhs, hyp, name, note=""):
    m = pf.fepois(f"{y} ~ annee_c{rhs} | id", data=d, vcov={"CRV1":"id"}, offset="log_mots"); t=m.tidy().loc["annee_c"]
    add(name, hyp, "annee", t.Estimate, t["Std. Error"], t["Pr(>|t|)"], m._N, note)
pois("long_explicite", "", "H2", "Poisson EF firme, exposition log(mots)")
pois("long_explicite", " + " + " + ".join(CTRL), "H2", "Poisson EF firme + controles services/industries")
pois("court_explicite", "", "Descriptif", "Poisson EF firme (court terme)", "evolution du court terme, rapportee a titre descriptif")

res = pd.DataFrame(out)
with pd.ExcelWriter("6_analysis/results_tests_h1_h2.xlsx") as w:
    res.to_excel(w, "Resultats", index=False); desc.to_excel(w, "Cooccurrence_descriptif")
print(res.to_string()); print(desc.to_string())
