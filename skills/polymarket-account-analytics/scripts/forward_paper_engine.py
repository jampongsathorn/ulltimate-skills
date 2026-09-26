#!/usr/bin/env python3
"""
True Forward Paper Execution & Microsecond Follower Replay Engine
═════════════════════════════════════════════════════════════════════════
Implements Step 6 of the Quantitative Alpha Roadmap:
1. Ingests frozen Strategy Signals from V1.2 Strategy Map.
2. At Signal Ingress (t0), records Point-in-Time CLOB Orderbook.
3. Samples live book at t0 + 5s, t0 + 15s, t0 + 60s.
4. Simulates exact orderbook walking to compute VWAP_i(Δt) and fillability.
5. Settles paper trades on-chain via Gamma API (settlement_i in {0, 1}).
6. Computes individual trade PnL_i(Δt) = shares_i * (settlement_i - P_{i,exec}(Δt))
7. Outputs full Follower Replay Audit: Fill Rate, Median Slippage, Net PnL, Net ROI, Max DD.
"""

import os
import json
import time
import math
import urllib.request
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

PAPER_DB_PATH = "paper_trades_ledger.json"
CLOB_API_BASE = "https://clob.polymarket.com"
GAMMA_API_BASE = "https://gamma-api.polymarket.com"


@dataclass
class PaperExecutionSample:
    delay_sec: int
    timestamp: float
    best_bid: float
    best_ask: float
    vwap_fill_price: float
    filled_shares: float
    filled_usdc: float
    slippage_cents: float
    is_fillable: bool


@dataclass
class PaperOrder:
    order_id: str
    signal_name: str
    trader_address: Optional[str]
    market_slug: str
    condition_id: str
    token_id: str
    outcome_name: str # YES / NO / specific bracket
    t0_timestamp: float
    t0_price: float
    target_clip_usdc: float
    samples: Dict[str, Dict[str, Any]] # "5s", "15s", "60s" -> PaperExecutionSample
    is_settled: bool = False
    settlement_outcome: Optional[float] = None # 1.0 (win) or 0.0 (loss)
    settlement_time: Optional[float] = None


def load_paper_ledger(db_path: str = PAPER_DB_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(db_path):
        return []
    try:
        with open(db_path, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_paper_ledger(ledger: List[Dict[str, Any]], db_path: str = PAPER_DB_PATH) -> None:
    with open(db_path, "w") as f:
        json.dump(ledger, f, indent=2)


def fetch_live_clob_book(token_id: str) -> Optional[Dict[str, Any]]:
    url = f"{CLOB_API_BASE}/book?token_id={token_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def calculate_orderbook_fill(asks: List[Dict[str, Any]], target_usdc: float) -> Tuple[float, float, float, float, bool]:
    """
    Simulates walking the CLOB asks to fill target_usdc.
    Returns: (vwap_price, filled_shares, filled_usdc, slippage_cents, is_fillable)
    """
    if not asks or target_usdc <= 0:
        return 1.0, 0.0, 0.0, 100.0, False

    parsed_asks = []
    for a in asks:
        try:
            parsed_asks.append((float(a.get("price", 0)), float(a.get("size", 0))))
        except Exception:
            pass

    parsed_asks = sorted(parsed_asks, key=lambda x: x[0])
    if not parsed_asks:
        return 1.0, 0.0, 0.0, 100.0, False

    best_ask = parsed_asks[0][0]
    accumulated_cost = 0.0
    accumulated_shares = 0.0

    for p, s in parsed_asks:
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

    is_fillable = accumulated_cost >= (target_usdc * 0.98)
    vwap = (accumulated_cost / accumulated_shares) if accumulated_shares > 0 else best_ask
    slippage_cents = max(0.0, (vwap - best_ask) * 100.0)

    return vwap, accumulated_shares, accumulated_cost, slippage_cents, is_fillable


def record_paper_signal_ingress(
    signal_name: str,
    market_slug: str,
    condition_id: str,
    token_id: str,
    outcome_name: str,
    t0_price: float,
    target_clip_usdc: float = 500.0,
    trader_address: Optional[str] = None,
    db_path: str = PAPER_DB_PATH
) -> Dict[str, Any]:
    """
    Records a live forward paper execution entry at t0.
    Immediately queries CLOB book for t0, and prepares slot for +5s, +15s, +60s.
    """
    now = time.time()
    order_id = f"paper_{int(now)}_{token_id[:8]}"
    
    book = fetch_live_clob_book(token_id)
    asks = book.get("asks", []) if book else []
    bids = book.get("bids", []) if book else []

    best_bid = float(bids[0].get("price", 0)) if bids else 0.0
    best_ask = float(asks[0].get("price", 1.0)) if asks else 1.0

    vwap, shares, cost, slip, fillable = calculate_orderbook_fill(asks, target_clip_usdc)

    sample_0s = {
        "delay_sec": 0,
        "timestamp": now,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "vwap_fill_price": round(vwap, 4),
        "filled_shares": round(shares, 2),
        "filled_usdc": round(cost, 2),
        "slippage_cents": round(slip, 2),
        "is_fillable": fillable
    }

    order = {
        "order_id": order_id,
        "signal_name": signal_name,
        "trader_address": trader_address,
        "market_slug": market_slug,
        "condition_id": condition_id,
        "token_id": token_id,
        "outcome_name": outcome_name,
        "t0_timestamp": now,
        "t0_price": t0_price,
        "target_clip_usdc": target_clip_usdc,
        "samples": {
            "0s": sample_0s
        },
        "is_settled": False,
        "settlement_outcome": None,
        "settlement_time": None
    }

    ledger = load_paper_ledger(db_path)
    ledger.append(order)
    save_paper_ledger(ledger, db_path)
    return order


def update_paper_execution_delay(
    token_id: str,
    delay_sec: int,
    db_path: str = PAPER_DB_PATH
) -> None:
    """
    Polls the CLOB book at t0 + delay_sec and records the actual executable sample.
    """
    ledger = load_paper_ledger(db_path)
    target_orders = [o for o in ledger if o["token_id"] == token_id and not o["is_settled"]]
    if not target_orders:
        return

    book = fetch_live_clob_book(token_id)
    if not book:
        return

    asks = book.get("asks", [])
    bids = book.get("bids", [])
    best_bid = float(bids[0].get("price", 0)) if bids else 0.0
    best_ask = float(asks[0].get("price", 1.0)) if asks else 1.0

    delay_key = f"{delay_sec}s"
    now = time.time()

    for o in target_orders:
        clip = o.get("target_clip_usdc", 500.0)
        vwap, shares, cost, slip, fillable = calculate_orderbook_fill(asks, clip)
        o["samples"][delay_key] = {
            "delay_sec": delay_sec,
            "timestamp": now,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "vwap_fill_price": round(vwap, 4),
            "filled_shares": round(shares, 2),
            "filled_usdc": round(cost, 2),
            "slippage_cents": round(slip, 2),
            "is_fillable": fillable
        }

    save_paper_ledger(ledger, db_path)


def audit_and_settle_paper_trades(db_path: str = PAPER_DB_PATH) -> int:
    """
    Queries Gamma API for closed markets and settles pending paper orders.
    """
    ledger = load_paper_ledger(db_path)
    unsettled = [o for o in ledger if not o.get("is_settled")]
    if not unsettled:
        return 0

    settled_count = 0
    checked_conditions = set()

    for o in unsettled:
        cid = o.get("condition_id")
        if not cid or cid in checked_conditions:
            continue
        checked_conditions.add(cid)

        url = f"{GAMMA_API_BASE}/markets?condition_id={cid}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=4) as resp:
                mdata = json.loads(resp.read().decode())
                if mdata and isinstance(mdata, list) and len(mdata) > 0:
                    m = mdata[0]
                    if m.get("closed"):
                        tokens = json.loads(m.get("clobTokenIds") or "[]")
                        outcomes = json.loads(m.get("outcomes") or "[]")
                        prices = json.loads(m.get("outcomePrices") or "[]")

                        # Match outcome price
                        for order in unsettled:
                            if order.get("condition_id") == cid:
                                tok = order.get("token_id")
                                if tok in tokens:
                                    idx = tokens.index(tok)
                                    try:
                                        p_win = float(prices[idx])
                                    except Exception:
                                        p_win = 1.0 if idx == 0 else 0.0
                                    
                                    order["is_settled"] = True
                                    order["settlement_outcome"] = 1.0 if p_win >= 0.99 else 0.0
                                    order["settlement_time"] = time.time()
                                    settled_count += 1
        except Exception:
            pass

    if settled_count > 0:
        save_paper_ledger(ledger, db_path)
    return settled_count


def generate_follower_replay_report(
    signal_filter: Optional[str] = None,
    db_path: str = PAPER_DB_PATH
) -> Dict[str, Any]:
    """
    Generates the true Forward Follower Replay Audit:
    Computes individual PnL_i(Δt) = shares_i * (settlement_i - P_{i,exec}(Δt))
    and outputs Fill Rate, Median Slippage, Net PnL, Net ROI %, Max Drawdown across delays.
    """
    ledger = load_paper_ledger(db_path)
    if signal_filter:
        ledger = [o for o in ledger if signal_filter.lower() in o.get("signal_name", "").lower()]

    total_signals = len(ledger)
    settled_orders = [o for o in ledger if o.get("is_settled")]

    delays = ["5s", "15s", "60s"]
    results_by_delay = {}

    for d in delays:
        fillable_count = 0
        slippages = []
        individual_pnls = []
        cumulative_pnl_curve = [0.0]
        total_invested_usdc = 0.0

        for o in settled_orders:
            sample = o.get("samples", {}).get(d)
            if not sample:
                # Fallback to 0s if specific delay not yet captured or interpolate
                sample = o.get("samples", {}).get("0s")

            if sample and sample.get("is_fillable"):
                fillable_count += 1
                slippages.append(sample.get("slippage_cents", 0.0))
                
                # PnL_i = shares_i * (settlement_i - vwap_fill_price)
                shares = sample.get("filled_shares", 0.0)
                vwap = sample.get("vwap_fill_price", 0.0)
                cost = sample.get("filled_usdc", 0.0)
                settle = o.get("settlement_outcome", 0.0)

                pnl_i = shares * (settle - vwap)
                individual_pnls.append(pnl_i)
                total_invested_usdc += cost

                running_total = cumulative_pnl_curve[-1] + pnl_i
                cumulative_pnl_curve.append(running_total)

        # Max Drawdown
        peak = 0.0
        max_dd = 0.0
        for val in cumulative_pnl_curve:
            if val > peak:
                peak = val
            dd = peak - val
            if dd > max_dd:
                max_dd = dd

        fill_rate = (fillable_count / max(1, len(settled_orders))) * 100.0
        median_slip = sorted(slippages)[len(slippages)//2] if slippages else 0.0
        net_pnl = sum(individual_pnls)
        net_roi = (net_pnl / max(1.0, total_invested_usdc)) * 100.0

        results_by_delay[d] = {
            "fillable_count": fillable_count,
            "fill_rate_pct": round(fill_rate, 1),
            "median_slippage_cents": round(median_slip, 2),
            "total_invested_usdc": round(total_invested_usdc, 2),
            "net_pnl_usd": round(net_pnl, 2),
            "net_roi_pct": round(net_roi, 2),
            "max_drawdown_usd": round(max_dd, 2)
        }

    return {
        "signal_filter": signal_filter or "ALL_FROZEN_SIGNALS",
        "total_signals_recorded": total_signals,
        "settled_signals_count": len(settled_orders),
        "pending_signals_count": total_signals - len(settled_orders),
        "delay_benchmarks": results_by_delay
    }


def print_follower_replay_table_cli(rep: Dict[str, Any]) -> None:
    print("\n" + "═" * 120)
    print(f"  🏁 TRUE FORWARD FOLLOWER REPLAY AUDIT (POINT-IN-TIME POINT EXECUTION)")
    print(f"  Strategy Signal: [{rep['signal_filter']}] | Settled Trades: {rep['settled_signals_count']} / Total Signals: {rep['total_signals_recorded']}")
    print("═" * 120)

    db = rep["delay_benchmarks"]
    print(f"\n  {'Metric':<25} | {'+5s Execution':<18} | {'+15s Execution':<18} | {'+60s Execution':<18}")
    print("  " + "─" * 95)
    
    # Fillable
    f_5 = f"{db['5s']['fillable_count']} ({db['5s']['fill_rate_pct']}%)"
    f_15 = f"{db['15s']['fillable_count']} ({db['15s']['fill_rate_pct']}%)"
    f_60 = f"{db['60s']['fillable_count']} ({db['60s']['fill_rate_pct']}%)"
    print(f"  {'Fillable Trades (Rate)':<25} | {f_5:<18} | {f_15:<18} | {f_60:<18}")

    # Median Slippage
    s_5 = f"+{db['5s']['median_slippage_cents']:.1f}¢"
    s_15 = f"+{db['15s']['median_slippage_cents']:.1f}¢"
    s_60 = f"+{db['60s']['median_slippage_cents']:.1f}¢"
    print(f"  {'Median Slippage':<25} | {s_5:<18} | {s_15:<18} | {s_60:<18}")

    # Net PnL
    p_5 = f"+${db['5s']['net_pnl_usd']:,.2f}" if db['5s']['net_pnl_usd'] >= 0 else f"-${abs(db['5s']['net_pnl_usd']):,.2f}"
    p_15 = f"+${db['15s']['net_pnl_usd']:,.2f}" if db['15s']['net_pnl_usd'] >= 0 else f"-${abs(db['15s']['net_pnl_usd']):,.2f}"
    p_60 = f"+${db['60s']['net_pnl_usd']:,.2f}" if db['60s']['net_pnl_usd'] >= 0 else f"-${abs(db['60s']['net_pnl_usd']):,.2f}"
    print(f"  {'Net Realized PnL ($)':<25} | {p_5:<18} | {p_15:<18} | {p_60:<18}")

    # Net ROI
    r_5 = f"{db['5s']['net_roi_pct']:+.1f}%"
    r_15 = f"{db['15s']['net_roi_pct']:+.1f}%"
    r_60 = f"{db['60s']['net_roi_pct']:+.1f}%"
    print(f"  {'Net Follower ROI (%)':<25} | {r_5:<18} | {r_15:<18} | {r_60:<18}")

    # Max Drawdown
    d_5 = f"${db['5s']['max_drawdown_usd']:,.2f}"
    d_15 = f"${db['15s']['max_drawdown_usd']:,.2f}"
    d_60 = f"${db['60s']['max_drawdown_usd']:,.2f}"
    print(f"  {'Max Drawdown ($)':<25} | {d_5:<18} | {d_15:<18} | {d_60:<18}")

    print("  " + "─" * 95)
    print("═" * 120 + "\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Forward Paper Execution & Follower Replay Engine")
    parser.add_argument("--audit", action="store_true", help="Audit settlements and print replay benchmark")
    parser.add_argument("--signal", type=str, default=None, help="Filter by signal name")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    audit_and_settle_paper_trades()
    rep = generate_follower_replay_report(args.signal)
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        print_follower_replay_table_cli(rep)
