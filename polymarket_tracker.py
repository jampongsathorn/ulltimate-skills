#!/usr/bin/env python3
"""
Polymarket Unified Analytics & Quantitative Tracker Engine (polymarket_tracker.py)
----------------------------------------------------------------------------------
Features:
1. True Merged Settlement Accounting with Complete Exhaustive Pagination
2. 3-Tier Market Hierarchy (market_slug -> event_id -> slug_group)
3. 3-Dimensional Trader Quality (Signal Quality | Sizing Quality | Evidence)
4. Strict Quantitative Evaluation Hierarchy:
   Signal Edge -> Capital Edge -> N_eff -> Rolling Walk-Forward Consistency
5. Multi-Fold Rolling Walk-Forward Out-of-Sample Engine
6. Meta-Backtest & Fixed-Budget Copy-Trading Portfolio Simulation
"""

import sys
import os
import json
import re
import math
import urllib.request
import urllib.parse
import argparse
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple

BASE_DATA_API = "https://data-api.polymarket.com"
BASE_GAMMA_API = "https://gamma-api.polymarket.com"

# ── 1. Slug Group Patterns (Cross-Market Generalization) ──────────────────────

SLUG_GROUP_PATTERNS = [
    ("highest-temp", r"highest-temp|highest-temperature"),
    ("lowest-temp", r"lowest-temp|lowest-temperature"),
    ("precipitation-weather", r"rain|snow|hurricane|weather|precipitation|celsius|fahrenheit"),
    ("btc-price", r"btc|bitcoin"),
    ("eth-price", r"eth|ethereum"),
    ("crypto-updown", r"up-or-down|updown|5m|15m|1h|sol|solana|crypto"),
    ("fed-rates", r"fed-|interest-rate|powell|rate-cut|fomc|basis-point"),
    ("us-politics", r"president|election|trump|harris|biden|democrat|republican|senate|governor|mayor|vote|poll|white-house"),
    ("sports-soccer", r"fifa|soccer|premier-league|champions-league|epl|la-liga|serie-a|bundesliga|world-cup"),
    ("sports-nba-basketball", r"nba|basketball|lakers|celtics|warriors|knicks"),
    ("sports-nfl-football", r"nfl|football|chiefs|49ers|patriots|super-bowl"),
    ("sports-general", r"tennis|ufc|chess|f1|formula|spread|winner-202|nhl|mlb|olympics"),
    ("tech-ai", r"claude|anthropic|openai|chatgpt|gpt|ai-|deepmind|gemini|nvidia"),
    ("pop-culture", r"spacex|starship|musk|box-office|movie|oscar|grammy|taylor|cavill")
]

def extract_slug_group(slug: str, event_slug: str, title: str) -> str:
    text = f"{slug} {event_slug} {title}".lower()
    for group_name, pattern in SLUG_GROUP_PATTERNS:
        if re.search(pattern, text):
            return group_name
    return "other"

def extract_event_id(slug: str, event_slug: str, title: str) -> str:
    if event_slug and event_slug.strip():
        return event_slug.strip().lower()
    
    s = slug.lower().strip()
    s = re.sub(r"-\d+-\d+f$", "", s)
    s = re.sub(r"-\d+f-or-(higher|below|more|less)$", "", s)
    s = re.sub(r"-\d+f$", "", s)
    s = re.sub(r"-(yes|no)$", "", s)
    return s or title.lower().strip()

# ── 2. HTTP API Client ─────────────────────────────────────────────────────────

def make_request(url: str, timeout: int = 15) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PolymarketUnifiedTracker/6.5 (Copy-Trading Meta; Python)",
            "Accept": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

def fetch_leaderboard(
    time_period: str = "ALL",
    limit: int = 25,
    order_by: str = "PNL",
    category: str = "OVERALL"
) -> List[Dict[str, Any]]:
    params = {
        "timePeriod": time_period.upper(),
        "limit": str(min(limit, 50)),
        "orderBy": order_by.upper(),
        "category": category.upper()
    }
    url = f"{BASE_DATA_API}/v1/leaderboard?{urllib.parse.urlencode(params)}"
    data = make_request(url)
    if not isinstance(data, list):
        return []
    
    results = []
    for item in data:
        pnl = float(item.get("pnl", 0))
        vol = float(item.get("vol", 0))
        roi_vol = (pnl / vol * 100.0) if vol > 0 else 0.0
        results.append({
            "rank": int(item.get("rank", 0)) if str(item.get("rank", "0")).isdigit() else item.get("rank"),
            "userName": item.get("userName") or "(Anonymous)",
            "proxyWallet": item.get("proxyWallet", "").lower(),
            "xUsername": item.get("xUsername", ""),
            "pnl": pnl,
            "vol": vol,
            "roi_vol_pct": round(roi_vol, 2),
            "profileImage": item.get("profileImage", "")
        })
    return results

def fetch_all_closed_positions(wallet: str, max_records: int = 3000) -> List[Dict[str, Any]]:
    all_positions = []
    offset = 0
    page_size = 50
    wallet = wallet.strip().lower()

    while offset < max_records:
        url = f"{BASE_DATA_API}/closed-positions?user={wallet}&limit={page_size}&offset={offset}"
        data = make_request(url)
        if not isinstance(data, list) or len(data) == 0:
            break
        all_positions.extend(data)
        if len(data) < page_size:
            break
        offset += page_size

    return all_positions

def fetch_all_open_positions(wallet: str, max_records: int = 2000) -> List[Dict[str, Any]]:
    all_positions = []
    offset = 0
    page_size = 100
    wallet = wallet.strip().lower()

    while offset < max_records:
        url = f"{BASE_DATA_API}/positions?user={wallet}&limit={page_size}&offset={offset}"
        data = make_request(url)
        if not isinstance(data, list) or len(data) == 0:
            break
        all_positions.extend(data)
        if len(data) < page_size:
            break
        offset += page_size

    return all_positions

def fetch_portfolio_value(wallet: str) -> float:
    url = f"{BASE_DATA_API}/value?user={wallet.strip().lower()}"
    data = make_request(url)
    if isinstance(data, list) and len(data) > 0:
        return float(data[0].get("value", 0))
    return 0.0

def fetch_official_user_stats(wallet: str) -> Dict[str, Any]:
    wallet_clean = wallet.strip().lower()
    stats = {}
    for tp in ["ALL", "MONTH", "WEEK", "DAY"]:
        url = f"{BASE_DATA_API}/v1/leaderboard?user={wallet_clean}&timePeriod={tp}"
        data = make_request(url)
        if isinstance(data, list) and len(data) > 0:
            stats[tp] = {
                "rank": data[0].get("rank"),
                "userName": data[0].get("userName") or "(Anonymous)",
                "vol": float(data[0].get("vol", 0)),
                "pnl": float(data[0].get("pnl", 0)),
                "roi_vol_pct": round((float(data[0].get("pnl", 0)) / float(data[0].get("vol", 1)) * 100.0) if float(data[0].get("vol", 0)) > 0 else 0.0, 2)
            }
    return stats

def parse_date_to_timestamp(date_str: Optional[str], default_ts: int, is_end_of_day: bool = False) -> int:
    if not date_str:
        return default_ts
    date_str = date_str.strip()
    
    if date_str.endswith("d") and date_str[:-1].isdigit():
        days = int(date_str[:-1])
        return int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    elif date_str.endswith("w") and date_str[:-1].isdigit():
        weeks = int(date_str[:-1])
        return int((datetime.now(timezone.utc) - timedelta(weeks=weeks)).timestamp())
    elif date_str.endswith("y") and date_str[:-1].isdigit():
        years = int(date_str[:-1])
        return int((datetime.now(timezone.utc) - timedelta(days=years*365)).timestamp())

    formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y/%m/%d", "%d-%m-%Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if is_end_of_day and fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"]:
                dt = dt.replace(hour=23, minute=59, second=59)
            return int(dt.timestamp())
        except ValueError:
            continue
            
    if date_str.isdigit():
        return int(date_str)
    raise ValueError(f"Unrecognized date format: '{date_str}'. Expected YYYY-MM-DD")

# ── 3. 3-Dimensional Quantitative Engine ───────────────────────────────────────

def compute_3d_trade_quality(settled_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not settled_positions:
        return {
            "signal_quality": {
                "mean_calibration_edge_pct": 0.0,
                "avg_entry_price": 0.0,
                "implied_market_winrate_pct": 50.0,
                "raw_win_rate_pct": 0.0,
                "price_adjusted_bayesian_wr_pct": 50.0
            },
            "sizing_quality": {
                "capital_weighted_edge_pct": 0.0,
                "sizing_edge_delta_pct": 0.0,
                "sizing_association": "Neutral"
            },
            "evidence": {
                "independent_events_count": 0,
                "total_positions_count": 0,
                "sample_reliability_pct": 0.0,
                "event_diversity_ratio": 0.0
            },
            "financial_risk": {
                "profit_factor": 1.0,
                "expectancy_usd": 0.0,
                "max_drawdown_usd": 0.0,
                "gross_profit_usd": 0.0,
                "gross_loss_usd": 0.0,
                "avg_win_usd": 0.0,
                "avg_loss_usd": 0.0
            },
            "trader_profile": "Insufficient Data"
        }

    sorted_pos = sorted(settled_positions, key=lambda x: x.get("timestamp") or 0)
    
    edges = []
    capital_weighted_num = 0.0
    total_shares = 0.0
    distinct_events = set()
    
    wins_pnl = []
    losses_pnl = []
    cum_pnl = 0.0
    peak_pnl = 0.0
    max_dd = 0.0
    total_cost = 0.0
    total_realized_pnl = 0.0
    entry_prices = []

    for p in sorted_pos:
        cur_p = float(p.get("curPrice", 0))
        entry_p = float(p.get("avgPrice", 0))
        shares = float(p.get("totalBought") or p.get("size") or 0)
        pnl = float(p.get("realizedPnl", 0))
        
        cost = shares * entry_p
        total_cost += cost
        total_realized_pnl += pnl
        entry_prices.append(entry_p)
        
        edge = cur_p - entry_p
        edges.append(edge)
        capital_weighted_num += (shares * edge)
        total_shares += shares
        
        event_id = p.get("event_id") or p.get("eventSlug") or p.get("slug") or ""
        if event_id:
            distinct_events.add(event_id)
        
        if pnl > 0.01:
            wins_pnl.append(pnl)
        elif pnl < -0.01:
            losses_pnl.append(abs(pnl))
            
        cum_pnl += pnl
        if cum_pnl > peak_pnl:
            peak_pnl = cum_pnl
        dd = peak_pnl - cum_pnl
        if dd > max_dd:
            max_dd = dd

    n_trades = len(sorted_pos)
    n_wins = len(wins_pnl)
    n_losses = len(losses_pnl)
    gross_profit = sum(wins_pnl)
    gross_loss = sum(losses_pnl)
    n_eff = len(distinct_events)

    # 1. Dimension 1: Signal Quality
    mean_edge = (sum(edges) / n_trades) if n_trades > 0 else 0.0
    avg_entry = (sum(entry_prices) / len(entry_prices)) if entry_prices else 0.50
    implied_market_wr = avg_entry * 100.0
    raw_wr = (n_wins / n_trades * 100.0) if n_trades > 0 else 0.0
    
    prior_weight = 15.0
    prior_wins = avg_entry * prior_weight
    dynamic_bayesian_wr = ((n_wins + prior_wins) / (n_trades + prior_weight)) * 100.0

    # 2. Dimension 2: Sizing Quality
    cap_weighted_edge = (capital_weighted_num / total_shares) if total_shares > 0 else 0.0
    sizing_delta = (cap_weighted_edge - mean_edge) * 100.0

    if sizing_delta > 3.0:
        sizing_desc = "Positive Size-Outcome Association (Larger sizes correlate with better outcomes)"
    elif sizing_delta < -3.0:
        sizing_desc = "Negative Size-Outcome Association (Larger sizes correlate with worse outcomes)"
    else:
        sizing_desc = "Uniform / Neutral Size Association"

    # 3. Dimension 3: Evidence
    sample_rel = (n_eff / (n_eff + 15.0)) * 100.0 if n_eff > 0 else 0.0
    diversity_ratio = (n_eff / n_trades) if n_trades > 0 else 1.0

    # 4. Financial & Risk Metrics
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = min(gross_profit, 20.0) if gross_profit > 0 else 1.0

    avg_win = (gross_profit / n_wins) if n_wins > 0 else 0.0
    avg_loss = (gross_loss / n_losses) if n_losses > 0 else 0.0
    win_prob = n_wins / n_trades if n_trades > 0 else 0.0
    loss_prob = n_losses / n_trades if n_trades > 0 else 0.0
    expectancy = (win_prob * avg_win) - (loss_prob * avg_loss)

    # 5. Strict Hierarchy Profile Diagnosis
    if cap_weighted_edge <= -0.02 or total_realized_pnl < 0:
        profile = "Negative Expectancy Profile (Sub-market calibration & negative return)"
    elif mean_edge > 0.02 and cap_weighted_edge > 0.02 and n_eff >= 20:
        profile = "Dual Positive Profile (Positive Signal Edge & Positive Capital Edge)"
    elif mean_edge <= 0.02 and cap_weighted_edge > 0.02 and total_realized_pnl > 0:
        profile = "Positive Size-Outcome Association (Low Signal Edge, Capital Edge via Sizing Delta)"
    elif raw_wr >= 80.0 and abs(mean_edge) <= 0.04:
        profile = "High-Winrate Favorite Profile (High WR by Buying High Market Implied Probabilities)"
    else:
        profile = "Mixed / Developing Profile"

    return {
        "signal_quality": {
            "mean_calibration_edge_pct": round(mean_edge * 100.0, 2),
            "avg_entry_price": round(avg_entry, 3),
            "implied_market_winrate_pct": round(implied_market_wr, 1),
            "raw_win_rate_pct": round(raw_wr, 1),
            "price_adjusted_bayesian_wr_pct": round(dynamic_bayesian_wr, 1)
        },
        "sizing_quality": {
            "capital_weighted_edge_pct": round(cap_weighted_edge * 100.0, 2),
            "sizing_edge_delta_pct": round(sizing_delta, 2),
            "sizing_association": sizing_desc
        },
        "evidence": {
            "independent_events_count": n_eff,
            "total_positions_count": n_trades,
            "sample_reliability_pct": round(sample_rel, 1),
            "event_diversity_ratio": round(diversity_ratio, 2)
        },
        "financial_risk": {
            "profit_factor": round(profit_factor, 2),
            "expectancy_usd": round(expectancy, 2),
            "max_drawdown_usd": round(max_dd, 2),
            "gross_profit_usd": round(gross_profit, 2),
            "gross_loss_usd": round(gross_loss, 2),
            "avg_win_usd": round(avg_win, 2),
            "avg_loss_usd": round(avg_loss, 2)
        },
        "trader_profile": profile
    }

# ── 4. Rolling Walk-Forward Out-of-Sample Engine ───────────────────────────────

def compute_rolling_walk_forward(settled_positions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    monthly = defaultdict(list)
    for p in settled_positions:
        ts = p.get("timestamp") or 0
        if not ts and p.get("endDate"):
            try:
                ts = int(datetime.strptime(p["endDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
            except Exception:
                pass
        if ts:
            m = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m")
            monthly[m].append(p)

    months = sorted([m for m in monthly.keys() if len(monthly[m]) >= 4])
    if len(months) < 3:
        return None

    folds = []
    for i in range(len(months) - 1):
        train_months = months[:i+1]
        test_month = months[i+1]
        
        train_pos = [p for m in train_months for p in monthly[m]]
        test_pos = monthly[test_month]
        
        q_train = compute_3d_trade_quality(train_pos)
        q_test = compute_3d_trade_quality(test_pos)
        
        train_pnl = sum(float(p.get("realizedPnl", 0)) for p in train_pos)
        test_pnl = sum(float(p.get("realizedPnl", 0)) for p in test_pos)
        
        t_cap = q_test["sizing_quality"]["capital_weighted_edge_pct"]
        is_cap = q_train["sizing_quality"]["capital_weighted_edge_pct"]
        
        folds.append({
            "train_window": f"{train_months[0]}..{train_months[-1]}",
            "test_window": test_month,
            "train_events": q_train["evidence"]["independent_events_count"],
            "test_events": q_test["evidence"]["independent_events_count"],
            "is_capital_edge_pct": is_cap,
            "oos_signal_edge_pct": q_test["signal_quality"]["mean_calibration_edge_pct"],
            "oos_capital_edge_pct": t_cap,
            "oos_sizing_edge_delta_pct": q_test["sizing_quality"]["sizing_edge_delta_pct"],
            "oos_pnl_usd": round(test_pnl, 2),
            "oos_profit_factor": q_test["financial_risk"]["profit_factor"],
            "oos_win_rate_pct": q_test["signal_quality"]["raw_win_rate_pct"],
            "oos_profitable": (t_cap > 0 and test_pnl > 0)
        })

    oos_cap_edges = [f["oos_capital_edge_pct"] for f in folds]
    oos_consistency = (sum(1 for f in folds if f["oos_profitable"]) / len(folds)) * 100.0
    mean_oos_cap = sum(oos_cap_edges) / len(oos_cap_edges)

    return {
        "total_folds": len(folds),
        "walk_forward_consistency_pct": round(oos_consistency, 1),
        "mean_oos_capital_edge_pct": round(mean_oos_cap, 2),
        "folds": folds
    }

# ── 5. Meta-Backtest & Fixed-Budget Copy-Trading Engine ───────────────────────

def run_meta_backtest_cli():
    from audit_weather_traders import find_active_weather_wallets
    print("\n" + "=" * 140)
    print("  POLYMARKET META-BACKTEST: PREDICTIVE VALIDITY & REALISTIC COPY-TRADING AUDIT")
    print("=" * 140)
    print("Gathering active cross-market trader cohort...")
    
    weather = find_active_weather_wallets()[:12]
    leaders_m = [l["proxyWallet"] for l in fetch_leaderboard("MONTH", limit=12)]
    seeds = [
        "0x3904e686bffade807ac746cd462c6f44724c539b",
        "0xf8dc8cd0fd55eccb5409ed99ed90a86bc7f0f31f",
        "0x111f73e91f85b6fe4de1ddec3de2fe32122e355b"
    ]
    cohort = list(dict.fromkeys(weather + leaders_m + seeds))
    
    def fetch_single(w):
        c = fetch_all_closed_positions(w, max_records=2000)
        o = fetch_all_open_positions(w, max_records=1000)
        all_s = []
        for p in c:
            slug = p.get("slug") or ""
            event_slug = p.get("eventSlug") or ""
            title = p.get("title", "")
            all_s.append({
                "title": title, "slug": slug, "event_slug": event_slug,
                "event_id": extract_event_id(slug, event_slug, title),
                "slug_group": extract_slug_group(slug, event_slug, title),
                "curPrice": float(p.get("curPrice", 0)),
                "avgPrice": float(p.get("avgPrice", 0)),
                "totalBought": float(p.get("totalBought", 0)),
                "realizedPnl": float(p.get("realizedPnl", 0)),
                "timestamp": p.get("timestamp") or 0,
                "endDate": p.get("endDate") or ""
            })
        for p in o:
            cur_p = float(p.get("curPrice", 0))
            if p.get("redeemable") and cur_p in [0.0, 1.0]:
                slug = p.get("slug") or ""
                event_slug = p.get("eventSlug") or ""
                title = p.get("title", "")
                all_s.append({
                    "title": title, "slug": slug, "event_slug": event_slug,
                    "event_id": extract_event_id(slug, event_slug, title),
                    "slug_group": extract_slug_group(slug, event_slug, title),
                    "curPrice": cur_p,
                    "avgPrice": float(p.get("avgPrice", 0)),
                    "totalBought": float(p.get("size", 0)),
                    "realizedPnl": float(p.get("cashPnl", 0)),
                    "timestamp": parse_date_to_timestamp(p.get("endDate"), default_ts=0),
                    "endDate": p.get("endDate") or ""
                })
        return w, all_s

    wallet_ledgers = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_single, w) for w in cohort]
        for f in as_completed(futures):
            w, led = f.result()
            if len(led) >= 15:
                wallet_ledgers[w] = led

    date_folds = [
        ("Fold 1: Train <= July 2026  -->  Forward Test: August 2026", "2026-07", "2026-08"),
        ("Fold 2: Train <= August 2026 -->  Forward Test: September 2026", "2026-08", "2026-09")
    ]

    budget_per_trader = 10000.0

    for fold_name, cutoff_train, test_month in date_folds:
        print(f"\n" + "-" * 140)
        print(f"📊 {fold_name}")
        print("-" * 140)
        
        qualified_wallets = []
        disqualified_wallets = []

        for w, led in wallet_ledgers.items():
            train_pos = []
            test_pos = []
            for p in led:
                ts = p.get("timestamp") or 0
                if not ts and p.get("endDate"):
                    try:
                        ts = int(datetime.strptime(p["endDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
                    except Exception:
                        pass
                if ts:
                    m = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m")
                    if m <= cutoff_train: train_pos.append(p)
                    elif m == test_month: test_pos.append(p)

            if len(train_pos) < 10 or len(test_pos) < 5:
                continue

            q_train = compute_3d_trade_quality(train_pos)
            q_test = compute_3d_trade_quality(test_pos)
            
            sig_t = q_train["signal_quality"]["mean_calibration_edge_pct"]
            cap_t = q_train["sizing_quality"]["capital_weighted_edge_pct"]
            neff_t = q_train["evidence"]["independent_events_count"]
            pf_t = q_train["financial_risk"]["profit_factor"]

            trader_pnl = sum(float(p["realizedPnl"]) for p in test_pos)
            trader_cost = sum(float(p["totalBought"]) * float(p["avgPrice"]) for p in test_pos)
            trader_roi = (trader_pnl / trader_cost) if trader_cost > 0 else -1.0
            
            copy_roi = max(-1.0, trader_roi)
            copy_pnl = budget_per_trader * copy_roi

            record = {
                "wallet": w,
                "oos_cap_edge": q_test["sizing_quality"]["capital_weighted_edge_pct"],
                "oos_sig_edge": q_test["signal_quality"]["mean_calibration_edge_pct"],
                "trader_pnl": trader_pnl,
                "copy_pnl": copy_pnl,
                "copy_roi": copy_roi * 100.0,
                "is_profitable": copy_pnl > 0
            }

            if sig_t > 0.0 and cap_t > 0.0 and neff_t >= 15 and pf_t >= 1.05:
                qualified_wallets.append(record)
            else:
                disqualified_wallets.append(record)

        def print_meta_table(q_list, d_list):
            def calc_metrics(g):
                n = len(g)
                if n == 0: return {"n": 0, "tot_inv": 0, "copy_pnl": 0, "port_roi": 0, "mean_sig": 0, "mean_cap": 0, "win_rate": 0}
                tot_inv = n * budget_per_trader
                tot_pnl = sum(x["copy_pnl"] for x in g)
                p_roi = (tot_pnl / tot_inv) * 100.0
                m_sig = sum(x["oos_sig_edge"] for x in g) / n
                m_cap = sum(x["oos_cap_edge"] for x in g) / n
                w_tr = sum(1 for x in g if x["is_profitable"])
                return {"n": n, "tot_inv": tot_inv, "copy_pnl": tot_pnl, "port_roi": p_roi, "mean_sig": m_sig, "mean_cap": m_cap, "win_rate": (w_tr/n)*100.0}

            m_q = calc_metrics(q_list)
            m_d = calc_metrics(d_list)

            print(f"{'Strategy / Cohort':<35} | {'Traders':<7} | {'Copy Portfolio ($)':<18} | {'Portfolio Return':<16} | {'Portfolio ROI %':<15} | {'Fwd Signal Edge':<15} | {'Trader Win Rate':<15}")
            print("-" * 140)
            print(f"{'✅ Framework Qualified (Passed)':<35} | {m_q['n']:>7} | ${m_q['tot_inv']:>16,.2f} | ${m_q['copy_pnl']:>14,.2f} | {m_q['port_roi']:>+13.2f}% | {m_q['mean_sig']:>+13.2f}% | {m_q['win_rate']:>13.1f}%")
            print(f"{'❌ Framework Disqualified (Failed)':<35} | {m_d['n']:>7} | ${m_d['tot_inv']:>16,.2f} | ${m_d['copy_pnl']:>14,.2f} | {m_d['port_roi']:>+13.2f}% | {m_d['mean_sig']:>+13.2f}% | {m_d['win_rate']:>13.1f}%")
            print("-" * 140)
            print(f"🎯 Portfolio Alpha Spread: Return Spread = ${(m_q['copy_pnl'] - m_d['copy_pnl']):+,.2f} | ROI Spread = {(m_q['port_roi'] - m_d['port_roi']):+.2f}% | Signal Edge Spread = {(m_q['mean_sig'] - m_d['mean_sig']):+.2f}%")

        print_meta_table(qualified_wallets, disqualified_wallets)

    print("=" * 140 + "\n")

# ── 6. Unified Wallet Analysis with 3-Tier Hierarchy ─────────────────────────

def analyze_wallet(
    wallet_address: str,
    slug_filter: Optional[str] = None,
    slug_group_filter: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_closed: int = 3000
) -> Dict[str, Any]:
    wallet = wallet_address.strip().lower()
    portfolio_value = fetch_portfolio_value(wallet)
    official_stats = fetch_official_user_stats(wallet)
    official_all = official_stats.get("ALL", {})
    user_name = official_all.get("userName") or "(Anonymous)"
    official_pnl = official_all.get("pnl")
    official_vol = official_all.get("vol")
    official_rank = official_all.get("rank")
    
    closed_raw = fetch_all_closed_positions(wallet, max_records=max(max_closed, 3000))
    open_raw = fetch_all_open_positions(wallet, max_records=2000)

    start_ts = parse_date_to_timestamp(start_date, default_ts=0, is_end_of_day=False) if start_date else 0
    now_ts = int(datetime.now(timezone.utc).timestamp())
    end_ts = parse_date_to_timestamp(end_date, default_ts=now_ts, is_end_of_day=True) if end_date else now_ts

    start_dt_str = datetime.fromtimestamp(start_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC") if start_ts else "ALL_EARLIEST"
    end_dt_str = datetime.fromtimestamp(end_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC") if end_date else "LATEST"

    all_settled_ledger = []
    truly_active_open = []
    
    # 1. Claimed Closed Positions
    for p in closed_raw:
        slug = p.get("slug") or ""
        event_slug = p.get("eventSlug") or ""
        title = p.get("title", "Unknown")
        
        all_settled_ledger.append({
            "title": title,
            "outcome": p.get("outcome", "-"),
            "slug": slug,
            "event_slug": event_slug,
            "event_id": extract_event_id(slug, event_slug, title),
            "slug_group": extract_slug_group(slug, event_slug, title),
            "curPrice": float(p.get("curPrice", 0)),
            "avgPrice": float(p.get("avgPrice", 0)),
            "totalBought": float(p.get("totalBought", 0)),
            "realizedPnl": float(p.get("realizedPnl", 0)),
            "timestamp": p.get("timestamp") or 0,
            "endDate": p.get("endDate") or "",
            "settlement_source": "CLAIMED_CLOSED"
        })

    # 2. Unclaimed Settled Positions
    for p in open_raw:
        cur_p = float(p.get("curPrice", 0))
        redeemable = p.get("redeemable", False)
        size = float(p.get("size", 0))
        avg_p = float(p.get("avgPrice", 0))
        cash_pnl = float(p.get("cashPnl", 0))
        slug = p.get("slug") or ""
        event_slug = p.get("eventSlug") or ""
        title = p.get("title", "Unknown")
        
        if cur_p == 0.0 and redeemable:
            all_settled_ledger.append({
                "title": title,
                "outcome": p.get("outcome", "-"),
                "slug": slug,
                "event_slug": event_slug,
                "event_id": extract_event_id(slug, event_slug, title),
                "slug_group": extract_slug_group(slug, event_slug, title),
                "curPrice": 0.0,
                "avgPrice": avg_p,
                "totalBought": size,
                "realizedPnl": cash_pnl,
                "timestamp": parse_date_to_timestamp(p.get("endDate"), default_ts=0),
                "endDate": p.get("endDate") or "",
                "settlement_source": "UNCLAIMED_SETTLED_LOSS"
            })
        elif cur_p == 1.0 and redeemable:
            all_settled_ledger.append({
                "title": title,
                "outcome": p.get("outcome", "-"),
                "slug": slug,
                "event_slug": event_slug,
                "event_id": extract_event_id(slug, event_slug, title),
                "slug_group": extract_slug_group(slug, event_slug, title),
                "curPrice": 1.0,
                "avgPrice": avg_p,
                "totalBought": size,
                "realizedPnl": cash_pnl,
                "timestamp": parse_date_to_timestamp(p.get("endDate"), default_ts=0),
                "endDate": p.get("endDate") or "",
                "settlement_source": "UNCLAIMED_SETTLED_WIN"
            })
        else:
            truly_active_open.append(p)

    filtered_settled = []
    group_settled = defaultdict(list)
    
    total_settled_cost = 0.0
    total_settled_pnl = 0.0
    wins = 0
    losses = 0
    pushes = 0
    unclaimed_loss_count = 0
    unclaimed_push_count = 0
    unclaimed_win_count = 0
    claimed_win_count = 0

    for pos in all_settled_ledger:
        pos_ts = pos.get("timestamp") or 0
        if not pos_ts and pos.get("endDate"):
            try:
                pos_ts = int(datetime.strptime(pos["endDate"], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
            except Exception:
                pos_ts = 0

        if start_date and pos_ts and pos_ts < start_ts: continue
        if end_date and pos_ts and pos_ts > end_ts: continue

        slug = pos["slug"].lower()
        event_slug = pos["event_slug"].lower()
        title = pos["title"].lower()
        grp = pos["slug_group"]
        combined_text = f"{slug} {event_slug} {title} {grp}".lower()

        if slug_filter and slug_filter.strip().lower() not in combined_text:
            continue
        if slug_group_filter and slug_group_filter.strip().lower() not in ["all", "any"] and slug_group_filter.strip().lower() != grp:
            continue

        pnl = float(pos.get("realizedPnl", 0))
        shares = float(pos.get("totalBought", 0))
        avg_price = float(pos.get("avgPrice", 0))
        cost = shares * avg_price

        total_settled_cost += cost
        total_settled_pnl += pnl
        filtered_settled.append(pos)
        group_settled[grp].append(pos)

        if pnl > 0.01:
            wins += 1
            if pos["settlement_source"] == "CLAIMED_CLOSED": claimed_win_count += 1
            elif pos["settlement_source"] == "UNCLAIMED_SETTLED_WIN": unclaimed_win_count += 1
        elif pnl < -0.01:
            losses += 1
            if pos["settlement_source"] == "UNCLAIMED_SETTLED_LOSS": unclaimed_loss_count += 1
        else:
            pushes += 1
            if pos["settlement_source"] == "UNCLAIMED_SETTLED_LOSS": unclaimed_push_count += 1

    # Active Open Positions
    processed_active_open = []
    total_active_cost = 0.0
    total_unrealized_pnl = 0.0

    if not start_date and not end_date:
        for pos in truly_active_open:
            slug = (pos.get("slug") or "").lower()
            event_slug = (pos.get("eventSlug") or "").lower()
            title = pos.get("title") or ""
            grp = extract_slug_group(slug, event_slug, title)
            combined_text = f"{slug} {event_slug} {title} {grp}".lower()

            if slug_filter and slug_filter.strip().lower() not in combined_text:
                continue
            if slug_group_filter and slug_group_filter.strip().lower() not in ["all", "any"] and slug_group_filter.strip().lower() != grp:
                continue

            size = float(pos.get("size", 0))
            avg_price = float(pos.get("avgPrice", 0))
            cur_price = float(pos.get("curPrice", 0))
            cost = size * avg_price
            cur_val = size * cur_price
            cash_pnl = float(pos.get("cashPnl", cur_val - cost))
            roi_pct = float(pos.get("percentPnl", (cash_pnl / cost * 100) if cost > 0 else 0))

            total_active_cost += cost
            total_unrealized_pnl += cash_pnl

            processed_active_open.append({
                "title": title,
                "outcome": pos.get("outcome", "-"),
                "slug_group": grp,
                "slug": slug,
                "size": round(size, 2),
                "avg_entry_price": round(avg_price, 4),
                "cur_price": round(cur_price, 4),
                "cost_usd": round(cost, 2),
                "current_value_usd": round(cur_val, 2),
                "unrealized_pnl_usd": round(cash_pnl, 2),
                "roi_pct": round(roi_pct, 2)
            })

    total_resolved = wins + losses + pushes
    win_rate = (wins / total_resolved * 100.0) if total_resolved > 0 else 0.0
    capital_roi = (total_settled_pnl / total_settled_cost * 100.0) if total_settled_cost > 0 else 0.0

    overall_3d = compute_3d_trade_quality(filtered_settled)
    walk_forward_eval = compute_rolling_walk_forward(filtered_settled)

    slug_group_breakdown = []
    for grp_name, g_positions in group_settled.items():
        g_cost = sum(float(p.get("totalBought", 0)) * float(p.get("avgPrice", 0)) for p in g_positions)
        g_pnl = sum(float(p.get("realizedPnl", 0)) for p in g_positions)
        g_roi = (g_pnl / g_cost * 100.0) if g_cost > 0 else 0.0
        g_3d = compute_3d_trade_quality(g_positions)
        g_wf = compute_rolling_walk_forward(g_positions)
        
        slug_group_breakdown.append({
            "slug_group": grp_name,
            "settled_pnl_usd": round(g_pnl, 2),
            "invested_usd": round(g_cost, 2),
            "roi_pct": round(g_roi, 2),
            "signal_edge_pct": g_3d["signal_quality"]["mean_calibration_edge_pct"],
            "capital_edge_pct": g_3d["sizing_quality"]["capital_weighted_edge_pct"],
            "sizing_edge_delta_pct": g_3d["sizing_quality"]["sizing_edge_delta_pct"],
            "independent_events_count": g_3d["evidence"]["independent_events_count"],
            "total_positions_count": g_3d["evidence"]["total_positions_count"],
            "profit_factor": g_3d["financial_risk"]["profit_factor"],
            "win_rate_pct": g_3d["signal_quality"]["raw_win_rate_pct"],
            "wf_consistency_pct": g_wf["walk_forward_consistency_pct"] if g_wf else None,
            "profile": g_3d["trader_profile"]
        })

    slug_group_breakdown.sort(key=lambda x: abs(x["settled_pnl_usd"]), reverse=True)

    # Cross-reconciliation with official Polymarket ground-truth platform ledger
    is_truncated = False
    ledger_coverage_pct = 100.0
    if official_vol and official_vol > 0 and total_settled_cost > 0:
        if official_vol > total_settled_cost * 3.0 and len(closed_raw) >= 2000:
            is_truncated = True
            ledger_coverage_pct = round((total_settled_cost / official_vol) * 100.0, 1)

    official_disqualified = False
    disqualify_reason = ""
    if official_pnl is not None and official_pnl < 0:
        official_disqualified = True
        disqualify_reason = f"Official Polymarket Lifetime PnL is Negative: -${abs(official_pnl):,.2f} (Rank #{official_rank})"

    return {
        "wallet": wallet,
        "userName": user_name,
        "polymarket_url": f"https://polymarket.com/{wallet}",
        "profile_url": f"https://polymarket.com/{wallet}",
        "official_ground_truth": {
            "userName": user_name,
            "lifetime_pnl_usd": official_pnl,
            "lifetime_volume_usd": official_vol,
            "lifetime_rank": official_rank,
            "is_truncated": is_truncated,
            "ledger_coverage_pct": ledger_coverage_pct,
            "official_disqualified": official_disqualified,
            "disqualify_reason": disqualify_reason,
            "timeframe_stats": official_stats
        },
        "filters": {
            "slug_keyword": slug_filter or "NONE",
            "slug_group": slug_group_filter or "ALL",
            "start_date": start_date or "NONE",
            "end_date": end_date or "NONE",
            "start_utc": start_dt_str,
            "end_utc": end_dt_str
        },
        "performance": {
            "portfolio_value_usd": round(portfolio_value, 2),
            "total_settled_pnl_usd": round(total_settled_pnl, 2),
            "active_unrealized_pnl_usd": round(total_unrealized_pnl, 2),
            "true_total_mtm_pnl_usd": round(total_settled_pnl + total_unrealized_pnl, 2),
            "total_capital_invested_usd": round(total_settled_cost, 2),
            "capital_roi_pct": round(capital_roi, 2),
            "win_rate_pct": round(win_rate, 2),
            "settled_breakdown": {
                "total_settled": total_resolved,
                "wins": wins,
                "losses": losses,
                "push": pushes,
                "claimed_wins": claimed_win_count,
                "unclaimed_settled": {
                    "total": unclaimed_loss_count + unclaimed_push_count + unclaimed_win_count,
                    "losses": unclaimed_loss_count,
                    "push": unclaimed_push_count,
                    "wins": unclaimed_win_count
                }
            },
            "active_positions_count": len(processed_active_open)
        },
        "trade_quality_3d": overall_3d,
        "walk_forward_validation": walk_forward_eval,
        "slug_group_breakdown": slug_group_breakdown,
        "settled_positions": filtered_settled[:50],
        "active_positions": processed_active_open[:20]
    }

# ── 7. Clean CLI Report Formatters ─────────────────────────────────────────────

def print_wallet_cli(data: Dict[str, Any], show_breakdown: bool = True):
    f = data["filters"]
    p = data["performance"]
    sb = p["settled_breakdown"]
    uc = sb["unclaimed_settled"]
    tq = data["trade_quality_3d"]
    sig = tq["signal_quality"]
    siz = tq["sizing_quality"]
    evi = tq["evidence"]
    fr = tq["financial_risk"]
    wf = data.get("walk_forward_validation")
    ogt = data.get("official_ground_truth", {})
    user_name = data.get("userName") or ogt.get("userName") or "(Anonymous)"
    off_pnl = ogt.get("lifetime_pnl_usd")
    off_vol = ogt.get("lifetime_volume_usd")
    off_rank = ogt.get("lifetime_rank")
    
    print("\n" + "=" * 125)
    print(f"  POLYMARKET 3-DIMENSIONAL QUANTITATIVE AUDIT & ROLLING WALK-FORWARD ENGINE")
    print(f"  Account / User:        {user_name} (Rank #{off_rank if off_rank is not None else 'N/A'})")
    print(f"  Wallet:                {data['wallet']}")
    print(f"  Polymarket Profile:    https://polymarket.com/{data['wallet']}")
    if off_pnl is not None:
        pnl_s = f"+${off_pnl:,.2f}" if off_pnl >= 0 else f"-${abs(off_pnl):,.2f}"
        vol_s = f"${off_vol:,.2f}" if off_vol is not None else "$0.00"
        print(f"  Official Platform:     PnL: {pnl_s} | Total Volume: {vol_s}")
    if ogt.get("is_truncated"):
        print(f"  ⚠️  DATA TRUNCATION NOTICE: High-frequency account. Sample represents {ogt.get('ledger_coverage_pct')}% of volume.")
        print(f"      Ground-truth lifetime PnL is {pnl_s}.")
    if ogt.get("official_disqualified"):
        print(f"  ❌ AUDIT DISQUALIFICATION: {ogt.get('disqualify_reason')}")
    if f["slug_group"] != "ALL":
        print(f"  Slug-Group Family:     [{f['slug_group']}]")
    if f["slug_keyword"] != "NONE":
        print(f"  Keyword Filter:        '{f['slug_keyword']}'")
    if f["start_date"] != "NONE" or f["end_date"] != "NONE":
        print(f"  Time Window:           {f['start_utc'][:10]} → {f['end_utc'][:10]}")
    print("=" * 125)

    sign = "+" if p['true_total_mtm_pnl_usd'] >= 0 else ""
    print(f"• Current Portfolio Value:     ${p['portfolio_value_usd']:,.2f}")
    print(f"• Total Settled PnL (True):    ${p['total_settled_pnl_usd']:+,.2f}")
    print(f"• Active Unrealized PnL:       ${p['active_unrealized_pnl_usd']:+,.2f}")
    print(f"• True Total MTM PnL:          {sign}${p['true_total_mtm_pnl_usd']:,.2f}")
    print(f"• Total Capital Invested:      ${p['total_capital_invested_usd']:,.2f}")
    print(f"• Capital Invested ROI:        {p['capital_roi_pct']:+.2f}%")
    print(f"• True Win Rate (All Settled): {p['win_rate_pct']:.1f}% ({sb['wins']} Wins / {sb['losses']} Losses / {sb['push']} Push)")
    print(f"  ├─ Claimed Wins:             {sb['claimed_wins']}")
    print(f"  └─ Unclaimed Settled:        {uc['total']} (Loss: {uc['losses']}, Push: {uc['push']}, Win: {uc['wins']})")
    
    print("-" * 125)
    print("🔬 3 DIMENSIONS OF TRADE QUALITY (Signal | Sizing | Evidence):")
    print(f"  [1] SIGNAL QUALITY (Market Calibration):")
    sig_sign = "+" if sig['mean_calibration_edge_pct'] >= 0 else ""
    print(f"      • Mean Calibration Edge:  {sig_sign}{sig['mean_calibration_edge_pct']:.2f}%  (Alpha over Market Implied Prob)")
    print(f"      • Avg Entry Price:        ${sig['avg_entry_price']:.3f}  (Market Implied Win Rate: {sig['implied_market_winrate_pct']:.1f}%)")
    print(f"      • Bayesian Calibrated WR: {sig['price_adjusted_bayesian_wr_pct']:.1f}%  (Shrunk towards market entry prior)")
    
    print(f"  [2] SIZING QUALITY (Capital Allocation):")
    cap_sign = "+" if siz['capital_weighted_edge_pct'] >= 0 else ""
    d_sign = "+" if siz['sizing_edge_delta_pct'] >= 0 else ""
    print(f"      • Capital-Weighted Edge:  {cap_sign}{siz['capital_weighted_edge_pct']:.2f}% per share")
    print(f"      • Sizing Edge Delta (Δ):  {d_sign}{siz['sizing_edge_delta_pct']:.2f}%  [{siz['sizing_association']}]")
    
    print(f"  [3] EVIDENCE & STATISTICAL SAMPLE:")
    print(f"      • Independent Events (N): {evi['independent_events_count']} events  (from {evi['total_positions_count']} positions, Diversity: {evi['event_diversity_ratio']*100:.0f}%)")
    print(f"      • Sample Reliability:     {evi['sample_reliability_pct']:.1f}%")
    print(f"      • Profit Factor (PF):     {fr['profit_factor']:.2f}  (Gross Profit: ${fr['gross_profit_usd']:,.2f} / Gross Loss: ${fr['gross_loss_usd']:,.2f})")
    print(f"      • Expectancy (EV):        ${fr['expectancy_usd']:+,.2f} / trade (Avg Win: +${fr['avg_win_usd']:,.2f} | Avg Loss: -${fr['avg_loss_usd']:,.2f})")
    print(f"      • Maximum Drawdown (MDD): ${fr['max_drawdown_usd']:,.2f}")
    print(f"  🎯 EMPIRICAL DIAGNOSIS:      {tq['trader_profile']}")
    print("-" * 125)

    if wf:
        print(f"🔄 ROLLING WALK-FORWARD OUT-OF-SAMPLE EVALUATION ({wf['total_folds']} Folds):")
        print(f"  • Forward OOS Consistency:   {wf['walk_forward_consistency_pct']:.1f}%  (Profitable & positive capital edge across forward windows)")
        print(f"  • Mean Forward OOS Cap Edge: {wf['mean_oos_capital_edge_pct']:+,.2f}%\n")
        print(f"  {'Train Window':<16} | {'Test OOS':<10} | {'IS CapEdge':<11} | {'OOS SigEdge':<12} | {'OOS CapEdge':<12} | {'OOS SizingΔ':<12} | {'OOS PnL ($)':<12} | {'OOS PF':<7}")
        print("  " + "-" * 115)
        for fld in wf["folds"]:
            tr_cap = f"{fld['is_capital_edge_pct']:>+9.2f}%"
            o_sig = f"{fld['oos_signal_edge_pct']:>+10.2f}%"
            o_cap = f"{fld['oos_capital_edge_pct']:>+10.2f}%"
            o_d = f"{fld['oos_sizing_edge_delta_pct']:>+10.2f}%"
            o_pnl = f"${fld['oos_pnl_usd']:>10,.2f}"
            print(f"  {fld['train_window']:<16} | {fld['test_window']:<10} | {tr_cap} | {o_sig} | {o_cap} | {o_d} | {o_pnl} | {fld['oos_profit_factor']:>6.2f}")
        print("-" * 125)

    if show_breakdown and data["slug_group_breakdown"]:
        print("\n📊 SLUG-GROUP MARKET FAMILY BREAKDOWN:")
        print(f"{'Slug Group Family':<24} | {'PnL ($)':<14} | {'ROI %':<9} | {'Signal Edge':<12} | {'Cap Edge':<10} | {'Sizing Δ':<9} | {'N_eff':<6} | {'OOS Cons.':<10} | {'PF':<5}")
        print("-" * 125)
        for g in data["slug_group_breakdown"]:
            g_sign = "+" if g['settled_pnl_usd'] >= 0 else ""
            s_s = "+" if g['signal_edge_pct'] >= 0 else ""
            c_s = "+" if g['capital_edge_pct'] >= 0 else ""
            d_s = "+" if g['sizing_edge_delta_pct'] >= 0 else ""
            wf_str = f"{g['wf_consistency_pct']:.0f}%" if g['wf_consistency_pct'] is not None else "N/A"
            print(f"{g['slug_group']:<24} | {g_sign}${g['settled_pnl_usd']:>12,.2f} | {g['roi_pct']:>+8.1f}% | {s_s}{g['signal_edge_pct']:>10.2f}% | {c_s}{g['capital_edge_pct']:>8.2f}% | {d_s}{g['sizing_edge_delta_pct']:>7.2f}% | {g['independent_events_count']:>5} | {wf_str:>10} | {g['profit_factor']:>5.2f}")
        print("-" * 125)

    print("=" * 125 + "\n")

def print_leaderboard_cli(leaders: List[Dict[str, Any]], timeframe: str):
    print(f"\n============================================================================================================================================")
    print(f"  POLYMARKET LEADERBOARD & % PNL RANKINGS (Timeframe: {timeframe})")
    print(f"============================================================================================================================================")
    print(f"{'Rank':<5} | {'Account / User':<20} | {'Net PnL ($)':<15} | {'Volume ($)':<16} | {'%PnL (ROI)':<11} | {'Polymarket Profile URL'}")
    print("-" * 140)
    for x in leaders:
        rank_str = f"#{x['rank']}"
        name = x['userName'][:19]
        pnl_str = f"${x['pnl']:>13,.2f}"
        vol_str = f"${x['vol']:>14,.2f}"
        roi_str = f"{x['roi_vol_pct']:>8.2f}%"
        print(f"{rank_str:<5} | {name:<20} | {pnl_str} | {vol_str} | {roi_str} | https://polymarket.com/{x['proxyWallet']}")
    print("=" * 140 + "\n")

def screen_top_traders(
    slug_group: str = "ALL",
    exclude_group: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_events: int = 15,
    limit: int = 10,
    max_workers: int = 20
) -> Dict[str, Any]:
    candidates = set()
    
    # Target-specific candidate selection
    if "temp" in slug_group.lower() or "weather" in slug_group.lower():
        seeds = [
            "0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e", "0x3653235d75a0d5969c42f7514d4df8ea5f8cef74",
            "0x3904e686bffade807ac746cd462c6f44724c539b", "0xd71776a8d4fddeb3c150c4607b3f8bec31213b85",
            "0x4e72c22cd76f9973a48aedfd79feeaacc8b7ffb9", "0x8b8b9c565c8dca43cfb767f0f2c20b2b323d2512",
            "0x03805a13a0b3e058f55f6c6af95389d4f431073d", "0xeb1d1cd1b31070fb34b1d1de20d700f59c9959b0",
            "0xb2e42d29690b7b63335a03c0fd5e64df0681b7f1", "0x1387d145aaf01f6e33b66525dda6e1f51f6955f8",
            "0x1f85eb9c455c5bdef5d96c2739076678c7157b02", "0xeb68675c06e0bb9f08ba510550912d77289ce362",
            "0x9b129ad05bc0a8df3c73dfcc66fe75252daec2d5"
        ]
        for s in seeds: candidates.add(s.lower())
    else:
        for tp in ["ALL", "MONTH"]:
            try:
                for row in fetch_leaderboard(time_period=tp, limit=35, order_by="PNL"):
                    candidates.add(row["proxyWallet"].lower())
            except Exception:
                pass
        seeds = [
            "0x204f72f35326db932158cba6adff0b9a1da95e14", "0x507e52ef684ca2dd91f90a9d26d149dd3288beae",
            "0xe549581668a5751c1972d3ad2d1991d900bd2d54", "0xf8831548531d56ad6a4331493243c447a827cd1f",
            "0xee00ba338c59557141789b127927a55f5cc5cea1", "0x14c7111afa871fb215339f365043d7b2837b9ccf",
            "0xd570e634aeb745d6501566dba5f81a555cc7e4f8", "0x5a218c7ad04135830a45c41aaed7294df7809318",
            "0xf68a281980f8c13828e84e147e3822381d6e5b1b", "0xb7271c112cbd83eb4c1ef1b554ff963604ae2a9d",
            "0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e", "0x3653235d75a0d5969c42f7514d4df8ea5f8cef74",
            "0x1610db79f753a80207e1d66716be9e91e627ae49", "0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b",
            "0x111f73e91f85b6fe4de1ddec3de2fe32122e355b", "0x05f6cb63d4ffdfaecd7ad8acd0765b6f6a5a25a1",
            "0xb0e74df9430a089aa102e2207af5fde1967439d2", "0xcd30f4698c6f5f3829893e68e183a8e5ea18f316",
            "0xc3acf5878a03523d09a3ac859943445d7baeb964"
        ]
        for s in seeds: candidates.add(s.lower())

    def audit_one(w):
        try:
            res = analyze_wallet(
                wallet_address=w,
                slug_group_filter=slug_group if slug_group not in ["ALL", "all"] else None,
                start_date=start_date,
                end_date=end_date,
                max_closed=800
            )
            ogt = res.get("official_ground_truth", {})
            off_pnl = ogt.get("lifetime_pnl_usd")
            if off_pnl is not None and off_pnl <= 0:
                return None
            
            perf = res["performance"]
            sb = perf["settled_breakdown"]
            tq = res["trade_quality_3d"]
            sig = tq["signal_quality"]
            siz = tq["sizing_quality"]
            evi = tq["evidence"]
            fr = tq["financial_risk"]
            
            slug_breakdown = res.get("slug_group_breakdown", [])
            if exclude_group and exclude_group.strip().lower() not in ["none", ""]:
                ex_slug = exclude_group.strip().lower()
                slug_breakdown = [g for g in slug_breakdown if g["slug_group"] != ex_slug]
            
            if sb["total_settled"] < min_events:
                return None
                
            top_market = "general"
            top_market_share = 0.0
            if slug_breakdown:
                by_count = sorted(slug_breakdown, key=lambda x: x["total_positions_count"], reverse=True)
                top_market = by_count[0]["slug_group"]
                top_count = by_count[0]["total_positions_count"]
                tot_count = sum(x["total_positions_count"] for x in slug_breakdown)
                top_market_share = round((top_count / tot_count * 100.0), 1) if tot_count > 0 else 0.0

            wf = res.get("walk_forward_validation")
            wf_cons = wf["walk_forward_consistency_pct"] if wf else 0.0

            return {
                "wallet": w,
                "userName": res.get("userName") or ogt.get("userName") or "(Anonymous)",
                "profile_url": f"https://polymarket.com/{w}",
                "official_pnl": off_pnl,
                "official_vol": ogt.get("lifetime_volume_usd", 0),
                "official_rank": ogt.get("lifetime_rank", "-"),
                "period_pnl": perf["total_settled_pnl_usd"],
                "period_roi": perf["capital_roi_pct"],
                "win_rate": perf["win_rate_pct"],
                "settled_count": sb["total_settled"],
                "n_eff": evi["independent_events_count"],
                "sig_edge": sig["mean_calibration_edge_pct"],
                "cap_edge": siz["capital_weighted_edge_pct"],
                "sizing_delta": siz["sizing_edge_delta_pct"],
                "pf": fr["profit_factor"],
                "mdd": fr["max_drawdown_usd"],
                "top_market": f"{top_market} ({top_market_share:.0f}%)",
                "wf_cons": wf_cons,
                "trader_profile": tq["trader_profile"]
            }
        except Exception:
            return None

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(audit_one, w) for w in candidates]
        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)

    tier1 = [r for r in results if r["sig_edge"] >= 3.0 and r["cap_edge"] >= 3.0 and r["n_eff"] >= max(min_events, 20) and r["pf"] >= 1.35 and r["period_pnl"] > 0]
    tier2 = [r for r in results if r["sig_edge"] > 0 and r["cap_edge"] > 0 and r["n_eff"] >= min_events and r["pf"] >= 1.15 and r["period_pnl"] > 0 and r not in tier1]
    avoid = [r for r in results if r["sig_edge"] <= 0 or r["cap_edge"] <= 0 or r["period_pnl"] <= 0]

    tier1.sort(key=lambda x: (x["official_pnl"] if x["official_pnl"] else x["period_pnl"]), reverse=True)
    tier2.sort(key=lambda x: (x["official_pnl"] if x["official_pnl"] else x["period_pnl"]), reverse=True)
    avoid.sort(key=lambda x: x["period_pnl"], reverse=False)

    return {
        "filters": {
            "slug_group": slug_group,
            "exclude_group": exclude_group or "NONE",
            "start_date": start_date or "NONE",
            "end_date": end_date or "NONE",
            "min_events": min_events
        },
        "total_audited": len(results),
        "tier1_high_conviction": tier1[:limit],
        "tier2_specialists": tier2[:limit],
        "avoid_cohort": avoid[:5]
    }

def print_screened_traders_cli(screen_res: Dict[str, Any]):
    flt = screen_res["filters"]
    t1 = screen_res["tier1_high_conviction"]
    t2 = screen_res["tier2_specialists"]
    av = screen_res["avoid_cohort"]

    print("\n" + "=" * 165)
    print("  POLYMARKET QUANTITATIVE SCREENER (GROUND-TRUTH ON-CHAIN VERIFIED)")
    print(f"  Target Market: [{flt['slug_group']}] | Exclude: [{flt['exclude_group']}] | Time Window: {flt['start_date']} → {flt['end_date']}")
    print("=" * 165)

    if t1:
        print("\n⭐ TIER 1: PRIME HIGH-CONVICTION CANDIDATES (STRONG SIGNAL + POSITIVE CAPITAL EDGE + VERIFIED)")
        print("-" * 165)
        print(f"{'Rank':<4} | {'User Name':<18} | {'Wallet / Profile Link':<42} | {'Official Lifetime PnL':<22} | {'Signal Edge':<11} | {'Cap Edge':<10} | {'N_eff':<5} | {'PF':<5} | {'WR %':<6} | {'Primary Market Family'}")
        print("-" * 165)
        for i, r in enumerate(t1, 1):
            off_pnl_str = f"${r['official_pnl']:>12,.2f} (#{r['official_rank']})" if r['official_pnl'] else f"${r['period_pnl']:>12,.2f}"
            sig_s = f"{r['sig_edge']:>+8.2f}%"
            cap_s = f"{r['cap_edge']:>+8.2f}%"
            print(f"#{i:<3} | {r['userName'][:17]:<18} | {r['wallet']:<42} | {off_pnl_str:<22} | {sig_s:<11} | {cap_s:<10} | {r['n_eff']:>5} | {r['pf']:>5.2f} | {r['win_rate']:>5.1f}% | {r['top_market']}")

    if t2:
        print("\n🥈 TIER 2: SPECIALIZED SATELLITE SNIPERS (MODERATE EDGE OR HIGH-WR BRACKET)")
        print("-" * 165)
        print(f"{'Rank':<4} | {'User Name':<18} | {'Wallet / Profile Link':<42} | {'Official Lifetime PnL':<22} | {'Signal Edge':<11} | {'Cap Edge':<10} | {'N_eff':<5} | {'PF':<5} | {'WR %':<6} | {'Primary Market Family'}")
        print("-" * 165)
        for i, r in enumerate(t2, 1):
            off_pnl_str = f"${r['official_pnl']:>12,.2f} (#{r['official_rank']})" if r['official_pnl'] else f"${r['period_pnl']:>12,.2f}"
            sig_s = f"{r['sig_edge']:>+8.2f}%"
            cap_s = f"{r['cap_edge']:>+8.2f}%"
            print(f"#{i:<3} | {r['userName'][:17]:<18} | {r['wallet']:<42} | {off_pnl_str:<22} | {sig_s:<11} | {cap_s:<10} | {r['n_eff']:>5} | {r['pf']:>5.2f} | {r['win_rate']:>5.1f}% | {r['top_market']}")

    print("=" * 165 + "\n")

# ── 8. Real-Time Discord Follow Bot ─────────────────────────────────────────────

DEFAULT_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL") or "https://discord.com/api/webhooks/1553388229225480293/J2W99-4z0CUnlYisb3RbHfwqcpFjiTSBJ_LX5xwSJrv4f3ggWOPa85LZAdSNe1Bt74lD"

DEFAULT_FOLLOW_TARGETS = [
    {
        "wallet": "0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e",
        "name": "Weather Master",
        "category": "🌡️ Weather & Temperature Arbitrage"
    }
]

STATE_FILE = os.path.expanduser("~/.follow_bot_seen_trades.json")

def load_seen_trades() -> set:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_seen_trades(seen_trades: set):
    try:
        # Keep recent 20,000 hashes
        recent = list(seen_trades)[-20000:]
        with open(STATE_FILE, "w") as f:
            json.dump(recent, f)
    except Exception:
        pass

def fetch_wallet_recent_activity(wallet: str, limit: int = 15) -> List[Dict[str, Any]]:
    url = f"{BASE_DATA_API}/activity?user={wallet.strip().lower()}&limit={limit}"
    data = make_request(url)
    if isinstance(data, list):
        return [item for item in data if item.get("type") == "TRADE"]
    return []

def send_discord_trade_alert(trade: Dict[str, Any], trader_info: Dict[str, str], webhook_url: str) -> bool:
    side = (trade.get("side") or "BUY").upper()
    is_buy = side == "BUY"
    color = 0x2ecc71 if is_buy else 0xe74c3c # Clean vibrant green / red
    outcome = (trade.get("outcome") or "YES").upper()
    action = f"🟢 BUY {outcome}" if is_buy else f"🔴 SELL {outcome}"
    
    w = trader_info["wallet"]
    name = trader_info.get("name") or trade.get("name") or trade.get("pseudonym") or "Trader"
    
    slug = trade.get("slug") or ""
    event_slug = trade.get("eventSlug") or ""
    title = trade.get("title") or "Polymarket Event"
    price = float(trade.get("price", 0))
    shares = float(trade.get("size", 0))
    usdc = float(trade.get("usdcSize") or (price * shares))

    # Extract clean concise bucket / bracket (e.g. Amsterdam 21°C, Milan 26°C, Donald Trump, etc.)
    m_temp = re.search(r"(\d+°[CF]|\d+-\d+°[CF]|\d+°[CF] or (?:higher|below|more|less))", title, re.IGNORECASE)
    m_city = re.search(r"in ([A-Za-z\s]+) be", title)
    city_str = m_city.group(1).strip() if m_city else ""
    
    if m_temp:
        temp_str = m_temp.group(1).strip()
        bucket_label = f"{city_str} {temp_str}".strip()
    elif "trump" in title.lower():
        bucket_label = "Donald Trump"
    elif "harris" in title.lower():
        bucket_label = "Kamala Harris"
    else:
        bucket_label = title[:50]

    target_slug = event_slug or slug
    event_url = f"https://polymarket.com/event/{target_slug}" if event_slug else f"https://polymarket.com/market/{slug}"
    profile_url = f"https://polymarket.com/{w}"

    # Ultra-clean spacious layout (Zero clutter, clear whitespace)
    desc = (
        f"👤 [{name}]({profile_url})\n\n"
        f"💰 **${price:.3f}** ({price*100:.0f}%)   •   📦 **${usdc:,.2f}** ({shares:,.0f} shares)\n\n"
        f"👉 **[เปิดดูบน Polymarket]({event_url})**"
    )

    embed = {
        "title": f"{action}  •  {bucket_label}",
        "url": event_url,
        "color": color,
        "description": desc,
        "timestamp": datetime.fromtimestamp(trade.get("timestamp") or int(datetime.now(timezone.utc).timestamp()), tz=timezone.utc).isoformat()
    }

    payload = {
        "username": "Polymarket Signal",
        "avatar_url": "https://polymarket.com/favicon.ico",
        "embeds": [embed]
    }

    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.getcode() in [200, 204]
    except Exception as e:
        print(f"Error sending Discord alert: {e}")
        return False

def run_follow_bot(
    webhook_url: str = DEFAULT_WEBHOOK_URL,
    targets: Optional[List[Dict[str, str]]] = None,
    include_groups: Optional[List[str]] = None,
    exclude_groups: Optional[List[str]] = None,
    min_price: Optional[float] = None,
    poll_interval: int = 15,
    run_once: bool = False,
    test_mode: bool = False
):
    if targets is None:
        targets = DEFAULT_FOLLOW_TARGETS

    seen_trades = load_seen_trades()
    inc_str = ", ".join(include_groups) if include_groups else "ALL"
    exc_str = ", ".join(exclude_groups) if exclude_groups else "NONE"
    
    print("=" * 105)
    print("  🤖 POLYMARKET REAL-TIME DISCORD FOLLOW BOT (WITH MARKET GROUP FILTERING)")
    print(f"  Webhook:        {webhook_url[:45]}...{webhook_url[-10:]}")
    print(f"  Include Groups: [{inc_str}]")
    print(f"  Exclude Groups: [{exc_str}]")
    if min_price is not None:
        print(f"  Min Price:      ${min_price:.3f}")
    print(f"  Tracking:       {len(targets)} Verified High-Alpha Traders")
    print("=" * 105)
    for i, t in enumerate(targets, 1):
        print(f"  #{i}. {t['name']:<18} ({t['wallet']}) -> {t.get('category', 'Trader')}")
    print("-" * 105)

    if test_mode:
        print("Sending sample test signal card to Discord...")
        sample_trade = {
            "proxyWallet": targets[0]["wallet"],
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "side": "BUY",
            "outcome": "No",
            "price": 0.085,
            "size": 520.0,
            "usdcSize": 44.20,
            "title": "Will the highest temperature in Paris be 22°C on September 26?",
            "slug": "highest-temperature-in-paris-on-september-26-2026-22c",
            "eventSlug": "highest-temperature-in-paris-on-september-26-2026",
            "transactionHash": "0xf2ef1b9694a8ecee593d90e99aed9571794949344242e8a3d2abf7625454b618"
        }
        success = send_discord_trade_alert(sample_trade, targets[0], webhook_url)
        print("Test Alert Sent Status:", "✅ Success" if success else "❌ Failed")
        return

    # First run initialization (mark current existing trades as seen so we don't spam historical orders)
    if len(seen_trades) == 0:
        print("First-time startup: Ingesting existing trades into seen cache to avoid spamming old history...")
        for t in targets:
            acts = fetch_wallet_recent_activity(t["wallet"], limit=20)
            for act in acts:
                trade_id = act.get("transactionHash") or f"{act.get('timestamp')}_{act.get('conditionId')}_{act.get('outcomeIndex')}_{act.get('side')}"
                seen_trades.add(trade_id)
        save_seen_trades(seen_trades)
        print(f"Ingested {len(seen_trades)} historical trades. Listening for NEW live incoming orders...\n")

    try:
        while True:
            new_alerts_count = 0
            for t in targets:
                acts = fetch_wallet_recent_activity(t["wallet"], limit=10)
                # Sort chronological
                acts = sorted(acts, key=lambda x: x.get("timestamp") or 0)
                for act in acts:
                    trade_id = act.get("transactionHash") or f"{act.get('timestamp')}_{act.get('conditionId')}_{act.get('outcomeIndex')}_{act.get('side')}"
                    if trade_id not in seen_trades:
                        seen_trades.add(trade_id)
                        
                        slug = act.get("slug") or ""
                        event_slug = act.get("eventSlug") or ""
                        title = act.get("title") or ""
                        grp = extract_slug_group(slug, event_slug, title)
                        price = float(act.get("price", 0))

                        # 1. Filter by include_groups
                        if include_groups and len(include_groups) > 0:
                            matched = False
                            for inc in include_groups:
                                inc_clean = inc.strip().lower()
                                if inc_clean in ["weather", "temp", "temperature"] and grp in ["highest-temp", "lowest-temp", "precipitation-weather"]:
                                    matched = True
                                    break
                                elif inc_clean in grp or grp in inc_clean:
                                    matched = True
                                    break
                            if not matched:
                                continue # Skip non-matching group

                        # 2. Filter by exclude_groups
                        if exclude_groups and len(exclude_groups) > 0:
                            excluded = False
                            for exc in exclude_groups:
                                exc_clean = exc.strip().lower()
                                if exc_clean in ["weather", "temp", "temperature"] and grp in ["highest-temp", "lowest-temp", "precipitation-weather"]:
                                    excluded = True
                                    break
                                elif exc_clean in grp or grp in exc_clean:
                                    excluded = True
                                    break
                            if excluded:
                                continue # Skip excluded group

                        # 3. Filter by min_price
                        if min_price is not None and price < min_price:
                            continue

                        new_alerts_count += 1
                        side = act.get("side", "BUY")
                        outcome = act.get("outcome", "-")
                        title_sub = act.get("title", "Market")[:50]
                        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] 🚨 NEW MATCHED SIGNAL from {t['name']}: {side} [{outcome}] @ ${price:.3f} on [{grp}] '{title_sub}'")
                        send_discord_trade_alert(act, t, webhook_url)
            
            if new_alerts_count > 0:
                save_seen_trades(seen_trades)
                
            if run_once:
                print(f"Single check complete. {new_alerts_count} new alerts processed.")
                break
                
            import time
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\nFollow Bot stopped by user.")
        save_seen_trades(seen_trades)

# ── 9. CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Polymarket 3-Dimensional Quantitative Engine & Rolling Walk-Forward Tracker")
    
    # Target
    parser.add_argument("--wallet", type=str, default="", help="Proxy wallet address (0x...) to analyze")
    parser.add_argument("--screen", "--screen-top", action="store_true", help="Run multi-trader quantitative screening across market families")
    parser.add_argument("--leaderboard", action="store_true", help="Display top traders leaderboard")
    parser.add_argument("--meta-backtest", action="store_true", help="Run Meta-Backtest to validate the predictive power of trader screening criteria")
    parser.add_argument("--follow-bot", "--alert-bot", action="store_true", help="Start real-time Discord Webhook alert bot tracking Alpha traders")
    parser.add_argument("--target", type=str, default=None, help="Custom target wallet address to follow (default: Weather Master)")
    parser.add_argument("--test-alert", action="store_true", help="Send a test trade alert card to Discord webhook")
    parser.add_argument("--webhook", type=str, default=DEFAULT_WEBHOOK_URL, help="Discord webhook URL")
    parser.add_argument("--poll-interval", type=int, default=15, help="Polling interval in seconds (default 15)")
    parser.add_argument("--min-price", type=float, default=None, help="Minimum trade price filter (e.g. 0.10 to filter out lotto bets)")
    parser.add_argument("--once", action="store_true", help="Run a single poll check and exit")
    
    # Filtering
    parser.add_argument("--slug-group", "--include-group", type=str, default="ALL", help="Filter by market family group (e.g. 'weather', 'highest-temp', 'us-politics', 'fed-rates')")
    parser.add_argument("--exclude-group", type=str, default=None, help="Exclude specific market family group (e.g. 'sports-soccer', 'pop-culture')")
    parser.add_argument("--slug", "--keyword", type=str, default=None, help="Filter by market slug or keyword pattern (e.g. 'atlanta', 'btc', 'president')")
    parser.add_argument("--timeframe", choices=["ALL", "MONTH", "WEEK", "DAY"], default="ALL", help="Leaderboard timeframe")
    parser.add_argument("--sort", choices=["pnl", "vol", "roi"], default="pnl", help="Sort leaderboard criteria")
    parser.add_argument("--category", default="OVERALL", help="Market category (OVERALL, POLITICS, SPORTS, CRYPTO, etc.)")
    parser.add_argument("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD or relative like '30d')")
    parser.add_argument("--end-date", type=str, default=None, help="End date (YYYY-MM-DD or relative like 'now')")
    parser.add_argument("--min-events", type=int, default=15, help="Minimum independent events required")
    parser.add_argument("--limit", type=int, default=10, help="Number of records/traders to display")
    
    # Output
    parser.add_argument("--breakdown", action="store_true", default=True, help="Show slug-group market breakdown")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON format")

    args = parser.parse_args()

    if args.meta_backtest:
        run_meta_backtest_cli()
    elif args.test_alert:
        run_follow_bot(webhook_url=args.webhook, test_mode=True)
    elif args.follow_bot:
        custom_targets = None
        if args.target:
            custom_targets = [{"wallet": args.target.strip().lower(), "name": "Target Trader", "category": "Custom Track"}]
        inc_groups = [g.strip() for g in args.slug_group.split(",") if g.strip()] if args.slug_group and args.slug_group != "ALL" else None
        exc_groups = [g.strip() for g in args.exclude_group.split(",") if g.strip()] if args.exclude_group else None
        run_follow_bot(
            webhook_url=args.webhook,
            targets=custom_targets,
            include_groups=inc_groups,
            exclude_groups=exc_groups,
            min_price=args.min_price,
            poll_interval=args.poll_interval,
            run_once=args.once
        )
    elif args.screen or (args.slug_group != "ALL" and not args.wallet and not args.leaderboard) or (args.exclude_group and not args.wallet):
        screen_res = screen_top_traders(
            slug_group=args.slug_group,
            exclude_group=args.exclude_group,
            start_date=args.start_date,
            end_date=args.end_date,
            min_events=args.min_events,
            limit=args.limit
        )
        if args.json:
            print(json.dumps(screen_res, indent=2))
        else:
            print_screened_traders_cli(screen_res)
    elif args.wallet:
        result = analyze_wallet(
            wallet_address=args.wallet,
            slug_filter=args.slug,
            slug_group_filter=args.slug_group,
            start_date=args.start_date,
            end_date=args.end_date,
            max_closed=args.limit if args.limit > 100 else 3000
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_wallet_cli(result, show_breakdown=args.breakdown)
    else:
        order_api = "VOL" if args.sort.lower() == "vol" else "PNL"
        leaders = fetch_leaderboard(time_period=args.timeframe, limit=args.limit if args.limit > 10 else 25, order_by=order_api, category=args.category)
        if args.sort.lower() in ["roi", "pct"]:
            leaders = sorted(leaders, key=lambda x: x["roi_vol_pct"], reverse=True)
        elif args.sort.lower() == "vol":
            leaders = sorted(leaders, key=lambda x: x["vol"], reverse=True)
            
        if args.json:
            print(json.dumps(leaders, indent=2))
        else:
            print_leaderboard_cli(leaders, timeframe=args.timeframe)

if __name__ == "__main__":
    main()
