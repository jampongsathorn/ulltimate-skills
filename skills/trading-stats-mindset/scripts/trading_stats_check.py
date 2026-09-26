#!/usr/bin/env python3
"""
trading_stats_check.py — Professor-level statistical mindset for time series trading strategy
Implements 5 mandatory checks + 4 priority behaviors
Stack: pandas, numpy, scipy, statsmodels

Usage:
  python3 trading_stats_check.py --input data.csv --pnl-col pnl --returns-col returns --output report/
  python3 trading_stats_check.py --input equity.csv --equity-col equity --output report/

If no file, generates synthetic example.
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd

def try_import():
    try:
        from scipy import stats
        from statsmodels.tsa.stattools import adfuller, kpss, grangercausalitytests
        from statsmodels.tsa.stattools import coint
        import statsmodels.stats.proportion as smp
        return True
    except ImportError as e:
        print(f"Missing deps: {e}. Install: pip install pandas numpy scipy statsmodels")
        return False

def load_data(path, pnl_col=None, returns_col=None, equity_col=None):
    if path is None:
        print("No input file — generating synthetic example with regime shift + fat tails")
        np.random.seed(42)
        n = 500
        # Regime 1: good
        r1 = np.random.normal(0.001, 0.01, 250)
        # Regime 2: bad + fat tail
        r2 = np.random.normal(-0.0005, 0.02, 250)
        r2[::20] = -0.1  # occasional large loss
        rets = pd.Series(np.concatenate([r1, r2]), name='returns')
        pnl = rets * 1000  # dummy pnl
        equity = (1+rets).cumprod()
        df = pd.DataFrame({'returns': rets, 'pnl': pnl, 'equity': equity})
        return df, 'pnl', 'returns', 'equity'
    
    df = pd.read_csv(path)
    if pnl_col and pnl_col not in df.columns:
        print(f"pnl-col {pnl_col} not in {df.columns.tolist()}, trying to infer")
        pnl_col = None
    if returns_col and returns_col not in df.columns:
        returns_col = None
    if equity_col and equity_col not in df.columns:
        equity_col = None
    return df, pnl_col, returns_col, equity_col

def check_distribution(series, name, report):
    from scipy import stats
    report.append(f"\n### 1. Distribution > Point Estimate — {name}\n")
    report.append(f"- Mean: {series.mean():.6f}, Median: {series.median():.6f}, Std: {series.std():.6f}")
    report.append(f"- Skew: {stats.skew(series):.3f} (|>1 = skewed), Kurtosis: {stats.kurtosis(series):.3f} (>5 = fat tail)")
    jb_stat, jb_p = stats.jarque_bera(series.dropna())
    report.append(f"- Jarque-Bera p-value: {jb_p:.4e} (<0.05 = non-normal)")
    # Professor heuristic
    if abs(stats.skew(series)) > 1:
        report.append(f"- **Heuristic FAIL:** Skew {stats.skew(series):.2f} >1, mean is misleading. Use median/expectancy.")
    if stats.kurtosis(series) > 5:
        report.append(f"- **Heuristic FAIL:** Kurtosis {stats.kurtosis(series):.2f} >5, fat tails present. Check tail risk.")
    # Win rate illusion if pnl
    if 'pnl' in name.lower():
        win_rate = (series > 0).mean()
        avg_win = series[series>0].mean() if (series>0).any() else 0
        avg_loss = series[series<0].mean() if (series<0).any() else 0
        expectancy = win_rate*avg_win + (1-win_rate)*avg_loss if not np.isnan(avg_win) and not np.isnan(avg_loss) else np.nan
        pf = series[series>0].sum() / abs(series[series<0].sum()) if (series<0).any() and series[series<0].sum()!=0 else np.nan
        report.append(f"- Win rate: {win_rate:.2%}, Avg win: {avg_win:.4f}, Avg loss: {avg_loss:.4f}")
        report.append(f"- Expectancy: {expectancy:.6f}, Profit Factor: {pf:.3f}")
        if win_rate > 0.6 and expectancy < 0:
            report.append(f"- **Trap:** High win rate {win_rate:.1%} but negative expectancy {expectancy:.4f} — classic win rate illusion.")

def check_stationarity(series, name, report):
    from statsmodels.tsa.stattools import adfuller, kpss
    report.append(f"\n### 2. Stationarity — {name}\n")
    try:
        adf_p = adfuller(series.dropna())[1]
        report.append(f"- ADF p-value: {adf_p:.4e} (<0.05 = stationary)")
    except Exception as e:
        adf_p = None
        report.append(f"- ADF failed: {e}")
    try:
        kpss_p = kpss(series.dropna(), nlags='auto')[1]
        report.append(f"- KPSS p-value: {kpss_p:.4e} (<0.05 = non-stationary)")
    except Exception as e:
        kpss_p = None
        report.append(f"- KPSS failed: {e}")
    if adf_p is not None and kpss_p is not None:
        if adf_p > 0.05 and kpss_p < 0.05:
            report.append(f"- **Heuristic FAIL:** Non-stationary (ADF p>0.05 and KPSS p<0.05). Past != future. Difference or split by regime.")
        elif adf_p < 0.05 and kpss_p > 0.05:
            report.append(f"- **PASS:** Likely stationary.")
        else:
            report.append(f"- **Mixed:** Check rolling stats.")
    # Rolling
    roll_mean = series.rolling(50).mean()
    roll_std = series.rolling(50).std()
    report.append(f"- Rolling mean last 5: {roll_mean.tail().tolist()[-3:]}")
    report.append(f"- Rolling std last 5: {roll_std.tail().tolist()[-3:]}")

def check_randomness(series, name, report):
    report.append(f"\n### 3. Randomness Test — {name} (Edge vs Noise)\n")
    # Sharpe-like
    if series.std() != 0:
        sharpe = series.mean() / series.std() * np.sqrt(252) if len(series)>1 else 0
        report.append(f"- Sharpe-like (mean/std*sqrt252): {sharpe:.3f}")
        # Permutation test
        np.random.seed(0)
        n_perm = 1000
        real_mean = series.mean()
        perm_means = [np.random.permutation(series).mean() for _ in range(n_perm)]
        p_val = np.mean(np.array(perm_means) >= real_mean) if real_mean>0 else np.mean(np.array(perm_means) <= real_mean)
        report.append(f"- Permutation test p-value (1000 shuffles): {p_val:.4f} (<0.05 = edge better than random)")
        if p_val > 0.05:
            report.append(f"- **Heuristic FAIL:** Can't beat random (p={p_val:.3f}). Edge may be luck.")
    else:
        report.append(f"- Std=0, cannot test randomness")

def check_sample_size(series, name, report):
    report.append(f"\n### 4. Sample Size & Power — {name}\n")
    n = len(series.dropna())
    report.append(f"- n = {n}")
    if n < 30:
        report.append(f"- **FAIL:** n<30 = anecdote. Professor rule: need 30+ per regime.")
    elif n < 100:
        report.append(f"- **Warning:** n=30-100 = suggestive, not robust.")
    elif n < 300:
        report.append(f"- **OK:** n=100-300 = start to trust.")
    else:
        report.append(f"- **Good:** n>=300 = robust.")
    # Win rate CI if pnl
    if 'pnl' in name.lower():
        wins = (series > 0).sum()
        try:
            import statsmodels.stats.proportion as smp
            ci_low, ci_upp = smp.proportion_confint(wins, n, alpha=0.05, method='wilson')
            report.append(f"- Win rate Wilson 95% CI: [{ci_low:.2%}, {ci_upp:.2%}]")
            if ci_upp - ci_low > 0.2:
                report.append(f"- **Wide CI:** Win rate CI width >20%, not precise.")
        except Exception as e:
            report.append(f"- Wilson CI failed: {e}")

def check_bias(report):
    report.append(f"\n### 5. Bias Checklist\n")
    checklist = [
        "[ ] Lookahead: Features shifted by 1? No future data?",
        "[ ] Survivorship: Includes delisted/dead assets?",
        "[ ] Transaction costs & slippage included?",
        "[ ] Out-of-sample exists? Walk-forward, not just in-sample?",
        "[ ] Number of trials reported? (p-hacking check)",
        "[ ] Data snooping: Same data used for idea and test?"
    ]
    for c in checklist:
        report.append(f"- {c}")
    report.append(f"- **Professor rule:** If any unchecked, backtest is inflated.")

def check_regime(equity_or_rets, report):
    report.append(f"\n### P1. Regime Shift Detection\n")
    series = equity_or_rets
    # Rolling Sharpe
    if len(series) >= 100:
        roll_sharpe = series.rolling(100).mean() / series.rolling(100).std()
        report.append(f"- Rolling Sharpe (100) last: {roll_sharpe.tail(3).tolist()}")
        # Simple regime: if rolling Sharpe changes sign
        if roll_sharpe.tail(100).min() < 0 and roll_sharpe.tail(100).max() > 0:
            report.append(f"- **Detected:** Rolling Sharpe crosses zero — possible regime shift.")
    # CUSUM simple
    try:
        import ruptures as rpt
        algo = rpt.Pelt(model="l2").fit(series.values)
        bkps = algo.predict(pen=10)
        report.append(f"- Ruptures breakpoints (pen=10): {bkps}")
        if len(bkps) > 2:
            report.append(f"- **Detected:** Multiple breakpoints — split by regime.")
    except ImportError:
        report.append(f"- ruptures not installed (pip install ruptures) — using simple mean shift")
        # Simple mean shift
        mid = len(series)//2
        m1, m2 = series.iloc[:mid].mean(), series.iloc[mid:].mean()
        report.append(f"- Mean first half: {m1:.6f}, second half: {m2:.6f}, diff: {m2-m1:.6f}")
    except Exception as e:
        report.append(f"- Regime detection failed: {e}")

def check_overfitting(report, df):
    report.append(f"\n### P2. Overfitting / Walk-Forward Degradation\n")
    report.append(f"- Need IS vs OOS Sharpe. If degradation >50%, overfit.")
    report.append(f"- Deflated Sharpe (Lopez de Prado) accounts for multiple trials.")
    report.append(f"- **Heuristic:** If you tried 100+ parameter combos, Sharpe needs >1.5 to be significant.")
    # Placeholder calc if we have two periods
    # User should provide IS/OOS, here we simulate
    report.append(f"- **Action:** Use TimeSeriesSplit, not KFold. Report PBO (Probability of Backtest Overfitting).")

def check_tail_risk(series, report):
    report.append(f"\n### P3. Tail Risk & Drawdown Clustering\n")
    var_1 = series.quantile(0.01)
    cvar_1 = series[series <= var_1].mean()
    report.append(f"- VaR 1%: {var_1:.6f}, CVaR 1%: {cvar_1:.6f}, Ratio CVaR/VaR: {cvar_1/var_1 if var_1!=0 else np.nan:.2f}")
    if abs(cvar_1) > abs(var_1)*1.5:
        report.append(f"- **Tail risk:** CVaR >> VaR, fat left tail.")
    # Drawdown if equity
    if len(series) > 10:
        # Assume series is returns, compute equity
        cum = (1+series.fillna(0)).cumprod()
        dd = cum / cum.cummax() - 1
        max_dd = dd.min()
        dd_duration = (dd < 0).astype(int).groupby((dd >= 0).astype(int).cumsum()).sum().max() if (dd<0).any() else 0
        report.append(f"- Max Drawdown: {max_dd:.2%}, Max DD duration: {dd_duration} bars")
        report.append(f"- DD clustering: {(dd < -0.05).sum()} bars < -5%")

def check_expectancy(pnl_series, report):
    report.append(f"\n### P4. Win Rate Illusion vs Expectancy\n")
    win_rate = (pnl_series > 0).mean()
    avg_win = pnl_series[pnl_series>0].mean() if (pnl_series>0).any() else 0
    avg_loss = pnl_series[pnl_series<0].mean() if (pnl_series<0).any() else 0
    expectancy = win_rate*avg_win + (1-win_rate)*avg_loss
    pf = pnl_series[pnl_series>0].sum() / abs(pnl_series[pnl_series<0].sum()) if (pnl_series<0).any() else np.nan
    report.append(f"- Win rate: {win_rate:.2%}, Avg win: {avg_win:.4f}, Avg loss: {avg_loss:.4f}")
    report.append(f"- Expectancy: {expectancy:.6f}, Profit Factor: {pf:.3f}")
    if expectancy <= 0:
        report.append(f"- **FAIL:** Expectancy <=0, strategy loses money after costs.")
    if win_rate > 0.7 and expectancy < 0:
        report.append(f"- **Classic trap:** High win rate but negative expectancy — cutting winners, letting losers run.")

def main():
    parser = argparse.ArgumentParser(description="Professor-level trading stats check")
    parser.add_argument('--input', type=str, default=None, help='CSV file')
    parser.add_argument('--pnl-col', type=str, default=None, help='PnL column name')
    parser.add_argument('--returns-col', type=str, default=None, help='Returns column name')
    parser.add_argument('--equity-col', type=str, default=None, help='Equity column name')
    parser.add_argument('--output', type=str, default='report', help='Output dir')
    args = parser.parse_args()

    if not try_import():
        sys.exit(1)

    df, pnl_col, returns_col, equity_col = load_data(args.input, args.pnl_col, args.returns_col, args.equity_col)
    os.makedirs(args.output, exist_ok=True)

    # Auto-detect columns if not provided
    if pnl_col is None:
        for cand in ['pnl','PnL','profit','p&l','trade_pnl']:
            if cand in df.columns:
                pnl_col = cand
                break
    if returns_col is None:
        for cand in ['returns','return','ret','r']:
            if cand in df.columns:
                returns_col = cand
                break
    if equity_col is None:
        for cand in ['equity','Equity','cum_pnl','capital']:
            if cand in df.columns:
                equity_col = cand
                break
    # Fallbacks
    if returns_col is None and pnl_col is not None:
        # Use pnl as returns proxy
        returns_col = pnl_col
    if pnl_col is None and returns_col is not None:
        pnl_col = returns_col

    report = []
    report.append("# Statistical Trading Analysis — Professor Report\n")
    report.append(f"Input: {args.input or 'synthetic example'}")
    report.append(f"Rows: {len(df)}, Columns: {df.columns.tolist()}")
    report.append(f"Detected: pnl_col={pnl_col}, returns_col={returns_col}, equity_col={equity_col}")

    # Run checks
    if returns_col and returns_col in df.columns:
        series = pd.to_numeric(df[returns_col], errors='coerce').dropna()
        check_distribution(series, f"Returns ({returns_col})", report)
        check_stationarity(series, f"Returns ({returns_col})", report)
        check_randomness(series, f"Returns ({returns_col})", report)
        check_sample_size(series, f"Returns ({returns_col})", report)
        check_regime(series, report)
        check_tail_risk(series, report)

    if pnl_col and pnl_col in df.columns:
        series = pd.to_numeric(df[pnl_col], errors='coerce').dropna()
        if pnl_col != returns_col:
            check_distribution(series, f"PnL ({pnl_col})", report)
            check_sample_size(series, f"PnL ({pnl_col})", report)
        check_expectancy(series, report)

    check_bias(report)
    check_overfitting(report, df)

    # Decision memo
    memo = []
    memo.append("# Decision Memo — Professor Verdict\n")
    memo.append("Based on 5 checks + 4 priorities:\n")
    memo.append("- If any FAIL in Distribution, Stationarity, Randomness, Sample Size, Bias → Do NOT deploy. Fix data/method first.")
    memo.append("- If Regime shift detected → Split by regime, report per-regime expectancy.")
    memo.append("- If Walk-forward degradation >50% → Overfitted. Reduce params or discard.")
    memo.append("- If Tail risk CVaR >> VaR or MaxDD >20% → Reduce size, add stop, or hedge tail.")
    memo.append("- If Expectancy <=0 or Win rate illusion → Fix risk/reward, not win rate.")
    memo.append("\n**Final Checklist (Professor Approval):**")
    for item in [
        "Distribution plotted, skew/kurtosis reported",
        "Stationarity ADF+KPSS + rolling",
        "Randomness permutation test p-value",
        "Sample size n per regime, Wilson CI",
        "Bias checklist all checked",
        "Regime shift checked",
        "Walk-forward degradation <30%",
        "Tail risk VaR/CVaR/MaxDD",
        "Expectancy >0, Profit Factor >1.2",
        "Data mixing validated, no leakage"
    ]:
        memo.append(f"- [ ] {item}")

    # Write files
    with open(os.path.join(args.output, "analysis-report.md"), "w") as f:
        f.write("\n".join(report))
    with open(os.path.join(args.output, "decision-memo.md"), "w") as f:
        f.write("\n".join(memo))

    print(f"Report written to {args.output}/analysis-report.md")
    print(f"Memo written to {args.output}/decision-memo.md")
    print("\n".join(report[-50:]))

if __name__ == "__main__":
    main()
