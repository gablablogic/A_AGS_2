"""
Connect_to_openai.py

Ce script permet d'effectuer une première connexion avec l'API d'OpenAI.
Il utilise une clé API stockée dans un fichier `.env` pour authentifier les requêtes.
Le script envoie une requête au modèle GPT-4 pour générer une réponse créative.

Prérequis :
- Un fichier `.env` contenant une clé API valide sous la variable `OPENAI_API_KEY`.
- Les bibliothèques `openai` et `python-dotenv` doivent être installées.

Fonctionnalités :
- Chargement de la clé API depuis le fichier `.env`.
- Vérification de la présence de la clé API.
- Envoi d'une requête au modèle GPT-4 pour générer une réponse.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv()) # Load environment variables from .env file
current_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=current_api_key)
if current_api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable not set")
else: print ("openai API key is ") # + current_api_key)

try:
  completion = client.chat.completions.create(
    model="gpt-4",
    messages=[
      {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex concepts with creative flair."},
      {"role": "user", "content": "Compose a 6 lines poem, in french language, that explains the concept of self-awareness"}
    ]
  )
  print(type(completion))
except Exception as e:
    print(f"Error connecting to OpenAI API: {e}")
print(completion.choices[0].message)