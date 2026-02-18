import requests
import json
import datetime
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send(msg):
    requests.post(
        f"{BASE}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )

# ---------- TELEGRAM COMMANDS ----------

def handle_commands():
    tg_state = json.load(open("telegram_state.json"))

    r = requests.get(
        f"{BASE}/getUpdates",
        params={"offset": tg_state["last_update_id"] + 1}
    ).json()

    last_id = tg_state["last_update_id"]

    for upd in r.get("result", []):
        last_id = max(last_id, upd["update_id"])

        msg = upd.get("message")
        if not msg:
            continue

        text = msg.get("text", "")

        if text == "/start":
            open("enabled.txt", "w").write("1")
            send("Monitoring włączony")

        elif text == "/stop":
            open("enabled.txt", "w").write("0")
            send("Monitoring zatrzymany")

        elif text.startswith("/set"):
            parts = text.split()
            if len(parts) < 2:
                send("Użycie: /set 4")
                continue

            val = parts[1]
            config = json.load(open("config.json"))

            for u in config["urls"]:
                parsed = urlparse(u["url"])
                qs = parse_qs(parsed.query)
                qs["czas_rezerwacji"] = [val]
                new_query = urlencode(qs, doseq=True)
                u["url"] = urlunparse(parsed._replace(query=new_query))

            json.dump(config, open("config.json", "w"), indent=2)
            send(f"Ustawiono czas_rezerwacji={val}")

        elif text.startswith("/hours"):
            parts = text.split()
            if len(parts) < 3:
                send("Użycie: /hours 16 22")
                continue

            _, s, e = parts
            config = json.load(open("config.json"))
            config["monitor_hours"]["start"] = int(s)
            config["monitor_hours"]["end"] = int(e)
            json.dump(config, open("config.json", "w"), indent=2)
            send(f"Ustawiono godziny {s}-{e}")

        elif text == "/status":
            config = json.load(open("config.json"))
            enabled = open("enabled.txt").read().strip()

            sample_url = config["urls"][0]["url"]
            qs = parse_qs(urlparse(sample_url).query)
            duration = int(qs.get("czas_rezerwacji", ["2"])[0]) * 0.5

            send(
                "Status monitoringu:\n"
                f"Aktywny: {'TAK' if enabled == '1' else 'NIE'}\n"
                f"Godziny: {config['monitor_hours']['start']}-{config['monitor_hours']['end']}\n"
                f"Długość slotu: {duration}h\n"
                f"Liczba kortów: {len(config['urls'])}"
            )

        elif text == "/list":
            config = json.load(open("config.json"))
            lines = ["Monitorowane korty:"]
            for u in config["urls"]:
                lines.append(f"- {u['name']}")
            send("\n".join(lines))

        elif text == "/run":
            if open("force_run.txt").read().strip() != "1":
                open("force_run.txt", "w").write("1")
                send("Wymuszono natychmiastowe sprawdzenie przy następnym uruchomieniu workflow.")

        elif text.startswith("/scope"):
            parts = text.split()
            if len(parts) < 3:
                send("Użycie: /scope 16 22")
                continue
        
            _, s, e = parts
            config = json.load(open("config.json"))
            config["slot_scope"]["start"] = int(s)
            config["slot_scope"]["end"] = int(e)
            json.dump(config, open("config.json", "w"), indent=2)
            send(f"Ustawiono zakres godzin slotów {s}-{e}")
        
            tg_state["last_update_id"] = last_id
            json.dump(tg_state, open("telegram_state.json", "w"), indent=2)

        elif text == "/help":
            send(
                "Dostępne komendy:\n\n"
                "/start – włącza monitoring\n"
                "/stop – wyłącza monitoring\n"
                "/status – pokazuje aktualne ustawienia\n"
                "/list – lista monitorowanych kortów\n"
                "/set N – ustawia czas_rezerwacji (np. /set 4)\n"
                "/hours H1 H2 – ustawia godziny monitorowania (np. /hours 16 22)\n"
                "/help – pokazuje tę pomoc"
            )


handle_commands()

# ---------- MONITORING ----------

force_run = open("force_run.txt").read().strip() == "1"

if open("enabled.txt").read().strip() != "1" and not force_run:
    exit()

config = json.load(open("config.json"))

slot_scope = config.get("slot_scope", {"start": 16, "end": 22})

hour = datetime.datetime.now().hour
if not force_run and not (config["monitor_hours"]["start"] <= hour <= config["monitor_hours"]["end"]):
    exit()

state = json.load(open("state.json"))
changed = False

currently_visible = set()

for item in config["urls"]:
    qs = parse_qs(urlparse(item["url"]).query)
    duration = int(qs.get("czas_rezerwacji", ["2"])[0]) * 0.5

    r = requests.get(item["url"], timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.select("a.btn-success"):
        term = a.get("data-termin")
        span = a.find("span")
        time_range = span.get_text(strip=True) if span else "?"
        start_hour = int(time_range.split(":")[0])
        
        if not (slot_scope["start"] <= start_hour <= slot_scope["end"]):
            continue        

        key = f"{item['name']}_{term}"
        currently_visible.add(key)

        if key not in state["reported"]:
            send(
                f"Wolny kort: {item['name']}\n"
                f"Termin: {time_range}\n"
                f"Długość: {duration}h\n"
                f"{item['url']}"
            )
            state["reported"].append(key)
            changed = True

# usuwamy sloty które już nie są dostępne
new_reported = [k for k in state["reported"] if k in currently_visible]

if len(new_reported) != len(state["reported"]):
    state["reported"] = new_reported
    changed = True

if changed:
    json.dump(state, open("state.json", "w"), indent=2)

if force_run:
    open("force_run.txt", "w").write("0")
    changed = True
