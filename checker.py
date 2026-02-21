import requests
import json
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from telegram import send, handle_commands


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
new_slots = []

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
                new_slots.append({
                    "name": item["name"],
                    "date": date,
                    "time_range": time_range,
                    "duration": duration,
                    "link": item["link"],
                    "key": key,
                })
                found_dates.add(date)

def _parse_slot_date(slot):
    try:
        day, month = map(int, slot["date"].split("/"))
        year = datetime.date.today().year
        if month < datetime.date.today().month:
            year += 1
        return datetime.date(year, month, day)
    except Exception:
        return datetime.date.max

new_slots.sort(key=_parse_slot_date)

for slot in new_slots:
    send(
        f"Wolny kort: {slot['name']}\n"
        f"Data: {slot['date']}\n"
        f"Termin: {slot['time_range']}\n"
        f"Długość: {slot['duration']}h\n"
        f"{slot['link']}"
    )
    state["reported"].append(slot["key"])
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
