#!/bin/bash

# Fonction pour afficher une erreur et quitter
error_exit() {
    echo "❌ Erreur : $1"
    exit 1
}

# --- Récupération de l'adresse IP ---
# Dans Git Bash, 'hostname -I' ne marche pas toujours.
# On interroge ipconfig via grep/awk.
IP_ADDRESS=$(ipconfig 2>/dev/null | grep "IPv4" | head -n 1 | awk -F: '{print $2}' | xargs)

if [ -z "$IP_ADDRESS" ]; then
    error_exit "Impossible de récupérer l'adresse IP (ipconfig non disponible ou parsing échoué)."
fi

# --- Récupération des variables d'environnement ---
if [ -z "$HTTP_PROXY" ]; then
    HTTP_PROXY_VALUE="(non définie)"
else
    HTTP_PROXY_VALUE="$HTTP_PROXY"
fi

if [ -z "$HTTPS_PROXY" ]; then
    HTTPS_PROXY_VALUE="(non définie)"
else
    HTTPS_PROXY_VALUE="$HTTPS_PROXY"
fi

# --- Affichage ---
echo "✅ Adresse IP locale : $IP_ADDRESS"
echo "✅ Variable HTTP_PROXY  : $HTTP_PROXY_VALUE"
echo "✅ Variable HTTPS_PROXY : $HTTPS_PROXY_VALUE"
echo "✅ GOOGLE_API_KEY : $GOOGLE_API_KEY"
echo "✅ GOOGLE_CSE_ID : $GOOGLE_CSE_ID"
