import os
import sys
import requests
import certifi

# Essayons d'importer certifi_win32 si présent
try:
    import certifi_win32
    HAS_CERTIFI_WIN32 = True
except ImportError:
    HAS_CERTIFI_WIN32 = False

# === Configuration ===
OPENAI_URL = "https://api.openai.com/v1/models"
API_KEY = os.getenv("OPENAI_API_KEY")  
ZSCALER_CERT_PATH = "./BK/250921_certif_Zscaler.cer"  # Facultatif. À fournir si vous avez exporté un certificat manuellement.

# === Headers ===
HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

def test_with_certifi():
    print("\n[1] Test avec certifi standard...")
    try:
        r = requests.get(OPENAI_URL, headers=HEADERS, timeout=10, verify=certifi.where())
        print(f"✅ Réponse {r.status_code} OK via certifi\n")
    except Exception as e:
        print(f"❌ Échec avec certifi : {e}")

def test_with_custom_cert():
    if not os.path.exists(ZSCALER_CERT_PATH):
        print(f"\n[2] Certificat Zscaler non trouvé ({ZSCALER_CERT_PATH}), test ignoré.")
        return
    print("\n[2] Test avec certifi + certificat Zscaler fusionné...")
    import tempfile

    # Crée un bundle temporaire
    with open(certifi.where(), "rb") as base, open(ZSCALER_CERT_PATH, "rb") as extra, tempfile.NamedTemporaryFile(delete=False, mode='wb') as merged:
        merged.write(base.read())
        merged.write(b"\n")
        merged.write(extra.read())
        merged_path = merged.name

    try:
        r = requests.get(OPENAI_URL, headers=HEADERS, timeout=10, verify=merged_path)
        print(f"✅ Réponse {r.status_code} OK avec certifi + Zscaler cert\n")
    except Exception as e:
        print(f"❌ Échec avec certifi + Zscaler : {e}")
    finally:
        os.unlink(merged_path)

def test_with_certifi_win32():
    if not HAS_CERTIFI_WIN32:
        print("\n[3] certifi_win32 non installé, test ignoré.")
        return
    print("\n[3] Test avec certifi_win32 (store Windows)...")
    try:
        r = requests.get(OPENAI_URL, headers=HEADERS, timeout=10, verify=certifi_win32.where())
        print(f"✅ Réponse {r.status_code} OK via certifi_win32\n")
    except Exception as e:
        print(f"❌ Échec avec certifi_win32 : {e}")

def main():
    print("== Test de connectivité OpenAI avec différents certificats SSL ==\n")
    test_with_certifi()
    test_with_custom_cert()
    test_with_certifi_win32()
    print("\n== Fin du test ==")

if __name__ == "__main__":
    main()
