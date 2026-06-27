#!/usr/bin/env bash
# Deploy/aktualizacja skanera kortow jako uslugi systemd.
# Uruchom NA MIKRUSIE jako root:  bash deploy.sh
# Idempotentny: pierwszy raz klonuje + tworzy venv + instaluje unit,
# kolejne razy aktualizuje kod do origin/$BRANCH i restartuje usluge.
set -euo pipefail

REPO="${REPO:-https://github.com/Vestelth/tennis-court-monitor.git}"
BRANCH="${BRANCH:-v2}"
DEST="${DEST:-/opt/court-monitor}"
SERVICE="court-monitor"
ENV_FILE="/etc/court-monitor.env"

echo "==> repo=$REPO branch=$BRANCH dest=$DEST"

# 1. Kod
if [ -d "$DEST/.git" ]; then
  echo "==> aktualizuje repo w $DEST"
  git -C "$DEST" fetch origin "$BRANCH"
  git -C "$DEST" checkout "$BRANCH"
  git -C "$DEST" reset --hard "origin/$BRANCH"
else
  echo "==> klonuje $REPO ($BRANCH) -> $DEST"
  git clone --branch "$BRANCH" "$REPO" "$DEST"
fi

# 2. venv + zaleznosci
if [ ! -d "$DEST/.venv" ]; then
  echo "==> tworze venv"
  python3 -m venv "$DEST/.venv"
fi
"$DEST/.venv/bin/pip" install --quiet --upgrade pip
"$DEST/.venv/bin/pip" install --quiet -r "$DEST/requirements.txt"

# 3. Sekrety — jesli brak pliku, utworz szablon i przerwij (nie nadpisuj istniejacych)
if [ ! -f "$ENV_FILE" ]; then
  echo "==> brak $ENV_FILE — tworze szablon"
  cat > "$ENV_FILE" <<'EOF'
BOT_TOKEN=
CHAT_ID=
EOF
  chmod 600 "$ENV_FILE"
  echo "!!! UZUPELNIJ $ENV_FILE (BOT_TOKEN, CHAT_ID) i uruchom deploy.sh ponownie."
  exit 1
fi
if ! grep -q '^BOT_TOKEN=.\+' "$ENV_FILE" || ! grep -q '^CHAT_ID=.\+' "$ENV_FILE"; then
  echo "!!! $ENV_FILE istnieje, ale BOT_TOKEN/CHAT_ID sa puste — uzupelnij i sprobuj ponownie."
  exit 1
fi

# 4. Unit systemd (podstaw sciezke instalacji)
echo "==> instaluje unit systemd"
sed "s#__DEST__#$DEST#g" "$DEST/deploy/court-monitor.service" > "/etc/systemd/system/$SERVICE.service"
systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl restart "$SERVICE"

echo "==> gotowe."
systemctl --no-pager --full status "$SERVICE" || true
echo
echo "Podglad logow:  journalctl -u $SERVICE -f"
