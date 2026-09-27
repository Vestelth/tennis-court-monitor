#!/usr/bin/env bash
# Weryfikacja po deployu — wykonywana NA SERWERZE (przez ssh ... bash -s).
# Argumenty: <oczekiwany short sha> <start deployu "YYYY-MM-DD HH:MM:SS"> <max sekund na skan>
set -euo pipefail
EXPECTED="$1"; START="$2"; SCAN_WAIT="$3"
APP=/opt/court-monitor

deployed=$(git -C "$APP" rev-parse --short HEAD)
echo "commit na serwerze: $deployed"
[ "$deployed" = "$EXPECTED" ] || { echo '!!! commit na serwerze != HEAD'; exit 1; }
systemctl is-active --quiet court-monitor || { echo '!!! usługa nie działa'; exit 1; }

# Czy usługa w ogóle zeskanuje? (ta sama reguła co service.should_scan, czas Europe/Warsaw)
read -r enabled h_start h_end < <("$APP/.venv/bin/python" -c "
import sqlite3
d = dict(sqlite3.connect('$APP/state.db').execute('select key, value from settings'))
print(d['enabled'], d['hours_start'], d['hours_end'])")
hour=$(TZ=Europe/Warsaw date +%-H)

logs() { journalctl -u court-monitor --since "$START" --no-pager -o cat; }

if [ "$enabled" = 1 ] && [ "$hour" -ge "$h_start" ] && [ "$hour" -le "$h_end" ]; then
  echo "czekam do ${SCAN_WAIT}s na pierwszy skan..."
  for _ in $(seq 1 "$SCAN_WAIT"); do
    logs | grep -q 'Skan zakończony' && break
    sleep 1
  done
  logs | grep -q 'Skan zakończony' || { logs | tail -20; echo '!!! brak skanu mimo godzin pracy'; exit 1; }
else
  sleep 3  # chwila na log startu
  reason="monitoring OFF"; [ "$enabled" = 1 ] && reason="godz. $hour poza /hours $h_start-$h_end"
  echo "(skan pominięty: $reason — nie czekam)"
fi

logs | grep -E 'INFO|WARNING|ERROR|Traceback' || true
! logs | grep -qE 'ERROR|Traceback' || { echo '!!! błędy w logu'; exit 1; }
