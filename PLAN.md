# PLAN.md — Task ย่อยที่โยงกลับหา North Star เสมอ

North Star: ผู้ใช้สามารถดูและค้นหารายชื่อ Account บน Polymarket พร้อมคำนวณและแสดงผลกำไร/ขาดทุน (PnL เป็น USD) และอัตราผลตอบแทน (% PnL / ROI) ของแต่ละ Account ได้อย่างถูกต้อง ชัดเจน และตรวจสอบได้

| # | Task ย่อย | เกี่ยวกับ North Star ยังไง | สถานะ | หมายเหตุ |
|---|---|---|---|---|
| 1 | สแกนและทดสอบ Polymarket Public API endpoints สำหรับ Leaderboard, User PnL, Volume, Activity | หาแหล่งข้อมูลจริง (Ground Truth) ของ Account, PnL, Volume | ✅ | ดึงจาก `data-api.polymarket.com` สำเร็จ |
| 2 | วิเคราะห์และกำหนดนิยามสูตรคำนวณ `% PnL` (เช่น PnL/Volume, PnL/Total Cost, ROI) | เพื่อให้ตัวเลข % PnL มีความหมายทางสถิติและการลงทุนที่ถูกต้อง | ✅ | กำหนดทั้ง Volume ROI % และ Capital Invested ROI % |
| 3 | สร้าง Script/Tool ดึงข้อมูล Leaderboard & Specific Account พร้อมคำนวณ % PnL | เครื่องมือทำงานหลักในการดึงและคำนวณข้อมูล | ✅ | สร้าง `polymarket_pnl_tracker.py` |
| 4 | ทดสอบรันและสอบทานกับข้อมูลจริง (Ground truth verification) | ตรวจสอบความถูกต้องของ PnL และ % PnL | ✅ | ตรวจสอบกับ Wallet จริง (`Theo4`, `fishalive`, `swisstony`) |
| 5 | สร้าง Report / Interactive Table สรุปผล Account ชั้นนำพร้อม % PnL | ส่งมอบผลลัพธ์ให้ผู้ใช้อ่านและนำไปใช้งานได้ทันที | ✅ | สร้าง `polymarket_pnl_report.html` & `POLYMARKET_PNL_REPORT.md` |
