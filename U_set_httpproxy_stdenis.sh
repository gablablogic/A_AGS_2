#!/usr/bin/env bash
set -euo pipefail

# ---------- HOME resolution for Git Bash on Windows ----------
resolve_home_dir() {
  if [ -n "${HOME-}" ]; then
    echo "$HOME"
  elif [ -n "${USERPROFILE-}" ]; then
    if [[ "$USERPROFILE" =~ ^[A-Za-z]:\\ ]]; then
      drive=$(printf '%s' "$USERPROFILE" | cut -c1 | tr 'A-Z' 'a-z')
      rest=$(printf '%s' "$USERPROFILE" | cut -c3- | tr '\\' '/')
      echo "/$drive/$rest"
    else
      echo "$USERPROFILE"
    fi
  else
    pwd
  fi
}

HOME_DIR="$(resolve_home_dir)"
BASHRC="$HOME_DIR/.bashrc"
BASH_PROFILE="$HOME_DIR/.bash_profile"

# ---------- IP detection ----------
get_private_ipv4() {
  local candidates=""
  if command -v hostname >/dev/null 2>&1; then
    candidates=$(hostname -I 2>/dev/null || true)
  fi
  if [ -z "${candidates:-}" ] && command -v ipconfig >/dev/null 2>&1; then
    candidates=$(ipconfig 2>/dev/null \
      | grep -E "IPv4 Address|Adresse IPv4" \
      | sed -E 's/.*:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+).*/\1/')
  fi
  [ -z "${candidates:-}" ] && { echo ""; return 0; }
  echo "$candidates" | tr ' ' '\n' \
    | grep -E '^(10\.[0-9]+\.[0-9]+\.[0-9]+|192\.168\.[0-9]+\.[0-9]+|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]+\.[0-9]+)$' \
    | head -n 1
}

# ---------- Persist block helpers ----------
upsert_bashrc_block() {
  local content="$1"
  local start="# >>> proxy-auto >>>"
  local end="# <<< proxy-auto <<<"

  mkdir -p "$HOME_DIR"
  touch "$BASHRC"

  if grep -qF "$start" "$BASHRC" 2>/dev/null; then
    awk -v start="$start" -v end="$end" -v repl="$content" '
      BEGIN{inblock=0}
      {
        if ($0 ~ start) {print repl; inblock=1; next}
        if ($0 ~ end)   {inblock=0; next}
        if (!inblock)   {print}
      }' "$BASHRC" > "${BASHRC}.tmp" && mv "${BASHRC}.tmp" "$BASHRC"
  else
    { echo ""; echo "$content"; } >> "$BASHRC"
  fi
}

remove_bashrc_block() {
  local start="# >>> proxy-auto >>>"
  local end="# <<< proxy-auto <<<"
  [ -f "$BASHRC" ] || return 0
  grep -qF "$start" "$BASHRC" || return 0
  awk -v start="$start" -v end="$end" '
    BEGIN{inblock=0}
    {
      if ($0 ~ start) {inblock=1; next}
      if ($0 ~ end)   {inblock=0; next}
      if (!inblock)   {print}
    }' "$BASHRC" > "${BASHRC}.tmp" && mv "${BASHRC}.tmp" "$BASHRC"
}

ensure_bash_profile_sources_bashrc() {
  mkdir -p "$HOME_DIR"
  touch "$BASH_PROFILE"
  if ! grep -qF ". ~/.bashrc" "$BASH_PROFILE"; then
    {
      echo '# ~/.bash_profile — charge ~/.bashrc si présent'
      echo '[ -f ~/.bashrc ] && . ~/.bashrc'
    } >> "$BASH_PROFILE"
  fi
}

# ---------- Main ----------
IP=$(get_private_ipv4)
[ -z "$IP" ] && { echo "❌ IP privée introuvable."; exit 1; }

last_octet=$(awk -F. '{print $NF}' <<< "$IP")
[[ "$last_octet" =~ ^[0-9]+$ ]] || { echo "❌ Dernier octet invalide: '$last_octet'"; exit 1; }

i=$(( last_octet % 4 ))
VAR_NAME="HTTP_PROXY_${i}"
HTTP_VAL="${!VAR_NAME-}"

echo "ℹ️ HOME_DIR     : $HOME_DIR"
echo "ℹ️ Bash config  : $BASHRC  |  $BASH_PROFILE"
echo "ℹ️ IP: $IP | dernier octet: $last_octet | i = $i"
echo "ℹ️ Variable requise: $VAR_NAME"

if [ -z "${HTTP_VAL:-}" ]; then
  echo "⚠️ $VAR_NAME non définie. Aucune config appliquée; bloc persistant supprimé."
  remove_bashrc_block
  ensure_bash_profile_sources_bashrc
  exit 0
fi

# Session courante
export HTTP_PROXY="$HTTP_VAL"
export HTTPS_PROXY="$HTTP_VAL"
export http_proxy="$HTTP_VAL"
export https_proxy="$HTTP_VAL"
echo "✅ HTTP_PROXY  = $HTTP_VAL"
echo "✅ HTTPS_PROXY = $HTTP_VAL"

# Persistance
BLOCK_CONTENT="# >>> proxy-auto >>>
# Bloc géré automatiquement — ne pas éditer entre ces marqueurs.
# HOME_DIR: $HOME_DIR
# IP: $IP | dernier octet: $last_octet | i = $i
export HTTP_PROXY=\"$HTTP_VAL\"
export HTTPS_PROXY=\"$HTTP_VAL\"
export http_proxy=\"$HTTP_VAL\"
export https_proxy=\"$HTTP_VAL\"
# <<< proxy-auto <<<"
upsert_bashrc_block "$BLOCK_CONTENT"

# S'assurer que .bash_profile source .bashrc
ensure_bash_profile_sources_bashrc

echo "📝 Écrit dans: $BASHRC"
echo "🧩 $BASH_PROFILE met bien en place 'source ~/.bashrc'"
echo "ℹ️ Ouvre un nouveau terminal Git Bash (ou VS Code / Git Bash) pour prise en compte."
