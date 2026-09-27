#!/usr/bin/env bash
# Deploy skanera na Mikrusa: testy -> push na v2 -> deploy.sh na serwerze ->
# weryfikacja (commit + start + pierwszy skan) -> git pull w głównym checkoucie.
# Uruchamiaj z Git Basha w repo (dowolny worktree): bash .claude/skills/deploy/deploy.sh
set -euo pipefail

BRANCH="${BRANCH:-v2}"
SSH="/c/Windows/System32/OpenSSH/ssh.exe"   # widzi Windows ssh-agent (ssh z Git Basha nie)
HOST="root@tadek310.mikrus.xyz"
PORT=10310
SCAN_WAIT="${SCAN_WAIT:-120}"               # sekundy na pierwszy skan po restarcie

step() { printf '\n==> %s\n' "$*"; }
fail() { printf '\n!!! %s\n' "$*" >&2; exit 1; }

ROOT="$(git rev-parse --show-toplevel)"
MAIN="$(git worktree list --porcelain | sed -n '1s/^worktree //p')"
PY="$MAIN/.venv/Scripts/python.exe"
cd "$ROOT"

step "Stan repo ($ROOT)"
[ -z "$(git status --porcelain --untracked-files=no)" ] || fail "Niezacommitowane zmiany — najpierw commit."
HEAD_SHA="$(git rev-parse --short HEAD)"
git fetch -q origin "$BRANCH"
git merge-base --is-ancestor "origin/$BRANCH" HEAD || fail "origin/$BRANCH ma commity, których nie ma HEAD — zrób pull/rebase."
echo "HEAD $HEAD_SHA: $(git log -1 --format=%s)"

step "Testy"
[ -x "$PY" ] || fail "Brak venv: $PY"
"$PY" -m pytest -q | tail -1

step "Klucz SSH w agencie"
/c/Windows/System32/OpenSSH/ssh-add.exe -l >/dev/null 2>&1 \
  || fail "Agent pusty — w zwykłym PowerShellu: ssh-add \$env:USERPROFILE\\.ssh\\id_ed25519"

step "Push HEAD -> origin/$BRANCH"
git push -q origin "HEAD:$BRANCH"

step "Deploy na serwerze"
START="$("$SSH" -o BatchMode=yes -p $PORT $HOST 'date "+%Y-%m-%d %H:%M:%S"')"
"$SSH" -o BatchMode=yes -p $PORT $HOST 'bash /opt/court-monitor/deploy/deploy.sh' 2>&1 \
  | grep -E '==>|Active:|!!!' || true

step "Weryfikacja"
"$SSH" -o BatchMode=yes -p $PORT $HOST "bash -s -- '$HEAD_SHA' '$START' '$SCAN_WAIT'" < "$(dirname "$0")/verify-remote.sh"

if [ "$MAIN" != "$ROOT" ]; then
  step "git pull w głównym checkoucie ($MAIN)"
  git -C "$MAIN" pull -q --ff-only && git -C "$MAIN" log --oneline -1
fi

step "OK — wdrożono $HEAD_SHA. Teraz wpis do wiki (patrz SKILL.md)."
