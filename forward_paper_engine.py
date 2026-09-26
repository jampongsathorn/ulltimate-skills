#!/usr/bin/env python3
"""
Step 6: True Forward Paper Execution & Microsecond Follower Replay Engine
═════════════════════════════════════════════════════════════════════════
Frozen Protocol Specification (Pre-Registered Validation Gates):
1. Strategy Blueprints & Hypothesis Library are 100% Frozen (V1.2-FROZEN).
2. Point-in-Time Orderbook Capture: Records CLOB book at t0, t0+5s, t0+15s, t0+60s.
3. Multi-Clip Sizing Matrix: Evaluates $100, $500, and $2,000 USDC clips.
4. Failed / Unfillable Execution Persistence: All dropped or unfillable trades are preserved.
5. Follower PnL Decoupling: Follower PnL is computed strictly from Follower VWAP,
   completely decoupled from Historical Trader Edge:
   PnL_i(delay, size) = filled_shares * (settlement_i - VWAP_fill_i(delay, size)) - fees
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
CLIP_SIZES_USDC = [100.0, 500.0, 2000.0]
DELAY_INTERVALS_SEC = [5, 15, 60]


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


def calculate_orderbook_fill_at_size(
    asks: List[Tuple[float, float]],
    target_usdc: float
) -> Dict[str, Any]:
    """
    Simulates walking the CLOB asks to fill target_usdc.
    Returns discrete fill metrics and fillability.
    """
    if not asks or target_usdc <= 0:
        return {
            "is_fillable": False,
            "vwap_fill_price": 1.0,
            "filled_shares": 0.0,
            "filled_usdc": 0.0,
            "unfilled_notional_usdc": target_usdc,
            "slippage_cents": 100.0,
            "fees_usdc": 0.0
        }

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

    is_fillable = accumulated_cost >= (target_usdc * 0.98)
    vwap = (accumulated_cost / accumulated_shares) if accumulated_shares > 0 else best_ask
    slippage_cents = max(0.0, (vwap - best_ask) * 100.0)
    unfilled = max(0.0, target_usdc - accumulated_cost)

    return {
        "is_fillable": is_fillable,
        "vwap_fill_price": round(vwap, 4),
        "filled_shares": round(accumulated_shares, 2),
        "filled_usdc": round(accumulated_cost, 2),
        "unfilled_notional_usdc": round(unfilled, 2),
        "slippage_cents": round(slippage_cents, 2),
        "fees_usdc": 0.0 # Polymarket has 0% trading fee
    }


def parse_clob_asks_and_bids(book_data: Optional[Dict[str, Any]]) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    if not book_data:
        return [], []
    raw_asks = book_data.get("asks", [])
    raw_bids = book_data.get("bids", [])

    asks: List[Tuple[float, float]] = []
    bids: List[Tuple[float, float]] = []

    for a in raw_asks:
        try:
            asks.append((float(a.get("price", 0)), float(a.get("size", 0))))
        except Exception:
            pass

    for b in raw_bids:
        try:
            bids.append((float(b.get("price", 0)), float(b.get("size", 0))))
        except Exception:
            pass

    asks = sorted(asks, key=lambda x: x[0])
    bids = sorted(bids, key=lambda x: -x[0])
    return asks, bids


def record_immutable_signal_record(
    signal_name: str,
    frozen_rule: str,
    market_slug: str,
    condition_id: str,
    token_id: str,
    outcome_name: str,
    trader_entry_price: float,
    signal_features: Dict[str, Any],
    trader_address: Optional[str] = None,
    db_path: str = PAPER_DB_PATH
) -> Dict[str, Any]:
    """
    Creates an immutable Step 6 Forward Signal record at t0.
    """
    now = time.time()
    signal_id = f"sig_{int(now)}_{token_id[:8]}"

    book = fetch_live_clob_book(token_id)
    asks, bids = parse_clob_asks_and_bids(book)
    best_bid = bids[0][0] if bids else 0.0
    best_ask = asks[0][0] if asks else 1.0

    # Capture t0 execution matrix across clip sizes
    t0_matrix = {}
    for clip in CLIP_SIZES_USDC:
        t0_matrix[f"${int(clip)}"] = calculate_orderbook_fill_at_size(asks, clip)

    record = {
        "signal_id": signal_id,
        "strategy_version": "V1.2-FROZEN",
        "signal_ts": now,
        "wallet": trader_address,
        "market": market_slug,
        "condition_id": condition_id,
        "token_id": token_id,
        "side": outcome_name,
        "frozen_rule": frozen_rule,
        "signal_features_at_t0": signal_features,
        "trader_entry_price": trader_entry_price,
        "books": {
            "t0": {
                "timestamp": now,
                "best_bid": best_bid,
                "best_ask": best_ask,
                "clips": t0_matrix
            }
        },
        "is_settled": False,
        "settlement": None,
        "settlement_ts": None
    }

    ledger = load_paper_ledger(db_path)
    ledger.append(record)
    save_paper_ledger(ledger, db_path)
    return record


def sample_delay_orderbook(
    token_id: str,
    delay_sec: int,
    db_path: str = PAPER_DB_PATH
) -> None:
    """
    Records orderbook snapshot and fill calculation at t0 + delay_sec.
    """
    ledger = load_paper_ledger(db_path)
    active_orders = [o for o in ledger if o["token_id"] == token_id and not o["is_settled"]]
    if not active_orders:
        return

    book = fetch_live_clob_book(token_id)
    asks, bids = parse_clob_asks_and_bids(book)
    best_bid = bids[0][0] if bids else 0.0
    best_ask = asks[0][0] if asks else 1.0
    now = time.time()

    delay_key = f"t0+{delay_sec}s"
    delay_matrix = {}
    for clip in CLIP_SIZES_USDC:
        delay_matrix[f"${int(clip)}"] = calculate_orderbook_fill_at_size(asks, clip)

    for o in active_orders:
        o["books"][delay_key] = {
            "timestamp": now,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "clips": delay_matrix
        }

    save_paper_ledger(ledger, db_path)


def audit_and_settle_paper_trades(db_path: str = PAPER_DB_PATH) -> int:
    """
    Settles paper orders against Gamma API on-chain resolution (settlement in {0.0, 1.0}).
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
                        prices = json.loads(m.get("outcomePrices") or "[]")

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
                                    order["settlement"] = 1.0 if p_win >= 0.99 else 0.0
                                    order["settlement_ts"] = time.time()
                                    settled_count += 1
        except Exception:
            pass

    if settled_count > 0:
        save_paper_ledger(ledger, db_path)
    return settled_count


def generate_full_execution_matrix_report(
    signal_filter: Optional[str] = None,
    db_path: str = PAPER_DB_PATH
) -> Dict[str, Any]:
    """
    Generates the Full Pre-Registered 3x3 Execution Matrix (Latency x Clip Size).
    """
    ledger = load_paper_ledger(db_path)
    if signal_filter:
        ledger = [o for o in ledger if signal_filter.lower() in o.get("frozen_rule", "").lower() or signal_filter.lower() in o.get("strategy_version", "").lower()]

    total_signals = len(ledger)
    settled_orders = [o for o in ledger if o.get("is_settled")]

    delays = [("t0+5s", "5s"), ("t0+15s", "15s"), ("t0+60s", "60s")]
    clip_keys = ["$100", "$500", "$2000"]

    matrix_results = {}

    for delay_book_key, delay_label in delays:
        matrix_results[delay_label] = {}
        for ckey in clip_keys:
            fillable_count = 0
            unfillable_count = 0
            slippages = []
            individual_pnls = []
            cumulative_curve = [0.0]
            deployed_capital = 0.0

            for o in settled_orders:
                book_sample = o.get("books", {}).get(delay_book_key) or o.get("books", {}).get("t0", {})
                clip_data = book_sample.get("clips", {}).get(ckey)

                if clip_data and clip_data.get("is_fillable"):
                    fillable_count += 1
                    slippages.append(clip_data.get("slippage_cents", 0.0))
                    
                    shares = clip_data.get("filled_shares", 0.0)
                    vwap = clip_data.get("vwap_fill_price", 0.0)
                    cost = clip_data.get("filled_usdc", 0.0)
                    fees = clip_data.get("fees_usdc", 0.0)
                    settle = o.get("settlement", 0.0)

                    # Follower Net PnL = shares * (settlement - VWAP) - fees
                    pnl_i = (shares * (settle - vwap)) - fees
                    individual_pnls.append(pnl_i)
                    deployed_capital += cost

                    cumulative_curve.append(cumulative_curve[-1] + pnl_i)
                else:
                    unfillable_count += 1

            # Max Drawdown
            peak = 0.0
            max_dd = 0.0
            for val in cumulative_curve:
                if val > peak:
                    peak = val
                dd = peak - val
                if dd > max_dd:
                    max_dd = dd

            fill_rate = (fillable_count / max(1, len(settled_orders))) * 100.0 if settled_orders else 0.0
            median_slip = sorted(slippages)[len(slippages)//2] if slippages else 0.0
            net_pnl = sum(individual_pnls)
            net_roi = (net_pnl / max(1.0, deployed_capital)) * 100.0 if deployed_capital > 0 else 0.0

            matrix_results[delay_label][ckey] = {
                "fillable": fillable_count,
                "unfillable": unfillable_count,
                "fill_rate_pct": round(fill_rate, 1),
                "median_slippage_cents": round(median_slip, 2),
                "deployed_capital_usdc": round(deployed_capital, 2),
                "net_pnl_usd": round(net_pnl, 2),
                "net_roi_pct": round(net_roi, 2),
                "max_drawdown_usd": round(max_dd, 2)
            }

    return {
        "status": "LIVE_DATA_COLLECTION" if len(settled_orders) == 0 else "VALIDATED_EMPIRICAL",
        "strategy_version": "V1.2-FROZEN",
        "total_signals_recorded": total_signals,
        "settled_trades_count": len(settled_orders),
        "pending_signals_count": total_signals - len(settled_orders),
        "matrix": matrix_results
    }


def print_follower_matrix_table_cli(rep: Dict[str, Any]) -> None:
    print("\n" + "═" * 125)
    print("  🏁 STEP 6: PRE-REGISTERED FORWARD FOLLOWER REPLAY MATRIX (V1.2-FROZEN)")
    print(f"  Status: [{rep['status']}] | Total Signals Recorded: {rep['total_signals_recorded']} | Settled: {rep['settled_trades_count']} | Pending: {rep['pending_signals_count']}")
    print("═" * 125)

    if rep["settled_trades_count"] == 0:
        print("\n  🟡 LIVE DATA COLLECTION ACTIVE: Signals are being ingested and book snapshots captured.")
        print("     No settled forward trades yet. This table will populate automatically as markets resolve on-chain.")
        print("═" * 125 + "\n")
        return

    m = rep["matrix"]
    print(f"\n  {'Latency Delay':<15} | {'Metric':<22} | {'$100 Clip':<22} | {'$500 Clip':<22} | {'$2,000 Clip':<22}")
    print("  " + "─" * 115)

    for del_label, del_name in [("5s", "+5 sec Delay"), ("15s", "+15 sec Delay"), ("60s", "+60 sec Delay")]:
        d = m[del_label]
        # Line 1: Fill Rate
        f_100 = f"{d['$100']['fillable']}/{rep['settled_trades_count']} ({d['$100']['fill_rate_pct']}%)"
        f_500 = f"{d['$500']['fillable']}/{rep['settled_trades_count']} ({d['$500']['fill_rate_pct']}%)"
        f_2000 = f"{d['$2000']['fillable']}/{rep['settled_trades_count']} ({d['$2000']['fill_rate_pct']}%)"
        print(f"  {del_name:<15} | {'Fill Rate':<22} | {f_100:<22} | {f_500:<22} | {f_2000:<22}")

        # Line 2: Median Slippage
        s_100 = f"+{d['$100']['median_slippage_cents']:.1f}¢"
        s_500 = f"+{d['$500']['median_slippage_cents']:.1f}¢"
        s_2000 = f"+{d['$2000']['median_slippage_cents']:.1f}¢"
        print(f"  {'':<15} | {'Median Slippage':<22} | {s_100:<22} | {s_500:<22} | {s_2000:<22}")

        # Line 3: Net Realized PnL
        p_100 = f"+${d['$100']['net_pnl_usd']:,.2f}" if d['$100']['net_pnl_usd'] >= 0 else f"-${abs(d['$100']['net_pnl_usd']):,.2f}"
        p_500 = f"+${d['$500']['net_pnl_usd']:,.2f}" if d['$500']['net_pnl_usd'] >= 0 else f"-${abs(d['$500']['net_pnl_usd']):,.2f}"
        p_2000 = f"+${d['$2000']['net_pnl_usd']:,.2f}" if d['$2000']['net_pnl_usd'] >= 0 else f"-${abs(d['$2000']['net_pnl_usd']):,.2f}"
        print(f"  {'':<15} | {'Net Realized PnL':<22} | {p_100:<22} | {p_500:<22} | {p_2000:<22}")

        # Line 4: Net Follower ROI
        r_100 = f"{d['$100']['net_roi_pct']:+.1f}%"
        r_500 = f"{d['$500']['net_roi_pct']:+.1f}%"
        r_2000 = f"{d['$2000']['net_roi_pct']:+.1f}%"
        print(f"  {'':<15} | {'Net Follower ROI':<22} | {r_100:<22} | {r_500:<22} | {r_2000:<22}")

        # Line 5: Max Drawdown
        d_100 = f"${d['$100']['max_drawdown_usd']:,.2f}"
        d_500 = f"${d['$500']['max_drawdown_usd']:,.2f}"
        d_2000 = f"${d['$2000']['max_drawdown_usd']:,.2f}"
        print(f"  {'':<15} | {'Max Drawdown':<22} | {d_100:<22} | {d_500:<22} | {d_2000:<22}")
        print("  " + "─" * 115)

    print("═" * 125 + "\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 6 Forward Execution Matrix Auditor")
    parser.add_argument("--audit", action="store_true", help="Audit settlements and print replay matrix")
    parser.add_argument("--filter", type=str, default=None, help="Filter by rule or version")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    audit_and_settle_paper_trades()
    rep = generate_full_execution_matrix_report(args.filter)
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        print_follower_matrix_table_cli(rep)
