# gaz_ore_tool.py
# Script autonome : une fonction "Tool" compatible AutogenStudio 0.4.2 + une main() pour tests locaux.
# Tous les imports utiles au tool sont faits *dans* la fonction (compatibilité outils "one-function").

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
    api_key: str = None,  # <— clé API Opendatasoft (optionnelle, pour quotas étendus / jeux restreints)
):
    """
    Interroge l’API Opendatasoft (Agence ORE) du dataset
    'consommation-annuelle-d-electricite-et-gaz-par-commune' en filtrant filiere=Gaz.

    Conçu pour AutogenStudio v0.4.x comme "Python Tool" :
    - Tous les imports sont locaux à la fonction.
    - Les paramètres sont simples (str/int/bool).
    - Retourne un dict JSON-serializable.

    Params (tous optionnels sauf rows/start/timeout) :
      - nom_commune                -> refine.nom_commune
      - code_insee_commune         -> refine.(code_commune_insee | code_insee_commune | code_commune) (fallback)
      - nom_departement            -> refine.nom_departement
      - nom_region                 -> refine.nom_region
      - annee                      -> refine.annee
      - code_naf                   -> refine.code_naf
      - categorie_consommation     -> refine.categorie_consommation
      - rows, start, timeout, debug, api_key

    Sortie (dict) :
      - query   : récapitulatif des filtres
      - nhits   : total des enregistrements correspondant sur le portail
      - count   : nb d’enregistrements renvoyés dans cette page
      - records : liste d’enregistrements simplifiés (id, timestamp, fields, geometry)
      - facets  : facettes si présentes
      - source  : métadonnées
      - http    : (debug=True) URL finale, status, content-type

    Remarques :
      - L’API utilisée est Records v1: /api/records/1.0/search/?dataset=...&refine.<champ>=...
      - Le nom du champ INSEE varie parfois ; cette fonction essaie plusieurs variantes.
      - L’api_key est facultative pour les jeux publics ; utile pour quotas/jeux privés.
    """
    # Imports locaux
    import json
    import time
    import urllib.parse
    from typing import Any, Dict

    try:
        import requests
    except Exception as e:
        raise RuntimeError(
            "Le module 'requests' est requis. Installez-le (pip install requests) avant d'utiliser ce tool."
        ) from e

    BASE_URL = "https://opendata.agenceore.fr/api/records/1.0/search/"
    DATASET_ID = "consommation-annuelle-d-electricite-et-gaz-par-commune"

    # Paramètres communs
    params: Dict[str, Any] = {
        "dataset": DATASET_ID,
        "rows": int(rows),
        "start": int(start),
    }

    # Filtres refine.* — on force Gaz
    params["refine.filiere"] = "Gaz"
    if nom_commune:
        params["refine.nom_commune"] = nom_commune
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

    # En-têtes HTTP (clé API facultative)
    headers: Dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Apikey {api_key}"

    # Helper HTTP avec retries
    def _http_get(url: str, params: Dict[str, Any], timeout: int, headers: Dict[str, str]) -> requests.Response:
        backoffs = [0.5, 1.0, 2.0]
        last_exc = None
        for delay in [0.0] + backoffs:
            if delay:
                time.sleep(delay)
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=timeout)
                if resp.status_code >= 500:
                    last_exc = RuntimeError(f"HTTP {resp.status_code} serveur")
                    continue
                return resp
            except Exception as e:
                last_exc = e
                continue
        if isinstance(last_exc, Exception):
            raise last_exc
        raise RuntimeError("Échec HTTP inconnu")

    # Exécution avec ou sans fallback INSEE
    data = None
    resp = None
    used_params = dict(params)  # pour debug/url finale

    if code_insee_commune:
        # Essayer plusieurs champs INSEE possibles
        insee_candidates = [
            "code_commune_insee",  # le plus courant
            "code_insee_commune",  # variante
            "code_commune"         # fallback ultime
        ]

        found = False
        for fld in insee_candidates:
            try_params = dict(params)
            try_params[f"refine.{fld}"] = code_insee_commune

            resp_try = _http_get(BASE_URL, try_params, timeout, headers)
            content_type_try = resp_try.headers.get("Content-Type", "")
            try:
                data_try = resp_try.json()
            except Exception:
                # Réponse non JSON : on passe au suivant
                continue

            nhits_try = int(data_try.get("nhits", 0))
            if resp_try.status_code == 200 and nhits_try > 0:
                # Bingo : on adopte cette variante
                resp = resp_try
                data = data_try
                used_params = try_params
                found = True
                break

        if not found:
            # Aucun champ n'a donné de résultats — on le signale clairement
            final_url = BASE_URL + "?" + urllib.parse.urlencode({**params, "TESTED_INSEE": code_insee_commune}, doseq=True)
            raise RuntimeError(
                f"Aucun résultat pour le code INSEE '{code_insee_commune}' avec les champs testés "
                f"{insee_candidates}. Vérifiez le code/millésime. URL (sans champ INSEE) pour debug : {final_url}"
            )
    else:
        # Chemin standard (pas de code INSEE)
        resp = _http_get(BASE_URL, params, timeout, headers)
        try:
            data = resp.json()
        except Exception:
            ct = resp.headers.get("Content-Type", "")
            raise RuntimeError(f"Réponse non-JSON de l'API (status={resp.status_code}, content-type={ct})")

    # Contrôle status
    if resp.status_code != 200:
        raise RuntimeError(f"Erreur API {resp.status_code}: {json.dumps(data, ensure_ascii=False)}")

    # Normalisation
    nhits = int(data.get("nhits", 0))
    records = data.get("records", []) or []
    facets = data.get("facet_groups", None)

    simplified = []
    for rec in records:
        simplified.append({
            "id": rec.get("recordid"),
            "timestamp": rec.get("record_timestamp"),
            "fields": rec.get("fields", {}),
            "geometry": rec.get("geometry"),
        })

    final_url = BASE_URL + "?" + urllib.parse.urlencode(used_params, doseq=True)
    content_type = resp.headers.get("Content-Type", "")

    result = {
        "query": {
            "dataset": DATASET_ID,
            "filters": {k: v for k, v in used_params.items() if k.startswith("refine.")},
            "rows": used_params.get("rows"),
            "start": used_params.get("start"),
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
            "content_type": content_type,
            "auth": "apikey" if api_key else "anonymous"
        }

    return result


def main():
    """Exécution locale en CLI pour tests rapides (VS Code / terminal)."""
    import json
    import argparse
    import os

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
    parser.add_argument("--api-key", dest="api_key", type=str, help="Clé API Opendatasoft (si nécessaire)")

    args = parser.parse_args()
    api_key = args.api_key or os.getenv("ODS_API_KEY")  # possibilité de passer la clé par variable d'env

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
        debug=args.debug,
        api_key=api_key,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
