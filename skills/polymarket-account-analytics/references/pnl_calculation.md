# Polymarket PnL and % PnL Calculation Methodology

## Core Formulas

### 1. % PnL on Volume (Turnover Return %)
$$\text{ROI}_{\text{vol}} = \left(\frac{\text{Net PnL (\USD)}}{\text{Total Cumulative Volume (\USD)}}\right) \times 100\%$$
- **Use case:** Comparing macro trading efficiency between different trader archetypes.
- **Directional Whales:** Typically 30% - 70%+
- **Market Makers / HFT:** Typically 0.5% - 2.5%

### 2. Capital Invested ROI % (True Capital Return)
$$\text{ROI}_{\text{capital}} = \left(\frac{\text{Total Realized PnL (\USD)}}{\sum (\text{totalBought} \times \text{avgPrice})}\right) \times 100\%$$
- **Use case:** Measuring exact cash-on-cash return across resolved positions.

### 3. Position-Level % PnL
$$\text{ROI}_{\text{position}} = \left(\frac{\text{Payout} - \text{Entry Cost}}{\text{Entry Cost}}\right) \times 100\% = \left(\frac{1.00 - P_{\text{entry}}}{P_{\text{entry}}}\right) \times 100\%$$
- For winning outcomes resolving at $1.00.
- Example: Entry at $0.35 yields $\frac{1.00 - 0.35}{0.35} \times 100\% = \mathbf{+185.7\%}$.
