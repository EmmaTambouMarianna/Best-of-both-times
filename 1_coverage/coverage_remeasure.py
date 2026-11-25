import os
import time
import requests
import pandas as pd

# ---------- REGLAGES ----------
FICHIER_ENTREE = "to_remeasure.csv"
FICHIER_SORTIE = "coverage_remeasure.csv"
FIN = 2025
PLANCHER = 1996                      # debut de la Wayback Machine
HEADERS = {"User-Agent": "Recherche academique (contact: votre.courriel@univ.ca)"}


def nettoyer(url):
    u = url.strip().lower()
    for pref in ("https://", "http://"):
        if u.startswith(pref):
            u = u[len(pref):]
    return u.rstrip("/")


def variante_www(u):
    return u[4:] if u.startswith("www.") else "www." + u


def captures_par_mois(url, debut):
    """Une requete: premiere capture de chaque mois (depuis 'debut'), avec son statut HTTP."""
    params = {"url": url, "from": str(debut), "to": str(FIN), "output": "json",
              "fl": "timestamp,statuscode", "collapse": "timestamp:6"}
    for essai in range(4):
        try:
            time.sleep(1.0)
            r = requests.get("https://web.archive.org/cdx/search/cdx",
                             params=params, headers=HEADERS, timeout=90)
            if r.status_code == 200:
                if not r.text.strip():
                    return []
                data = r.json()
                return [(int(l[0][:4]), l[1]) for l in data[1:]]
            time.sleep(8 * (essai + 1))
        except Exception:
            time.sleep(5 * (essai + 1))
    return None   # echec de la requete


def traiter(org):
    if pd.isna(org["url_generale"]) or not str(org["url_generale"]).strip():
        return {"id": org["id"], "nom": org["nom"], "id_firme": org["id_firme"], "alertes": "url manquante"}
    url = nettoyer(str(org["url_generale"]))
    try:
        debut_firme = int(float(org["annee_debut"]))
    except Exception:
        debut_firme = PLANCHER
    debut = max(debut_firme, PLANCHER)

    url_testee = url
    caps = captures_par_mois(url_testee, debut)
    if caps == []:                                   # essai avec/sans www
        url_testee = variante_www(url)
        caps = captures_par_mois(url_testee, debut)
    echec = caps is None
    caps = caps or []

    # "-" = capture identique a une precedente: comptee comme archivee
    a200 = sorted({a for a, s in caps if s in ("200", "-")})
    a3xx = sorted({a for a, s in caps if s.startswith("3")})
    n_pot = FIN - debut + 1
    premiere = min(a200) if a200 else None
    derniere = max(a200) if a200 else None
    redir_apres = [a for a in a3xx if derniere is not None and a > derniere]

    alertes = []
    if echec:
        alertes.append("requete echouee (a relancer)")
    elif not a200:
        alertes.append("aucune capture")
    else:
        if derniere < FIN - 1:
            alertes.append("captures s'arretent tot")
        if redir_apres:
            alertes.append("redirections apres derniere capture (changement de domaine?)")
        if premiere > debut + 3:
            alertes.append("premiere capture tardive")

    return {"id": org["id"], "nom": org["nom"], "id_firme": org["id_firme"],
            "url_testee": url_testee, "annee_debut_fenetre": debut,
            "premiere_capture": premiere, "derniere_capture": derniere,
            "n_annees_archivees": len(a200), "n_annees_potentielles": n_pot,
            "taux_couverture": round(len(a200) / n_pot, 2) if n_pot > 0 else None,
            "liste_annees": ";".join(map(str, a200)),
            "annees_redirection_apres": ",".join(map(str, redir_apres)),
            "alertes": " | ".join(alertes)}


# ---------- Lecture de la liste ----------
orgs = None
for enc in ("utf-8-sig", "cp1252", "mac_roman"):
    try:
        orgs = pd.read_csv(FICHIER_ENTREE, dtype=str, encoding=enc, sep=";")
        break
    except Exception as e:
        print("Lecture impossible avec", enc, ":", e)
if orgs is None:
    raise SystemExit("Impossible de lire " + FICHIER_ENTREE)

# ---------- Reprise: on garde ce qui est deja fait ----------
resultats = []
if os.path.exists(FICHIER_SORTIE):
    try:
        ancien = pd.read_csv(FICHIER_SORTIE, dtype=str, encoding="utf-8-sig")
        ancien = ancien[~ancien["alertes"].fillna("").str.contains("echouee")]
        resultats = ancien.to_dict("records")
    except Exception:
        resultats = []
deja = {str(r["id"]) for r in resultats}
a_faire = [o for _, o in orgs.iterrows() if str(o["id"]) not in deja]
print(f"{len(deja)} lignes deja traitees, {len(a_faire)} a traiter")

# ---------- Traitement (une requete a la fois, pour limiter les echecs) ----------
for k, org in enumerate(a_faire, 1):
    try:
        res = traiter(org)
    except Exception as e:
        res = {"id": org["id"], "nom": org["nom"], "id_firme": org["id_firme"],
               "alertes": "requete echouee (a relancer): " + str(e)}
    resultats.append(res)
    print(f"{k}/{len(a_faire)} {res['nom']}: {res.get('n_annees_archivees', '-')} annees archivees")
    pd.DataFrame(resultats).to_csv(FICHIER_SORTIE, index=False, encoding="utf-8-sig")

print("Termine. Resultats dans", FICHIER_SORTIE)
