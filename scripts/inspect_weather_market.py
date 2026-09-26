import urllib.request
import json
from datetime import datetime, timezone

def fetch_event(slug):
    url = f"https://gamma-api.polymarket.com/events?slug={slug}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("Error fetching event:", e)
        return []

# Test recent September highest-temperature markets
slugs = [
    "highest-temperature-in-los-angeles-on-september-24-2026",
    "highest-temperature-in-miami-on-september-8-2026",
    "highest-temperature-in-wellington-on-may-15-2026",
    "highest-temperature-in-paris-on-april-15-2026"
]

for s in slugs:
    ev = fetch_event(s)
    if ev:
        e = ev[0]
        print(f"==================================================")
        print(f"Event: {e.get('title')}")
        print(f"Slug:  {e.get('slug')}")
        print(f"End Date: {e.get('endDate')} | Closed: {e.get('closed')} | Active: {e.get('active')}")
        markets = e.get("markets", [])
        print(f"Markets count: {len(markets)}")
        
        # Check if any outcome is resolved / pending
        for m in markets[:5]:
            outcome = m.get("groupItemTitle") or m.get("question")
            cid = m.get("conditionId")
            closed = m.get("closed")
            active = m.get("active")
            prices = m.get("outcomePrices")
            uma_status = m.get("umaResolutionStatus")
            print(f"  • Option: {outcome:<16} | Closed: {closed} | Active: {active} | Prices: {prices} | UMA: {uma_status}")
            print(f"    ConditionId: {cid}")
        print()
