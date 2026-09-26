---
name: polymarket-account-analytics
description: "Unified Quantitative Analytics, Ground-Truth On-Chain Reconciliation, 3D Trade Quality Evaluation, Rolling Walk-Forward Engine, Multi-Market Screener, and Fixed-Budget Meta-Backtest for Polymarket traders."
version: 7.0.0
author: Arena Quantitative Agent
---

# Polymarket Account Analytics & Quantitative Alpha Engine

A comprehensive, production-grade CLI and Python API tool for discovering, evaluating, and copy-trading top prediction market traders on Polymarket.

---

## 🌟 Core Architecture & Features

1. **Ground-Truth On-Chain Cross-Reconciliation**:
   - Directly verifies lifetime balances, official ranks, and PnL against Polymarket Platform Ground-Truth (`/v1/leaderboard?user=<wallet>`).
   - Automatically detects and flags **High-Frequency Data Truncation** (e.g. accounts with 50k+ trades).
   - Hard Gate: Automatically disqualifies negative lifetime PnL accounts (e.g. volume-farming bots like `GoalLineGhost`).

2. **True Settlement Merged Accounting**:
   - Seamlessly reconciles claimed closed positions (`/closed-positions`) and unclaimed settled losses/wins sitting in open positions (`/positions` with `curPrice in [0.0, 1.0]`).
   - Completely eliminates **Asymmetric Truncation Selection Bias**.

3. **3 Dimensions of Trade Quality (Signal | Sizing | Evidence)**:
   - **Signal Quality**: Mean Calibration Edge vs entry price, Bayesian shrinkage probability.
   - **Sizing Quality**: Capital-weighted edge per share, Sizing Edge Delta ($\Delta$).
   - **Evidence & Tail Risk**: Independent effective events ($N_{\text{eff}}$), Profit Factor, Max Drawdown, Expectancy.

4. **Rolling Walk-Forward Out-of-Sample Engine**:
   - Evaluates performance across sequential monthly forward time windows.

5. **Multi-Market Quantitative Screener (`--screen-top`)**:
   - Screen top traders by market family (`--slug-group highest-temp`, `fed-rates`, `us-politics`, `btc-price`, etc.).
   - Support category exclusion (`--exclude-group sports-soccer`).
   - Custom timeframes (`--start-date 2026-03-01 --end-date 2026-09-30`).

6. **Meta-Backtest Engine (`--meta-backtest`)**:
   - Simulates fixed-budget ($10k/trader) forward copy-trading portfolios comparing Qualified vs Disqualified cohorts.

---

## 💻 CLI Usage Guide

### 1. Multi-Market Screening (Ground-Truth Verified)

```bash
# Screen top traders across all markets
python3 polymarket_tracker.py --screen-top

# Screen top traders in Temperature / Weather markets
python3 polymarket_tracker.py --slug-group highest-temp

# Screen top traders excluding World Cup / Soccer
python3 polymarket_tracker.py --screen-top --exclude-group sports-soccer --start-date 2026-03-01 --end-date 2026-09-30

# Screen politics specialists
python3 polymarket_tracker.py --slug-group us-politics
```

### 2. Deep Forensic Audit for a Single Wallet

```bash
# Full audit with profile URL, ground-truth reconciliation, 3D metrics & walk-forward folds
python3 polymarket_tracker.py --wallet 0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e

# Audit specific market family for a wallet
python3 polymarket_tracker.py --wallet 0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e --slug-group highest-temp

# Output machine-readable JSON for agents
python3 polymarket_tracker.py --wallet 0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e --json
```

### 3. Meta-Backtest & Copy-Trading Simulation

```bash
# Run multi-fold walk-forward copy portfolio simulation
python3 polymarket_tracker.py --meta-backtest
```

### 4. Official Leaderboard & Rankings

```bash
# Monthly leaderboard ranked by PnL
python3 polymarket_tracker.py --leaderboard --timeframe MONTH

# All-time leaderboard ranked by Volume ROI
python3 polymarket_tracker.py --leaderboard --timeframe ALL --sort roi
```
