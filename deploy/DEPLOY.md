# Deploy na Mikrus (Etap 5)

Skaner uruchamiany jako **usługa systemd** na Mikrusie. Jeden długożyjący
proces (`service.py`): long-polling komend Telegram + skan grafików co 10 min.
Stan w SQLite (`state.db` w katalogu instalacji — poza gitem).

- **Serwer:** `tadek310.mikrus.xyz:10310` (SSH, klucz ed25519 z passphrase)
- **System:** Ubuntu 24.04, systemd 255, Python 3.12 — wszystko first-class
- **Repo:** https://github.com/Vestelth/tennis-court-monitor (branch `v2`)

## Założenia
- Deploy robi się **na serwerze** skryptem `deploy/deploy.sh` (idempotentny:
  pierwsze odpalenie klonuje + tworzy venv + instaluje unit; kolejne aktualizują
  kod do `origin/$BRANCH` i restartują usługę).
- Sekrety (`BOT_TOKEN`, `CHAT_ID`) **nie są w repo** — leżą w
  `/etc/court-monitor.env` (uprawnienia 600), wczytywane przez systemd
  (`EnvironmentFile`).
- Domyślna ścieżka instalacji: `/opt/court-monitor` (zmienna `DEST`).

## Kroki

### 1. SSH na Mikrusa
```bash
ssh -p 10310 root@tadek310.mikrus.xyz
```
(passphrase do klucza albo wcześniej `ssh-add` do agenta)

### 2. Pierwsze uruchomienie deploya
Pobierz sam skrypt (lub sklonuj repo ręcznie) i odpal:
```bash
# najprościej — ściągnij deploy.sh z brancha v2 i odpal:
curl -fsSL https://raw.githubusercontent.com/Vestelth/tennis-court-monitor/v2/deploy/deploy.sh -o /tmp/deploy.sh
bash /tmp/deploy.sh
```
Za pierwszym razem skrypt utworzy `/etc/court-monitor.env` (pusty szablon)
i **przerwie**.

### 3. Uzupełnij sekrety
```bash
nano /etc/court-monitor.env
# BOT_TOKEN=123456:ABC...
# CHAT_ID=987654321
chmod 600 /etc/court-monitor.env   # skrypt już ustawia, ale dla pewności
```

### 4. Odpal deploy ponownie
```bash
bash /tmp/deploy.sh
```
Teraz: zainstaluje zależności, wgra unit, `enable` + `restart`. Na końcu
pokaże status i podpowie `journalctl`.

### 5. Smoke test end-to-end
```bash
journalctl -u court-monitor -f          # powinno: "Start usługi, N kortów..."
```
W Telegramie wyślij `/status` → natychmiastowa odpowiedź; `/run` → wymuszony
skan i podsumowanie „X nowych powiadomień".

## Cutover v1 → v2 (WAŻNE — nie odpalać dwóch botów naraz)
v1 chodzi na GitHub Actions (`.github/workflows/check.yml`, cron co 10 min na
`main`, `checker.py`). Po potwierdzeniu, że v2 działa na Mikrusie:

1. **Wyłącz cron Actions** — w GitHub: repo → Actions → „Court monitor" →
   `•••` → *Disable workflow* (albo usuń/zakomentuj blok `schedule:` w
   `check.yml` na `main`).
2. Dopiero wtedy oba boty nie będą rywalizować o ten sam `getUpdates`/wysyłkę.

> Long-polling: tylko **jeden** konsument `getUpdates` na token. Jeśli v1 i v2
> działają jednocześnie, komendy Telegram będą się gubić. Stąd cutover = twardy
> warunek, a nie kosmetyka.

## Aktualizacje w przyszłości
Po wypchnięciu zmian na `v2` (lub `main` po cutoverze):
```bash
ssh -p 10310 root@tadek310.mikrus.xyz 'bash /opt/court-monitor/deploy/deploy.sh'
```
(ewentualnie `BRANCH=main bash ...` jeśli przeniesiesz produkcję na `main`)

## Przydatne komendy
```bash
systemctl status court-monitor
systemctl restart court-monitor
journalctl -u court-monitor -f          # logi na żywo
journalctl -u court-monitor --since "1 hour ago"
```
