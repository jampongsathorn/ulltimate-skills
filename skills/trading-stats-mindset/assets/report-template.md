# Statistical Trading Analysis Report — Template

**Strategy:** {{strategy_name}}
**Period:** {{start}} to {{end}}
**Data:** {{data_description}}
**Trades:** {{n_trades}}

## 1. Distribution > Point Estimate

- Mean: {{mean}}, Median: {{median}}, Std: {{std}}
- Skew: {{skew}}, Kurtosis: {{kurtosis}}
- Jarque-Bera p: {{jb_p}}
- P&L Distribution: [plot hist + KDE]
- Verdict: {{distribution_verdict}}

## 2. Stationarity

- ADF p: {{adf_p}}, KPSS p: {{kpss_p}}
- Rolling mean/std plot: [plot]
- Verdict: {{stationarity_verdict}}

## 3. Randomness (Edge vs Noise)

- Real Sharpe: {{sharpe}}
- Permutation p (1000 shuffles): {{perm_p}}
- Bootstrap 95% CI: {{bootstrap_ci}}
- Verdict: {{randomness_verdict}}

## 4. Sample Size & Power

- n = {{n}}, per regime n = {{n_per_regime}}
- Win rate Wilson CI: {{wilson_ci}}
- Power analysis: {{power}}
- Verdict: {{sample_verdict}}

## 5. Bias Checklist

- [ ] Lookahead shift by 1?
- [ ] Survivorship includes delisted?
- [ ] Costs & slippage included?
- [ ] Walk-forward exists?
- [ ] Trials reported?
- Verdict: {{bias_verdict}}

## P1. Regime Shift

- Rolling Sharpe plot: [plot]
- Breakpoints: {{breakpoints}}
- Per-regime expectancy: {{per_regime}}
- Verdict: {{regime_verdict}}

## P2. Overfitting / Walk-Forward

- IS Sharpe: {{is_sharpe}}, OOS Sharpe: {{oos_sharpe}}, Degradation: {{degradation}}
- Deflated Sharpe: {{deflated_sharpe}}
- Verdict: {{overfit_verdict}}

## P3. Tail Risk & Drawdown

- VaR 1%: {{var}}, CVaR 1%: {{cvar}}, Max DD: {{max_dd}}, DD duration: {{dd_duration}}
- Plot: [equity + drawdown]
- Verdict: {{tail_verdict}}

## P4. Win Rate Illusion vs Expectancy

- Win rate: {{win_rate}}, Avg win: {{avg_win}}, Avg loss: {{avg_loss}}
- Expectancy: {{expectancy}}, Profit Factor: {{pf}}
- Verdict: {{expectancy_verdict}}

## Decision Memo

**Edge real?** {{edge_real}}
**Deploy?** {{deploy_decision}} (No / Paper / Small size / Full)
**What to fix?** {{fix_list}}
**Next test?** {{next_test}}

## Closing Checklist (Professor Approval)

- [ ] Distribution plotted
- [ ] Stationarity tested
- [ ] Randomness p-value
- [ ] Sample size checked
- [ ] Bias checklist passed
- [ ] Regime shift checked
- [ ] Walk-forward <30%
- [ ] Tail risk VaR/CVaR/MaxDD
- [ ] Expectancy >0, PF>1.2
- [ ] Data mixing validated
