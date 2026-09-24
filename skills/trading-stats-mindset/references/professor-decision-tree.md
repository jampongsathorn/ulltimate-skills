# Professor Decision Tree — When to Use Which Statistical Test

```
Observation → Statistical Question → Test → Interpretation → Trading Decision
```

## Tree

### 1. High Sharpe, Low n
**Obs:** Sharpe >2 but n<30 trades
**Q:** Sample size enough? Luck?
**Test:** Permutation test (shuffle pnl 1000x), Wilson CI for win rate, Power analysis
**Interpret:** If p>0.05 or CI wide → not significant
**Decision:** Need 100+ trades or 1+ year. Don't deploy.

### 2. Equity Curve Trending Then Flat
**Obs:** Good 6 months, flat 6 months
**Q:** Regime shift?
**Test:** Rolling Sharpe 100-bar, CUSUM / ruptures, HMM 2-state, Chow test
**Interpret:** If breakpoints detected or rolling Sharpe crosses zero → regime changed
**Decision:** Split by regime, report per-regime expectancy. Reduce size in bad regime. Don't average.

### 3. Win Rate High, P&L Negative
**Obs:** Win rate 75% but losing money
**Q:** Expectancy?
**Test:** Avg win vs avg loss, Expectancy = win*avg_win + loss*avg_loss, Profit Factor
**Interpret:** If avg loss 5x avg win → cutting winners, letting losers run
**Decision:** Fix risk/reward, not win rate. Need expectancy >0.

### 4. Small Losses Frequent, Large Loss Rare
**Obs:** Looks stable until one big loss
**Q:** Tail risk?
**Test:** VaR 1%, CVaR 1%, Skew, Kurtosis, Max DD, DD duration
**Interpret:** If CVaR >> VaR or kurtosis >5 → fat tail
**Decision:** Size by CVaR not Sharpe. Add stop or hedge.

### 5. In-Sample Great, Out-of-Sample Bad
**Obs:** IS Sharpe 2.5, OOS 0.8
**Q:** Overfitting?
**Test:** Walk-forward degradation = (IS-OOS)/IS, Deflated Sharpe (Lopez de Prado), PBO
**Interpret:** Degradation >50% = overfit. If tried 100+ params, need Sharpe >1.5 to be significant.
**Decision:** Reduce parameters, add regularization, or discard. Use TimeSeriesSplit not KFold.

### 6. Strategy Uses Multiple Time Series
**Obs:** Mixing price + volume + volatility
**Q:** Mixing valid? Leakage?
**Test:** Align timestamps, ADF/KPSS per series, Correlation vs Granger vs Cointegration, Feature importance vs random, Shift test
**Interpret:** If mixing non-stationary with stationary without differencing → spurious. If feature uses future bar → leakage.
**Decision:** Difference non-stationary, use merge_asof, shift features by 1, check Granger not just correlation.

### 7. Returns Look Normal But Strategy Fails in Crisis
**Obs:** Backtest ok, fails in 2020 crash, 2022 bear
**Q:** Non-stationarity / tail dependence?
**Test:** Rolling mean/std, Drawdown clustering, Correlation breakdown in stress
**Interpret:** If rolling std spikes or correlation → 1 in crisis → strategy not robust
**Decision:** Stress test, include crisis period, size for worst regime.

### 8. Many Indicators, One Works
**Obs:** Tested 50 indicators, 1 has p<0.05
**Q:** p-hacking?
**Test:** Bonferroni correction, Deflated Sharpe, Number of trials reported
**Interpret:** With 50 trials, p<0.05 expected by chance. Need p<0.001 or Deflated Sharpe.
**Decision:** Report all trials, not just winner. Use hold-out.

## Professor Heuristics (10-year rules)

- **30 trades rule:** <30 = anecdote, 30-100 = suggestive, 100+ = start to trust, 300+ = robust
- **1 market cycle:** Need at least 1 full bull+bear cycle, not just bull
- **Skew >1 or Kurtosis >5:** Mean lies, use median/expectancy
- **ADF p>0.05 + KPSS p<0.05:** Non-stationary, past != future
- **Permutation p>0.05:** Can't beat random, no edge
- **Degradation >50%:** Overfit
- **CVaR / VaR >1.5:** Tail risk
- **Profit Factor <1.2:** Not enough edge after costs
- **Wilson CI width >20%:** Win rate not precise

## Traps Students Make

1. Reporting mean without distribution
2. Using t-test on non-stationary returns
3. Backtesting on price levels not returns
4. No shift → lookahead bias
5. KFold on time series → leakage
6. Trusting win rate alone
7. Ignoring transaction costs
8. Not reporting number of trials (p-hacking)
9. Mixing frequencies without alignment
10. Using Sharpe without checking skew

## References (Professor Canon)

- Lo (2002) — Statistics of Sharpe Ratio
- Taleb — Fat tails, fooled by randomness
- Lopez de Prado — Deflated Sharpe, PBO, backtest overfitting
- Hamilton — Regime switching, time series analysis
- Hyndman — Forecasting principles, stationarity
