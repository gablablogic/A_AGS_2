# cre_rss_tool.py

try:
    from promptflow import tool
except ImportError:
    # Pour test local si promptflow n'est pas installé
    def tool(func):
        return func

@tool
def cre_rss_tool() -> list:
    """
    Tool compatible AutogenStudio v0.4.2.
    Récupère les dernières actualités depuis le flux RSS de la CRE (Commission de Régulation de l'Énergie).
    Retourne une liste de dictionnaires contenant : titre, lien, date.
    """

    # ----- IMPORTS INTERNES -----
    import feedparser  # pip install feedparser
    from datetime import datetime

    # ----- URL DU FLUX RSS DE LA CRE -----
    rss_url = "https://renewablesnow.com/feed/"

    # ----- PARSING DU FLUX RSS -----
    feed = feedparser.parse(rss_url)

    if feed.bozo:
        # Affiche l'erreur mais ne bloque pas
        print(f"[AVERTISSEMENT] Flux partiellement invalide : {feed.bozo_exception}")
   

    results = []
    for entry in feed.entries:
        results.append({
            "title": entry.get("title", "Titre inconnu"),
            "link": entry.get("link", "Lien manquant"),
            "published": entry.get("published", "Date inconnue")
        })



# ----- TEST LOCAL -----
if __name__ == "__main__":
    print("Test local du Tool AutogenStudio — Flux RSS CRE\n")
    entries = cre_rss_tool()
    for i, item in enumerate(entries[:5], 1):
        print(f"{i}. {item['title']}")
        print(f"   {item['link']}")
        print(f"   {item['published']}")
        print("-" * 60)
