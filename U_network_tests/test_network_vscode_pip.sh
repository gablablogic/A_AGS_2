#!/bin/bash
export HTTP_PROXY=http://10.146.229.177:80
export HTTPS_PROXY=http://10.146.229.177:80

#unset HTTP_PROXY
#unset HTTPS_PROXY

# Listes des domaines critiques
VSCODE_URLS=(
  "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
  "https://az764295.vo.msecnd.net"
  "https://update.code.visualstudio.com/api/update"
  "https://vscode.blob.core.windows.net"
  "https://code.visualstudio.com"
)

PIP_URLS=(
  "https://pypi.org/simple"
  "https://files.pythonhosted.org"
  "https://pypi.python.org"
)

test_urls() {
  local title=$1
  shift
  local urls=("$@")
  
  echo
  echo "🔍 $title"
  echo "========================================"
  
  for URL in "${urls[@]}"; do
    echo "➡️  Test de : $URL"
    curl -s -I --max-time 10 "$URL" | grep -E "HTTP|Server|Content-Type"
    echo "----------------------------------------"
  done
}

echo
echo "🧪 Détection des blocages proxy/Zscaler pour VS Code et pip"
echo "📍 Variables proxy actuelles :"
echo "  HTTP_PROXY=$HTTP_PROXY"
echo "  HTTPS_PROXY=$HTTPS_PROXY"
echo

test_urls "Test des domaines VS Code" "${VSCODE_URLS[@]}"
test_urls "Test des domaines pip / PyPI" "${PIP_URLS[@]}"
