import os
import time
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

FICHIER_ENTREE = "coverage_list.csv"
FICHIER_SORTIE = "coverage_wayback.csv"
DEBUT, FIN = 1996, 2025
TRAVAILLEURS = 1
HEADERS = {"User-Agent": "Recherche academique (contact: votre.courriel@univ.ca)"}

def nettoyer(url):
    u = url.strip().lower()
    for pref in ("https://", "http://"):
        if u.startswith(pref):
            u = u[len(pref):]
    return u.rstrip("/")

def variante_www(u):
    return u[4:] if u.startswith("www.") else "www." + u

def captures_par_mois(url):
    """Une requête: première capture de chaque mois, avec son statut HTTP."""
    params = {"url": url, "from": str(DEBUT), "to": str(FIN), "output": "json",
              "fl": "timestamp,statuscode", "collapse": "timestamp:6"}
    for essai in range(3):
        try:
            time.sleep(0.5)
            r = requests.get("https://web.archive.org/cdx/search/cdx",
                             params=params, headers=HEADERS, timeout=45)
            if r.status_code == 200:
                if not r.text.strip():
                    return []
                data = r.json()
                return [(int(l[0][:4]), l[1]) for l in data[1:]]
            time.sleep(5 * (essai + 1))
        except Exception:
            time.sleep(3 * (essai + 1))
    return None

def traiter(org):
    try:
        if pd.isna(org["url_generale"]) or not str(org["url_generale"]).strip():
            return {"id": org["id"], "nom": org["nom"], "alertes": "url manquante"}
        url = nettoyer(str(org["url_generale"]))
        try:
            debut_firme = int(float(org["annee_debut"]))
        except Exception:
            debut_firme = DEBUT
        debut_obs = max(debut_firme, DEBUT)

        url_testee = url
        caps = captures_par_mois(url_testee)
        if caps == []:                      # aucune capture: essai avec/sans www
            url_testee = variante_www(url)
            caps = captures_par_mois(url_testee)
        echec = caps is None
        caps = caps or []

        # "-" = capture identique à une précédente (comptée comme archivée)
        a200 = sorted({a for a, s in caps if s in ("200", "-")})
        a3xx = sorted({a for a, s in caps if s.startswith("3")})
        n_pot = FIN - debut_obs + 1
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
            if premiere > debut_obs + 3:
                alertes.append("premiere capture tardive")

        return {"id": org["id"], "nom": org["nom"], "url_testee": url_testee,
                "annee_debut": debut_firme, "premiere_capture": premiere,
                "derniere_capture": derniere, "n_annees_archivees": len(a200),
                "n_annees_potentielles": n_pot,
                "taux_couverture": round(len(a200) / n_pot, 2) if n_pot > 0 else None,
                "annees_redirection_apres": ",".join(map(str, redir_apres)),
                "alertes": " | ".join(alertes)}
    except Exception as e:
        return {"id": org["id"], "nom": org["nom"], "alertes": "requete echouee (a relancer): " + str(e)}

# ---------- Lecture du fichier ----------
orgs = None
for enc in ("utf-8-sig", "cp1252", "mac_roman"):
    try:
        orgs = pd.read_csv(FICHIER_ENTREE, dtype=str, encoding=enc, sep=";", engine="python")
        break
    except Exception:
        continue
orgs.columns = ["id", "nom", "url_generale", "annee_debut"] + list(orgs.columns[4:])

# ---------- Reprise: on garde ce qui est déjà fait ----------
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
print(f"{len(deja)} firmes déjà traitées, {len(a_faire)} à traiter")

# ---------- Traitement en parallèle ----------
fait = 0
with ThreadPoolExecutor(max_workers=TRAVAILLEURS) as ex:
    futurs = [ex.submit(traiter, o) for o in a_faire]
    for f in as_completed(futurs):
        res = f.result()
        resultats.append(res)
        fait += 1
        print(f"{fait}/{len(a_faire)} {res['nom']}: {res.get('n_annees_archivees', '-')} années archivées")
        pd.DataFrame(resultats).to_csv(FICHIER_SORTIE, index=False, encoding="utf-8-sig")

print("Terminé. Résultats dans", FICHIER_SORTIE)
