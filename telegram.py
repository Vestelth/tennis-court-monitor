import requests
import json
import os
import datetime
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
