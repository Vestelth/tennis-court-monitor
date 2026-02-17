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
            send(
