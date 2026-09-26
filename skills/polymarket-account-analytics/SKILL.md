---
name: polymarket-account-analytics
description: "Unified Quantitative Analytics, Market Structure Classification, Ground-Truth On-Chain Reconciliation, 3D Trade Quality Evaluation, Rolling Walk-Forward Engine, Multi-Market Screener, Macro Market Performance Analytics, and Real-Time Discord Follow Bot for Polymarket."
version: 8.0.0
author: Arena Quantitative Agent
---

# Polymarket Account Analytics & Quantitative Alpha Engine

A comprehensive, production-grade CLI and Python API tool for discovering, evaluating, and copy-trading top prediction market traders on Polymarket.

---

## 🌟 Core Architecture & Features

1. **Market Structure Classification Layer**:
   - Explicitly classifies every contract archetype (`Binary`, `Bracket / Range`, `Multi-Choice 1-of-N`, `Ordinal Threshold`).
   - Disentangles **Settlement Structure / Outcome Distribution** from **Trading Alpha / Edge**, preventing false assumptions that high NO resolution in multi-choice markets represents an edge.

2. **Ground-Truth On-Chain Cross-Reconciliation**:
   - Directly verifies lifetime balances, official ranks, and PnL against Polymarket Platform Ground-Truth (`/v1/leaderboard?user=<wallet>`).
   - Automatically detects and flags **High-Frequency Data Truncation** (e.g. accounts with 50k+ trades).
   - Hard Gate: Automatically disqualifies negative lifetime PnL accounts (e.g. volume-farming bots like `GoalLineGhost`).

3. **True Settlement Merged Accounting**:
   - Seamlessly reconciles claimed closed positions (`/closed-positions`) and unclaimed settled losses/wins sitting in open positions (`/positions` with `curPrice in [0.0, 1.0]`).
   - Completely eliminates **Asymmetric Truncation Selection Bias**.

4. **3 Dimensions of Trade Quality (Signal | Sizing | Evidence)**:
   - **Signal Quality**: Mean Calibration Edge vs entry price, Bayesian shrinkage probability.
   - **Sizing Quality**: Capital-weighted edge per share, Sizing Edge Delta ($\Delta$).
   - **Evidence & Tail Risk**: Independent effective events ($N_{\text{eff}}$), Profit Factor, Max Drawdown, Expectancy.

5. **Rolling Walk-Forward Out-of-Sample Engine**:
   - Evaluates performance across sequential monthly forward time windows.

6. **Multi-Market Quantitative Screener (`--screen-top`)**:
   - Screen top traders by market family (`--slug-group highest-temp`, `fed-rates`, `us-politics`, `btc-price`, etc.).
   - Support category exclusion (`--exclude-group sports-soccer`).
   - Custom timeframes (`--start-date 2026-03-01 --end-date 2026-09-30`).

7. **Macro Market Group Performance & Time-Series Analytics (`--market-performance`)**:
   - Analyzes platform-wide market volume, settled count, and outcome distribution aggregated by market group or date period (`--group-by {group,month,week,day}`).

8. **Real-Time Discord Follow Bot (`--follow-bot`)**:
   - Automated trade detection with group inclusion/exclusion filtering and minimum price gates.

---

## 🧱 Quantitative Methodology & Pipeline

```
Market Family (slug_group)
      ↓
Market Structure Classification
  ├── Binary (Yes/No proposition, 50/50 baseline)
  ├── Bracket / Range (Mutually exclusive continuous ranges; 1 of K outcome)
  ├── Multi-Choice (1 of N candidate/team winners)
  └── Ordinal Threshold (Cumulative monotonic milestones)
      ↓
Event De-duplication & Hierarchy (event_id)
      ↓
Position Accounting & Settlement (True Settlement Accounting)
      ↓
3-Tier Quantitative Edge Hierarchy (Signal Edge → Capital Edge → N_eff → Temporal Persistence)
      ↓
Trader Evaluation & Portfolio Recommendation
```

---

## 💻 CLI Usage Guide

### 1. Universal Strategy Reverse Engineer (Empirical Hypothesis Falsification)

```bash
# Reverse-engineer any trader (Crypto, Weather, Sports, Politics, etc.)
python3 polymarket_tracker.py --reverse-engineer 0xcc500cbcc8b7cf5bd21975ebbea34f21b5644c82

# Reverse-engineer Weather Master
python3 polymarket_tracker.py --reverse-engineer 0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e
```

### 2. Trader Liveness & Activity Scanner (Step 2 Gate)

```bash
# Scan Top Crypto leaderboard for active traders
python3 polymarket_tracker.py --active-traders --category CRYPTO

# Check specific trader liveness
python3 polymarket_tracker.py --active-traders --wallet 0x55be7aa03ecfbe37aa5460db791205f7ac9ddca3
```

### 3. Macro Market Performance & Settlement Structure

```bash
# Analyze all market groups across 2026
python3 polymarket_tracker.py --market-performance --start-date 2026-01-01 --end-date 2026-09-26

# Group by Month and analyze market outcome distribution
python3 polymarket_tracker.py --market-performance --start-date 2026-01-01 --end-date 2026-09-26 --group-by month

# Filter specifically for Weather markets across time
python3 polymarket_tracker.py --market-performance --slug-group weather --group-by month
```

### 4. Multi-Market Screening (Ground-Truth Verified)

```bash
# Screen top traders across all markets
python3 polymarket_tracker.py --screen-top

# Screen top traders in Temperature / Weather markets
python3 polymarket_tracker.py --slug-group highest-temp

# Screen top traders excluding World Cup / Soccer
python3 polymarket_tracker.py --screen-top --exclude-group sports-soccer --start-date 2026-01-01 --end-date 2026-09-26
```

### 5. Deep Forensic Audit for a Single Wallet

```bash
# Full audit with profile URL, ground-truth reconciliation, 3D metrics & walk-forward folds
python3 polymarket_tracker.py --wallet 0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e

# Output machine-readable JSON for agents
python3 polymarket_tracker.py --wallet 0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e --json
```

### 6. Real-Time Discord Follow Bot

```bash
# Follow Weather Master for Weather markets only
python3 polymarket_tracker.py --follow-bot --target 0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e --include-group weather
```
