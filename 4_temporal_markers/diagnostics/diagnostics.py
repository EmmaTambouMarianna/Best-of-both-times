import numpy as np, pandas as pd, pyfixest as pf, statsmodels.api as sm
from statsmodels.discrete.conditional_models import ConditionalLogit
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ACC="#2F6DB5"; NEU="#8A8F98"; INK="#1F2328"
p=pd.read_csv("windows_with_topics.csv"); p=p[p.dominant>0].copy()
p["long"]=(p.horizon=="long").astype(int); p["t"]=p.annee-2010; p["theme"]=p.dominant.astype(str)
CL={"CRV1":"id"}; res=[]
def add(lab,b,se,pv,N,note=""): res.append(dict(modele=lab,beta=round(b,4),erreur_type=round(se,4),p=round(pv,4),N=N,remarque=note))

m=pf.feols("long ~ t | id + theme",data=p,vcov=CL); td=m.tidy()
b0,se0,p0=td.loc["t","Estimate"],td.loc["t","Std. Error"],td.loc["t","Pr(>|t|)"]
add("MPL : EF firme + EF thème (modèle proposé)",b0,se0,p0,m._N,"erreurs-types groupées par firme")
try:
    wb=m.wildboottest(param="t",reps=9999,seed=7); add("MPL, bootstrap sauvage par grappe",b0,se0,float(wb["Pr(>|t|)"]),m._N,"9 999 réplications")
except Exception as e: print("wildboot:",e)

# logit conditionnel (a la Chamberlain) : pas d'hypothese de normalite
X=pd.get_dummies(p[["theme"]],drop_first=True).astype(float); X["t"]=p.t.values
cl=ConditionalLogit(p.long.values,X,groups=p.id.values).fit(disp=0)
i=list(X.columns).index("t"); add("Logit conditionnel à EF firme",cl.params.iloc[i],cl.bse.iloc[i],cl.pvalues.iloc[i],int(cl.nobs),"log-cotes, pas comparable en taille")

# comptages : Poisson a EF, cellule firme-annee-theme, exposition = nb de marqueurs
c=p.groupby(["id","annee","theme"]).long.agg(L="sum",n="size").reset_index(); c["t"]=c.annee-2010
Xc=sm.add_constant(pd.concat([pd.get_dummies(c[["theme"]],drop_first=True).astype(float),
                              pd.get_dummies(c[["id"]].astype(str),drop_first=True).astype(float),c[["t"]]],axis=1))
po=sm.GLM(c.L,Xc,family=sm.families.Poisson(),offset=np.log(c.n)).fit(cov_type="cluster",cov_kwds={"groups":c.id})
add("Poisson à EF, exposition = nb de marqueurs",po.params["t"],po.bse["t"],po.pvalues["t"],int(po.nobs),"cellules firme-année-thème")
fl=sm.GLM(c.L/c.n,Xc,family=sm.families.Binomial(),freq_weights=c.n).fit(cov_type="cluster",cov_kwds={"groups":c.id})
add("Logit fractionnaire (Papke & Wooldridge)",fl.params["t"],fl.bse["t"],fl.pvalues["t"],int(fl.nobs),"part de long terme par cellule")

# panel desequilibre : pentes intra-firme moyennees (mean group)
sl=[]
for fid,q in p.groupby("id"):
    if q.annee.nunique()>=5 and len(q)>=8 and q.long.nunique()>1:
        sl.append(np.polyfit(q.t,q.long,1)[0])
sl=np.array(sl); tt=sl.mean()/(sl.std(ddof=1)/np.sqrt(len(sl)))
from scipy import stats
add("Mean group : moyenne des pentes intra-firme",sl.mean(),sl.std(ddof=1)/np.sqrt(len(sl)),2*(1-stats.t.cdf(abs(tt),len(sl)-1)),len(sl),f"{len(sl)} firmes à ≥5 années ; médiane {np.median(sl):+.4f}")
# sous-echantillons
for lab,q in [("Firmes présentes avant et après 2015",p[p.id.isin(set(p[p.annee<2015].id)&set(p[p.annee>=2015].id))]),
              ("Années 2010-2025 (couverture dense)",p[p.annee>=2010]),
              ("Firmes à ≥10 fenêtres",p[p.groupby('id').long.transform('size')>=10])]:
    mm=pf.feols("long ~ t | id + theme",data=q,vcov=CL); t2=mm.tidy()
    add(lab,t2.loc["t","Estimate"],t2.loc["t","Std. Error"],t2.loc["t","Pr(>|t|)"],mm._N)
R=pd.DataFrame(res); print(R.to_string(index=False))

# ---- normalite / structure
resid=m.resid(); jb=stats.jarque_bera(resid); sw=stats.shapiro(resid[:5000])
fy=p.groupby(["id","annee"]).long.agg(L="sum",n="size").reset_index(); fy["ix"]=(2*fy.L-fy.n)/fy.n
print(f"\nJarque-Bera residus MPL : stat={jb[0]:.0f} p={jb[1]:.3g} | Shapiro p={sw[1]:.3g}")
print(f"indice firme-annee : {100*((fy.ix.abs()==1).mean()):.1f} % des firmes-annees sont a -1 ou +1 ; mediane de marqueurs par firme-annee = {fy.n.median():.0f}")

# ---- figure
fig,ax=plt.subplots(2,3,figsize=(13.5,7.4)); fig.patch.set_facecolor("white")
for a in ax.ravel():
    a.set_facecolor("white"); [s.set_visible(False) for s in (a.spines["top"],a.spines["right"])]
    for s in (a.spines["left"],a.spines["bottom"]): s.set_color(NEU)
    a.tick_params(colors=NEU,labelsize=8); a.grid(axis="y",color="#E6E8EB",lw=.8); a.set_axisbelow(True)
g=p.groupby("annee").agg(firmes=("id","nunique"),fen=("long","size"))
ax[0,0].bar(g.index,g.firmes,color=ACC,width=.75); ax[0,0].set_title("a. Panel déséquilibré : firmes par année",fontsize=9.5,color=INK,loc="left")
ny=p.groupby("id").annee.nunique()
ax[0,1].hist(ny,bins=range(1,ny.max()+2),color=ACC,rwidth=.85); ax[0,1].set_title(f"b. Années observées par firme (médiane {ny.median():.0f})",fontsize=9.5,color=INK,loc="left")
ax[0,2].hist(fy.ix,bins=21,color=ACC,rwidth=.9); ax[0,2].set_title("c. Indice par firme-année : masse aux bornes ±1",fontsize=9.5,color=INK,loc="left")
yr=p.groupby("annee").long.agg(["mean","size"]); se=np.sqrt(yr["mean"]*(1-yr["mean"])/yr["size"])
ok=yr["size"]>=10
ax[1,0].errorbar(yr.index[ok],yr["mean"][ok]*100,yerr=1.96*se[ok]*100,fmt="o",ms=4,color=ACC,ecolor=NEU,elinewidth=1,capsize=0)
z=np.polyfit(yr.index[ok],yr["mean"][ok]*100,1); ax[1,0].plot(yr.index[ok],np.polyval(z,yr.index[ok]),color=INK,lw=1.5)
ax[1,0].set_title("d. Part de marqueurs long terme par année (IC 95 %)",fontsize=9.5,color=INK,loc="left"); ax[1,0].set_ylabel("%",color=NEU,fontsize=8)
sm.qqplot(resid,line="s",ax=ax[1,1],markerfacecolor=ACC,markeredgecolor=ACC,markersize=3)
ax[1,1].get_lines()[1].set_color(INK); ax[1,1].set_title("e. Résidus du MPL : deux nuages, non normaux",fontsize=9.5,color=INK,loc="left")
ax[1,1].set_xlabel("quantiles théoriques",fontsize=8,color=NEU); ax[1,1].set_ylabel("résidus",fontsize=8,color=NEU)
ax[1,2].hist(sl*100,bins=16,color=ACC,rwidth=.9); ax[1,2].axvline(0,color=INK,lw=1)
ax[1,2].set_title(f"f. Pentes intra-firme ({len(sl)} firmes), pts/an",fontsize=9.5,color=INK,loc="left")
fig.suptitle("Diagnostics : structure du panel et distribution de la variable dépendante",fontsize=11,color=INK,x=.012,ha="left",y=.985)
fig.tight_layout(rect=[0,0,1,.95]); fig.savefig("panel_diagnostics.png",dpi=180)
R.to_csv("estimator_comparison.csv",index=False,encoding="utf-8-sig")
