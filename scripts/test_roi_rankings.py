import sys
sys.path.append('/home/user')
from polymarket_pnl_tracker import get_leaderboard

for tf in ["ALL", "MONTH", "WEEK"]:
    leaders = get_leaderboard(time_period=tf, limit=50)
    print(f"\n=== Top 7 by % PnL (Volume ROI) in timeframe: {tf} ===")
    sorted_by_roi = sorted([x for x in leaders if x["vol"] > 10000], key=lambda x: x["roi_vol_pct"], reverse=True)
    for x in sorted_by_roi[:7]:
        print(f"Leaderboard #{x['rank']:<2} {x['userName']:<24} | PnL: ${x['pnl']:>12,.2f} | Vol: ${x['vol']:>12,.2f} | %PnL/Vol: {x['roi_vol_pct']:>6.2f}%")
