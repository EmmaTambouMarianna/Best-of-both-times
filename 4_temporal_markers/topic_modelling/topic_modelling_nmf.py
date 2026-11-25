import re, sys, pandas as pd, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.decomposition import NMF
p = pd.read_csv("temporal_windows.csv")
MARK = r"\b(long|longer|short|near|term|terms|future|futures|years?|ahead|coming|come|next|decades?|immediate(ly)?|urgen\w*|rapid(ly)?|quickly|fast|faster|paced|track\w*|quick|wins?|within|hours|days|weeks|months|20\d\d)\b"
names = set(w.lower() for n in p.nom.unique() for w in re.findall(r"[A-Za-z]{3,}", str(n)))
NAV = {"news","events","event","careers","career","media","latest","thinking","journal","conference","conferences","skip","english","united","states","kingdom","download","pdf","article","articles","study","read","insights","insight","home","menu","search","login","subscribe","blog","webinar","webinars","podcast","overview","member","membership","press","releases","report","reports","publications","privacy","cookies","cookie","policy","terms","contact","locations","offices","office","site","page","click","view","videos","video","case","studies","india","canada","china","japan","germany","france","australia","espa","deutsch","italiano","fran","ais","bsr","cognizanti","helix","itsm","magic","quadrant","forrester","gartner","compendium","inc","llc","ltd","copyright","rights","reserved","jobs","join","alumni","explore","featured","stories","story","resources","library","brochure","whitepaper","white","paper","papers"}
GEN = {"client","clients","help","helps","helping","helped","business","businesses","services","service","company","companies","organization","organizations","organisations","organisation","work","working","team","teams","new","make","way","ways","need","needs","provide","provides","providing","including","based","support","ensure","approach","solutions","solution","firm","firms","consulting","consultants","consultancy","partner","partners","people","value","results","deliver","delivering","delivers","right","just","like","use","key","world","today","time","current","know","want","able","well","good","best","great","sure","order","also","every","may","many","much","one","two","three","expertise","experience","experts","expert","industry","industries","global","leading","leader","leaders","offer","offers","across","help","years","year","whether","together","within","through","core","full","range","wide","unique","ensure","successful","success","achieve","achieving"}
def clean(t):
    t = re.sub(r"https?://\S+|\S+@\S+", " ", str(t).lower()); t = re.sub(MARK, " ", t); t = re.sub(r"[^a-z\s-]", " ", t)
    return " ".join(w for w in t.split() if w not in names and w not in NAV and len(w) > 2)
p["txt"] = p.fenetre.map(clean)
p["sig"] = p.txt.str.split().map(lambda w: " ".join(sorted(set(w)))[:200])
u = p.drop_duplicates(["id","sig"])
stop = list(ENGLISH_STOP_WORDS | NAV | GEN)
K = int(sys.argv[1]); seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
from collections import Counter
fv = Counter(); 
for fid, grp in u.groupby("id"): fv.update(set(" ".join(grp.txt).split()))
VOC = sorted(w for w, c in fv.items() if c >= 6 and w not in set(stop))
vec = TfidfVectorizer(vocabulary=VOC, max_df=1.0, sublinear_tf=True, token_pattern=r"(?u)\b[a-z][a-z-]+\b")
X = vec.fit_transform(u.txt); voc = np.array(vec.get_feature_names_out())
m = NMF(n_components=K, init="nndsvda", random_state=seed, max_iter=1000, alpha_W=0.0).fit(X)
Wt = m.transform(vec.transform(p.txt)); s = Wt.sum(1, keepdims=True); Wt = Wt / np.where(s == 0, 1, s)
p[[f"T{k+1}" for k in range(K)]] = Wt; p["dominant"] = np.where(s.ravel() > 0, Wt.argmax(1) + 1, 0)
tops = []
for k in range(K):
    top = voc[m.components_[k].argsort()[::-1][:12]]; q = p[p.dominant == k+1]
    sh = q.id.value_counts(normalize=True).iloc[0] if len(q) else 0
    tops.append(dict(theme=f"T{k+1}", n=len(q), firmes=q.id.nunique(), part_firme_max=round(sh,2), part_long=round((q.horizon=="long").mean(),2), mots=", ".join(top)))
    print(f"T{k+1:>2} n={len(q):4} firmes={q.id.nunique():3} maxf={sh:.2f} long={(q.horizon=='long').mean():.2f} | " + ", ".join(top))
print("sans theme:", (p.dominant==0).sum())
p.to_csv(f"fenetres_topics_K{K}.csv", index=False, encoding="utf-8-sig"); pd.DataFrame(tops).to_csv(f"themes_K{K}.csv", index=False, encoding="utf-8-sig")
