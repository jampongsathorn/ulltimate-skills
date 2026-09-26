# 🦅 Polymarket Alpha Tracker & Follow Bot

[![Polymarket Follow Bot Cron Check](https://github.com/jampongsathorn/polymarket-alpha-tracker/actions/workflows/polymarket-follow-bot.yml/badge.svg)](https://github.com/jampongsathorn/polymarket-alpha-tracker/actions/workflows/polymarket-follow-bot.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> **All-in-One Polymarket Quantitative Analytics Engine, Multi-Trader Screener & Real-Time Discord Follow Bot.**
> Fully reconciled with on-chain ground-truth data, eliminating sampling truncation artifacts and false alphas.

---

## 🌟 Key Features

1. **Multi-Trader Quantitative Screening (`--screen-top`)**:
   - Filter by market family/slug-group (e.g. `highest-temp`, `lowest-temp`, `precipitation-weather`, `btc-price`, `fed-rates`, `us-politics`, etc.).
   - Exclude specific groups (e.g. `--exclude-group sports-soccer,pop-culture`).
   - True Settlement Accounting & Effective Event Count ($N_{\text{eff}}$) calculation.
   - Rigorous 3-Tier Metric Hierarchy: $\text{Signal Edge} \longrightarrow \text{Capital Edge} \longrightarrow N_{\text{eff}} \longrightarrow \text{Temporal Persistence}$.

2. **Real-Time Discord Follow Bot (`--follow-bot`)**:
   - Ultra-clean, non-cluttered signal cards sent to Discord Webhooks.
   - **Market Group Filtering**: Target specific categories (e.g. `--include-group weather`) or exclude noise (`--exclude-group sports-soccer`).
   - **Minimum Price Filtering**: Filter out low-probability lottery bets (e.g. `--min-price 0.10`).
   - Direct clickable Polymarket trade URLs and profile links.

3. **Multi-Fold Rolling Walk-Forward Validation**:
   - Sequential chronological out-of-sample testing to prevent lookahead and hindsight bias.

4. **Zero-Dependency Architecture**:
   - Built exclusively using Python 3 standard libraries (`urllib`, `json`, `sqlite3`, `datetime`).
   - Runs out-of-the-box on GitHub Actions, VPS, Raspberry Pi, Docker, or local machine.

---

## ⚡ Quick Start

### 1. Run Quantitative Screener
```bash
# Screen Top 10 Weather traders in 2026
python3 polymarket_tracker.py --screen-top --slug-group weather --start-date 2026-01-01

# Screen Top traders excluding sports
python3 polymarket_tracker.py --screen-top --exclude-group sports-soccer
```

### 2. Analyze Single Wallet
```bash
python3 polymarket_tracker.py --wallet 0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e
```

### 3. Run Real-Time Follow Bot
```bash
# Follow Weather Master for Weather markets only
python3 polymarket_tracker.py \
  --follow-bot \
  --target 0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e \
  --include-group weather \
  --poll-interval 15
```

---

## 🤖 24/7 Automated Hosting via GitHub Actions

This repository includes an automated GitHub Actions cron workflow (`.github/workflows/polymarket-follow-bot.yml`) that runs every 5 minutes completely for free.

### Setup:
1. Go to your repo **Settings** > **Secrets and variables** > **Actions**.
2. Add a repository secret named `DISCORD_WEBHOOK_URL` with your Discord webhook URL.
3. Head to the **Actions** tab and enable the workflow. It will automatically check and alert new trades!

---

## 📊 2026 YTD Top Weather Traders (1 Jan 2026 - 26 Sep 2026)

| Rank | Trader | Wallet | Weather PnL | ROI % | Win Rate | $N_{\text{eff}}$ |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| **#1** | **Weather Master** | [`0x005ed9...6d8e`](https://polymarket.com/0x005ed998fcb786679eb8bfd0d20c15c0903d6d8e) | **+$125,110.91** | +874.8% | 99.0% | 370 |
| **#2** | **Weather Sniper** | [`0x365323...ef74`](https://polymarket.com/0x3653235d75a0d5969c42f7514d4df8ea5f8cef74) | **+$90,677.80** | +970.7% | 95.5% | 263 |
| **#3** | **0x1F85EB9C4** | [`0x1f85eb...7b02`](https://polymarket.com/0x1f85eb9c455c5bdef5d96c2739076678c7157b02) | **+$89,641.91** | +1287.3% | 100.0% | 202 |
| **#4** | **0x8B8b9c565C** | [`0x8b8b9c...2512`](https://polymarket.com/0x8b8b9c565c8dca43cfb767f0f2c20b2b323d2512) | **+$81,000.03** | +1333.6% | 93.9% | 224 |
| **#5** | **Lucerys** | [`0x1387d1...55f8`](https://polymarket.com/0x1387d145aaf01f6e33b66525dda6e1f51f6955f8) | **+$79,526.53** | +114.8% | 91.6% | 581 |

---

## 📜 License
MIT © [jampongsathorn](https://github.com/jampongsathorn)
