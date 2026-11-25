# Variables de controle : pays, industries clientes, categories de services
# + classement de l'orientation temporelle des categories de services
# Corpus : pages services du panel (source "principale", firmes eligibles, annees valides)
# Lancer depuis le dossier wayback :  python3 4_temporal_markers/controls_services.py
import pandas as pd, numpy as np, re
from pathlib import Path

B = Path(__file__).resolve().parents[1]
N = B / "3_cleaning_panel"; O = B / "4_temporal_markers"; C = B / "5_controls"; C.mkdir(exist_ok=True)

panel = pd.read_csv(N / "panel_firm_year.csv")
elig = pd.read_csv(N / "eligible_firms_final.csv")
E_ids = set(elig[elig.eligible == 1].id)
t = pd.read_csv(N / "cleaned_texts.csv")
d = t[t.source == "principale"].merge(panel[panel.valide][["id", "annee", "langue_nett"]], on=["id", "annee"])
d = d[d.id.isin(E_ids)].copy()
d["lg"] = ["fr" if l == "fr" else "en" for l in d.langue_nett]

def phrases(txt):
    txt = re.sub(r"\s*\|\s*", " . ", str(txt))
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9«“\"(])", txt) if s.strip()]

# --------------------------------------------------------------------------
# 1. CATEGORIES DE SERVICES (ce que la firme offre) : (code, libelle, regex en, regex fr)
# --------------------------------------------------------------------------
SERV = [
 ("strategie", "Stratégie et croissance", r"\bstrateg(y|ies|ic)\b|\bgrowth strateg\w*|market entry|corporate development|portfolio strategy|business planning", r"\bstrat[ée]gi\w*|croissance externe|plan d.affaires"),
 ("operations", "Opérations et chaîne d'approvisionnement", r"\boperations?\b|operational excellence|supply chain|procurement|\bsourcing\b|\blean\b|logistics|manufacturing excellence|process improvement", r"\bop[ée]rations?\b|excellence op[ée]rationnelle|cha[iî]ne d.approvisionnement|\bachats?\b|logistique|\blean\b"),
 ("techno", "Technologie, numérique et données", r"\bdigital\b|\btechnolog\w*|\bcloud\b|\bdata\b|analytics|artificial intelligence|\bAI\b|\bIT\b(?! is)|software|automation|\bERP\b|\bSAP\b", r"num[ée]rique|\bdigital\w*|technolog\w*|donn[ée]es|intelligence artificielle|\bIA\b|syst[èe]mes d.information|logiciel"),
 ("risque", "Risque, conformité et cybersécurité", r"\brisks?\b|compliance|regulatory|\bcyber\w*|security|internal audit|\bfraud\b|resilience", r"\brisques?\b|conformit[ée]|r[ée]glementa\w*|cyber\w*|s[ée]curit[ée]|audit interne|fraude|r[ée]silience"),
 ("transactions", "Finance, transactions et fusions-acquisitions", r"\bM&A\b|mergers?|acquisitions?|due diligence|transaction\w*|valuations?|corporate finance|private equity|capital markets|deal\b", r"fusions?|acquisitions?|due diligence|transaction\w*|[ée]valuation d.entreprise|finance d.entreprise|capital[- ]investissement"),
 ("performance", "Performance, coûts et restructuration", r"performance improvement|\bcosts?\b|restructur\w*|turn[- ]?around|profitability|efficiency|productivity|insolvenc\w*", r"performance|\bco[uû]ts?\b|restructur\w*|redressement|rentabilit[ée]|efficacit[ée]|productivit[ée]"),
 ("rh", "Capital humain, organisation et changement", r"human capital|\bHR\b|human resources|\btalent\b|workforce|people (strategy|advisory|analytics)|leadership development|organi[sz]ational (design|effectiveness|change)|change management|culture\b|compensation|executive search", r"ressources humaines|\bRH\b|talents?|capital humain|conduite du changement|gestion du changement|organisation\b|r[ée]mun[ée]ration|leadership"),
 ("marketing", "Marketing, clients et ventes", r"marketing|customer\w*|\bbrand\w*|pricing|\bsales\b|commercial excellence|consumer insights?|customer experience", r"marketing|clients? |\bmarques?\b|tarification|\bprix\b|\bventes?\b|exp[ée]rience client"),
 ("durabilite", "Durabilité, climat et ESG", r"sustainab\w*|\bESG\b|\bclimate\b|net[- ]zero|decarboni\w*|energy transition|circular economy|environmental", r"durabilit[ée]|d[ée]veloppement durable|\bESG\b|\bclimat\w*|d[ée]carbon\w*|transition [ée]nerg\w*|environnement\w*"),
 ("innovation", "Innovation, R&D et design", r"innovation|\bR&D\b|research and development|product development|design thinking|\bventur\w*|new product", r"innovation|\bR&D\b|recherche et d[ée]veloppement|d[ée]veloppement de produits?|\bdesign\b"),
 ("ingenierie", "Ingénierie, infrastructures et projets", r"engineering|infrastructure|construction|project management|capital projects|asset management|architecture", r"ing[ée]nierie|infrastructures?|construction|gestion de projets?|architecture"),
 ("politiques", "Politiques publiques et développement", r"public policy|policy advisory|government advisory|economic development|international development|public affairs|advocacy", r"politiques? publiques?|d[ée]veloppement [ée]conomique|d[ée]veloppement international|affaires publiques"),
 ("litiges", "Litiges, expertise économique et forensique", r"litigation|disputes?|forensic|expert witness|antitrust|competition economics|economic consulting|arbitration", r"litiges?|contentieux|expertise judiciaire|forensique|concurrence|arbitrage"),
]
# --------------------------------------------------------------------------
# 2. INDUSTRIES CLIENTES (a qui la firme s'adresse)
# --------------------------------------------------------------------------
IND = [
 ("finance", "Services financiers et assurance", r"financial services|\bbank\w*|insurance|insurers?|asset managers?|wealth management|capital markets|payments", r"services financiers|\bbanqu\w*|assurance\w*|gestion d.actifs"),
 ("energie", "Énergie, services publics et ressources", r"\benergy\b|\butilit(y|ies)\b|oil and gas|oil & gas|power (generation|sector|and utilities)|renewables?|\bmining\b|natural resources|\bmetals\b", r"[ée]nergie|services publics|p[ée]trol\w*|\bgaz\b|renouvelables?|\bmines?\b|ressources naturelles"),
 ("sante", "Santé et sciences de la vie", r"health ?care|health systems?|life sciences|pharma\w*|biotech\w*|medical devices?|medtech|hospitals?", r"sant[ée]|sciences de la vie|pharma\w*|biotech\w*|m[ée]dical\w*|h[ôo]pita\w*"),
 ("secteur_public", "Secteur public et gouvernement", r"public sector|government|federal|\bdefen[cs]e\b|non-?profits?|education|higher education|\bstate and local\b", r"secteur public|gouvernement\w*|administration publique|\bd[ée]fense\b|[ée]ducation|organismes? sans but lucratif"),
 ("tmt", "Technologie, médias et télécommunications", r"telecom\w*|\bmedia\b|entertainment|high tech|technology companies|\bTMT\b|software companies", r"t[ée]l[ée]com\w*|m[ée]dias|divertissement|haute technologie"),
 ("conso", "Consommation et commerce de détail", r"consumer (goods|products|packaged)|\bretail\w*|\bCPG\b|food and beverage|luxury|hospitality", r"biens de consommation|commerce de d[ée]tail|\bdistribution\b|grande consommation|agroalimentaire|\bluxe\b|h[ôo]tellerie"),
 ("industrie", "Industrie manufacturière et automobile", r"industrial\w*|manufactur\w*|automotive|chemicals?|aerospace|engineering companies|machinery", r"industri\w*|manufactur\w*|automobile|chimie|a[ée]ronautique|a[ée]rospatial"),
 ("transport", "Transport et logistique", r"\btransport(ation)?\b|logistics|aviation|airlines?|airports?|\brail\b|shipping|\bports?\b", r"transport\w*|logistique|aviation|ferroviaire|maritime"),
 ("immobilier", "Immobilier et construction", r"real estate|\bpropert(y|ies)\b|construction|built environment", r"immobilier|construction|b[âa]timent"),
 ("pe", "Capital-investissement (clients investisseurs)", r"private equity|portfolio companies|sponsors? and investors|investment funds", r"capital[- ]investissement|fonds d.investissement"),
]

def compile_(L): return [(k, lib, {"en": re.compile(en, re.I), "fr": re.compile(fr, re.I)}) for k, lib, en, fr in L]
SRX, IRX = compile_(SERV), compile_(IND)

# marqueurs EXPLICITES uniquement (lexique v4), pour le classement : evite toute circularite avec l'implicite
LONG_E = {"en": re.compile(r"long[- ]term|longer[- ]term|\bfutures?\b(?![- ]proof)|years ahead|coming years|years to come|next \d+ years|(next|coming) decades?|(?<!PAS )\b20[3-6]\d\b", re.I),
          "fr": re.compile(r"long terme|\bavenir\b|\bfutur(e|s|es)?\b|prochaines ann[ée]es|ann[ée]es [àa] venir|prochaines d[ée]cennies|(?<!PAS )\b20[3-6]\d\b", re.I)}
COURT_E = {"en": re.compile(r"short[- ]term|near[- ]term|\bimmediate(ly)?\b|\burgen(t|cy)\w*|\bwithin (hours|days|weeks|months)\b|quick[- ]wins?|\brapid(ly)?\b(?! (response|search))|\bquickly\b|\bfast[- ]paced\b|\bfaster\b|\bfast[- ]track\w*", re.I),
           "fr": re.compile(r"court terme|\bimm[ée]diat\w*|\burgen\w*|\ben quelques (heures|jours|semaines)\b|gains rapides|\brapide(s|ment)?\b", re.I)}

rows, win = [], []
for _, r in d.iterrows():
    ph = phrases(r.texte_nettoye); txt = " ".join(ph); nm = max(len(txt.split()), 1)
    row = dict(id=r.id, nom=r.nom, annee=r.annee, n_mots=nm)
    for k, _, rx in SRX:
        n = len(rx[r.lg].findall(txt)); row["serv_" + k] = int(n > 0); row["serv_" + k + "_1000"] = 1000 * n / nm
    for k, _, rx in IRX:
        n = len(rx[r.lg].findall(txt)); row["ind_" + k] = int(n > 0); row["ind_" + k + "_1000"] = 1000 * n / nm
    rows.append(row)
    # fenetre phrase +-1 autour de chaque mention de categorie de service
    for i, s in enumerate(ph):
        cats = [k for k, _, rx in SRX if rx[r.lg].search(s)]
        if not cats: continue
        ctx = " ".join(ph[max(0, i - 1): i + 2])
        L, Cn = len(LONG_E[r.lg].findall(ctx)), len(COURT_E[r.lg].findall(ctx))
        for k in cats: win.append(dict(id=r.id, annee=r.annee, cat=k, L=L, C=Cn))

fa = pd.DataFrame(rows)
# pays (siege social, liste Forbes 2026)
pays = pd.read_csv(C / "firm_countries.csv")[["id", "pays"]]
fa = fa.merge(pays, on="id", how="left")
fa["anglo"] = fa.pays.isin(["United States", "United Kingdom", "Canada", "Ireland", "Australia"]).astype(int)
cols = ["id", "nom", "pays", "anglo", "annee", "n_mots"] + [c for c in fa.columns if c.startswith(("serv_", "ind_"))]
fa[cols].to_csv(C / "controls_firm_year.csv", index=False, encoding="utf-8-sig")

# profil firme (invariant dans le temps) : part des annees ou la categorie est mentionnee
dum = [c for c in fa.columns if c.startswith(("serv_", "ind_")) and not c.endswith("_1000")]
prof = fa.groupby(["id", "nom", "pays", "anglo"])[dum].mean().round(3).reset_index()
lib = {**{"serv_" + k: l for k, l, *_ in SERV}, **{"ind_" + k: l for k, l, *_ in IND}}
prof["services_principaux"] = prof[[c for c in dum if c.startswith("serv_")]].apply(lambda s: " ; ".join(lib[c] for c in s[s >= 0.5].sort_values(ascending=False).index[:4]), axis=1)
prof["industries_principales"] = prof[[c for c in dum if c.startswith("ind_")]].apply(lambda s: " ; ".join(lib[c] for c in s[s >= 0.5].sort_values(ascending=False).index[:4]), axis=1)
prof.to_csv(C / "controls_firm_profile.csv", index=False, encoding="utf-8-sig")

# --------------------------------------------------------------------------
# 3. CLASSEMENT : orientation temporelle EXPLICITE autour de chaque categorie de service
#    indice = (L - C) / (L + C) ; IC 95 % par bootstrap sur les firmes (1000 tirages)
# --------------------------------------------------------------------------
w = pd.DataFrame(win)
rng = np.random.default_rng(20261024)
def bidx(g): return (g.L.sum() - g.C.sum()) / max(g.L.sum() + g.C.sum(), 1)
res = []
for k, l, *_ in SERV:
    g = w[w.cat == k]; fl = g.groupby("id")[["L", "C"]].sum()
    ids = fl.index.to_numpy(); bs = []
    for _ in range(1000):
        s = fl.loc[rng.choice(ids, len(ids))]; tot = s.L.sum() + s.C.sum()
        if tot: bs.append((s.L.sum() - s.C.sum()) / tot)
    early, late = g[g.annee <= 2012], g[g.annee >= 2013]
    res.append(dict(code=k, categorie=l, phrases=len(g), firmes=g.id.nunique(),
                    marqueurs_long=int(g.L.sum()), marqueurs_court=int(g.C.sum()),
                    pct_phrases_avec_marqueur=round(100 * ((g.L + g.C) > 0).mean(), 1),
                    indice_orientation=round(bidx(g), 3),
                    ic95_bas=round(np.percentile(bs, 2.5), 3), ic95_haut=round(np.percentile(bs, 97.5), 3),
                    indice_1996_2012=round(bidx(early), 3) if len(early) else np.nan,
                    indice_2013_2025=round(bidx(late), 3) if len(late) else np.nan))
rk = pd.DataFrame(res).sort_values("indice_orientation", ascending=False).reset_index(drop=True)
rk.insert(0, "rang", rk.index + 1)
base = (w.groupby(["id","annee"]).size() > 0).sum()
rk.to_csv(C / "services_orientation_ranking.csv", index=False, encoding="utf-8-sig")
pd.DataFrame([(k, l, en, fr) for k, l, en, fr in SERV], columns=["code","libelle","regex_en","regex_fr"]).assign(type="service").to_csv(C / "dictionary_controls.csv", index=False, encoding="utf-8-sig")
pd.DataFrame([(k, l, en, fr) for k, l, en, fr in IND], columns=["code","libelle","regex_en","regex_fr"]).assign(type="industrie").to_csv(C / "dictionary_controls.csv", mode="a", header=False, index=False, encoding="utf-8-sig")

print("firme-annees", len(fa), "firmes", fa.id.nunique(), "pays manquants", fa.pays.isna().sum())
print((fa[[c for c in dum if c.startswith("serv_")]].mean()*100).round(1).sort_values(ascending=False).to_string())
print((fa[[c for c in dum if c.startswith("ind_")]].mean()*100).round(1).sort_values(ascending=False).to_string())
print(rk.to_string(index=False))
