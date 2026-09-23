---
name: deploy
description: Use when the user asks to deploy, ship, or release the tennis court monitor (skaner kortów) to the Mikrus server, or to push finished v2 changes to production.
disable-model-invocation: true
---

# Deploy skanera na Mikrusa

Produkcja = usługa systemd `court-monitor` na Mikrusie (`/opt/court-monitor`, branch `v2`).
Deploy to akcja produkcyjna — odpalaj tylko na wyraźne polecenie użytkownika.

## Kroki

1. **Commit gotowy.** Zmiany zacommitowane (konwencja: `feat(v2): …` / `fix(v2): …`, po polsku).
2. **Skrypt** (Git Bash, z katalogu repo lub worktree; trwa ~1–3 min → timeout ≥ 300000):
   ```bash
   bash .claude/skills/deploy/deploy.sh
   ```
   Robi: czyste drzewo + `origin/v2` jest przodkiem HEAD → pytest → klucz w agencie →
   push `HEAD:v2` → `deploy.sh` na serwerze → sprawdza commit, usługę i pierwszy skan →
   `git pull` w głównym checkoucie. Kończy się `!!!` przy pierwszym błędzie.
3. **Wiki** — obowiązkowe, deploy bez tego nie jest skończony. W
   `C:/Users/conta/Documents/Obsidian/personal-wiki/wiki/projects/tennis-court-monitor.md`:
   - blok „▶ Wznowienie”: HEAD (short sha) i liczba testów;
   - odhacz ukończone punkty etapu;
   - linia w „## Log”: `- RRRR-MM-DD — <co wdrożono i po co>. Commit <sha>`;
   - frontmatter `updated:` na dziś.
4. **Raport:** commit, wynik pierwszego skanu (liczba powiadomień), zmiany zachowania widoczne dla użytkownika.

## Gdy skrypt przerwie

| Komunikat | Co zrobić |
|---|---|
| `Agent pusty` | Użytkownik w **zwykłym PowerShellu**: `ssh-add $env:USERPROFILE\.ssh\id_ed25519`. Nie przez `!` — passphrase nie da się tam wpisać, komenda wisi. |
| `Niezacommitowane zmiany` / `origin/v2 ma commity` | Commit albo pull/rebase — nie wymuszaj pusha. |
| testy czerwone | Nie deployuj; napraw (superpowers:systematic-debugging). |
| `commit na serwerze != HEAD`, `usługa nie działa`, `błędy w logu` | `journalctl -u court-monitor -n 50` przez SSH, diagnoza przed ponownym deployem. |
| `brak skanu` | Nie błąd: poza `/hours` albo monitoring OFF — powiedz użytkownikowi. |

## Pułapki

- SSH tylko przez `C:\Windows\System32\OpenSSH\ssh.exe` — `ssh` z Git Basha nie widzi Windows ssh-agent.
- Nigdy nie nadpisuj `/etc/court-monitor.env` (sekrety).
- Serwer w Finlandii; logika godzin w aplikacji jest w `Europe/Warsaw`.
