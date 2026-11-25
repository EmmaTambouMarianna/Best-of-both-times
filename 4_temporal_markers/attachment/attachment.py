# A quoi le marqueur temporel est-il rattache : l'ENVIRONNEMENT de la firme, ou son OFFRE ?
import re, numpy as np, pandas as pd
P="/mnt/user-data/uploads/wayback/4_temporal_markers/markers_v4.py"
src=open(P,encoding="utf-8").read().split("rows, terms = [], []")[0]
g={"__file__":P}; exec(src,g); d=g["d"].copy(); RX,XR=g["RX"],g["XR"]; phr=g["phrases"]
rows=[]
for _,r in d[d.lg=="en"].iterrows():
    ph=phr(r.texte_nettoye)
    for i,s in enumerate(ph):
        for c,e,rx in RX:
            if c not in ("long_explicite","court_explicite"): continue
            t=XR[e]["en"].sub(lambda m:" "*len(m.group()),s) if e in XR else s
            for m in rx["en"].finditer(t):
                a,b=m.start(),m.end(); toks_av=s[:a].split(); toks_ap=s[b:].split()
                rows.append(dict(id=r.id,nom=r.nom,annee=r.annee,
                    horizon="long" if c=="long_explicite" else "court",etiquette=e,marqueur=m.group(),
                    avant=" ".join(toks_av[-10:]),apres=" ".join(toks_ap[:10]),phrase=s[:400]))
M=pd.DataFrame(rows); print("occurrences de marqueurs :",len(M))

ENV=r"\b(world|environment|environments|market|markets|economy|economic|industry|industries|landscape|sector|sectors|times|era|context|conditions|climate|society|societal|technolog\w+|digitali\w+|change|changes|changing|disruption|disruptive|evolution|evolving|shift|shifts|trends?|pace|regulation|regulatory|competition|competitive|consumer\w*|demand|uncertainty|volatil\w+|complexity)\b"
OFF=r"\b(we|our|us|help|helps|helping|deliver\w*|provide[sd]?|providing|support\w*|enable[sd]?|offer\w*|service[sd]?|solutions?|approach|team[s]?|partnership|engagement|advise|advice|advisory|consult\w*|work with|design\w*|build\w*|implement\w*|drive[sn]?|create[sd]?)\b"
CLI=r"\b(you|your|client[s']?|customer[s']?|organi[sz]ations?|compan(y|ies)|business(es)?|firms?)\b"
def classe(r):
    ap,av=r.apres.lower(),r.avant.lower()
    # 1) le mot qualifie par le marqueur, juste apres
    if re.search(ENV,ap[:60]): return "environnement"
    if re.search(OFF,ap[:60]): return "offre"
    # 2) sinon, le contexte immediat avant
    env_av=bool(re.search(ENV,av[-60:])); off_av=bool(re.search(OFF,av[-60:]))
    if env_av and not off_av: return "environnement"
    if off_av and not env_av: return "offre"
    if re.search(CLI,av[-60:]) or re.search(CLI,ap[:60]): return "client"
    return "indetermine"
M["rattachement"]=M.apply(classe,axis=1)
print(M.rattachement.value_counts(normalize=True).mul(100).round(1).to_dict())
M["post"]=(M.annee>=2010).astype(int)
print("\n=== QUADRANT : horizon x rattachement (% des occurrences)")
for lab,q in [("avant 2010",M[M.post==0]),("2010-2017",M[(M.annee>=2010)&(M.annee<=2017)]),("2018-2025",M[M.annee>=2018])]:
    x=pd.crosstab(q.horizon,q.rattachement,normalize="all").mul(100).round(1)
    print(f"\n{lab}  (n={len(q)})"); print(x.to_string())
print("\n=== part de LONG terme, separement par rattachement")
per=pd.cut(M.annee,[1995,2009,2014,2019,2025],labels=["≤2009","2010-14","2015-19","2020-25"])
t=M.assign(L=(M.horizon=="long").astype(int)).pivot_table(index=per,columns="rattachement",values="L",aggfunc="mean",observed=True).mul(100).round(0)
n=M.pivot_table(index=per,columns="rattachement",values="annee",aggfunc="size",observed=True)
print(t.to_string()); print("\neffectifs :"); print(n.to_string())
M.to_csv("attachment_markers.csv",index=False,encoding="utf-8-sig")
print("\n--- exemples")
for r in M[(M.rattachement=="environnement")&(M.horizon=="court")].sample(3,random_state=3).itertuples(): print("  ENV/court :",r.avant[-45:],"[",r.marqueur,"]",r.apres[:45])
for r in M[(M.rattachement=="offre")&(M.horizon=="long")].sample(3,random_state=3).itertuples(): print("  OFF/long  :",r.avant[-45:],"[",r.marqueur,"]",r.apres[:45])
for r in M[(M.rattachement=="offre")&(M.horizon=="court")].sample(3,random_state=3).itertuples(): print("  OFF/court :",r.avant[-45:],"[",r.marqueur,"]",r.apres[:45])
