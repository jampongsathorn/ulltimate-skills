# Polymarket Data API Endpoints Reference

Base URL: `https://data-api.polymarket.com` (Fully public, no authentication required for reads)

## 1. Leaderboard API
- **Endpoint:** `GET /v1/leaderboard`
- **Parameters:**
  - `timePeriod`: `ALL` (lifetime), `MONTH` (30 days), `WEEK` (7 days), `DAY` (24 hours)
  - `orderBy`: `PNL` (default), `VOL`
  - `category`: `OVERALL`, `POLITICS`, `SPORTS`, `CRYPTO`, `FINANCE`, `CULTURE`, `TECH`
  - `limit`: `1` - `50`
  - `offset`: `0` - `1000`
- **Output fields:** `rank`, `proxyWallet`, `userName`, `xUsername`, `vol`, `pnl`, `profileImage`

## 2. Positions API
- **Endpoint:** `GET /positions`
- **Parameters:**
  - `user`: Proxy wallet address (`0x...`)
  - `limit`: `1` - `500`
  - `sizeThreshold`: minimum tokens (default: `1.0`)
- **Output fields:** `conditionId`, `asset`, `size`, `avgPrice`, `curPrice`, `initialValue`, `currentValue`, `cashPnl`, `percentPnl`, `title`, `outcome`

## 3. Closed Positions API
- **Endpoint:** `GET /closed-positions`
- **Parameters:**
  - `user`: Proxy wallet address (`0x...`)
  - `limit`: `1` - `50`
- **Output fields:** `conditionId`, `asset`, `totalBought`, `avgPrice`, `curPrice`, `realizedPnl`, `title`, `outcome`, `endDate`, `timestamp`

## 4. Portfolio Value API
- **Endpoint:** `GET /value`
- **Parameters:**
  - `user`: Proxy wallet address (`0x...`)
- **Output fields:** Array with `user` and `value` (USD total of open positions)
