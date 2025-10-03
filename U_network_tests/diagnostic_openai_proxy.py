import ssl
import certifi
import os
import urllib.request
import socket
import traceback

def test_ssl_connection(host="api.openai.com", port=443):
    print(f"\n🔍 Test de connexion SSL à {host}:{port}")
    context = ssl.create_default_context(cafile=certifi.where())
    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                print("✅ Connexion SSL réussie. Certificat serveur :")
                print(f" - Sujet: {cert.get('subject')}")
                print(f" - Émetteur: {cert.get('issuer')}")
    except ssl.SSLError as e:
        print("❌ Échec de la connexion SSL :", e)
    except Exception:
        print("❌ Erreur générale lors de la connexion :")
        traceback.print_exc()

def test_https_request(url="https://api.openai.com/v1/models"):
    print(f"\n🌐 Test d'une requête HTTPS à {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5, context=ssl.create_default_context(cafile=certifi.where())) as response:
            print("✅ Requête HTTPS réussie :", response.status, response.reason)
    except Exception:
        print("❌ Erreur lors de la requête HTTPS :")
        traceback.print_exc()

def print_proxy_settings():
    print("\n🌐 Variables d’environnement liées aux proxys :")
    for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
        value = os.environ.get(var)
        print(f" - {var}: {value if value else '(non définie)'}")

def main():
    print("🛠️ Diagnostic de connexion OpenAI et environnement réseau\n")
    print(f"📜 Fichier de certificats utilisé par certifi : {certifi.where()}")
    print_proxy_settings()
    test_ssl_connection()
    test_https_request()

if __name__ == "__main__":
    main()
