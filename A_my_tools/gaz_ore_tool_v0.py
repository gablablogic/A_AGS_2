# gaz_ore_tool.py
# Script autonome : une fonction "Tool" compatible AutogenStudio 0.4.2 + une main() pour tests locaux.
# Aucun import global : tous les imports sont dans les fonctions (conforme aux contraintes de certains "Python tools").

def consommation_annuelle_gaz_tool(
    nom_commune: str = None,
    code_insee_commune: str = None,
    nom_departement: str = None,
    nom_region: str = None,
    annee: int = None,
    code_naf: str = None,
    categorie_consommation: str = None,
    rows: int = 100,
    start: int = 0,
    timeout: int = 20,
    debug: bool = False,
    api_key: str = None
):
    """
    Interroge l'API Opendatasoft Agence ORE pour la "Consommation annuelle d'électricité 
    et gaz par commune",
    filtrée sur la filière Gaz, et renvoie un objet JSON-serializable (dict).

    Conçu pour être utilisé comme "Python Tool" (AutogenStudio v0.4.x) :
    - Tous les imports sont locaux à la fonction.
    - L'appelant peut passer des filtres par arguments simples.

    Paramètres (tous optionnels sauf rows/start/timeout) :
      - nom_commune: str                   -> applique refine.nom_commune
      - code_insee_commune: str            -> applique refine.code_insee_commune (si le champ exact diffère, l'API l'ignorera)
      - nom_departement: str               -> applique refine.nom_departement
      - nom_region: str                    -> applique refine.nom_region
      - annee: int                         -> applique refine.annee
      - code_naf: str                      -> applique refine.code_naf
      - categorie_consommation: str        -> applique refine.categorie_consommation
      - rows: int                          -> nombre de lignes renvoyées (maxi pratique ~10k, selon portail)
      - start: int                         -> décalage (pagination)
      - timeout: int                       -> timeout HTTP (secondes)
      - debug: bool                        -> si True, renvoie des infos supplémentaires (URL finale)

    Retour:
      dict avec les clés:
        - "query": récap paramètres envoyés
        - "nhits": total de résultats sur le portail
        - "count": nombre d’enregistrements dans cette page
        - "records": liste d’enregistrements simplifiés (id, fields, geometry, etc.)
        - "facets": si présents dans la réponse
        - "source": métadonnées sur la source utilisée
        - "http": infos de requête si debug=True

    Remarques:
      - Les noms de champs "refine.*" correspondent aux colonnes du dataset ORE.
        Les plus courants: filiere, annee, nom_commune, nom_departement, nom_region, code_naf, categorie_consommation.
      - L’API Records v1: /api/records/1.0/search/?dataset=...&refine.<champ>=...
    """
    # Imports locaux (compatibilité "tool" AutogenStudio)
    import json
    import time
    import urllib.parse
    from typing import Any, Dict, List, Optional

    try:
        import requests
    except Exception as e:
        # Cas rare: si AutogenStudio exécute dans un env minimal sans requests
        raise RuntimeError(
            "Le module 'requests' est requis. Installez-le (pip install requests) avant d'utiliser ce tool."
        ) from e

    BASE_URL = "https://opendata.agenceore.fr/api/records/1.0/search/"
    DATASET_ID = "consommation-annuelle-d-electricite-et-gaz-par-commune"

    # Construction des paramètres
    # NB: On force filiere=Gaz
    params: Dict[str, Any] = {
        "dataset": DATASET_ID,
        "rows": int(rows),
        "start": int(start),
        # Vous pouvez ajouter des "facet" si besoin, ex.: "facet": ["annee", "nom_commune"]
    }

    # Filtres "refine.*"
    params["refine.filiere"] = "Gaz"  # obligatoire pour la demande

    if nom_commune:
        params["refine.nom_commune"] = nom_commune
    if code_insee_commune:
        # Selon le portail, le champ peut être "code_insee_commune" ou "code_commune_insee".
        # On tente d'abord "code_insee_commune".
        params["refine.code_insee_commune"] = code_insee_commune
    if nom_departement:
        params["refine.nom_departement"] = nom_departement
    if nom_region:
        params["refine.nom_region"] = nom_region
    if annee is not None:
        params["refine.annee"] = str(annee)
    if code_naf:
        params["refine.code_naf"] = code_naf
    if categorie_consommation:
        params["refine.categorie_consommation"] = categorie_consommation

    # Petite fonction de requête avec retry simple (backoff 0.5s, 1s, 2s)
    def _http_get(url: str, params: Dict[str, Any], timeout: int) -> requests.Response:
        backoffs = [0.5, 1.0, 2.0]
        last_exc = None
        for i, delay in enumerate([0.0] + backoffs):
            if delay:
                time.sleep(delay)
            try:
                resp = requests.get(url, params=params, timeout=timeout)
                if resp.status_code >= 500:
                    last_exc = RuntimeError(f"HTTP {resp.status_code} serveur")
                    continue
                return resp
            except Exception as e:
                last_exc = e
                continue
        # si on arrive ici, tous les essais ont échoué
        if isinstance(last_exc, Exception):
            raise last_exc
        raise RuntimeError("Échec HTTP inconnu")

    # Appel API
    resp = _http_get(BASE_URL, params, timeout)
    content_type = resp.headers.get("Content-Type", "")
    try:
        data = resp.json()
    except Exception:
        # cas CSV/texte inattendu
        raise RuntimeError(
            f"Réponse non-JSON de l'API (status={resp.status_code}, content-type={content_type})"
        )

    if resp.status_code != 200:
        # L’API renvoie souvent un JSON d'erreur descriptif
        raise RuntimeError(
            f"Erreur API {resp.status_code}: {json.dumps(data, ensure_ascii=False)}"
        )

    # Normalisation de la sortie
    nhits = int(data.get("nhits", 0))
    records = data.get("records", []) or []
    facets = data.get("facet_groups", None)

    # On simplifie chaque record
    simplified = []
    for rec in records:
        simplified.append({
            "id": rec.get("recordid"),
            "timestamp": rec.get("record_timestamp"),
            "fields": rec.get("fields", {}),
            "geometry": rec.get("geometry"),
        })

    # URL finale pour debug
    final_url = BASE_URL + "?" + urllib.parse.urlencode(params, doseq=True)

    result = {
        "query": {
            "dataset": DATASET_ID,
            "filters": {k: v for k, v in params.items() if k.startswith("refine.")},
            "rows": params["rows"],
            "start": params["start"],
        },
        "nhits": nhits,
        "count": len(simplified),
        "records": simplified,
        "facets": facets,
        "source": {
            "portal": "opendata.agenceore.fr",
            "api": "/api/records/1.0/search/",
            "dataset_identifier": DATASET_ID,
            "license": "Voir conditions d'utilisation sur le portail",
        },
    }

    if debug:
        result["http"] = {
            "final_url": final_url,
            "status_code": resp.status_code,
            "content_type": content_type
        }

    return result


def main():
    """Exécution locale en CLI pour tests rapides (VS Code / terminal)."""
    import json
    import argparse

    parser = argparse.ArgumentParser(
        description="Test local - consommation_annuelle_gaz_tool (Agence ORE / Opendatasoft)"
    )
    parser.add_argument("--commune", dest="nom_commune", type=str, help="Nom de la commune (ex: Paris)")
    parser.add_argument("--insee", dest="code_insee_commune", type=str, help="Code INSEE commune (ex: 75056)")
    parser.add_argument("--departement", dest="nom_departement", type=str, help="Nom du département (ex: Gironde)")
    parser.add_argument("--region", dest="nom_region", type=str, help="Nom de la région (ex: Île-de-France)")
    parser.add_argument("--annee", dest="annee", type=int, help="Année ex: 2023")
    parser.add_argument("--naf", dest="code_naf", type=str, help="Code NAF")
    parser.add_argument("--categorie", dest="categorie_consommation", type=str, help="Catégorie de consommation")
    parser.add_argument("--rows", type=int, default=10, help="Nombre de lignes")
    parser.add_argument("--start", type=int, default=0, help="Décalage (pagination)")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout HTTP (s)")
    parser.add_argument("--debug", action="store_true", help="Afficher l'URL finale et le statut HTTP")

    args = parser.parse_args()

    print("le code insee passé en argument au tool est "+ args.code_insee_commune)

    result = consommation_annuelle_gaz_tool(
        nom_commune=args.nom_commune,
        code_insee_commune=args.code_insee_commune,
        nom_departement=args.nom_departement,
        nom_region=args.nom_region,
        annee=args.annee,
        code_naf=args.code_naf,
        categorie_consommation=args.categorie_consommation,
        rows=args.rows,
        start=args.start,
        timeout=args.timeout,
        debug=args.debug
    )


    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
