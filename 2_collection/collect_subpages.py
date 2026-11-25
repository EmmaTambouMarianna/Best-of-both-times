import os
import re
import sys
import time
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode

import pandas as pd
import requests
from bs4 import BeautifulSoup

# ---------- REGLAGES ----------
META_ENTREE = "services_metadata.csv"      # resultats de la collecte principale
DOSSIER_HTML = "archives_services"            # pages-pivots deja telechargees
FICHIER_META = "subpages_metadata.csv"
FICHIER_TEXTES = "subpages_texts.csv"
DOSSIER_SOUS = "archives_subpages"
MAX_SOUS_PAGES = 10                           # nombre maximal de sous-pages par page-pivot
PAUSE = 3.0
ANNEES_DEFAUT = [2000, 2005, 2010, 2015, 2020, 2025]
HEADERS = {"User-Agent": "Recherche academique Emma Tambou Marianna (contact: emmatamboumarianna@uvic.ca)"}
PARAMS_SUIVI = ("icid", "utm_", "cid", "ref", "fbclid", "gclid", "mc_", "trk")
EXCLUS = ["career", "carriere", "carrière", "job", "news", "blog", "contact", "login", "privacy",
          "cookie", "investor", "press", "event", "customer-support", "legal", "sitemap",
          "actualit", "presse", "emploi", "recrut", "mentions", "confidentialit"]
COLONNES_META = ["id", "nom", "annee", "url_pivot", "n_candidates", "n_collectees", "n_hors_annee",
                 "menus_utilises", "n_mots_pivot", "n_mots_sous_pages", "statut"]
COLONNES_TEXTES = ["id", "nom", "annee", "url_sous_page", "ts", "n_mots", "texte"]


def fetch_archive(ts_cible, url, essais=3):
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


def extraire(contenu):
    soup = BeautifulSoup(contenu, "html.parser")
    for b in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
        b.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def nettoyer_url(u):
    """Retire le fragment (#...) et les parametres de suivi (icid, utm_...)."""
    p = urlparse(u)
    q = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith(PARAMS_SUIVI)]
    return urlunparse(p._replace(fragment="", query=urlencode(q)))


def sous_pages(contenu, url_pivot, inclure_menus=False):
    """Liens situes sous l'adresse de la page-pivot (ex.: /services.html -> /services/...)."""
    soup = BeautifulSoup(contenu, "html.parser")
    if not inclure_menus:
        for b in soup(["header", "nav", "footer"]):
            b.decompose()
    for b in soup(["script", "style", "noscript"]):
        b.decompose()
    p_pivot = urlparse(url_pivot)
    site = p_pivot.netloc.lower().replace("www.", "")
    souche = re.sub(r"\.(html?|php|aspx?)$", "", p_pivot.path).rstrip("/").lower()
    # page d'index (ex.: /Services/index.htm) -> les sous-pages sont dans le dossier parent
    if souche.rsplit("/", 1)[-1] in ("index", "default", "home", "main"):
        souche = souche.rsplit("/", 1)[0]
    if souche in ("", "/"):
        return []
    vus, res = set(), []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        if re.search(r"\.(pdf|jpe?g|png|gif|zip|docx?|xlsx?)(\?|$)", href.lower()):
            continue
        u = urlparse(nettoyer_url(urljoin(url_pivot, href)))
        if u.netloc.lower().replace("www.", "") != site:
            continue
        chemin = u.path.rstrip("/")
        if not chemin.lower().startswith(souche + "/"):
            continue
        if chemin.lower() == p_pivot.path.rstrip("/").lower():   # la page-pivot elle-meme
            continue
        texte = " ".join(a.get_text(" ", strip=True).lower().split())
        if any(x in chemin.lower() or x in texte for x in EXCLUS):
            continue
        if chemin in vus:
            continue
        vus.add(chemin)
        res.append(urlunparse(u))
    return res


def ajouter(fichier, colonnes, ligne):
    pd.DataFrame([ligne]).reindex(columns=colonnes).to_csv(
        fichier, mode="a", index=False, encoding="utf-8-sig", header=not os.path.exists(fichier))


# ---------- PROGRAMME ----------
if __name__ == "__main__":
    # Usage: python3 collect_subpages.py Deloitte 2005,2010,2015,2020,2025
    #        python3 collect_subpages.py tous 2010,2020
    cible = sys.argv[1] if len(sys.argv) > 1 else "tous"
    annees = [int(a) for a in sys.argv[2].split(",")] if len(sys.argv) > 2 else ANNEES_DEFAUT

    meta = pd.read_csv(META_ENTREE, dtype=str, encoding="utf-8-sig")
    meta = meta[(meta["statut"] == "ok services") & (meta["valide_annee"] == "oui")].copy()
    meta["annee_i"] = meta["annee"].astype(int)
    meta = meta[meta["annee_i"].isin(annees)]
    if cible != "tous":
        meta = meta[meta["nom"] == cible]
    os.makedirs(DOSSIER_SOUS, exist_ok=True)

    deja = set()
    if os.path.exists(FICHIER_META):
        d = pd.read_csv(FICHIER_META, dtype=str, encoding="utf-8-sig")
        deja = set(d[~d["statut"].fillna("").str.contains("echec")][["id", "annee"]].astype(str).agg("_".join, axis=1))
    print(f"{len(meta)} pages-pivots a approfondir; {len(deja)} deja traitees")

    for _, r in meta.sort_values(["id", "annee_i"]).iterrows():
        cle = f"{r['id']}_{r['annee']}"
        if cle in deja:
            continue
        chemin = os.path.join(DOSSIER_HTML, f"{r['id']}_{r['annee']}_services.html")
        ligne = {"id": r["id"], "nom": r["nom"], "annee": r["annee"], "url_pivot": r["lien_services"]}
        if not os.path.exists(chemin):
            ligne["statut"] = "page-pivot introuvable sur disque"
            ajouter(FICHIER_META, COLONNES_META, ligne)
            continue
        html = open(chemin, "rb").read()
        ligne["n_mots_pivot"] = len(extraire(html).split())
        cands = sous_pages(html, r["lien_services"])
        menus = False
        if len(cands) < 2:                              # pas de liens dans le corps: on regarde les menus
            cands = sous_pages(html, r["lien_services"], inclure_menus=True)
            menus = True
        ligne.update({"n_candidates": len(cands), "menus_utilises": "oui" if menus else "non"})
        collectees, hors, echec, mots = 0, 0, False, 0
        for k, url in enumerate(cands[:MAX_SOUS_PAGES], 1):
            st, contenu, ts, url_cap = fetch_archive(r["ts_services"], url)
            if st == "echec":
                echec = True
                continue
            if st != "ok":
                continue
            if not ts or ts[:4] != str(r["annee"]):      # meme regle: capture de l'annee visee seulement
                hors += 1
                continue
            texte = extraire(contenu)
            open(os.path.join(DOSSIER_SOUS, f"{r['id']}_{r['annee']}_{k}.html"), "wb").write(contenu)
            ajouter(FICHIER_TEXTES, COLONNES_TEXTES, {"id": r["id"], "nom": r["nom"], "annee": r["annee"],
                                                      "url_sous_page": url_cap, "ts": ts,
                                                      "n_mots": len(texte.split()), "texte": texte})
            collectees += 1
            mots += len(texte.split())
        ligne.update({"n_collectees": collectees, "n_hors_annee": hors, "n_mots_sous_pages": mots,
                      "statut": "echec reseau (a relancer)" if echec else "ok"})
        ajouter(FICHIER_META, COLONNES_META, ligne)
        print(f"  {r['nom']} {r['annee']}: {len(cands)} sous-pages candidates, {collectees} collectees "
              f"({hors} hors annee), {mots} mots (pivot: {ligne['n_mots_pivot']} mots)", flush=True)
    print("Termine. Resultats dans", FICHIER_META, "et", FICHIER_TEXTES)
