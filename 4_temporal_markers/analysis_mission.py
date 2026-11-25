import pandas as pd, re, collections, numpy as np
from langdetect import detect_langs, DetectorFactory; DetectorFactory.seed=123456789
B="../"
m=pd.read_csv(B+"2_collection/mission_metadata.csv",encoding="utf-8-sig")
t=pd.read_csv(B+"2_collection/mission_texts.csv",encoding="utf-8-sig")
serv=pd.read_csv(B+"2_collection/services_texts.csv",encoding="utf-8-sig",sep=None,engine="python")
panel=pd.read_csv(B+"3_cleaning_panel/panel_firm_year.csv")
ix=pd.read_csv(B+"4_temporal_markers/horizon_index_by_page.csv",encoding="utf-8-sig")
ok=m[(m.statut=="ok")].merge(t,on=["id","annee","type_lien"])
# --- nettoyage du texte repete: shingles de 6 mots presents dans >=30% des documents de la firme (services bruts + mission/apropos)
K=6
def toks(s): return str(s).split()
docs=collections.defaultdict(list)
for r in serv.itertuples(): docs[r.id].append(toks(r.texte_services))
for r in ok.itertuples(): docs[r.id].append(toks(r.texte_mission))
boiler={}
for f,L in docs.items():
    c=collections.Counter()
    for w in L: c.update(set(tuple(w[i:i+K]) for i in range(len(w)-K+1)))
    n=len(L); boiler[f]={s for s,v in c.items() if n>=3 and v>=max(3,0.3*n)}
def nettoie(f,txt):
    w=toks(txt); keep=np.ones(len(w),bool); B=boiler.get(f,set())
    for i in range(len(w)-K+1):
        if tuple(w[i:i+K]) in B: keep[i:i+K]=False
    return " ".join(x for x,k in zip(w,keep) if k)
ok["texte_nettoye"]=[nettoie(r.id,r.texte_mission) for r in ok.itertuples()]
ok["n_mots_apres"]=ok.texte_nettoye.str.split().str.len()
def lang(s):
    try:
        l=detect_langs(s)[0]; return l.lang if l.prob>=0.9 else "?"
    except Exception: return "?"
ok["langue_nett"]=[lang(s) if n>=20 else "?" for s,n in zip(ok.texte_nettoye,ok.n_mots_apres)]
ok["f_mots"]=ok.n_mots_apres<50; ok["f_lang"]=~ok.langue_nett.isin(["en","fr"])
# doublon: la page mission est la meme URL que la page services cette annee-la
su=panel.set_index(["id","annee"]).url_services_capture.to_dict()
ok["meme_url_services"]=[str(su.get((i,a),"")).split("id_/")[-1].rstrip("/").lower()==str(u).split("id_/")[-1].rstrip("/").lower() for i,a,u in zip(ok.id,ok.annee,ok.url_capture)]
ok["valide"]=~(ok.f_mots|ok.f_lang|ok.meme_url_services)
print("collectees ok",len(ok),"| <50 mots",ok.f_mots.sum(),"| langue",(ok.f_lang&~ok.f_mots).sum(),"| meme url que services",ok.meme_url_services.sum())
print(pd.crosstab(ok.type_lien,ok.valide)); print(ok[ok.valide].groupby("type_lien").n_mots_apres.median())
# --- lexique d'horizon (identique a extract_threat_horizon.py)
LONG={"en":r"long[- ]term|longer[- ]term|\bfuture\b|\bfutures\b|sustainab\w*|\bdecades?\b|next generation|\btomorrow\b|years ahead|\bbeyond\b|20[3-9]\d\b|net[- ]zero|\blong[- ]lasting|enduring|\bstrategic(ally)? (horizon|vision)|\bfuture[- ]proof\w*|ahead of (the )?(curve|change)|\bnext[- ]gen\w*",
      "fr":r"long terme|\bavenir\b|\bfutur\w*|durable\w*|d[ée]cennies?|demain|\bau[- ]del[àa]\b|20[3-9]\d\b"}
COURT={"en":r"short[- ]term|near[- ]term|\bimmediate\w*|\burgent\w*|\bquick(ly)?\b|\brapid(ly)?\b|\bnow\b|\btoday\b|\bwithin (days|weeks|months)\b|\bquarter(ly)?\b|\bday[- ]to[- ]day\b|\bfast\b|\bimmediately\b|quick wins?|\bagil\w*",
       "fr":r"court terme|\bimm[ée]diat\w*|\burgen\w*|\brapide\w*|\bmaintenant\b|aujourd.hui|\btrimestr\w*|\bquotidien\w*|\br[ée]activit\w*|\bgestion de crise\b"}
MEN={"en":r"\buncertain\w*|\bunpredictab\w*|\bunforeseen\b|\bunknowns?\b|\brisks?\b|\bthreats?\w*|\bcrisis\b|\bcrises\b|\bvolatil\w*|\bturbulen\w*|\bdisrupt\w*|\bvulnerab\w*|\bresilien\w*|\bshocks?\b|\bexposure\b|\bfraud\b|\bdisputes?\b|\bcompliance\b",
 "fr":r"\bincertain\w*|\bincertitude\w*|\bimpr[ée]visib\w*|\bimpr[ée]vu\w*|\brisques?\b|\bmenaces?\b|\bcrises?\b|\bvolatil\w*|\bturbulen\w*|\bperturbation\w*|\bvuln[ée]rab\w*|\br[ée]silien\w*|\bchocs?\b"}
C=lambda D:{k:re.compile(v,re.I) for k,v in D.items()}
L,Cr,M=C(LONG),C(COURT),C(MEN)
v=ok[ok.valide].copy()
lg=np.where(v.langue_nett=="fr","fr","en")
v["n_long"]=[len(L[g].findall(s)) for g,s in zip(lg,v.texte_nettoye)]
v["n_court"]=[len(Cr[g].findall(s)) for g,s in zip(lg,v.texte_nettoye)]
v["n_menace"]=[len(M[g].findall(s)) for g,s in zip(lg,v.texte_nettoye)]
v["indice_horizon"]=[(a-b)/(a+b) if a+b else np.nan for a,b in zip(v.n_long,v.n_court)]
v["n_mots"]=v.n_mots_apres
# services: pages principales du panel
s=ix[ix.page=="principale"].copy(); s["n_menace"]=np.nan; s["type_lien"]="services"
s=s[s.id.isin(v.id.unique())|True]
def resume(d,nom):
    return dict(corpus=nom,pages=len(d),firmes=d.id.nunique(),mediane_mots=int(d.n_mots.median()),
        pct_avec_marqueur=round(100*((d.n_long+d.n_court)>0).mean(),1),
        marqueurs_1000mots=round(1000*(d.n_long+d.n_court).sum()/d.n_mots.sum(),2),
        long_1000=round(1000*d.n_long.sum()/d.n_mots.sum(),2),court_1000=round(1000*d.n_court.sum()/d.n_mots.sum(),2),
        part_long=round(d.n_long.sum()/(d.n_long.sum()+d.n_court.sum()),2),indice_moyen=round(d.indice_horizon.mean(),2))
R=pd.DataFrame([resume(s,"services (panel)"),resume(v[v.type_lien=="mission"],"mission"),resume(v[v.type_lien=="apropos_repli"],"a propos (repli)")])
print(R.T.to_string())
print("menace /1000 mots mission:",round(1000*v[v.type_lien=="mission"].n_menace.sum()/v[v.type_lien=="mission"].n_mots.sum(),2))
v["periode"]=pd.cut(v.annee,[1995,2004,2009,2014,2019,2026],labels=["<=2004","2005-09","2010-14","2015-19","2020-25"])
s["periode"]=pd.cut(s.annee,[1995,2004,2009,2014,2019,2026],labels=["<=2004","2005-09","2010-14","2015-19","2020-25"])
def per(d):
    g=d.groupby("periode",observed=True)
    return pd.DataFrame({"pages":g.size(),"pct_marq":g.apply(lambda x:round(100*((x.n_long+x.n_court)>0).mean())),
        "m1000":g.apply(lambda x:round(1000*(x.n_long+x.n_court).sum()/x.n_mots.sum(),1)),
        "part_long":g.apply(lambda x:round(x.n_long.sum()/max(1,x.n_long.sum()+x.n_court.sum()),2))})
print("SERVICES\n",per(s)); print("MISSION\n",per(v[v.type_lien=="mission"]))
# termes les plus frequents
for k,P in [("long",L),("court",Cr)]:
    c=collections.Counter(x.lower() for g,txt in zip(lg[v.type_lien.values=="mission"],v[v.type_lien=="mission"].texte_nettoye) for x in P[g].findall(txt) if isinstance(x,str))
    c2=collections.Counter(mm.group(0).lower() for g,txt in zip(lg[v.type_lien.values=="mission"],v[v.type_lien=="mission"].texte_nettoye) for mm in P[g].finditer(txt))
    print(k,c2.most_common(12))
# couverture firme: annees valides mission
cm=v[v.type_lien=="mission"].groupby("id").annee.nunique()
print("firmes avec >=1 page mission valide:",(cm>=1).sum(),"| >=5 ans:",(cm>=5).sum(),"| >=10 ans:",(cm>=10).sum())
# option 2 sur les 93: annees combinees
sv=set(zip(panel[panel.valide].id,panel[panel.valide].annee)); mv=set(zip(v[v.type_lien=="mission"].id,v[v.type_lien=="mission"].annee))
print("firme-annees services",len(sv),"| mission",len(mv),"| mission sans services",len(mv-sv),"| union",len(sv|mv))
# stabilite: part des pages mission identiques a l'annee precedente
vm=v[v.type_lien=="mission"].sort_values(["id","annee"]); prev=vm.groupby("id").texte_nettoye.shift()
print("pages mission identiques a l'annee precedente:",round(100*(vm.texte_nettoye==prev)[prev.notna()].mean()),"%")
v.drop(columns=["texte_mission"]).to_csv("./mission_panel_horizon.csv",index=False,encoding="utf-8-sig")
R.to_csv("./corpus_comparison.csv",index=False,encoding="utf-8-sig")
