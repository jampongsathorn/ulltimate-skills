# รายงานการวิเคราะห์ PnL และ % PnL ราย Account บน Polymarket

## 📌 บทนำและภาพรวม
Polymarket เป็นตลาดพยากรณ์แบบกระจายศูนย์ (Decentralized Prediction Market) บนเครือข่าย Polygon ที่มีปริมาณการซื้อขายและสภาพคล่องสูงสุดในโลก โดยข้อมูล PnL (Profit and Loss) และ Volume ของผู้ใช้ทุกคนสามารถตรวจสอบได้แบบโปร่งใสผ่าน **Polymarket Public Data API** (`https://data-api.polymarket.com`)

---

## 📐 การทำความเข้าใจสูตรคำนวณ `% PnL` บน Polymarket

การคำนวณ `% PnL` ในตลาด Prediction Market มี 2 มิติสำคัญ:

### 1. % PnL ต่อ Volume (Turnover ROI / Volume Efficiency %)
$$\text{\% PnL on Volume} = \left(\frac{\text{Net PnL (USD)}}{\text{Total Trading Volume (USD)}}\right) \times 100\%$$
- **ความหมาย:** บ่งบอกว่าใน Volume การเทรดทุกๆ $100 ดอลลาร์ บัญชีนั้นสามารถแปลงเป็น "กำไรสุทธิ" ได้กี่ดอลลาร์
- **สถิติจริงจากตลาด:**
  - **Directional Whales (เทรดเดอร์เก็งทิศทาง):** จะมี `% PnL ต่อ Volume สูงมาก (30% - 70%+)` เพราะซื้อแล้วถือจนกระทั่งตลาด Resolve
  - **Market Makers / Arbitrageurs:** จะมี `% PnL ต่อ Volume อยู่ที่ ~0.5% - 2%` เพราะทำกำไรจาก Spread เล็กๆ แต่หมุนรอบ Volume หลายพันล้านดอลลาร์

### 2. % PnL ต่อเงินต้นลงทุนจริง (Capital Invested ROI %)
$$\text{Capital ROI \%} = \left(\frac{\text{Total Realized PnL (USD)}}{\text{Total Net Capital Cost Invested (USD)}}\right) \times 100\%$$
- **ความหมาย:** ผลตอบแทนที่แท้จริงเทียบกับเงินที่จ่ายซื้อสัญญา (Total Bought × Entry Avg Price)
- **ตัวอย่างการคำนวณระดับสัญญา (Position-level):**
  - ซื้อสัญญา "Yes" ที่ราคาเฉลี่ย $0.37 (37¢)
  - เมื่อผลลัพธ์ออกและชนะ สัญญาจะชำระราคาที่ $1.00 (100¢)
  - กำไร = $1.00 - $0.37 = +$0.63 ต่อสัญญา
  - **% PnL = $(0.63 / 0.37) \times 100\% = \mathbf{+170.27\%}$**

---

## 🏆 อันดับ Top Account ที่ทำ PnL และ % PnL สูงสุด (All-Time)

| อันดับ | ชื่อบัญชี (Account) | Wallet Address | Net PnL ($) | Total Volume ($) | % PnL on Vol | สไตล์การเทรด (Archetype) |
|:---:|:---|:---|:---:|:---:|:---:|:---|
| **#1** | **Theo4** | `0x56687bf447db...` | **+$22,053,933.75** | $43,013,258.52 | **+51.27%** | Directional Whale (French Whale) |
| **#2** | **swisstony** | `0x204f72f35326...` | **+$18,419,243.53** | $1,850,584,673.06 | **+1.00%** | Ultra High-Frequency Market Maker |
| **#3** | **Fredi9999** | `0x1f2dd6d473f3...` | **+$16,619,506.63** | $76,611,316.91 | **+21.69%** | Directional Whale |
| **#4** | **RN1** | `0x2005d16a84ce...` | **+$12,669,968.56** | $1,286,607,068.96 | **+0.98%** | Market Maker & Prop Desk |
| **#5** | **kch123** | `0x6a72f61820b2...` | **+$11,351,406.80** | $293,444,002.75 | **+3.87%** | Hybrid Liquidity Trader |
| **#6** | **mintblade** | `0x96cfcb0c3094...` | **+$9,110,689.71** | $17,759,922.23 | **+51.30%** | Directional Conviction |
| **#7** | **fishalive** | `0xed64a7bf0290...` | **+$8,998,446.90** | $13,281,460.37 | **+67.75%** | **Highest % on Volume in Top 10** |
| **#8** | **frostrizz** | `0xbc11a64ab34a...` | **+$8,801,837.99** | $23,091,318.16 | **+38.12%** | High Conviction Trader |
| **#9** | **Len9311238** | `0x78b9ac44a6d7...` | **+$8,709,972.99** | $16,402,744.76 | **+53.10%** | Directional Conviction |
| **#10** | **sparklingwater123** | `0x664ce9fb97ae...` | **+$8,350,187.80** | $19,001,698.93 | **+43.94%** | Directional Conviction |
| **#11** | **zxgngl** | `0xd235973291b2...` | **+$7,807,265.59** | $40,551,790.62 | **+19.25%** | Macro/Event Trader |
| **#12** | **RepTrump** | `0x863134d00841...` | **+$7,532,409.67** | $13,983,231.10 | **+53.87%** | Directional Whale |
| **#13** | **GRIMDRIP** | `0x3f87d51f27ba...` | **+$7,512,274.94** | $13,603,969.28 | **+55.22%** | Directional Conviction |

---

## 🔍 วิเคราะห์เจาะลึกพฤติกรรม (Trader Deep Dive)

### 1. `Theo4` (อันดับ 1 ตลอดกาล)
- **Net Realized PnL:** **+$22,053,933.75**
- **เงินต้นที่ใช้ซื้อสัญญาจริง (Capital Invested):** $20,052,204.64
- **Capital Invested ROI (%):** **+109.98%** (เงินต้นโตขึ้นกว่า 1 เท่าตัว)
- **Win Rate:** **81.8%** (ชนะ 18 สัญญา / แพ้ 4 สัญญา)
- **ไม้เด่น:**
  - *Donald Trump Popular Vote (Yes):* ลงทุน $4.87M ที่ราคา 0.369 -> กำไร **+$8,303,171.23 (+170.56% ROI)**
  - *Kamala Harris Popular Vote (No):* ลงทุน $3.62M ที่ราคา 0.374 -> กำไร **+$6,061,140.18 (+167.21% ROI)**

### 2. `fishalive` (อันดับ % PnL on Volume สูงสุดใน Top 10)
- **Net Realized PnL:** **+$8,998,446.90**
- **Trading Volume:** $13,281,460.37
- **% PnL on Volume:** **+67.75%** (ทุก $100 ที่เทรด กลายเป็นกำไรสุทธิ $67.75)
- **Capital Invested ROI:** **+122.05%**

### 3. `swisstony` (Top Market Maker)
- **Net PnL:** **+$18,419,243.53**
- **Trading Volume:** $1,850,584,673.06 ($1.85 พันล้านดอลลาร์)
- **% PnL on Volume:** **+1.00%**
- **สไตล์:** เน้นปูสภาพคล่องทั้งฝั่ง Bid/Ask และเก็บ Spread เล็กๆ + Maker Rebates ความเสี่ยงต่ำแต่กำไรสะสมมหาศาล

---

## 🛠️ วิธีการใช้งานสคริปต์ตรวจสอบใน Workspace

ในระบบได้ติดตั้งสคริปต์ `polymarket_pnl_tracker.py` และ Dashboard ไว้ให้คุณเรียกดูข้อมูลสดได้ตลอดเวลา:

```bash
# 1. ดู Leaderboard ตลอดกาล (All-Time) พร้อม % PnL
python3 polymarket_pnl_tracker.py --timeframe ALL --limit 25

# 2. ดูผลงานในรอบ 30 วันล่าสุด (Month)
python3 polymarket_pnl_tracker.py --timeframe MONTH --limit 20

# 3. ดูผลงานในรอบ 7 วันล่าสุด (Week)
python3 polymarket_pnl_tracker.py --timeframe WEEK --limit 20

# 4. เจาะลึก Wallet รายบุคคล (คำนวณ Capital ROI %, Win Rate, ไม้ที่เทรด)
python3 polymarket_pnl_tracker.py --wallet 0x56687bf447db6ffa42ffe2204a05edaa20f55839
```
