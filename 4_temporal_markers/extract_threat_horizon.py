import pandas as pd, re
S="/home/claude/nett/"; O="/mnt/user-data/outputs/"
panel=pd.read_csv(O+"panel_firm_year.csv"); elig=pd.read_csv(O+"eligible_firms_final.csv")
ver=pd.read_csv(O+"pivot_verdicts.csv",sep=";",encoding="utf-8-sig")
ex=set(zip(ver[ver.pivot_exclu==1].id,ver[ver.pivot_exclu==1].annee))
E_ids=set(elig[elig.eligible==1].id)
t=pd.read_csv(S+"cleaned_texts.csv")
nomm=dict(zip(panel.id,panel.nom))
# sources : principale (panel valide) + profondeur (>10 mots, firmes eligibles, pivot non exclu)
a=t[t.source=="principale"].merge(panel[panel.valide][["id","annee","type_page","langue_nett"]],on=["id","annee"])
a["page"]="principale"
b=t[(t.source=="profondeur")&(t.n_mots_apres>10)&(t.id.isin(E_ids))].copy()
b=b[[ (i,y) not in ex for i,y in zip(b.id,b.annee)]]
b["type_page"]=["industrie" if re.search(r"industr|sector|financial-services",str(u),re.I) else "generale" for u in b.url]
b["langue_nett"]="en"; b["page"]="sous-page"
d=pd.concat([a,b],ignore_index=True); d=d[d.id.isin(E_ids)]
# lexiques
MENACE={ # danger / incertitude (ce que les clients cherchent a eviter)
 "en":r"\buncertain\w*|\bunpredictab\w*|\bunforeseen\b|\bunknowns?\b|\brisks?\b|\bthreats?\w*|\bcrisis\b|\bcrises\b|\bvolatil\w*|\bturbulen\w*|\bdisrupt\w*|\bvulnerab\w*|\bresilien\w*|\bshocks?\b|\bexposure\b|\bfraud\b|\bdisputes?\b|\bcompliance\b",
 "fr":r"\bincertain\w*|\bincertitude\w*|\bimpr[ée]visib\w*|\bimpr[ée]vu\w*|\brisques?\b|\bmenaces?\b|\bcrises?\b|\bvolatil\w*|\bturbulen\w*|\bperturbation\w*|\bvuln[ée]rab\w*|\br[ée]silien\w*|\bchocs?\b"}
COEUR={"en":r"\buncertain\w*|\bunpredictab\w*|\bunforeseen\b|\bunknowns?\b|\bvolatil\w*|\bturbulen\w*","fr":r"\bincertain\w*|\bincertitude\w*|\bimpr[ée]visib\w*|\bimpr[ée]vu\w*|\bvolatil\w*|\bturbulen\w*"}
LONG={"en":r"long[- ]term|longer[- ]term|\bfuture\b|\bfutures\b|sustainab\w*|\bdecades?\b|next generation|\btomorrow\b|years ahead|\bbeyond\b|20[3-9]\d\b|net[- ]zero|\blong[- ]lasting|enduring|\bstrategic(ally)? (horizon|vision)|\bfuture[- ]proof\w*|ahead of (the )?(curve|change)|\bnext[- ]gen\w*",
      "fr":r"long terme|\bavenir\b|\bfutur\w*|durable\w*|d[ée]cennies?|demain|\bau[- ]del[àa]\b|20[3-9]\d\b"}
COURT={"en":r"short[- ]term|near[- ]term|\bimmediate\w*|\burgent\w*|\bquick(ly)?\b|\brapid(ly)?\b|\bnow\b|\btoday\b|\bwithin (days|weeks|months)\b|\bquarter(ly)?\b|\bday[- ]to[- ]day\b|\bfast\b|\bimmediately\b|quick wins?|\bagil\w*",
       "fr":r"court terme|\bimm[ée]diat\w*|\burgen\w*|\brapide\w*|\bmaintenant\b|aujourd.hui|\btrimestr\w*|\bquotidien\w*|\br[ée]activit\w*|\bgestion de crise\b"}
C=lambda D:{k:re.compile(v,re.I) for k,v in D.items()}
M,Co,L,Cr=C(MENACE),C(COEUR),C(LONG),C(COURT)
def phrases(txt):
    txt=re.sub(r"\s*\|\s*"," . ",str(txt))
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9«“\"(])",txt) if s.strip()]
rows=[]; idx=[]
for _,r in d.iterrows():
    lg="fr" if r.langue_nett=="fr" else "en"
    ph=phrases(r.texte_nettoye); txt=" ".join(ph)
    nl=len(L[lg].findall(txt)); nc=len(Cr[lg].findall(txt)); nm=len(txt.split())
    idx.append(dict(id=r.id,nom=nomm[r.id],annee=r.annee,page=r.page,url=r.url,type_page=r.type_page,n_mots=nm,n_long=nl,n_court=nc,
                    indice_horizon=(nl-nc)/(nl+nc) if nl+nc>0 else None))
    for i,s in enumerate(ph):
        if not M[lg].search(s): continue
        ctx=" ".join(ph[max(0,i-1):i+2])
        hl=bool(L[lg].search(ctx)); hc=bool(Cr[lg].search(ctx))
        hor="long" if hl and not hc else "court" if hc and not hl else "mixte" if hl and hc else "non precise"
        rows.append(dict(id=r.id,nom=nomm[r.id],annee=r.annee,page=r.page,type_page=r.type_page,url=r.url,langue=lg,
              coeur=int(bool(Co[lg].search(s))),terme_menace=M[lg].search(s).group(0).lower(),horizon_dico=hor,phrase=s,contexte=" ".join(ctx.split()[:120])))
x=pd.DataFrame(rows); x.insert(0,"id_passage",range(1,len(x)+1))
ix=pd.DataFrame(idx)
x.to_csv(O+"threat_horizon_passages_v2.csv",index=False,encoding="utf-8-sig"); ix.to_csv(O+"horizon_index_by_page.csv",index=False,encoding="utf-8-sig")
print("pages",len(d),d.page.value_counts().to_dict(),"passages",len(x),"coeur",x.coeur.sum())
print("pages avec passage",x.groupby(["id","annee","url"]).ngroups, "firmes",x.id.nunique())
print(x.horizon_dico.value_counts(normalize=True).round(2).to_dict())
print(x.terme_menace.value_counts().head(10).to_dict())
g=x.groupby("annee").horizon_dico.value_counts(normalize=True).unstack().round(2); print(g.loc[[2000,2005,2010,2015,2020,2025]] if set([2000,2005,2010,2015,2020,2025])<=set(g.index) else g)
print(ix.groupby("annee").indice_horizon.agg(["mean","count"]).round(2).loc[[2005,2010,2015,2020,2025]].to_dict())
