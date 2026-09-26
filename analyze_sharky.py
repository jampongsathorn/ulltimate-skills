import sys
sys.path.append("/home/user")
from polymarket_tracker import fetch_all_closed_positions, make_request
from collections import defaultdict
from datetime import datetime, timezone

w = "0x751a2b86cab503496efd325c8344e10159349ea1"
closed = fetch_all_closed_positions(w, max_records=1000)

print(f"Total closed positions analyzed: {len(closed)}")

cats = defaultdict(lambda: {"count": 0, "pnl": 0.0, "volume": 0.0, "wins": 0, "losses": 0, "prices": []})

for c in closed:
    t = c.get("title", "")
    pnl = float(c.get("realizedPnl") or 0)
    price = float(c.get("avgPrice") or 0)
    size = float(c.get("totalBought") or 0)
    cost = float(c.get("totalCost") or (price * size))
    
    t_low = t.lower()
    if "up or down" in t_low:
        cat = "Crypto 5m/1h Up-Down (Micro Sniping)"
    elif any(k in t_low for k in ["bitcoin", "btc", "ethereum", "eth", "solana"]):
        cat = "Macro Crypto (Thresholds/Dips)"
    elif any(k in t_low for k in ["counter-strike", "lol:", "dota", "valorant", "iem"]):
        cat = "Esports Live In-Play"
    elif any(k in t_low for k in [" vs ", " vs. ", "win on"]):
        cat = "Sports Live In-Play"
    elif any(k in t_low for k in ["election", "trump", "harris", "biden", "president"]):
        cat = "Politics & Elections"
    else:
        cat = "Other Events"

    cats[cat]["count"] += 1
    cats[cat]["pnl"] += pnl
    cats[cat]["volume"] += cost
    cats[cat]["prices"].append(price)
    if pnl > 0:
        cats[cat]["wins"] += 1
    elif pnl < 0:
        cats[cat]["losses"] += 1

print("\n" + "="*115)
header = f"  {'Category':<38} | {'Trades':<7} | {'WinRate':<8} | {'PnL ($)':<16} | {'Volume ($)':<16} | {'Avg Price'}"
print(header)
print("="*115)
for cat, stats in sorted(cats.items(), key=lambda x: x[1]["pnl"], reverse=True):
    wr = (stats["wins"] / stats["count"] * 100) if stats["count"] > 0 else 0
    pnl_str = f"${stats['pnl']:>14,.2f}"
    vol_str = f"${stats['volume']:>14,.2f}"
    avg_p = sum(stats["prices"]) / len(stats["prices"]) if stats["prices"] else 0
    print(f"  {cat:<38} | {stats['count']:>7} | {wr:>6.1f}% | {pnl_str} | {vol_str} | ${avg_p:.3f}")
print("="*115)

# Detailed analysis on Top Trades
print("\n🔥 TOP 10 LARGEST WINNING POSITIONS FOR SHARKY6999:")
top_wins = sorted(closed, key=lambda x: float(x.get("realizedPnl") or 0), reverse=True)[:10]
for i, tw in enumerate(top_wins, 1):
    title = tw.get("title", "")
    pnl = float(tw.get("realizedPnl") or 0)
    price = float(tw.get("avgPrice") or 0)
    outcome = tw.get("outcome", "")
    print(f"  #{i}. +${pnl:>10,.2f} | Entry: ${price:.3f} [{outcome}] | {title}")

print("\n⚠️ TOP 5 LARGEST LOSING POSITIONS FOR SHARKY6999:")
top_losses = sorted(closed, key=lambda x: float(x.get("realizedPnl") or 0))[:5]
for i, tl in enumerate(top_losses, 1):
    title = tl.get("title", "")
    pnl = float(tl.get("realizedPnl") or 0)
    price = float(tl.get("avgPrice") or 0)
    outcome = tl.get("outcome", "")
    print(f"  #{i}. -${abs(pnl):>10,.2f} | Entry: ${price:.3f} [{outcome}] | {title}")
