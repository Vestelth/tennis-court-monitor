import requests
import json
import datetime
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

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
    last_id = tg_state.get("last_update_id", 0)

    r = requests.get(
        f"{BASE}/getUpdates",
        params={"offset": last_id + 1}
    ).json()

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

                new_query = "&".join(
                    f"{k}={v[0]}" for k, v in qs.items()
                )
                base_url = u["url"].split("?")[0]
                u["url"] = f"{base_url}?{new_query}"

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
            send(f"Ustawiono godziny działania monitoringu {s}-{e}")

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

        elif text == "/list":
            config = json.load(open("config.json"))
            lines = ["Monitorowane korty:"]
            for u in config["urls"]:
                lines.append(f"- {u['name']}")
            send("\n".join(lines))

        elif text == "/status":
            config = json.load(open("config.json"))
            enabled = open("enabled.txt").read().strip()
            slot_scope = config.get("slot_scope", {"start": 0, "end": 23})

            sample_url = config["urls"][0]["url"]
            qs = parse_qs(urlparse(sample_url).query)
            duration = int(qs.get("czas_rezerwacji", ["2"])[0]) * 0.5

            send(
                "Status monitoringu:\n"
                f"Aktywny: {'TAK' if enabled == '1' else 'NIE'}\n"
                f"Godziny działania: {config['monitor_hours']['start']}-{config['monitor_hours']['end']}\n"
                f"Zakres godzin slotów: {slot_scope['start']}-{slot_scope['end']}\n"
                f"Długość slotu: {duration}h\n"
                f"Liczba kortów: {len(config['urls'])}"
            )

        elif text == "/run":
            if open("force_run.txt").read().strip() != "1":
                open("force_run.txt", "w").write("1")
                send("Wymuszono natychmiastowe sprawdzenie przy następnym uruchomieniu workflow.")

        elif text == "/help":
            send(
                "Dostępne komendy:\n\n"
                "/start – włącza monitoring\n"
                "/stop – wyłącza monitoring\n"
                "/status – pokazuje ustawienia\n"
                "/list – lista monitorowanych kortów\n"
                "/set N – ustawia czas_rezerwacji\n"
                "/hours H1 H2 – ustawia godziny działania monitoringu\n"
                "/scope H1 H2 – ustawia zakres godzin slotów\n"
                "/run – wymusza sprawdzenie\n"
                "/help – pokazuje tę pomoc"
            )

    tg_state["last_update_id"] = last_id
    json.dump(tg_state, open("telegram_state.json", "w"), indent=2)


handle_commands()

# ---------- MONITORING ----------

force_run = open("force_run.txt").read().strip() == "1"

if open("enabled.txt").read().strip() != "1" and not force_run:
    exit()

config = json.load(open("config.json"))
slot_scope = config.get("slot_scope", {"start": 0, "end": 23})

hour = datetime.datetime.now().hour
if not force_run and not (
    config["monitor_hours"]["start"] <= hour <= config["monitor_hours"]["end"]
):
    exit()

state = json.load(open("state.json"))
state.setdefault("reported", [])

changed = False
currently_visible = set()

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}

today = datetime.date.today().strftime("%Y-%m-%d")

for item in config["urls"]:
    qs = parse_qs(urlparse(item["url"]).query)
    duration = int(qs.get("czas_rezerwacji", ["2"])[0]) * 0.5

    ajax_url = f"{item['url']}&data_grafiku={today}"

    r = requests.get(ajax_url, headers=headers, timeout=30)
    if r.status_code != 200:
        continue

    soup = BeautifulSoup(r.text, "html.parser")

    headers_row = soup.select("thead th.text-center")
    dates = []
    for h in headers_row:
        text = h.get_text(separator=" ", strip=True)
        parts = text.split()
        if len(parts) >= 2:
            dates.append(parts[-1])

    rows = soup.select("tbody tr")
    found_dates = set()

    for row in rows:
        cells = row.find_all("td")
        if not cells:
            continue

        for idx, cell in enumerate(cells[1:]):
            a = cell.select_one("a.btn-success")
            if not a:
                continue

            date = dates[idx] if idx < len(dates) else "?"
            if date in found_dates:
                continue

            span = a.find("span")
            time_range = span.get_text(strip=True) if span else "?"

            try:
                start_hour = int(time_range.split("-")[0].split(":")[0])
            except:
                continue

            if not (slot_scope["start"] <= start_hour <= slot_scope["end"]):
                continue

            key = f"{item['name']}_{date}"
            currently_visible.add(key)

            if key not in state["reported"]:
                send(
                    f"Wolny kort: {item['name']}\n"
                    f"Data: {date}\n"
                    f"Termin: {time_range}\n"
                    f"Długość: {duration}h\n"
                    f"{item['link']}"
                )
                state["reported"].append(key)
                found_dates.add(date)
                changed = True

# usuwamy dni które już zniknęły
new_reported = [k for k in state["reported"] if k in currently_visible]

if len(new_reported) != len(state["reported"]):
    state["reported"] = new_reported
    changed = True

if changed:
    json.dump(state, open("state.json", "w"), indent=2)

if force_run:
    open("force_run.txt", "w").write("0")
