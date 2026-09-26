import urllib.request
import json

url = "https://data-api.polymarket.com/v1/leaderboard?limit=25&timePeriod=ALL&orderBy=PNL"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read().decode())

print(f"{'Rank':<5} | {'Username':<22} | {'Wallet':<42} | {'PnL ($)':<15} | {'Volume ($)':<16} | {'PnL/Vol %':<10}")
print("-" * 125)
for d in data:
    rank = d.get("rank", "-")
    name = d.get("userName") or "(Anon)"
    wallet = d.get("proxyWallet", "")
    pnl = float(d.get("pnl", 0))
    vol = float(d.get("vol", 0))
    roi = (pnl / vol * 100) if vol > 0 else 0
    print(f"#{rank:<4} | {name:<22} | {wallet:<42} | ${pnl:>13,.2f} | ${vol:>14,.2f} | {roi:>8.2f}%")
