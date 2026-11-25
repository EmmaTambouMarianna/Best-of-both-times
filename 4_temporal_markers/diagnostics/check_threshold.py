import re, numpy as np, pandas as pd, pyfixest as pf
P="/mnt/user-data/uploads/wayback/4_temporal_markers/markers_v4.py"
src=open(P,encoding="utf-8").read().split("rows, terms = [], []")[0]
g={"__file__":P}; exec(src,g); d=g["d"].copy(); phr=g["phrases"]
d["txt"]=[" ".join(phr(t)) for t in d.texte_nettoye]; d["n_mots"]=d.txt.str.split().map(len)
STOP={"the","of","and","to","for","in","a","on","with","your","our","&","is","as","at","by","from"}
def caps(t):
    w=[x for x in re.findall(r"[A-Za-z][A-Za-z'’-]*",str(t)) if x.lower() not in STOP]
    return np.mean([x[0].isupper() for x in w]) if w else 0
d["caps_page"]=d.txt.map(caps)
pg=d[["id","annee","n_mots","caps_page"]].drop_duplicates(["id","annee"])

p=pd.read_csv("windows_with_topics.csv"); p=p[p.dominant>0].copy()
p["long"]=(p.horizon=="long").astype(int); p["theme"]=p.dominant.astype(str)
p["post"]=(p.annee>=2010).astype(int); p["t"]=p.annee-2010
p["nav"]=(p.fenetre.map(caps)>0.6).astype(int)
p=p.merge(pg,on=["id","annee"],how="left"); p["log_mots"]=np.log(p.n_mots.clip(lower=1))
CL={"CRV1":"id"}
print("=== A. les pages anciennes sont-elles differentes ? (moyennes par periode)")
print(p.groupby(p.post).agg(fenetres=("long","size"),mots_page=("n_mots","median"),
      part_menu=("nav","mean"),caps_page=("caps_page","mean"),part_long=("long","mean")).round(3).to_string())
print("\n=== B. le palier 2010 survit-il aux controles ?")
rows=[]
def run(lab,f,data=p):
    m=pf.feols(f,data=data,vcov=CL); t=m.tidy()
    b,se,pv=t.loc["post","Estimate"],t.loc["post","Std. Error"],t.loc["post","Pr(>|t|)"]
    print(f"  {lab:52} post={b:+.4f} (se={se:.4f}, p={pv:.3f}) N={m._N}")
    rows.append(dict(specification=lab,beta_post2010=round(b,4),erreur_type=round(se,4),p=round(pv,4),N=m._N)); return b
b0=run("1. reference : EF firme + EF theme","long ~ post | id + theme")
run("2. + longueur de page (log)","long ~ post + log_mots | id + theme")
run("3. + indicatrice fenetre de menu","long ~ post + nav | id + theme")
run("4. + longueur + menu (fenetre) + menu (page)","long ~ post + log_mots + nav + caps_page | id + theme")
run("5. hors fenetres de menu","long ~ post + log_mots | id + theme",p[p.nav==0])
run("6. pages >= 300 mots seulement","long ~ post + log_mots | id + theme",p[p.n_mots>=300])
run("7. pages >= 300 mots ET hors menu","long ~ post + log_mots | id + theme",p[(p.n_mots>=300)&(p.nav==0)])
run("8. 36 firmes observees avant ET apres","long ~ post + log_mots + nav | id + theme",p[p.id.isin(set(p[p.annee<2010].id)&set(p[p.annee>=2010].id))])
print("\n=== C. le palier depend-il d'une seule etiquette de marqueur ?")
for e in sorted(p.etiquette.unique()):
    q=p[p.etiquette!=e]
    if q.post.nunique()<2 or len(q)<300: continue
    m=pf.feols("long ~ post + log_mots | id + theme",data=q,vcov=CL); t=m.tidy()
    print(f"  sans « {e[:34]:34} » post={t.loc['post','Estimate']:+.4f} (p={t.loc['post','Pr(>|t|)']:.3f}) N={m._N}")
print("\n  composition des etiquettes avant / apres 2010 (% des fenetres) :")
c=pd.crosstab(p.etiquette,p.post,normalize="columns").mul(100).round(1); c.columns=["avant 2010","apres 2010"]
print(c.to_string())
print("\n=== D. tendance post-2010 avec controles")
for lab,q in [("2010+",p[p.annee>=2010]),("2010+ hors menu, pages>=300",p[(p.annee>=2010)&(p.nav==0)&(p.n_mots>=300)])]:
    m=pf.feols("long ~ t + log_mots | id + theme",data=q,vcov=CL); t=m.tidy()
    print(f"  {lab:30} t={t.loc['t','Estimate']:+.4f} (se={t.loc['t','Std. Error']:.4f}, p={t.loc['t','Pr(>|t|)']:.3f}) N={m._N}")
pd.DataFrame(rows).to_csv("threshold_check.csv",index=False,encoding="utf-8-sig")
