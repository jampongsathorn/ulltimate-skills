# GOAL.md — Goal Brief

## 1. North Star (ผลลัพธ์สุดท้าย ไม่ใช่ activity)
- ผู้ใช้สามารถดูและค้นหารายชื่อ Account บน Polymarket พร้อมคำนวณและแสดงผลกำไร/ขาดทุน (PnL เป็น USD) และอัตราผลตอบแทน (% PnL / ROI) ของแต่ละ Account ได้อย่างถูกต้อง ชัดเจน และตรวจสอบได้ พร้อมเครื่องมือ/สคริปต์ที่ดึงข้อมูลจริงจาก Polymarket API

## 2. ทำไมงานนี้ถึงสำคัญ (บริบท/แรงจูงใจ)
- เพื่อทำการวิเคราะห์ Trader ประสิทธิภาพสูง (Top Performers / Smart Money) บน Polymarket เพื่อดูว่าแต่ละ Account ทำกำไรได้กี่ USD และกี่ % PnL (ROI) เพื่อใช้ในการศึกษาแนวทางการเทรดหรือติดตามกระเป๋า (Wallet tracking)

## 3. Definition of Done (เกณฑ์ผ่าน/ไม่ผ่าน ตรวจสอบได้จริง)
- [ ] 1. ศึกษาและทดสอบ Polymarket API (Data API, Leaderboard API, Profile/Activity API) สำเร็จ สามารถดึงข้อมูล Account, PnL (USD), Volume, และ Cash Flow/Investment ได้จริง
- [ ] 2. กำหนดและแจกแจงสูตรคำนวณ `% PnL` อย่างเป็นระบบ (เช่น `PnL / Volume`, `PnL / Total Investment`, หรือ Polymarket native ROI)
- [ ] 3. สร้างสคริปต์และเครื่องมือ (CLI tool / Python pipeline) ดึงข้อมูลบัญชี (Top Leaderboard หรือระบุเฉพาะ Account/Wallet address) และคำนวณ PnL ($) + % PnL ออกมาเป็นตาราง/รายงาน
- [ ] 4. มี Interactive / Rich Viewer หรือ Dashboard รายงานผลที่แสดงผล Top Accounts พร้อม % PnL, Total PnL, Volume, และ Win Rate/Trades
- [ ] 5. ทดสอบรันและตรวจสอบผลลัพธ์ว่าข้อมูลถูกต้อง ตรงกับ Polymarket Explorer / Profile จริง

## 4. Non-goals (สิ่งที่ตั้งใจ "ไม่ทำ" ในรอบนี้)
- ไม่ทำการ Trade อัตโนมัติ (Automated Execution) หรือขอ Private Key ของผู้ใช้
- ไม่ bypass rate limit หรือใช้ scraping ที่ละเมิดเงื่อนไข

## 5. Constraints (ข้อจำกัดที่ห้ามละเมิด)
- ใช้เฉพาะ Public API และ On-chain / Public endpoints ที่เปิดเผย
- ตรวจสอบความถูกต้องของข้อมูลจาก Ground Truth (เปรียบเทียบกับหน้าเว็บ/API ของ Polymarket)

## 6. สัญญาณเตือนว่ากำลังหลงทาง (สร้างไว้ล่วงหน้า)
- ถ้าเริ่มเขียนโค้ด execution/trading บอทโดยที่ยังไม่ได้ข้อมูล PnL ราย account
- ถ้าคำนวณ % PnL โดยไม่มีคำนิยาม/สูตรที่ชัดเจน

## Changelog
| วันที่ | เปลี่ยนอะไร | เหตุผล |
|---|---|---|
| 2026-09-26 | สร้าง Goal Brief เริ่มต้น | กำหนด North Star และ DoD สำหรับการดึงและคำนวณ PnL / %PnL ราย account บน Polymarket |
