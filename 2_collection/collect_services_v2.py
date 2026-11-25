import os
import re
import sys
import time
import threading
from datetime import datetime
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    from langdetect import detect_langs, DetectorFactory
    DetectorFactory.seed = 123456789
    LANGDETECT = True
except Exception:
    LANGDETECT = False
    print("ATTENTION: langdetect n'est pas installe (pip3 install langdetect): la colonne langue restera vide")

# ---------- REGLAGES ----------
FICHIER_ENTREE = "sample.csv"
FICHIER_META = "services_metadata.csv"
FICHIER_TEXTES = "services_texts.csv"
FICHIER_APROPOS = "about_texts.csv"
DOSSIER_HTML = "archives_services"
FIN = 2025
PLANCHER = 1996                 # debut de la Wayback Machine
PAUSE = 2.5                     # secondes entre les requetes (par fil de traitement)
TRAVAILLEURS = 1                # nombre de firmes traitees en parallele (mettre 1 si erreurs 429)
CIBLE = "0702120000"            # 2 juillet, midi (comme Haans et Mertens, 2024)
HEADERS = {"User-Agent": "Recherche academique - Emma Tambou Marianna (emmatamboumarianna@uvic.ca)"}
verrou = threading.Lock()
ARRET = threading.Event()        # active par Ctrl+C: les fils s'arretent proprement

COLONNES_META = ["id", "nom", "annee", "statut", "domaine_utilise", "ts_accueil", "ecart_jours_accueil",
                 "url_accueil_capture", "n_liens_accueil", "n_mots_accueil", "lien_services",
                 "ts_services", "annee_capture_services", "valide_annee", "ecart_jours_services",
                 "url_services_capture", "n_mots_services", "langue", "proba_langue"]
COLONNES_TEXTES = ["id", "annee", "texte_services"]
COLONNES_APROPOS = ["id", "nom", "annee_accueil", "lien_about", "ts_about", "url_about_capture", "n_mots_about", "texte_about"]

SERV_EXACT = {"services", "our services", "expertise", "our expertise", "what we do", "solutions",
              "our solutions", "capabilities", "our capabilities", "offerings", "our offerings",
              "service offerings", "how we help", "what we offer", "consulting services",
              "services & solutions", "services and solutions",
              "nos services", "notre expertise", "nos expertises", "expertises", "nos solutions",
              "notre offre", "nos prestations", "ce que nous faisons", "nos domaines d'expertise",
              "domaines d'expertise", "nos domaines d'intervention", "offre de services",
              "practice areas", "our practice areas", "practices", "our practices", "areas of expertise",
              "areas of focus", "focus areas", "specialties", "specialities", "our capabilities & expertise",
              "domaines de pratique", "champs d'expertise", "domaines de competence", "nos competences"}
SERV_CONTIENT = ["service", "expertise", "solution", "what we do", "capabilit", "offering",
                 "what we offer", "how we help", "prestation", "domaines d'intervention",
                 "ce que nous faisons", "notre offre", "nos domaines", "practice area", "areas of expertise",
                 "focus area", "areas of focus", "champs d'expertise", "competenc"]
ABOUT_EXACT = {"about", "about us", "who we are", "our company", "company", "our mission", "mission",
               "our story", "about the company", "company profile",
               "a propos", "à propos", "qui sommes-nous", "qui sommes nous", "notre entreprise",
               "notre histoire", "notre mission", "le cabinet", "presentation", "présentation"}
ABOUT_CONTIENT = ["about", "who we are", "our mission", "our company", "our story", "propos",
                  "qui sommes", "company profile", "notre histoire", "notre mission", "notre cabinet"]
EXCLUS = ["career", "carriere", "carrière", "job", "news", "blog", "contact", "login", "privacy",
          "cookie", "investor", "press", "event", "customer", "support", "legal", "sitemap",
          "actualit", "presse", "emploi", "recrut", "mentions", "confidentialit", "evenement", "événement"]


def fetch_archive(ts_cible, url, essais=3):
    """Retourne (statut, contenu, timestamp_reel, url_capture). statut: ok / absent / echec."""
    adresse = f"https://web.archive.org/web/{ts_cible}id_/{url}"
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


def ecart_jours(ts, annee):
    cible = datetime(annee, 7, 2, 12)
    return abs((datetime.strptime(ts, "%Y%m%d%H%M%S") - cible).days)


def extraire(contenu):
    soup = BeautifulSoup(contenu, "html.parser")
    for b in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
        b.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def detecter_langue(texte):
    if not LANGDETECT or len(texte.split()) < 10:
        return "", ""
    try:
        r = detect_langs(texte[:5000])[0]
        return r.lang, round(r.prob, 2)
    except Exception:
        return "", ""


def trouver_lien(contenu, base_url, exacts, contenus):
    soup = BeautifulSoup(contenu, "html.parser")
    site = urlparse(base_url).netloc.lower().replace("www.", "")
    meilleur, score_max = None, 0
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        if re.search(r"\.(pdf|jpe?g|png|gif|zip|docx?|xlsx?)(\?|$)", href.lower()):
            continue
        absu = urljoin(base_url, href)
        p = urlparse(absu)
        if p.netloc.lower().replace("www.", "") != site:
            continue
        texte = " ".join(a.get_text(" ", strip=True).lower().split())
        chemin = p.path.lower()
        if any(x in texte or x in chemin for x in EXCLUS):
            continue
        if texte in exacts:
            score = 100
        elif any(m in texte for m in contenus):
            score = 60
        elif any(m in chemin for m in contenus):
            score = 30
        else:
            continue
        score -= chemin.strip("/").count("/") * 2     # on prefere les pages peu profondes
        if score > score_max:
            meilleur, score_max = absu, score
    return meilleur


def sauver(nom_fichier, contenu):
    with open(os.path.join(DOSSIER_HTML, nom_fichier), "wb") as f:
        f.write(contenu)


def ajouter(fichier, colonnes, ligne):
    with verrou:
        pd.DataFrame([ligne]).reindex(columns=colonnes).to_csv(
            fichier, mode="a", index=False, encoding="utf-8-sig", header=not os.path.exists(fichier))


def traiter(firme, annee):
    fid = firme["id"]
    base = {"id": fid, "nom": firme["nom"], "annee": annee}
    domaines = [d.strip() for d in str(firme["domaines"]).split("|") if d.strip()]

    # 1) page d'accueil: capture la plus proche du 2 juillet, acceptee seulement si elle date de l'annee visee
    accueil, echec = None, False
    for dom in domaines:
        statut, contenu, ts, url_cap = fetch_archive(f"{annee}{CIBLE}", "https://" + dom)
        if statut == "echec":
            echec = True
        if statut == "ok" and ts and ts[:4] == str(annee):
            accueil = (dom, contenu, ts, url_cap)
            break
    if accueil is None:
        base["statut"] = "echec reseau (a relancer)" if echec else "aucune capture cette annee"
        return base, None

    dom, html_acc, ts_acc, url_acc = accueil
    base_url = "https://" + dom
    base.update({"domaine_utilise": dom, "ts_accueil": ts_acc, "ecart_jours_accueil": ecart_jours(ts_acc, annee),
                 "url_accueil_capture": url_acc})
    sauver(f"{firme['id']}_{annee}_home.html", html_acc)
    base["n_liens_accueil"] = len(BeautifulSoup(html_acc, "html.parser").find_all("a"))
    base["n_mots_accueil"] = len(extraire(html_acc).split())

    # 2) page de services (lien detecte sur l'accueil). Valide seulement si capturee la meme annee.
    lien = trouver_lien(html_acc, base_url, SERV_EXACT, SERV_CONTIENT)
    base["lien_services"] = lien
    if not lien:
        base["statut"] = "accueil seulement"
        return base, None
    st, html_s, ts_s, url_s = fetch_archive(ts_acc, lien)
    if st != "ok":
        base["statut"] = "echec reseau (a relancer)" if st == "echec" else "accueil seulement"
        return base, None
    base.update({"ts_services": ts_s, "annee_capture_services": ts_s[:4] if ts_s else None,
                 "ecart_jours_services": ecart_jours(ts_s, annee) if ts_s else None, "url_services_capture": url_s})
    if not ts_s or ts_s[:4] != str(annee):
        base["valide_annee"] = "non"
        base["statut"] = "services hors annee"         # page d'une autre annee: non utilisee
        return base, None
    texte = extraire(html_s)
    langue, proba = detecter_langue(texte)
    sauver(f"{fid}_{annee}_services.html", html_s)
    base.update({"valide_annee": "oui", "n_mots_services": len(texte.split()), "langue": langue, "proba_langue": proba,
                 "statut": "ok services"})
    return base, {"id": fid, "annee": annee, "texte_services": texte}


def apropos_une_fois(firme):
    """Page 'a propos' recuperee une seule fois par firme (annee la plus recente disponible)."""
    with verrou:
        if os.path.exists(FICHIER_APROPOS):
            if str(firme["id"]) in set(pd.read_csv(FICHIER_APROPOS, dtype=str, encoding="utf-8-sig")["id"]):
                return
        if not os.path.exists(FICHIER_META):
            return
        meta = pd.read_csv(FICHIER_META, dtype=str, encoding="utf-8-sig")
    m = meta[(meta["id"].astype(str) == str(firme["id"])) & meta["domaine_utilise"].notna()]
    for _, r in m.sort_values("annee", ascending=False).head(3).iterrows():
        chemin = os.path.join(DOSSIER_HTML, f"{firme['id']}_{r['annee']}_home.html")
        if not os.path.exists(chemin):
            continue
        html = open(chemin, "rb").read()
        lien = trouver_lien(html, "https://" + r["domaine_utilise"], ABOUT_EXACT, ABOUT_CONTIENT)
        if not lien:
            continue
        st, h, ts, url = fetch_archive(r["ts_accueil"], lien)
        if st == "ok":
            texte = extraire(h)
            ajouter(FICHIER_APROPOS, COLONNES_APROPOS, {
                "id": firme["id"], "nom": firme["nom"], "annee_accueil": r["annee"], "lien_about": lien,
                "ts_about": ts, "url_about_capture": url, "n_mots_about": len(texte.split()), "texte_about": texte})
            return


def traiter_firme(f, deja):
    debut = max(int(float(f["annee_debut"])), PLANCHER, int(float(f["premiere_capture"])))
    fin = min(FIN, int(float(f["derniere_capture"])))
    print(f"=== {f['nom']} ({debut}-{fin}) ===", flush=True)
    for annee in range(debut, fin + 1):
        if ARRET.is_set():
            return
        if f"{f['id']}_{annee}" in deja:
            continue
        try:
            ligne, textes = traiter(f, annee)
        except Exception as e:
            ligne, textes = {"id": f["id"], "nom": f["nom"], "annee": annee,
                             "statut": "echec reseau (a relancer): " + str(e)}, None
        ajouter(FICHIER_META, COLONNES_META, ligne)
        if textes:
            ajouter(FICHIER_TEXTES, COLONNES_TEXTES, textes)
        print(f"  {f['nom']} {annee}: {ligne['statut']}", flush=True)
    try:
        apropos_une_fois(f)
    except Exception as e:
        print("  (page a propos non recuperee:", e, ")", flush=True)


# ---------- PROGRAMME ----------
if __name__ == "__main__":
    firmes = pd.read_csv(FICHIER_ENTREE, sep=";", dtype=str, encoding="utf-8-sig")
    if len(sys.argv) > 1:
        firmes = firmes.head(int(sys.argv[1]))      # ex.: python3 collect_services_v2.py 2  (test sur 2 firmes)
    os.makedirs(DOSSIER_HTML, exist_ok=True)

    # Reprise: on retire les lignes echouees, on garde le reste
    deja = set()
    if os.path.exists(FICHIER_META):
        meta = pd.read_csv(FICHIER_META, dtype=str, encoding="utf-8-sig")
        ok = ~meta["statut"].fillna("").str.contains("echec")
        echoues = set(meta[~ok][["id", "annee"]].astype(str).agg("_".join, axis=1))
        meta[ok].to_csv(FICHIER_META, index=False, encoding="utf-8-sig")
        if os.path.exists(FICHIER_TEXTES):
            tx = pd.read_csv(FICHIER_TEXTES, dtype=str, encoding="utf-8-sig")
            tx = tx[~tx[["id", "annee"]].astype(str).agg("_".join, axis=1).isin(echoues)]
            tx.to_csv(FICHIER_TEXTES, index=False, encoding="utf-8-sig")
        deja = set(meta[ok][["id", "annee"]].astype(str).agg("_".join, axis=1))
    print(f"{len(deja)} firmes-annees deja traitees; {len(firmes)} firmes dans la liste; {TRAVAILLEURS} en parallele")

    ex = ThreadPoolExecutor(max_workers=TRAVAILLEURS)
    futurs = [ex.submit(traiter_firme, f, deja) for _, f in firmes.iterrows()]
    try:
        for fu in futurs:
            fu.result()
    except KeyboardInterrupt:
        print("\nArret demande: fin de l'annee en cours, puis arret (la reprise sera automatique)...", flush=True)
        ARRET.set()
        ex.shutdown(wait=True, cancel_futures=True)
        sys.exit(0)
    ex.shutdown()
    print("Termine. Resultats dans", FICHIER_META, ",", FICHIER_TEXTES, "et", FICHIER_APROPOS)
