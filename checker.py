import requests
import json
import datetime
from bs4 import BeautifulSoup
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )

if open("enabled.txt").read().strip() != "1":
    exit()

config = json.load(open("config.json"))

hour = datetime.datetime.now().hour
if not (config["monitor_hours"]["start"] <= hour <= config["monitor_hours"]["end"]):
    exit()

for item in config["urls"]:
    r = requests.get(item["url"], timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    if "wolny" in soup.text.lower():
        send(f"Możliwy wolny kort: {item['name']}\n{item['url']}")
