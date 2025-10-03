import requests

url = "https://www.cre.fr/actualites/rss"

headers = {
    "User-Agent": "Mozilla/5.0",  # pour simuler un navigateur classique
    "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"
}

response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)

print(f"🔍 Statut HTTP : {response.status_code}")
print(f"📍 URL demandée : {url}")
print(f"📍 URL redirigée : {response.headers.get('Location')}")
print(f"🧾 Content-Type : {response.headers.get('Content-Type')}")

print("\n--- Début du contenu brut (XML ou HTML) ---")
print(response.text[:500])
