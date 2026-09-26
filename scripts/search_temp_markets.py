import urllib.request
import urllib.parse
import json

def search(query):
    # Try markets endpoint with search
    url = f"https://gamma-api.polymarket.com/markets?limit=25&search={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("err:", e)
        return []

def search_events(query):
    url = f"https://gamma-api.polymarket.com/events?limit=25&search={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("err:", e)
        return []

markets = search("temperature")
print(f"Found {len(markets)} markets for 'temperature':")
for m in markets[:10]:
    q = m.get("question") or m.get("title")
    cid = m.get("conditionId")
    closed = m.get("closed")
    active = m.get("active")
    end_date = m.get("endDate")
    slug = m.get("slug")
    print(f"• Question: {q}")
    print(f"  Slug: {slug} | Closed: {closed} | Active: {active} | EndDate: {end_date} | ConditionId: {cid}")
    print(f"  UMA Status / Outcome: {m.get('umaResolutionStatus')} | OutcomePrices: {m.get('outcomePrices')}")
    print()

events = search_events("temperature")
print(f"\nFound {len(events)} events for 'temperature':")
for e in events[:5]:
    print(f"• Event: {e.get('title')} | Slug: {e.get('slug')} | Closed: {e.get('closed')} | Markets count: {len(e.get('markets', []))}")
