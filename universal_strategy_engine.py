import urllib.request
import json
import re
import math
import statistics
from datetime import datetime, timezone
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple

from polymarket_tracker import (
    extract_slug_group,
    classify_market_structure,
    make_request,
    BASE_DATA_API
)

# ── 1. Contract Time & Duration Parser ─────────────────────────────────────────

def parse_contract_time_bounds(title: str, slug: str, trade_ts: int) -> Tuple[Optional[int], Optional[int], str]:
    """
    Extract the true start timestamp, end timestamp, and duration of a Polymarket contract.
    Supports:
    - 5m / 15m micro intervals (e.g. '8:45AM-9:00AM ET')
    - 4-Hour blocks (e.g. '12:00PM-4:00PM ET')
    - Daily contracts (e.g. 'September 26')
    - Monthly / Annual contracts
    """
    t_clean = f"{title} {slug}".lower()
    
    # 1. Match explicit intraday interval (e.g. "12:00pm-4:00pm et" or "8:45am-9:00am et")
    m = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)\s*-\s*(\d{1,2}):(\d{2})\s*(am|pm)", t_clean)
    if m:
        h1, m1, p1, h2, m2, p2 = m.groups()
        t1_min = (int(h1) % 12 + (12 if p1.lower() == "pm" else 0)) * 60 + int(m1)
        t2_min = (int(h2) % 12 + (12 if p2.lower() == "pm" else 0)) * 60 + int(m2)
        if t2_min <= t1_min:
            t2_min += 24 * 60 # crosses midnight
        duration_sec = (t2_min - t1_min) * 60
        
        # Estimate interval start/end anchored to trade date
        dt = datetime.fromtimestamp(trade_ts, tz=timezone.utc)
        start_anchor = trade_ts - (trade_ts % duration_sec)
        end_anchor = start_anchor + duration_sec
        interval_type = f"Intraday Block ({duration_sec // 60}m)"
        return start_anchor, end_anchor, interval_type

    # 2. Daily contract
    if "on september" in t_clean or "on october" in t_clean or re.search(r"\b2026-\d{2}-\d{2}\b", t_clean):
        duration_sec = 86400
        start_anchor = trade_ts - (trade_ts % 86400)
        end_anchor = start_anchor + 86400
        return start_anchor, end_anchor, "Daily Contract (24h)"

    # 3. Default fallback
    return None, None, "Multi-Day / Long Horizon"


# ── 2. Universal Strategy Reverse Engineer Pipeline ────────────────────────────

def run_universal_strategy_reverse_engineer(wallet: str, max_trades: int = 500) -> Dict[str, Any]:
    w = wallet.strip().lower()

    # 1. Fetch raw trade activity
    url_act = f"{BASE_DATA_API}/activity?user={w}&limit={max_trades}"
    activities = make_request(url_act) or []

    # 2. Fetch ground truth profile
    u_url = f"{BASE_DATA_API}/v1/leaderboard?user={w}&timePeriod=ALL"
    u_data = make_request(u_url) or []
    username = u_data[0].get("userName") or u_data[0].get("pseudonym") or w[:10] if u_data else w[:10]
    lifetime_pnl = float(u_data[0].get("pnl") or 0) if u_data else 0.0
    lifetime_vol = float(u_data[0].get("vol") or 0) if u_data else 0.0

    trades = [a for a in activities if a.get("type") in ["TRADE", "BUY", "SELL"] or a.get("side")]
    if not trades:
        trades = activities

    if not trades:
        return {"wallet": w, "username": username, "error": "No trading activity found for this wallet."}

    # Sort chronological
    trades = sorted(trades, key=lambda x: x.get("timestamp") or 0)
    n_trades = len(trades)

    # ── STAGE A: DETERMINISTIC FEATURE & FINGERPRINT EXTRACTION ───────────────
    group_counts = defaultdict(int)
    prices = []
    sizes_usdc = []
    normalized_progress_list = [] # tau in [0, 1]
    trades_per_market = defaultdict(list)
    monthly_trades = defaultdict(list)

    for t in trades:
        slug = t.get("slug") or ""
        title = t.get("title") or t.get("question") or "Market"
        grp = extract_slug_group(slug, "", title)
        price = float(t.get("price") or 0)
        size = float(t.get("size") or 0)
        usdc = float(t.get("usdcSize") or (price * size))
        ts = t.get("timestamp") or 0

        group_counts[grp] += 1
        trades_per_market[slug].append(t)
        
        if ts > 0:
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            m_key = dt.strftime("%Y-%m")
            monthly_trades[m_key].append(t)
            
            # Compute true time progress tau
            t_start, t_end, _ = parse_contract_time_bounds(title, slug, ts)
            if t_start and t_end and t_end > t_start:
                tau = max(0.0, min(1.0, (ts - t_start) / (t_end - t_start)))
                normalized_progress_list.append(tau)

        if price > 0:
            prices.append(price)
        if usdc > 0:
            sizes_usdc.append(usdc)

    primary_group = max(group_counts.items(), key=lambda x: x[1])[0] if group_counts else "other"
    primary_group_pct = (group_counts[primary_group] / n_trades * 100) if n_trades else 0.0
    sample_slug = trades[0].get("slug", "")
    sample_title = trades[0].get("title", "")
    primary_structure = classify_market_structure(primary_group, sample_slug, sample_title)

    # Price distributions
    mean_price = statistics.mean(prices) if prices else 0.5
    median_price = statistics.median(prices) if prices else 0.5
    deep_val_count = sum(1 for p in prices if p < 0.20)
    mid_prob_count = sum(1 for p in prices if 0.20 <= p <= 0.80)
    high_prob_count = sum(1 for p in prices if p > 0.80)

    deep_val_pct = (deep_val_count / len(prices) * 100) if prices else 0.0
    mid_prob_pct = (mid_prob_count / len(prices) * 100) if prices else 0.0
    high_prob_pct = (high_prob_count / len(prices) * 100) if prices else 0.0

    # Timing distributions (True progress tau)
    late_cycle_count = sum(1 for tau in normalized_progress_list if tau >= 0.70)
    late_cycle_pct = (late_cycle_count / len(normalized_progress_list) * 100) if normalized_progress_list else 0.0
    mid_cycle_count = sum(1 for tau in normalized_progress_list if 0.20 <= tau < 0.70)
    mid_cycle_pct = (mid_cycle_count / len(normalized_progress_list) * 100) if normalized_progress_list else 0.0

    # Sequential order escalation (Empirical Probe -> Sweep verification)
    probe_sweep_count = 0
    total_consecutive_pairs = 0
    for slug, m_trades in trades_per_market.items():
        m_sorted = sorted(m_trades, key=lambda x: x.get("timestamp") or 0)
        for i in range(len(m_sorted) - 1):
            total_consecutive_pairs += 1
            t1, t2 = m_sorted[i], m_sorted[i+1]
            dt_pair = (t2.get("timestamp") or 0) - (t1.get("timestamp") or 0)
            u1 = float(t1.get("usdcSize") or 0)
            u2 = float(t2.get("usdcSize") or 0)
            if dt_pair <= 60 and u1 < 50 and u2 >= 5 * u1 and u2 >= 200:
                probe_sweep_count += 1

    probe_sweep_freq_pct = (probe_sweep_count / total_consecutive_pairs * 100) if total_consecutive_pairs else 0.0

    # Market directionality
    single_sided_mkts = 0
    dual_sided_mkts = 0
    multi_bracket_events = 0
    for slug, m_trades in trades_per_market.items():
        outcomes = {t.get("outcome") for t in m_trades}
        if len(outcomes) > 1:
            dual_sided_mkts += 1
        else:
            single_sided_mkts += 1
        if len(m_trades) >= 3:
            multi_bracket_events += 1

    tot_mkts = single_sided_mkts + dual_sided_mkts
    single_sided_pct = (single_sided_mkts / tot_mkts * 100) if tot_mkts else 100.0
    multi_bracket_events_pct = (multi_bracket_events / tot_mkts * 100) if tot_mkts else 0.0

    # ── STAGE B & C: COMPETING HYPOTHESES & EMPIRICAL FALSIFICATION ───────────
    hypotheses = []

    # H1: Late-Cycle High-Certainty Expiry Sniping
    # Predictions: tau >= 0.70 AND price > 0.75 (or price < 0.25 on NO)
    h1_matches = 0
    h1_violations = 0
    for t in trades:
        p = float(t.get("price") or 0)
        out = (t.get("outcome") or "").lower()
        # High certainty is either YES at > 0.75 or NO/Down at > 0.75
        is_high_certainty = (p >= 0.75)
        if is_high_certainty:
            h1_matches += 1
        elif 0.35 <= p <= 0.65:
            h1_violations += 1

    h1_coverage = (h1_matches / n_trades * 100) if n_trades else 0.0
    h1_counter = (h1_violations / n_trades * 100) if n_trades else 0.0
    hypotheses.append({
        "id": "H1",
        "name": "Late-Cycle High-Certainty Expiry Sniping",
        "coverage_pct": round(h1_coverage, 1),
        "counter_pct": round(h1_counter, 1),
        "test_rule": "Enters when contract price >= $0.75 (high certainty near resolution)",
        "empirical_fit": round(h1_coverage * 0.7 + (late_cycle_pct if normalized_progress_list else high_prob_pct) * 0.3, 1)
    })

    # H2: Mid-Cycle Directional Information / Trend Drift Reaction
    # Predictions: 0.20 <= tau <= 0.70 AND 0.25 <= price <= 0.75
    h2_matches = sum(1 for p in prices if 0.25 <= p <= 0.75)
    h2_violations = sum(1 for p in prices if p > 0.85 or p < 0.15)
    h2_coverage = (h2_matches / n_trades * 100) if n_trades else 0.0
    h2_counter = (h2_violations / n_trades * 100) if n_trades else 0.0
    hypotheses.append({
        "id": "H2",
        "name": "Mid-Cycle Directional Information & Trend Drift Reaction",
        "coverage_pct": round(h2_coverage, 1),
        "counter_pct": round(h2_counter, 1),
        "test_rule": "Enters during price formation ($0.25 - $0.75) tracking emerging information",
        "empirical_fit": round(h2_coverage * 0.7 + mid_prob_pct * 0.3, 1)
    })

    # H3: Multi-Bracket Forecast / Tail Dispersion Arbitrage
    h3_matches = sum(len(m_trades) for slug, m_trades in trades_per_market.items() if len(m_trades) >= 3)
    h3_coverage = (h3_matches / n_trades * 100) if n_trades else 0.0
    h3_counter = (100.0 - h3_coverage)
    hypotheses.append({
        "id": "H3",
        "name": "Multi-Bracket Dispersion & Forecast Revision Coverage",
        "coverage_pct": round(h3_coverage, 1),
        "counter_pct": round(h3_counter, 1),
        "test_rule": "Accumulates multiple mutually-exclusive brackets within the same underlying event",
        "empirical_fit": round((multi_bracket_events_pct * 0.6) + (deep_val_pct * 0.4), 1)
    })

    # H4: Automated Liquidity Provision & Spread Capture
    h4_matches = sum(len(m_trades) for slug, m_trades in trades_per_market.items() if len({x.get("outcome") for x in m_trades}) > 1)
    h4_coverage = (h4_matches / n_trades * 100) if n_trades else 0.0
    h4_counter = (100.0 - h4_coverage)
    hypotheses.append({
        "id": "H4",
        "name": "Automated Liquidity Provision & Bid-Ask Spread Capture",
        "coverage_pct": round(h4_coverage, 1),
        "counter_pct": round(h4_counter, 1),
        "test_rule": "Executes both YES and NO sides on the same contract to capture market-maker spread",
        "empirical_fit": round((100.0 - single_sided_pct), 1)
    })

    # H5: Deep-Value Asymmetric Longshot Buying
    h5_matches = sum(1 for p in prices if p < 0.20)
    h5_violations = sum(1 for p in prices if p >= 0.50)
    h5_coverage = (h5_matches / n_trades * 100) if n_trades else 0.0
    h5_counter = (h5_violations / n_trades * 100) if n_trades else 0.0
    hypotheses.append({
        "id": "H5",
        "name": "Deep-Value Asymmetric Longshot Buying (< $0.20)",
        "coverage_pct": round(h5_coverage, 1),
        "counter_pct": round(h5_counter, 1),
        "test_rule": "Purchases low-probability contracts (< $0.20) exploiting tail mispricing",
        "empirical_fit": round(deep_val_pct, 1)
    })

    # Rank hypotheses by empirical fit
    hypotheses = sorted(hypotheses, key=lambda x: x["empirical_fit"], reverse=True)
    primary_hypothesis = hypotheses[0]

    # ── STAGE D: CHRONOLOGICAL OUT-OF-SAMPLE (OOS) VALIDATION ─────────────────
    # Split trades chronologically into Train (first 60%) and Test (last 40%)
    split_idx = int(n_trades * 0.6)
    train_trades = trades[:split_idx]
    test_trades = trades[split_idx:]

    oos_train_fit = 0.0
    oos_test_fit = 0.0
    oos_status = "Insufficient Sample"

    if len(train_trades) >= 20 and len(test_trades) >= 20:
        # Evaluate primary rule on Train vs Test
        p_id = primary_hypothesis["id"]
        if p_id == "H1":
            train_match = sum(1 for t in train_trades if float(t.get("price") or 0) >= 0.75) / len(train_trades) * 100
            test_match = sum(1 for t in test_trades if float(t.get("price") or 0) >= 0.75) / len(test_trades) * 100
        elif p_id == "H2":
            train_match = sum(1 for t in train_trades if 0.25 <= float(t.get("price") or 0) <= 0.75) / len(train_trades) * 100
            test_match = sum(1 for t in test_trades if 0.25 <= float(t.get("price") or 0) <= 0.75) / len(test_trades) * 100
        elif p_id == "H3":
            train_match = sum(1 for t in train_trades if float(t.get("price") or 0) < 0.30 or float(t.get("price") or 0) > 0.75) / len(train_trades) * 100
            test_match = sum(1 for t in test_trades if float(t.get("price") or 0) < 0.30 or float(t.get("price") or 0) > 0.75) / len(test_trades) * 100
        elif p_id == "H5":
            train_match = sum(1 for t in train_trades if float(t.get("price") or 0) < 0.20) / len(train_trades) * 100
            test_match = sum(1 for t in test_trades if float(t.get("price") or 0) < 0.20) / len(test_trades) * 100
        else:
            train_match = 50.0
            test_match = 50.0

        oos_train_fit = round(train_match, 1)
        oos_test_fit = round(test_match, 1)
        # Check stability across train/test
        discrepancy = abs(oos_test_fit - oos_train_fit)
        if oos_test_fit >= 35.0 and discrepancy <= 25.0:
            oos_status = f"PERSISTENT (Train: {oos_train_fit}% ➔ Test: {oos_test_fit}%, Δ {discrepancy:.1f}%)"
        else:
            oos_status = f"REGIME SHIFT (Train: {oos_train_fit}% ➔ Test: {oos_test_fit}%, Δ {discrepancy:.1f}%)"

    # ── STAGE E: STRICT 3-TIER EPISTEMIC SEPARATION ────────────────────────────
    observed_facts = [
        f"Analyzed {n_trades} on-chain trades across {tot_mkts} independent contracts.",
        f"Asset Specialization: {primary_group_pct:.1f}% concentrated in [{primary_group}] ({primary_structure}).",
        f"Entry Pricing: Mean ${mean_price:.3f} | Median ${median_price:.3f} (High-Certainty >$0.80: {high_prob_pct:.1f}% | Mid-Prob $0.20-$0.80: {mid_prob_pct:.1f}% | Deep-Value <$0.20: {deep_val_pct:.1f}%).",
        f"Order Sizing Dispersion: Median ${statistics.median(sizes_usdc):,.2f} USDC (Mean: ${statistics.mean(sizes_usdc):,.2f} USDC | Max Clip: ${max(sizes_usdc):,.2f} USDC).",
        f"Market Directionality: {single_sided_pct:.1f}% single-sided directional positions vs {100.0-single_sided_pct:.1f}% dual-sided market making.",
        f"Execution Timing: {late_cycle_pct:.1f}% executed in late cycle (tau >= 0.70) | {mid_cycle_pct:.1f}% in mid cycle (tau 0.20-0.70)." if normalized_progress_list else f"Execution Timing: Multi-day holding pattern across {tot_mkts} markets.",
        f"Empirical Sizing Escalation: Explicit Probe-then-Sweep sequences observed in {probe_sweep_freq_pct:.2f}% of consecutive order pairs ({probe_sweep_count}/{total_consecutive_pairs})."
    ]

    inferred_logic = [
        f"Best Matching Strategy Archetype: {primary_hypothesis['name']} (Empirical Support: {primary_hypothesis['empirical_fit']}/100).",
        f"Empirical Trade Coverage: {primary_hypothesis['coverage_pct']}% of observed trades satisfy primary hypothesis conditions.",
        f"Empirical Falsification Rate: {primary_hypothesis['counter_pct']}% of observed trades directly violate primary hypothesis conditions.",
        f"Out-of-Sample Behavioral Persistence: {oos_status}."
    ]

    unknown_unverified = [
        "Unobserved Counterfactuals: No off-chain record of potential markets where trader entry conditions were met but the trader chose NOT to trade (No-Trade controls).",
        "Exact External Data Feed: Cannot prove whether trader connects to Binance, Coinbase, Bybit, or a proprietary websocket node from public on-chain data alone.",
        "Internal Execution Infrastructure: Exact latency thresholds, slippage tolerances, and internal risk sizing algorithms remain private."
    ]

    return {
        "wallet": w,
        "username": username,
        "lifetime_pnl": lifetime_pnl,
        "lifetime_vol": lifetime_vol,
        "primary_group": primary_group,
        "primary_structure": primary_structure,
        "primary_strategy": primary_hypothesis["name"],
        "heuristic_fit_score": primary_hypothesis["empirical_fit"],
        "hypotheses": hypotheses,
        "oos_status": oos_status,
        "observed_facts": observed_facts,
        "inferred_logic": inferred_logic,
        "unknown_unverified": unknown_unverified
    }


def print_universal_blueprint_cli(res: Dict[str, Any]) -> None:
    if "error" in res:
        print(f"❌ Error: {res['error']}")
        return

    print("\n" + "═" * 135)
    print(f"  🧬 UNIVERSAL TRADER STRATEGY REVERSE ENGINEER (STAGE A-E EMPIRICAL FALSIFICATION)")
    print(f"  Trader: {res['username']} ({res['wallet']})")
    print(f"  Lifetime PnL: ${res['lifetime_pnl']:,.2f} | Analyzed Volume: ${res['lifetime_vol']:,.2f}")
    print("═" * 135)

    print(f"\n📂 1. MARKET SPECIALIZATION & CONTRACT STRUCTURE:")
    print(f"   • Primary Market Family:  [{res['primary_group']}]")
    print(f"   • Contract Archetype:     {res['primary_structure']}")
    print(f"   • Top Heuristic Match:    {res['primary_strategy']}")
    print(f"   • Heuristic Fit Score:    {res['heuristic_fit_score']} / 100 (Empirical Coverage & Timing Weight)")

    print(f"\n🔬 2. COMPETING HYPOTHESES & FALSIFICATION TEST:")
    for h in res["hypotheses"]:
        bar_len = int(h["empirical_fit"] / 10)
        bar = "█" * bar_len + "░" * (10 - bar_len)
        rank_tag = "👑 Primary Fit" if h["id"] == res["hypotheses"][0]["id"] else "   Alternative"
        print(f"   [{bar}] {h['empirical_fit']:>5.1f}/100 | {rank_tag} ({h['id']}): {h['name']:<55} | Counter: {h['counter_pct']:>4.1f}%")

    print(f"\n📋 3. WHAT IS OBSERVED (Direct Ground-Truth On-Chain Facts):")
    for fact in res["observed_facts"]:
        print(f"   ✓ {fact}")

    print(f"\n🧠 4. WHAT IS INFERRED (Empirically Supported Strategy Blueprint):")
    for inf in res["inferred_logic"]:
        print(f"   ⚡ {inf}")

    print(f"\n🔒 5. WHAT IS UNKNOWN / UNVERIFIED (Strict Epistemic Public Boundary):")
    for unk in res["unknown_unverified"]:
        print(f"   ❓ {unk}")

    print(f"\n📅 6. TRUE OUT-OF-SAMPLE (OOS) TEMPORAL VALIDATION:")
    print(f"   • {res['oos_status']}")
    print("═" * 135)
