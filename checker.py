import requests
import json
import datetime
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )

def get_duration(url):
    qs = parse_qs(urlparse(url).query)
    val = int(qs.get("czas_rezerwacji", ["2"])[0])
    return val * 0.5

# sprawdzenie czy monitoring włączony
if open("enabled.txt").read().strip() != "1":
    exit()

config = json.load(open("config.json"))

# sprawdzenie godzin monitorowania
hour = datetime.datetime.now().hour
if not (config["monitor_hours"]["start"] <= hour <= config["monitor_hours"]["end"]):
    exit()

state = json.load(open("state.json"))
changed = False

for item in config["urls"]:

    duration = get_duration(item["url"])

    r = requests.get(item["url"], timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    # wszystkie wolne sloty
    for a in soup.select("a.btn-success"):
        term = a.get("data-termin")

        span = a.find("span")
        time_range = span.get_text(strip=True) if span else "nieznany czas"

        key = f"{item['name']}_{term}"

        if key not in state["reported"]:
            send(
                f"Wolny kort: {item['name']}\n"
                f"Termin: {time_range}\n"
                f"Długość: {duration}h\n"
                f"{item['url']}"
            )
            state["reported"].append(key)
            changed = True

if changed:
    json.dump(state, open("state.json", "w"), indent=2)
