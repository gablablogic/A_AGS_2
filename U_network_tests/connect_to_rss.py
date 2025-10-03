import os
import requests

def test_rss_connectivity(url):
    print(f"🔍 Test de connexion vers : {url}")
    print(f"➡️ Proxy HTTP  : {os.environ.get('HTTP_PROXY')}")
    print(f"➡️ Proxy HTTPS : {os.environ.get('HTTPS_PROXY')}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, timeout=10, allow_redirects=True)
        print(f"📍 URL finale : {response.url}")
        print(f"✅ Statut HTTP : {response.status_code}")
        content_type = response.headers.get("Content-Type", "")
        print(f"🧾 Content-Type : {content_type}")
        
        if "xml" in content_type or "rss" in content_type:
            print("✅ Le flux semble valide.")
        else:
            print("⚠️ Le contenu reçu n'est pas du XML (peut-être bloqué, redirigé ou remplacé).")

        # Affiche les 300 premiers caractères pour vérification
        print("\n--- Extrait du contenu ---")
        print(response.text[:300])
        print("--- (tronqué) ---")

    except requests.exceptions.ProxyError:
        print("❌ Erreur de proxy : vérifie tes variables d'environnement.")
    except requests.exceptions.SSLError as e:
        print(f"❌ Erreur SSL : {e}")
    except Exception as e:
        print(f"❌ Autre erreur : {e}")

if __name__ == "__main__":
    # À tester : Renewables Now RSS
    rss_test_url = "https://www.cre.fr/actualites/rss"
    test_rss_connectivity(rss_test_url)
