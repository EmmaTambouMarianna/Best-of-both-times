"""Collecte des pages mission / aim / purpose (et repli sur 'a propos') pour les firmes du panel.
Usage (depuis 2_collection):  caffeinate -i python3 collect_mission.py [N_FIRMES]
 - sans argument: toutes les firmes eligibles; avec N: seulement les N premieres (test)
 - reprise automatique; un seul Ctrl+C = arret propre.
"""
import os, re, sys, time
from datetime import datetime
from urllib.parse import urljoin, urlparse
import pandas as pd, requests
from bs4 import BeautifulSoup
try:
    from langdetect import detect_langs, DetectorFactory
    DetectorFactory.seed = 123456789
except Exception:
    detect_langs = None

DOSSIER_ACC = "archives_services"
DOSSIER_HTML = "archives_mission"
FICHIER_META = "mission_metadata.csv"
FICHIER_TEXTES = "mission_texts.csv"
PANEL = "../3_cleaning_panel/eligible_firms_final.csv"
META_SERV = "services_metadata.csv"
PAUSE = 2.5
HEADERS = {"User-Agent": "Recherche academique - Emma Tambou Marianna (emmatamboumarianna@uvic.ca)"}

# Priorite 1: mission / aim / purpose / vision / valeurs ; priorite 2 (repli): a propos
MISSION_EXACT = {"our mission", "mission", "mission statement", "our mission and values", "mission & values",
                 "mission and values", "our aim", "our aims", "aim", "aims", "our purpose", "purpose",
                 "our vision", "vision", "vision & mission", "mission & vision", "mission and vision",
                 "our values", "values", "our vision and values", "purpose and values", "purpose & values",
                 "our beliefs", "what we believe", "our philosophy", "our goal", "our goals", "our commitment",
                 "notre mission", "mission et valeurs", "notre vision", "nos valeurs", "notre raison d'etre",
                 "notre raison d'être", "notre raison d’être", "nos objectifs", "notre engagement", "notre philosophie"}
MISSION_MOTS = [r"\bmission\b", r"\baims?\b", r"\bpurpose\b", r"\bvision\b", r"\bvalues\b", r"\bbeliefs?\b",
                r"\bphilosophy\b", r"\bgoals?\b", r"raison d.{1,2}tre", r"\bvaleurs\b", r"\bobjectifs\b"]
APROPOS_EXACT = {"about", "about us", "who we are", "our company", "company", "our story", "about the company",
                 "company profile", "a propos", "à propos", "qui sommes-nous", "qui sommes nous", "notre entreprise"}
APROPOS_MOTS = [r"\babout\b", r"who we are", r"our company", r"our story", r"propos", r"qui sommes"]
EXCLUS = ["career", "carriere", "carrière", "job", "news", "blog", "contact", "login", "privacy", "cookie",
          "investor", "press", "event", "customer", "support", "legal", "sitemap", "actualit", "presse",
          "emploi", "recrut", "mentions", "confidentialit", "evenement", "événement", "award", "csr", "sustainab"]
COLS_META = ["id", "nom", "annee", "type_lien", "lien", "ts_accueil", "ts_capture", "annee_capture", "valide_annee",
             "url_capture", "n_mots", "langue", "proba_langue", "statut"]
COLS_TEXTES = ["id", "annee", "type_lien", "texte_mission"]


def fetch(ts, url, essais=3):
    adresse = f"https://web.archive.org/web/{ts}id_/{url}"
    for i in range(essais):
        try:
            time.sleep(PAUSE)
            r = requests.get(adresse, headers=HEADERS, timeout=90)
            if r.status_code == 200:
                m = re.search(r"/web/(\d{14})id_/", r.url)
                return "ok", r.content, (m.group(1) if m else None), r.url
            if r.status_code in (404, 403, 410):
                return "absent", None, None, None
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(15 * (i + 1))
        except requests.RequestException:
            time.sleep(8 * (i + 1))
    return "echec", None, None, None


def extraire(contenu):
    soup = BeautifulSoup(contenu, "html.parser")
    for b in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
        b.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def langue(texte):
    if detect_langs is None or len(texte.split()) < 10:
        return "", ""
    try:
        r = detect_langs(texte[:5000])[0]
        return r.lang, round(r.prob, 2)
    except Exception:
        return "", ""


def trouver(contenu, base_url, exacts, mots, exclure=()):
    soup = BeautifulSoup(contenu, "html.parser")
    site = urlparse(base_url).netloc.lower().replace("www.", "")
    best, smax = None, 0
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        if re.search(r"\.(pdf|jpe?g|png|gif|zip|docx?|xlsx?)(\?|$)", href.lower()):
            continue
        u = urljoin(base_url, href)
        p = urlparse(u)
        if p.netloc.lower().replace("www.", "") != site:
            continue
        t = " ".join(a.get_text(" ", strip=True).lower().split())
        ch = p.path.lower()
        if any(x in t or x in ch for x in EXCLUS):
            continue
        if u in exclure:
            continue
        if t in exacts:
            s = 100
        elif any(re.search(m, t) for m in mots):
            s = 60
        elif any(re.search(m, ch) for m in mots):
            s = 30
        else:
            continue
        s -= ch.strip("/").count("/") * 2
        if s > smax:
            best, smax = u, s
    return best


def ecart_an(ts, annee):
    return ts[:4] == str(annee)


def main():
    n_max = int(sys.argv[1]) if len(sys.argv) > 1 else None
    os.makedirs(DOSSIER_HTML, exist_ok=True)
    pan = pd.read_csv(PANEL, encoding="utf-8-sig")
    ids = pan.loc[pan.eligible == 1, "id"].tolist()
    if n_max:
        ids = ids[:n_max]
    meta = pd.read_csv(META_SERV, encoding="utf-8-sig")
    meta = meta[meta.id.isin(ids) & meta.ts_accueil.notna()].copy()
    meta["ts_accueil"] = meta.ts_accueil.astype("int64").astype(str)
    meta = meta.sort_values(["id", "annee"])
    deja = set()
    if os.path.exists(FICHIER_META):
        d = pd.read_csv(FICHIER_META, encoding="utf-8-sig")
        deja = set(zip(d.id, d.annee)) if len(d) else set()
        # on retraitera seulement les echecs reseau
        ech = d[d.statut.astype(str).str.startswith("echec")]
        deja -= set(zip(ech.id, ech.annee))
    todo = [r for r in meta.itertuples() if (r.id, r.annee) not in deja]
    print(f"{len(ids)} firmes, {len(meta)} accueils archives, {len(todo)} a traiter (~{len(todo)*PAUSE*2/60:.0f} min).", flush=True)
    try:
        for k, r in enumerate(todo, 1):
            chemin = os.path.join(DOSSIER_ACC, f"{r.id}_{r.annee}_home.html")
            if not os.path.exists(chemin):
                continue
            html = open(chemin, "rb").read()
            base_url = "https://" + str(r.domaine_utilise)
            lien, typ = trouver(html, base_url, MISSION_EXACT, MISSION_MOTS), "mission"
            if not lien:
                lien, typ = trouver(html, base_url, APROPOS_EXACT, APROPOS_MOTS), "apropos_repli"
            ligne = {"id": r.id, "nom": r.nom, "annee": r.annee, "type_lien": typ if lien else "", "lien": lien,
                     "ts_accueil": r.ts_accueil}
            texte = None
            if not lien:
                ligne["statut"] = "aucun lien"
            else:
                st, h, ts, url = fetch(r.ts_accueil, lien)
                if st != "ok":
                    ligne["statut"] = "echec reseau (a relancer)" if st == "echec" else "absent"
                else:
                    ligne.update({"ts_capture": ts, "annee_capture": ts[:4] if ts else "", "url_capture": url})
                    if not ts or ts[:4] != str(r.annee):
                        ligne.update({"valide_annee": "non", "statut": "hors annee"})
                    else:
                        texte = extraire(h)
                        lg, pr = langue(texte)
                        with open(os.path.join(DOSSIER_HTML, f"{r.id}_{r.annee}_{typ}.html"), "wb") as f:
                            f.write(h)
                        ligne.update({"valide_annee": "oui", "n_mots": len(texte.split()), "langue": lg,
                                      "proba_langue": pr, "statut": "ok"})
            pd.DataFrame([ligne]).reindex(columns=COLS_META).to_csv(
                FICHIER_META, mode="a", index=False, encoding="utf-8-sig", header=not os.path.exists(FICHIER_META))
            if texte:
                pd.DataFrame([{"id": r.id, "annee": r.annee, "type_lien": typ, "texte_mission": texte}]).to_csv(
                    FICHIER_TEXTES, mode="a", index=False, encoding="utf-8-sig", header=not os.path.exists(FICHIER_TEXTES))
            if k % 25 == 0:
                print(f"  {k}/{len(todo)}", flush=True)
    except KeyboardInterrupt:
        print("\nArret demande. Relancer la meme commande pour reprendre.")
        return
    print("Termine:", FICHIER_META, "et", FICHIER_TEXTES)


if __name__ == "__main__":
    main()
