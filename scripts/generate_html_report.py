import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime

sys.path.append('/home/user')
from polymarket_pnl_tracker import get_leaderboard, get_wallet_deep_dive

print("Fetching all timeframes...")
all_time = get_leaderboard(time_period="ALL", limit=50)
month_time = get_leaderboard(time_period="MONTH", limit=50)
week_time = get_leaderboard(time_period="WEEK", limit=50)
day_time = get_leaderboard(time_period="DAY", limit=50)

print("Fetching deep dive for top whale profiles...")
whales_to_profile = [
    ("Theo4", "0x56687bf447db6ffa42ffe2204a05edaa20f55839"),
    ("swisstony", "0x204f72f35326db932158cba6adff0b9a1da95e14"),
    ("Fredi9999", "0x1f2dd6d473f3e824cd2f8a89d9c69fb96f6ad0cf"),
    ("fishalive", "0xed64a7bf029040aa331abc87902434d815ef217d")
]

whale_profiles = []
for name, wallet in whales_to_profile:
    print(f"Deep diving {name} ({wallet[:10]}...)...")
    dive = get_wallet_deep_dive(wallet)
    dive["name"] = name
    whale_profiles.append(dive)

data_payload = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
    "all_time": all_time,
    "month_time": month_time,
    "week_time": week_time,
    "day_time": day_time,
    "whale_profiles": whale_profiles
}

html_template = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Polymarket Account PnL & % PnL Analytics Dashboard</title>
<style>
  :root {
    --bg-primary: #0b0f19;
    --bg-secondary: #111827;
    --bg-card: #1f2937;
    --border: #374151;
    --text-main: #f9fafb;
    --text-muted: #9ca3af;
    --accent-blue: #3b82f6;
    --accent-cyan: #06b6d4;
    --accent-green: #10b981;
    --accent-red: #ef4444;
    --accent-yellow: #f59e0b;
    --accent-purple: #8b5cf6;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
  body { background: var(--bg-primary); color: var(--text-main); line-height: 1.5; padding: 24px; }
  .container { max-width: 1300px; margin: 0 auto; }
  
  header { margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
  .badge { display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; background: rgba(59, 130, 246, 0.2); color: #60a5fa; margin-bottom: 8px; }
  h1 { font-size: 28px; font-weight: 800; background: linear-gradient(to right, #60a5fa, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  p.subtitle { color: var(--text-muted); font-size: 14px; margin-top: 4px; }

  /* Key Metrics Grid */
  .grid-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .card { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px; padding: 18px; position: relative; overflow: hidden; }
  .card::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--accent-blue); }
  .card.green::before { background: var(--accent-green); }
  .card.purple::before { background: var(--accent-purple); }
  .card.yellow::before { background: var(--accent-yellow); }
  .card-title { font-size: 13px; font-weight: 600; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; }
  .card-val { font-size: 24px; font-weight: 800; margin: 8px 0 4px; color: #fff; }
  .card-sub { font-size: 12px; color: var(--text-muted); }

  /* Archetype cards */
  .archetypes { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
  .arch-box { background: rgba(31, 41, 55, 0.5); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
  .arch-box h3 { font-size: 16px; font-weight: 700; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
  .arch-box ul { padding-left: 20px; font-size: 13px; color: var(--text-muted); }
  .arch-box li { margin-bottom: 4px; }
  .arch-box strong { color: var(--text-main); }

  /* Controls */
  .controls { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; }
  .tabs { display: flex; gap: 8px; background: var(--bg-secondary); padding: 4px; border-radius: 8px; border: 1px solid var(--border); }
  .tab-btn { background: transparent; border: none; color: var(--text-muted); padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
  .tab-btn:hover { color: #fff; }
  .tab-btn.active { background: var(--accent-blue); color: #fff; shadow: 0 2px 4px rgba(0,0,0,0.3); }

  .search-box { position: relative; }
  .search-box input { background: var(--bg-secondary); border: 1px solid var(--border); color: #fff; padding: 8px 14px 8px 32px; border-radius: 8px; font-size: 13px; width: 260px; outline: none; }
  .search-box input:focus { border-color: var(--accent-blue); }
  .search-box svg { position: absolute; left: 10px; top: 10px; width: 14px; height: 14px; fill: var(--text-muted); }

  /* Table */
  .table-container { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px; overflow-x: auto; margin-bottom: 30px; }
  table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
  th { background: #1a2234; padding: 12px 16px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; border-bottom: 1px solid var(--border); cursor: pointer; }
  th:hover { color: #fff; }
  td { padding: 12px 16px; border-bottom: 1px solid rgba(55, 65, 81, 0.5); }
  tr:hover td { background: rgba(59, 130, 246, 0.05); }

  .rank-badge { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; font-size: 12px; font-weight: 700; }
  .rank-1 { background: #fbbf24; color: #78350f; }
  .rank-2 { background: #94a3b8; color: #1e293b; }
  .rank-3 { background: #b45309; color: #fff; }
  .rank-norm { background: var(--border); color: var(--text-muted); }

  .trader-cell { display: flex; align-items: center; gap: 10px; }
  .trader-avatar { width: 28px; height: 28px; border-radius: 50%; background: #374151; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #60a5fa; font-size: 11px; overflow: hidden; }
  .trader-avatar img { width: 100%; height: 100%; object-fit: cover; }
  .trader-name { font-weight: 600; color: #fff; }
  .trader-wallet { font-family: monospace; font-size: 11px; color: var(--text-muted); }

  .pnl-pos { color: var(--accent-green); font-weight: 700; font-family: monospace; }
  .pnl-neg { color: var(--accent-red); font-weight: 700; font-family: monospace; }
  .roi-pill { display: inline-block; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-family: monospace; font-size: 12px; }
  .roi-high { background: rgba(16, 185, 129, 0.2); color: #34d399; }
  .roi-mid { background: rgba(6, 182, 212, 0.2); color: #38bdf8; }
  .roi-low { background: rgba(156, 163, 175, 0.2); color: #cbd5e1; }

  /* Deep Dive Section */
  .section-title { font-size: 20px; font-weight: 700; margin-bottom: 16px; color: #fff; display: flex; align-items: center; gap: 8px; }
  .whale-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .whale-card { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px; padding: 18px; }
  .whale-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
  .whale-header h4 { font-size: 16px; font-weight: 700; color: #fff; }
  .whale-stats-row { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; }
  .whale-stats-row span:first-child { color: var(--text-muted); }
  .whale-stats-row span:last-child { font-weight: 600; font-family: monospace; }

  .tag { font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 600; text-transform: uppercase; }
  .tag-whale { background: rgba(139, 92, 246, 0.25); color: #a78bfa; }
  .tag-mm { background: rgba(245, 158, 11, 0.25); color: #fbbf24; }
  
  footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border); text-align: center; font-size: 12px; color: var(--text-muted); }
</style>
</head>
<body>
<div class="container">
  <header>
    <span class="badge">Live On-Chain Polymarket Analytics</span>
    <h1>Polymarket Account PnL & % PnL Analytics</h1>
    <p class="subtitle">วิเคราะห์ผลกำไรขาดทุน (PnL in USD) และอัตราผลตอบแทน (% PnL / ROI) รายบัญชีบน Polymarket | ข้อมูลล่าสุด ณ วันที่ DATA_GENERATED_AT</p>
  </header>

  <!-- Key Aggregate Stats -->
  <div class="grid-stats">
    <div class="card green">
      <div class="card-title">Top All-Time Profit Leader</div>
      <div class="card-val">Theo4 ($22.05M)</div>
      <div class="card-sub">% PnL บน Volume: +51.27% | Capital ROI: +109.98%</div>
    </div>
    <div class="card yellow">
      <div class="card-title">Highest % PnL on Volume (Top 10)</div>
      <div class="card-val">fishalive (+67.75%)</div>
      <div class="card-sub">Net Profit: $8.99M จาก Volume เพียง $13.28M</div>
    </div>
    <div class="card purple">
      <div class="card-title">Top Volume Market Maker</div>
      <div class="card-val">swisstony ($18.42M PnL)</div>
      <div class="card-sub">Volume: $1.85 Billion | % PnL/Vol: 1.00% (High-Freq MM)</div>
    </div>
    <div class="card">
      <div class="card-title">30-Day Top Performer</div>
      <div class="card-val">e46m3 (+147.64%)</div>
      <div class="card-sub">30-Day Profit: $3.89M จาก Volume $2.63M</div>
    </div>
  </div>

  <!-- Understanding % PnL on Polymarket -->
  <div class="archetypes">
    <div class="arch-box">
      <h3 style="color: #60a5fa;">💡 1. % PnL on Volume (Turnover ROI %)</h3>
      <p style="font-size: 13px; margin-bottom: 8px;"><code>% PnL (Vol) = (Net PnL / Total Volume) × 100%</code></p>
      <ul>
        <li><strong>Directional Whales (30% - 70%+):</strong> ผู้เล่นที่เข้าเก็งผลลัพธ์แบบเจาะจง (เช่น เลือกข้างชนะเลือกตั้ง/กีฬา) มี % PnL สูงมาก เช่น <em>fishalive</em> (67.75%), <em>Theo4</em> (51.27%)</li>
        <li><strong>Market Makers (~0.5% - 2%):</strong> ผู้เล่นที่วางสภาพคล่องสองฝั่ง เน้นกิน Spread และ Rebate แม้ % บน Volume จะต่ำ (~1%) แต่ทำกำไรสุทธิมหาศาล ($18M+) จาก Volume หลักพันล้านดอลลาร์</li>
      </ul>
    </div>
    <div class="arch-box">
      <h3 style="color: #34d399;">📈 2. Capital Invested ROI % (ผลตอบแทนต่อเงินต้น)</h3>
      <p style="font-size: 13px; margin-bottom: 8px;"><code>Capital ROI % = (Realized PnL / Total Cost Invested) × 100%</code></p>
      <ul>
        <li><strong>Position Level:</strong> ใน Polymarket สัญญาซื้อขายคิดเป็นเหรียญ $0.00 – $1.00 หากซื้อ Yes ที่ $0.37 แล้วชนะ ($1.00) จะได้ % PnL ทันที <strong>+170.5%</strong></li>
        <li><strong>Account Level:</strong> เช่น <em>Theo4</em> ใช้เงินทุนซื้อสัญญารวม $20.05M ได้เงินกลับมารวม $42.10M คิดเป็นกำไรสุทธิ $22.05M (<strong>Capital ROI = +109.98%</strong>) ด้วย Win Rate สูงถึง 81.8%</li>
      </ul>
    </div>
  </div>

  <!-- Interactive Leaderboard Section -->
  <div class="section-title">
    <span>🏆 ตารางอันดับ Account และ % PnL</span>
  </div>

  <div class="controls">
    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab('ALL')">All-Time (ตลอดกาล)</button>
      <button class="tab-btn" onclick="switchTab('MONTH')">Past 30 Days (30 วัน)</button>
      <button class="tab-btn" onclick="switchTab('WEEK')">Past 7 Days (7 วัน)</button>
      <button class="tab-btn" onclick="switchTab('DAY')">24 Hours (24 ชม.)</button>
    </div>
    <div class="search-box">
      <svg viewBox="0 0 24 24"><path d="M21.71 20.29l-5.4-5.4A8.93 8.93 0 0 0 18 9a9 9 0 1 0-9 9 8.93 8.93 0 0 0 5.89-2.31l5.4 5.4a1 1 0 0 0 1.42-1.42zM4 9a5 5 0 1 1 5 5 5 5 0 0 1-5-5z"/></svg>
      <input type="text" id="searchInput" placeholder="ค้นหาชื่อหรือ Wallet Address..." oninput="filterTable()">
    </div>
  </div>

  <div class="table-container">
    <table id="leaderTable">
      <thead>
        <tr>
          <th onclick="sortTable(0)">Rank</th>
          <th onclick="sortTable(1)">Account / Wallet</th>
          <th onclick="sortTable(2)">Net PnL ($) ⬍</th>
          <th onclick="sortTable(3)">Volume ($) ⬍</th>
          <th onclick="sortTable(4)">% PnL on Volume (ROI) ⬍</th>
          <th>Archetype</th>
        </tr>
      </thead>
      <tbody id="tableBody">
        <!-- Rendered by JS -->
      </tbody>
    </table>
  </div>

  <!-- Deep Dive Showcase -->
  <div class="section-title">
    <span>🔍 เจาะลึกกระเป๋าเทรดเดอร์ชั้นนำ (Account Deep Dive)</span>
  </div>

  <div class="whale-grid" id="whaleProfilesContainer">
    <!-- Rendered by JS -->
  </div>

  <footer>
    <p>Polymarket PnL Analytics Engine • Data source: Official Polymarket Data API (data-api.polymarket.com)</p>
  </footer>
</div>

<script>
const DATA = DATA_JSON_PAYLOAD;

let currentTab = 'ALL';
let currentSortCol = 2;
let sortAsc = false;

function renderTable() {
  const dataset = DATA[currentTab.toLowerCase() + '_time'] || [];
  const query = document.getElementById('searchInput').value.toLowerCase().trim();
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = '';

  let filtered = dataset.filter(item => {
    return item.userName.toLowerCase().includes(query) || item.proxyWallet.toLowerCase().includes(query);
  });

  filtered.sort((a, b) => {
    let valA, valB;
    if (currentSortCol === 0) { valA = a.rank; valB = b.rank; }
    else if (currentSortCol === 1) { valA = a.userName; valB = b.userName; }
    else if (currentSortCol === 2) { valA = a.pnl; valB = b.pnl; }
    else if (currentSortCol === 3) { valA = a.vol; valB = b.vol; }
    else if (currentSortCol === 4) { valA = a.roi_vol_pct; valB = b.roi_vol_pct; }
    
    if (valA < valB) return sortAsc ? -1 : 1;
    if (valA > valB) return sortAsc ? 1 : -1;
    return 0;
  });

  filtered.forEach(item => {
    const tr = document.createElement('tr');
    
    let rankClass = 'rank-norm';
    if (item.rank === 1) rankClass = 'rank-1';
    else if (item.rank === 2) rankClass = 'rank-2';
    else if (item.rank === 3) rankClass = 'rank-3';

    let roiClass = 'roi-low';
    if (item.roi_vol_pct >= 40) roiClass = 'roi-high';
    else if (item.roi_vol_pct >= 10) roiClass = 'roi-mid';

    let archetype = '<span class="tag tag-whale">Directional Whale</span>';
    if (item.vol > 100000000 && item.roi_vol_pct < 5) {
      archetype = '<span class="tag tag-mm">Market Maker / Arb</span>';
    }

    const avatarInitial = item.userName.charAt(0).toUpperCase();
    const avatarContent = item.profileImage 
      ? `<img src="${item.profileImage}" alt="${item.userName}">`
      : avatarInitial;

    tr.innerHTML = `
      <td><span class="rank-badge ${rankClass}">#${item.rank}</span></td>
      <td>
        <div class="trader-cell">
          <div class="trader-avatar">${avatarContent}</div>
          <div>
            <div class="trader-name">${item.userName}</div>
            <div class="trader-wallet">${item.proxyWallet}</div>
          </div>
        </div>
      </td>
      <td class="${item.pnl >= 0 ? 'pnl-pos' : 'pnl-neg'}">${item.pnl >= 0 ? '+' : ''}$${item.pnl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
      <td style="font-family: monospace;">$${item.vol.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
      <td><span class="roi-pill ${roiClass}">${item.roi_vol_pct >= 0 ? '+' : ''}${item.roi_vol_pct.toFixed(2)}%</span></td>
      <td>${archetype}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderWhaleProfiles() {
  const container = document.getElementById('whaleProfilesContainer');
  container.innerHTML = '';

  DATA.whale_profiles.forEach(p => {
    const card = document.createElement('div');
    card.className = 'whale-card';
    
    let sampleTradesHtml = '';
    if (p.closed_positions && p.closed_positions.length > 0) {
      const topWins = p.closed_positions.slice(0, 3);
      sampleTradesHtml = '<div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--border); font-size: 11px;">' +
        '<div style="font-weight: 700; color: var(--text-muted); margin-bottom: 6px;">TOP RESOLVED TRADES:</div>' +
        topWins.map(t => `
          <div style="margin-bottom: 4px; color: #d1d5db;">
            • ${t.title.substring(0, 35)}... [<strong>${t.outcome}</strong>]: <span class="pnl-pos">+$${t.realizedPnl.toLocaleString('en-US', {maximumFractionDigits: 0})}</span> (+${t.roi_pct.toFixed(1)}%)
          </div>
        `).join('') +
        '</div>';
    }

    card.innerHTML = `
      <div class="whale-header">
        <div>
          <h4>${p.name}</h4>
          <span style="font-family: monospace; font-size: 11px; color: var(--text-muted);">${p.wallet.substring(0, 10)}...${p.wallet.substring(34)}</span>
        </div>
        <span class="tag ${p.capital_roi_pct > 30 ? 'tag-whale' : 'tag-mm'}">
          ${p.capital_roi_pct > 30 ? 'High Conviction' : 'Market Maker'}
        </span>
      </div>
      <div class="whale-stats-row">
        <span>Total Realized PnL:</span>
        <span class="pnl-pos">+$${p.total_realized_pnl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
      </div>
      <div class="whale-stats-row">
        <span>Capital Invested (Closed):</span>
        <span>$${p.total_invested_closed.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
      </div>
      <div class="whale-stats-row">
        <span>Capital ROI %:</span>
        <span class="roi-pill ${p.capital_roi_pct > 50 ? 'roi-high' : 'roi-mid'}">+${p.capital_roi_pct.toFixed(2)}%</span>
      </div>
      <div class="whale-stats-row">
        <span>Win Rate:</span>
        <span style="color: #60a5fa;">${p.win_rate_pct.toFixed(1)}% (${p.wins}W / ${p.losses}L)</span>
      </div>
      ${sampleTradesHtml}
    `;
    container.appendChild(card);
  });
}

function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.textContent.includes(tab) || (tab === 'ALL' && btn.textContent.includes('All-Time')));
  });
  renderTable();
}

function filterTable() {
  renderTable();
}

function sortTable(colIndex) {
  if (currentSortCol === colIndex) {
    sortAsc = !sortAsc;
  } else {
    currentSortCol = colIndex;
    sortAsc = false;
  }
  renderTable();
}

// Initial render
renderTable();
renderWhaleProfiles();
</script>
</body>
</html>
"""

html_final = html_template.replace("DATA_GENERATED_AT", data_payload["generated_at"])
html_final = html_final.replace("DATA_JSON_PAYLOAD", json.dumps(data_payload))

output_path = "/home/user/polymarket_pnl_report.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_final)

print(f"Report generated successfully at: {output_path}")
