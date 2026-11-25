import re, numpy as np, pandas as pd, statsmodels.api as sm
P="/mnt/user-data/uploads/wayback/4_temporal_markers/markers_v4.py"
src=open(P,encoding="utf-8").read().split("rows, terms = [], []")[0]
g={"__file__":P}; exec(src,g); d=g["d"].copy(); phr=g["phrases"]
d["txt"]=[" ".join(phr(t)) for t in d.texte_nettoye]; d["nm"]=d.txt.str.split().map(len)
ELITE=r"McKinsey|BCG|Bain & Company|Deloitte|^EY$|PwC|KPMG|Accenture|Booz Allen|Oliver Wyman"
d["elite"]=d.nom.str.contains(ELITE,case=False,regex=True)
print("longueur mediane des pages : elite=%.0f mots, autres=%.0f mots"%(d[d.elite].nm.median(),d[~d.elite].nm.median()))
BUZZ={"sustainability":r"sustainab\w*","ESG":r"\bESG\b","net zero":r"net[- ]zero|decarboni[sz]\w*|carbon[- ]neutral\w*",
 "digital transformation":r"digital transformation","big data":r"big data","AI / ML":r"\bAI\b|artificial intelligence|machine learning",
 "agile":r"\bagil\w*","resilience":r"resilien\w*","disruption":r"disrupt\w*","purpose":r"\bpurpose[- ]driven\b|\bour purpose\b",
 "long term":r"long[- ]term|longer[- ]term","future":r"\bfutures?\b(?![- ]proof)","generative AI":r"generative ai|\bgen ?ai\b",
 "knowledge management":r"knowledge management","outsourcing":r"outsourcing|offshoring","benchmarking":r"benchmarking","best practice":r"best practices?"}
def panel(trunc=None):
    t=d.txt.map(lambda s:" ".join(s.split()[:trunc])) if trunc else d.txt
    rows=[]
    for k,rx in BUZZ.items():
        r=re.compile(rx,re.I); h=[len(r.findall(x))>0 for x in t]
        q=pd.DataFrame(dict(annee=d.annee.values,elite=d.elite.values,h=h))
        p=q.groupby(["annee","elite"]).h.agg(["mean","size"]).reset_index()
        p=p[p["size"]>=5].pivot(index="annee",columns="elite",values="mean").dropna()
        if len(p)<8: continue
        for y in p.index: rows.append(dict(terme=k,annee=y,E=p.loc[y,True],A=p.loc[y,False]))
    L=pd.DataFrame(rows).sort_values(["terme","annee"])
    for c in ("E","A"): L[c+"z"]=L.groupby("terme")[c].transform(lambda s:(s-s.mean())/(s.std() or 1))
    return L
for lab,tr in [("texte complet",None),("300 premiers mots",300)]:
    L=panel(tr); print(f"\n--- {lab} (series standardisees par terme) ---")
    for lag in (1,2):
        q=L.copy(); q["Ez"]=q.groupby("terme").Ez.shift(lag); q["Az_l"]=q.groupby("terme").Az.shift(lag); q=q.dropna(subset=["Ez","Az_l"])
        r=sm.OLS(q.Az,sm.add_constant(q[["Ez","Az_l"]])).fit(cov_type="cluster",cov_kwds={"groups":q.terme})
        r2=sm.OLS(q.Ez if False else q.Ez*0+q.Ez,sm.add_constant(q[["Ez"]])).fit() # placeholder
        s=sm.OLS(q.groupby(level=0).Ez.first()*0+0,sm.add_constant(q[["Ez"]])).fit() if False else None
        print(f"  autres(t) ~ elite(t-{lag}): b={r.params['Ez']:+.3f} (p={r.pvalues['Ez']:.3f})   [autres(t-{lag}) b={r.params['Az_l']:+.3f}]  N={len(q)}")
        qq=L.copy(); qq["Az_s"]=qq.groupby("terme").Az.shift(lag); qq["Ez_l"]=qq.groupby("terme").Ez.shift(lag); qq=qq.dropna(subset=["Az_s","Ez_l"])
        r3=sm.OLS(qq.Ez,sm.add_constant(qq[["Az_s","Ez_l"]])).fit(cov_type="cluster",cov_kwds={"groups":qq.terme})
        print(f"  elite(t)  ~ autres(t-{lag}): b={r3.params['Az_s']:+.3f} (p={r3.pvalues['Az_s']:.3f})   [elite(t-{lag}) b={r3.params['Ez_l']:+.3f}]")
    L.to_csv(f"mode_leadlag_{'full' if tr is None else tr}.csv",index=False,encoding="utf-8-sig")
