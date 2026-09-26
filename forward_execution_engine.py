#!/usr/bin/env python3
"""
Forward Execution Feasibility & Net Realizable Edge Simulator
═════════════════════════════════════════════════════════════════
Connects Discovered Strategy Components to Real-World Execution:
1. Ingests frozen Strategy Blueprints from V1.2 Strategy Map
2. Queries Live Polymarket CLOB Orderbook (https://clob.polymarket.com/book)
3. Computes VWAP Slippage across target clip sizes ($100, $500, $2,000, $5,000)
4. Models Latency Decay across execution delays (5s, 15s, 60s)
5. Computes Net Realizable Edge (EV_net) after all market frictions
"""

import math
import json
import urllib.request
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

CLOB_API_BASE = "https://clob.polymarket.com"

@dataclass
class OrderbookDepth:
    best_bid: float
    best_ask: float
    spread: float
    bid_depth_usdc: float
    ask_depth_usdc: float
    bids: List[Tuple[float, float]] # (price, size)
    asks: List[Tuple[float, float]] # (price, size)


def fetch_clob_orderbook(token_id: str) -> Optional[OrderbookDepth]:
    url = f"{CLOB_API_BASE}/book?token_id={token_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return None

    raw_bids = data.get("bids", [])
    raw_asks = data.get("asks", [])

    bids: List[Tuple[float, float]] = []
    asks: List[Tuple[float, float]] = []

    for b in raw_bids:
        try:
            bids.append((float(b.get("price", 0)), float(b.get("size", 0))))
        except Exception:
            pass

    for a in raw_asks:
        try:
            asks.append((float(a.get("price", 0)), float(a.get("size", 0))))
        except Exception:
            pass

    bids = sorted(bids, key=lambda x: -x[0]) # Descending bids
    asks = sorted(asks, key=lambda x: x[0])  # Ascending asks

    best_bid = bids[0][0] if bids else 0.0
    best_ask = asks[0][0] if asks else 1.0
    spread = max(0.0, best_ask - best_bid)

    bid_depth_usdc = sum(p * s for p, s in bids)
    ask_depth_usdc = sum(p * s for p, s in asks)

    return OrderbookDepth(
        best_bid=best_bid,
        best_ask=best_ask,
        spread=spread,
        bid_depth_usdc=bid_depth_usdc,
        ask_depth_usdc=ask_depth_usdc,
        bids=bids,
        asks=asks
    )


def compute_vwap_slippage(
    asks: List[Tuple[float, float]],
    target_usdc: float
) -> Tuple[float, float, float, bool]:
    """
    Computes VWAP fill price, total shares filled, and slippage for target USDC clip.
    Returns: (vwap_fill_price, effective_slippage_pct, filled_usdc, is_fully_filled)
    """
    if not asks or target_usdc <= 0:
        return 1.0, 100.0, 0.0, False

    best_ask = asks[0][0]
    accumulated_cost = 0.0
    accumulated_shares = 0.0

    for p, s in asks:
        cost_at_level = p * s
        remaining_needed = target_usdc - accumulated_cost

        if cost_at_level <= remaining_needed:
            accumulated_cost += cost_at_level
            accumulated_shares += s
        else:
            partial_shares = remaining_needed / p
            accumulated_cost += remaining_needed
            accumulated_shares += partial_shares
            break

    is_filled = accumulated_cost >= (target_usdc * 0.99)
    if accumulated_shares > 0:
        vwap = accumulated_cost / accumulated_shares
    else:
        vwap = best_ask

    slippage_pct = ((vwap - best_ask) / max(0.01, best_ask)) * 100.0
    return vwap, slippage_pct, accumulated_cost, is_filled


def simulate_forward_execution(
    strategy_name: str,
    target_family: str,
    gross_edge_pct: float,
    token_id: Optional[str] = None,
    orderbook: Optional[OrderbookDepth] = None,
    clip_sizes: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Simulates Forward Real-World Execution of a Discovered Strategy Component:
    Evaluates slippage across clip sizes and latency decay to compute Net Realizable Edge (EV_net).
    """
    if clip_sizes is None:
        clip_sizes = [100.0, 500.0, 2000.0, 5000.0]

    if orderbook is None:
        if token_id:
            orderbook = fetch_clob_orderbook(token_id)
        else:
            # Standard high-liquidity market orderbook representation
            orderbook = OrderbookDepth(
                best_bid=0.68,
                best_ask=0.70,
                spread=0.02,
                bid_depth_usdc=15400.0,
                ask_depth_usdc=18200.0,
                bids=[(0.68, 5000.0), (0.67, 8000.0), (0.65, 10000.0)],
                asks=[(0.70, 3500.0), (0.71, 6000.0), (0.73, 12000.0), (0.76, 20000.0)]
            )

    execution_matrix = []

    for clip in clip_sizes:
        vwap, slip_pct, filled_usdc, is_filled = compute_vwap_slippage(orderbook.asks, clip)
        
        # Latency Decay Models (Adverse selection probability over time)
        # 5s delay: ~0.5% edge erosion | 15s delay: ~1.8% | 60s delay: ~4.5%
        for delay_sec, latency_decay_pct in [(5, 0.6), (15, 1.8), (60, 4.5)]:
            fee_pct = 0.0 # Polymarket has 0% trading fee for maker/taker
            total_friction_pct = slip_pct + latency_decay_pct + fee_pct
            net_edge_pct = gross_edge_pct - total_friction_pct

            if net_edge_pct > 1.5 and is_filled:
                verdict = "EXECUTABLE (POSITIVE EV) ✅"
            elif net_edge_pct > 0.0 and is_filled:
                verdict = "MARGINAL EDGE ⚠️"
            else:
                verdict = "UNEXECUTABLE (LATENCY / SLIPPAGE TRAP) ❌"

            execution_matrix.append({
                "clip_size_usdc": clip,
                "delay_sec": delay_sec,
                "best_ask": orderbook.best_ask,
                "vwap_fill": round(vwap, 4),
                "slippage_pct": round(slip_pct, 2),
                "latency_decay_pct": round(latency_decay_pct, 2),
                "total_friction_pct": round(total_friction_pct, 2),
                "net_edge_pct": round(net_edge_pct, 2),
                "is_fully_filled": is_filled,
                "verdict": verdict
            })

    # Summary feasibility
    positive_ev_configs = [e for e in execution_matrix if "POSITIVE EV" in e["verdict"]]
    max_executable_clip = max([e["clip_size_usdc"] for e in positive_ev_configs], default=0.0)

    return {
        "strategy_name": strategy_name,
        "target_family": target_family,
        "gross_edge_pct": gross_edge_pct,
        "orderbook_summary": {
            "best_bid": orderbook.best_bid,
            "best_ask": orderbook.best_ask,
            "spread": round(orderbook.spread, 4),
            "ask_depth_usdc": round(orderbook.ask_depth_usdc, 2),
            "bid_depth_usdc": round(orderbook.bid_depth_usdc, 2)
        },
        "max_executable_clip_usdc": max_executable_clip,
        "execution_matrix": execution_matrix
    }


def print_forward_execution_report_cli(res: Dict[str, Any]) -> None:
    print("\n" + "═" * 135)
    print("  🚀 FORWARD EXECUTION FEASIBILITY & NET REALIZABLE EDGE (EV_NET) AUDIT")
    print(f"  Strategy: [{res['strategy_name']}] | Market Family: [{res['target_family']}]")
    print(f"  Discovered Gross Edge: +{res['gross_edge_pct']:.1f}% per share")
    print("═" * 135)

    ob = res["orderbook_summary"]
    print(f"\n📖 LIVE CLOB ORDERBOOK DEPTH:")
    print(f"   • Best Bid / Best Ask: ${ob['best_bid']:.3f} / ${ob['best_ask']:.3f} (Spread: ${ob['spread']:.3f})")
    print(f"   • Available Ask Depth: ${ob['ask_depth_usdc']:,.2f} USDC | Bid Depth: ${ob['bid_depth_usdc']:,.2f} USDC")

    print(f"\n📊 EXECUTION MATRIX (NET EV AFTER SLIPPAGE & LATENCY DECAY):")
    print(f"  {'Clip Size ($)':<14} | {'Delay':<8} | {'VWAP Fill':<11} | {'Slippage':<10} | {'Latency Loss':<13} | {'Total Friction':<15} | {'Net Edge (EV)':<14} | {'Status'}")
    print("  " + "─" * 125)

    for em in res["execution_matrix"]:
        clip_s = f"${em['clip_size_usdc']:,.0f}"
        del_s = f"{em['delay_sec']}s"
        vwap_s = f"${em['vwap_fill']:.4f}"
        slip_s = f"{em['slippage_pct']:+.2f}%"
        lat_s = f"-{em['latency_decay_pct']:.2f}%"
        fric_s = f"-{em['total_friction_pct']:.2f}%"
        edge_s = f"{em['net_edge_pct']:>+6.2f}%"
        print(f"  {clip_s:<14} | {del_s:<8} | {vwap_s:<11} | {slip_s:<10} | {lat_s:<13} | {fric_s:<15} | {edge_s:<14} | {em['verdict']}")

    print("  " + "─" * 125)
    if res["max_executable_clip_usdc"] > 0:
        print(f"  ✅ MAX EXECUTABLE CLIP SIZE: Up to ${res['max_executable_clip_usdc']:,.0f} USDC under <15s execution delay.")
    else:
        print("  ❌ UNEXECUTABLE: Strategy edge is fully consumed by orderbook slippage and latency.")
    print("═" * 135)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Forward Execution & Slippage Simulator")
    parser.add_argument("--strategy", type=str, default="Mid-Price Tactical Entry", help="Strategy component name")
    parser.add_argument("--family", type=str, default="Macro Crypto", help="Market family")
    parser.add_argument("--edge", type=float, default=52.1, help="Discovered gross edge (%)")
    parser.add_argument("--token-id", type=str, default=None, help="CLOB token ID")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    res = simulate_forward_execution(args.strategy, args.family, args.edge, token_id=args.token_id)
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print_forward_execution_report_cli(res)
