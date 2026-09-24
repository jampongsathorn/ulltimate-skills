---
name: trading-stats-mindset
description: Think like a 10-year statistics professor for time series trading strategy analysis. Use when analyzing trading strategy behavior, equity curves, P&L distributions, or any time series mix — forces Distribution > Point estimate, Stationarity check, Randomness test, Sample size & power, and Bias checklist. Detects regime shifts, overfitting/walk-forward degradation, tail risk/drawdown clustering, and win rate illusion. Stack generic Python pandas, numpy, scipy, statsmodels.
---

# Trading Stats Mindset — Professor Level

Make your agent analyze trading strategies like a professor with 10 years experience, not a junior calculating Sharpe.

## When to use

- Analyzing any time series trading strategy behavior (equity curve, returns, P&L, drawdown, indicators)
- Time series mix — price + volume + volatility + external regime, many frequencies
- You want to know if edge is real or luck, if past = future, if strategy is overfitted
- Before deploying, after drawdown, or when performance decays
- Agent needs to choose best statistical test strategically, not just run formulas

If you haven't gathered facts, call `agentic-code-workflow` Scan first, then `grilling` to map what you are trying to prove.

## Core Professor Mindset — 5 Mandatory Checks

Every analysis must pass these 5. Each has Theory / Heuristic / Trap.

### 1. Distribution > Point Estimate (Don't trust mean without variance/skew)

**Theory:** Mean hides risk. Returns are fat-tailed, skewed. CLT fails with dependence.
**Heuristic:** Professor rule — Always plot distribution before reporting mean. If skew |skew|>1 or kurtosis>5, mean is lying. Use median, trimmed mean, or expectancy.
**Trap:** Student reports "Avg win $100" but hides 1 loss of $10k. Always show full P&L distribution.
**Tests:**
```python
import pandas as pd
from scipy import stats
rets.plot.hist(bins=50); rets.plot.kde()
stats.skew(rets), stats.kurtosis(rets)
# Fat tail test
stats.jarque_bera(rets)
```

### 2. Stationarity Check (Is past = future?)

**Theory:** Most stats assume stationarity. Price is not stationary, returns might be, volatility is not.
**Heuristic:** If ADF p>0.05 and KPSS p<0.05 → non-stationary → difference or regime split. Never backtest on non-stationary without handling.
**Trap:** Backtesting on price levels, or using rolling mean on trending series.
**Tests:**
```python
from statsmodels.tsa.stattools import adfuller, kpss
adfuller(returns)[1]  # p-value <0.05 = stationary
kpss(returns)[1]
# Rolling stats
returns.rolling(100).mean().plot(); returns.rolling(100).std().plot()
```

### 3. Randomness Test (Is edge vs noise?)

**Theory:** Any equity curve can be luck. Need to beat random.
**Heuristic:** If you can't beat 1000 shuffled versions of your trades, you have no edge. Professor asks "Would random do same?"
**Trap:** High Sharpe with 20 trades = luck. Always run permutation test.
**Tests:**
```python
import numpy as np
# Permutation test
real_sharpe = sharpe(pnl)
shuffled = [sharpe(np.random.permutation(pnl)) for _ in range(1000)]
p_val = np.mean(np.array(shuffled) >= real_sharpe)
# Bootstrap confidence interval
from scipy.stats import bootstrap
bootstrap((pnl,), np.mean, confidence_level=0.95)
```

### 4. Sample Size & Power (Do you have enough data?)

**Theory:** Small n = low power = false confidence. Need 30+ per regime minimum.
**Heuristic:** Professor rule — <30 trades = anecdote, 30-100 = suggestive, 100+ = start to trust, 300+ = robust. For Sharpe, need 2+ years or 1+ market cycles.
**Trap:** "Win rate 80%!" with n=10. Use Wilson interval.
**Tests:**
```python
import statsmodels.stats.proportion as prop
prop.proportion_confint(wins, nobs, alpha=0.05, method='wilson')
# Power analysis
from statsmodels.stats.power import TTestIndPower
TTestIndPower().solve_power(effect_size=0.2, alpha=0.05, power=0.8)
```

### 5. Bias Checklist (Lookahead, Survivorship, Overfitting)

**Theory:** Bias inflates performance. Lookahead = using future, survivorship = only winners, overfitting = fitting noise.
**Heuristic:** Professor checklist before trusting any backtest:
- [ ] No future data in features (shift by 1)
- [ ] Includes delisted / dead coins/stocks?
- [ ] Walk-forward, not just in-sample
- [ ] Out-of-sample degrades <30%?
- [ ] Transaction costs, slippage included?
**Tests:**
```python
# Lookahead check
df['feature'].shift(1).corr(df['future_return'])  # should not use unshifted
# Walk-forward
from sklearn.model_selection import TimeSeriesSplit
TimeSeriesSplit(n_splits=5)
```

## Priority Behaviors — What Professor Looks For First

### P1. Regime Shift Detection

**Observation:** Equity curve flat then trending, or volatility clustering.
**Question:** Did market regime change?
**Test:** CUSUM, HMM, rolling Sharpe, Chow test.
```python
# Rolling Sharpe
rets.rolling(100).mean() / rets.rolling(100).std() * np.sqrt(252)
# CUSUM
import ruptures as rpt
rpt.Pelt(model="l2").fit(equity_curve.values).predict(pen=10)
```
**Decision:** If regime shift detected, split analysis by regime, don't average.

### P2. Overfitting / Walk-Forward Degradation

**Observation:** In-sample great, live bad.
**Question:** Is strategy overfitted?
**Test:** Walk-forward, Deflated Sharpe (Lopez de Prado), PBO.
```python
# Walk-forward degradation
is_sharpe = 2.5; oos_sharpe = 1.2
degradation = (is_sharpe - oos_sharpe) / is_sharpe
# >0.5 = likely overfit
```
**Decision:** If degradation >50%, reduce parameters, add regularization, or discard.

### P3. Tail Risk & Drawdown Clustering

**Observation:** Small losses frequent, large loss rare but catastrophic.
**Question:** Are tails heavier than normal? Do drawdowns cluster?
**Test:** VaR, CVaR, max drawdown distribution, drawdown duration.
```python
rets.quantile(0.01)  # VaR 1%
rets[rets <= rets.quantile(0.01)].mean()  # CVaR
# Drawdown
cum = (1+rets).cumprod()
dd = cum / cum.cummax() - 1
dd.min(), (dd < -0.1).sum()  # max DD and frequency
```
**Decision:** If CVaR >> VaR, you have tail risk. Size position by CVaR, not Sharpe.

### P4. Win Rate Illusion vs Expectancy

**Observation:** High win rate but negative P&L, or vice versa.
**Question:** Is expectancy positive?
**Test:** Expectancy = win_rate * avg_win + loss_rate * avg_loss.
```python
win_rate = (pnl > 0).mean()
avg_win = pnl[pnl>0].mean()
avg_loss = pnl[pnl<0].mean()
expectancy = win_rate*avg_win + (1-win_rate)*avg_loss
# Profit factor
pnl[pnl>0].sum() / abs(pnl[pnl<0].sum())
```
**Decision:** Never trade on win rate alone. Need expectancy >0 after costs.

## Decision Tree — Professor Strategic Use

See `references/professor-decision-tree.md` for full tree.

```
Observation → Statistical Question → Test → Interpretation → Trading Decision

Example 1:
Obs: Sharpe 3.0 with 25 trades
Q: Sample size enough? Random?
Test: Permutation test + Wilson CI
Interpret: p=0.2, CI wide
Decision: Not enough evidence, need 100+ trades

Example 2:
Obs: Equity curve trending then flat 6 months
Q: Regime shift?
Test: Rolling Sharpe + CUSUM + HMM
Interpret: Regime changed after Fed hike
Decision: Re-train per regime, reduce size in new regime

Example 3:
Obs: Win rate 75% but P&L negative
Q: Expectancy?
Test: Avg win vs avg loss
Interpret: Avg loss 5x avg win
Decision: Fix risk/reward, not win rate
```

## Data Mixing Strategy — Time Series Can Be Many

1. **Align:** `pd.merge_asof` or resample to common freq, check timezone
2. **Stationarity:** Difference non-stationary before mixing. Don't mix price (non-stationary) with returns (stationary) directly.
3. **Correlation vs Causation:** Correlation != edge. Use Granger, cointegration.
```python
from statsmodels.tsa.stattools import grangercausalitytests, coint
grangercausalitytests(df[['x','y']], maxlag=5)
coint(df['price1'], df['price2'])
```
4. **Leakage:** If feature uses future (e.g., close price to predict same bar close), shift by 1. Check feature importance vs random.
5. **Frequency:** Don't mix tick noise with daily signal without aggregation.

## Workflow — How Agent Should Use This Skill

### 1. Scan
```bash
ls -la *.csv *.parquet 2>/dev/null | head -20
head -5 data.csv
python3 -c "import pandas as pd; df=pd.read_csv('data.csv'); print(df.describe())"
```

### 2. Run Professor Script
```bash
python3 skills/trading-stats-mindset/scripts/trading_stats_check.py --input data.csv --pnl-col pnl --returns-col returns --output report/
```

### 3. Read Report + Decision Memo
```
read_file report/analysis-report.md
read_file report/decision-memo.md
```

### 4. Act on Decision

## Scripts

- `scripts/trading_stats_check.py` — Runs all 5 checks + 4 priorities, outputs `report/analysis-report.md` + `report/decision-memo.md` + plots
- See `references/` for decision tree and checklists

## Closing Checklist (Professor Would Approve)

- [ ] Distribution plotted, not just mean (hist + KDE + skew/kurtosis)
- [ ] Stationarity tested (ADF + KPSS + rolling mean/std plot)
- [ ] Randomness tested (permutation test / bootstrap CI, p-value reported)
- [ ] Sample size & power checked (n per regime, Wilson CI for win rate, 30+ rule)
- [ ] Bias checklist passed (lookahead shift, survivorship, costs, walk-forward)
- [ ] Regime shift checked (rolling Sharpe + CUSUM/HMM)
- [ ] Walk-forward degradation calculated (<30% ok, >50% overfit)
- [ ] Tail risk quantified (VaR, CVaR, max DD, DD clustering)
- [ ] Expectancy calculated (not win rate alone, profit factor)
- [ ] Data mixing validated (aligned, stationarity handled, no leakage)
- [ ] Report has decision memo: "Edge real? Deploy? What to fix?"
- [ ] No p-hacking (report number of tests tried)
```

This is the skill. Now create the script and references.
