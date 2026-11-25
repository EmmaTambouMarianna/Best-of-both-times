# Signatures de "mode managériale" (Abrahamson) testables sur le corpus existant
import re, sys, numpy as np, pandas as pd
P="/mnt/user-data/uploads/wayback/4_temporal_markers/markers_v4.py"
src=open(P,encoding="utf-8").read().split("rows, terms = [], []")[0]
g={"__file__":P}; exec(src,g)
d,RX,XR=g["d"],g["RX"],g["XR"]; phrases=g["phrases"]
d=d.copy(); d["txt"]=[" ".join(phrases(t)) for t in d.texte_nettoye]; d["nm"]=d.txt.str.split().map(len)

# --- 1. prevalence annuelle de "buzzwords" connus (test de cycle de vie) ---
BUZZ={
 "reengineering":r"re[- ]?engineering",
 "TQM / quality management":r"total quality management|\bTQM\b",
 "knowledge management":r"knowledge management",
 "benchmarking":r"benchmarking",
 "core competenc*":r"core competenc\w*",
 "balanced scorecard":r"balanced scorecard",
 "six sigma / lean":r"six sigma|\blean\b",
 "e-business / dot-com":r"e-business|e-commerce|\bdot[- ]?com\b",
 "outsourcing / offshoring":r"outsourcing|offshoring",
 "CRM":r"\bCRM\b|customer relationship management",
 "best practice":r"best practices?",
 "big data":r"big data",
 "digital transformation":r"digital transformation",
 "agile":r"\bagil\w*",
 "disruption":r"disrupt\w*",
 "innovation":r"\binnovation\b",
 "resilience":r"resilien\w*",
 "sustainability":r"sustainab\w*",
 "ESG":r"\bESG\b",
 "net zero / decarbonisation":r"net[- ]zero|decarboni[sz]\w*|carbon[- ]neutral\w*",
 "purpose":r"\bpurpose[- ]driven\b|\bour purpose\b",
 "AI / machine learning":r"\bAI\b|artificial intelligence|machine learning",
 "generative AI":r"generative ai|\bgen ?ai\b|large language model",
 "long term (marqueur)":r"long[- ]term|longer[- ]term",
 "future (marqueur)":r"\bfutures?\b(?![- ]proof)",
 "short/near term (marqueur)":r"short[- ]term|near[- ]term",
 "urgent/immediate (marqueur)":r"\burgen(t|cy)\w*|\bimmediate(ly)?\b",
}
rows=[]
for k,rx in BUZZ.items():
    r=re.compile(rx,re.I)
    for _,x in d.iterrows():
        n=len(r.findall(x.txt))
        rows.append((k,x.id,x.annee,n,x.nm))
b=pd.DataFrame(rows,columns=["terme","id","annee","n","nm"])
ny=d.groupby("annee").id.nunique()
prev=b.groupby(["terme","annee"]).apply(lambda s:(s.n>0).mean()*100,include_groups=False).unstack()
prev=prev.loc[:,ny[ny>=8].index]           # annees avec >=8 firmes
prev.to_csv("fashion_term_prevalence.csv",encoding="utf-8-sig")
# forme du cycle : annee du pic, prevalence au pic, prev finale / pic
sm=prev.T.rolling(3,center=True,min_periods=2).mean().T
f=pd.DataFrame({"pic_annee":sm.idxmax(1),"prev_pic":sm.max(1).round(1),
                "prev_2020_25":sm.loc[:,[c for c in sm.columns if c>=2020]].mean(1).round(1),
                "prev_1996_04":sm.loc[:,[c for c in sm.columns if c<=2004]].mean(1).round(1)})
f["declin_depuis_pic_%"]=(100*(1-f.prev_2020_25/f.prev_pic)).round(0)
print("=== CYCLE DE VIE DES TERMES (prevalence = % de firmes employant le terme) ===")
print(f.sort_values("pic_annee").to_string())

# --- 2. convergence du vocabulaire entre firmes (herding) ---
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
v=TfidfVectorizer(stop_words="english",min_df=5,max_df=0.6,sublinear_tf=True)
V=v.fit(d.txt)
conv=[]
for y,grp in d.groupby("annee"):
    if grp.id.nunique()<12: continue
    X=V.transform(grp.groupby("id").txt.apply(" ".join))
    S=cosine_similarity(X); iu=np.triu_indices_from(S,1)
    conv.append(dict(annee=y,firmes=grp.id.nunique(),similarite_moy=S[iu].mean()))
conv=pd.DataFrame(conv); conv.to_csv("fashion_convergence.csv",index=False,encoding="utf-8-sig")
import statsmodels.api as sm_
r=sm_.OLS(conv.similarite_moy,sm_.add_constant(conv.annee-2010)).fit()
print("\n=== CONVERGENCE DU VOCABULAIRE (cosinus moyen entre firmes, par annee) ===")
print(conv.round(3).to_string(index=False))
print(f"pente = {r.params.iloc[1]*100:+.3f} pt/an  p={r.pvalues.iloc[1]:.4f}")

# --- 3. courbe de diffusion : % de firmes employant un marqueur long terme ---
ix=pd.read_csv("/Users/x") if False else None
