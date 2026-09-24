---
name: bugfix-systematic
description: Systematic bug fixing for code agentic agents that fixes root cause and all dependent files, not just one file. Use when bug fixes are slow, incomplete, fix one file but break others, or when agent debugs endlessly without a clear workflow. Enforces Reproduce → Root Cause Tree → Dependency Search → Fix Root → Fix All Impacted → Validate → Regression Guard. Works dual-mode Claude Code + Arena, stack generic JS/TS + Python.
---

# Bugfix Systematic

แก้ bug แบบเป็นระบบ ครอบคลุม ไม่เหลือหลายบัคต่อ

## When to use

- แก้ bug แล้วบัคยังอยู่ หรือไปโผล่ไฟล์อื่น (dependency bug)
- แก้ไฟล์เดียวแต่ function นั้นถูก import หลายที่
- Agent ใช้เวลานานเพราะ debug ไปเรื่อยๆ ไม่มี workflow ก่อนลงมือ
- อยากได้ definition ของ "ครอบคลุม" ที่วัดได้: reproduce + root cause + fix all + test

ถ้ายังไม่มีแผน ให้เรียก `agentic-code-workflow` ก่อน แล้วค่อยเรียก skill นี้สำหรับขั้น bug โดยเฉพาะ หรือเรียก `grilling` เพื่อเคลียร์ design tree ก่อน

## Definition of Done (ครอบคลุม = 4 อย่าง)

1. **reproduce ได้** — มี script ที่ fail ก่อนแก้ pass หลังแก้
2. **หา root cause + ทุกที่ที่ใช้ pattern เดียวกัน** — `rg` + `ast-grep` + import graph
3. **fix แบบ minimal diff ที่ราก** — แก้ที่ต้นตอ ไม่ใช่แก้อาการ
4. **มี test + rerun** — test เดิมผ่าน + test ใหม่กัน regression

## Workflow 7 ขั้น (ห้ามข้าม)

### 1. Reproduce — สร้างหลักฐานว่า bug มีจริง

```bash
# สร้างไฟล์ reproduce ตรงๆ ไม่ต้องเดา
# JS/TS
cat > /tmp/reproduce.js <<'JS'
const { buggyFunc } = require('./src/utils');
console.log(buggyFunc('test')); // ควรได้ X แต่ได้ Y
JS
node /tmp/reproduce.js

# Python
cat > /tmp/reproduce.py <<'PY'
from src.utils import buggy_func
print(buggy_func('test'))  # ควรได้ X แต่ได้ Y
PY
python3 /tmp/reproduce.py

# ถ้าเป็น web bug
cat > reproduce.sh <<'SH'
curl -s http://localhost:3000/api/test | jq .
SH
bash reproduce.sh
```

ต้องเห็น fail ก่อนไปขั้นต่อไป ถ้า reproduce ไม่ได้ = ยังไม่เข้าใจ bug

### 2. Root Cause Tree — ทำไม bug นี้เกิด

ใช้ `grilling` ถามตัวเอง:

```
Root: ทำไม buggyFunc คืนค่าผิด?
├── Branch A: logic ในฟังก์ชันผิดเอง?
├── Branch B: dependency ที่มันเรียกผิด?
│   ├── B1: config ผิด?
│   └── B2: อีกไฟล์ที่มัน import เปลี่ยน signature?
└── Branch C: มีหลายที่ copy-paste pattern เดียวกัน?
```

เขียนลง `bug-analysis.md`:

```markdown
## Bug: ...
## Reproduce: /tmp/reproduce.py → fail with ...
## Root Cause: ...
## Why only fixing one file fails: ...
```

### 3. Dependency & Similar Search — หาทุกไฟล์ที่โดน

นี่คือขั้นที่แก้ปัญหา "แก้ไฟล์เดียวแต่พังไฟล์อื่น"

```bash
# 3.1 หาทุกที่ที่ใช้ function/ชื่อเดียวกัน
rg -n "buggyFunc|buggy_func" --type js --type ts --type py --type tsx --type jsx

# 3.2 หาทุกที่ที่ import ไฟล์ที่เราจะแก้
# JS/TS
rg -n "from ['\"].*utils|import.*utils|require.*utils" --type js --type ts --type tsx
npx madge --circular --extensions js,ts,tsx src/ 2>&1 | head -100
npx madge --image /tmp/dep.png src/ 2>&1 | tail -5

# Python
rg -n "from.*utils import|import.*utils" --type py
# ใช้ pydeps ถ้ามี
pip install pydeps -q && pydeps src/ --show-deps 2>&1 | head -100 || rg -n "^import|^from" --type py src/ | head -50

# 3.3 หา pattern เดียวกันด้วย ast-grep (ถ้าติดตั้ง)
# ตัวอย่าง: หาทุกที่ที่ bind 127.0.0.1 แทน 0.0.0.0
rg -n "127\.0\.0\.1" --type js --type ts --type py
ast-grep --pattern 'app.listen($$$ARGS, "127.0.0.1")' -l js,ts,tsx
ast-grep --pattern 'def $FUNC($$$):' -l python

# 3.4 สร้าง Impacted Files list
cat > /tmp/impacted.txt <<'TXT'
src/utils.ts
src/api/handler.ts (imports utils.ts)
src/components/Widget.tsx (imports utils.ts)
tests/utils.test.ts
TXT
cat /tmp/impacted.txt
```

### 4. Fix Root — แก้ที่รากด้วย diff เล็ก

กฎ:
- อ่านไฟล์ก่อนแก้ทุกครั้ง
- แก้ที่ root cause ไม่ใช่แก้อาการ
- diff เล็กสุดเท่าที่ทำได้

```bash
# ก่อนแก้ อ่าน
read_file src/utils.ts  # ใน Arena ใช้ tool read_file
# ใน bash
cat src/utils.ts | head -100
```

### 5. Fix All Impacted — ไล่แก้ทุกไฟล์ใน list

อย่าหยุดที่ไฟล์เดียว — เปิด `/tmp/impacted.txt` แล้วแก้ทุกไฟล์:

```bash
# ตัวอย่าง: ถ้าเปลี่ยน signature ของ function
# ต้องไล่แก้ทุกที่ที่เรียก
rg -n "buggyFunc\(" --type js --type ts | while read line; do echo "$line"; done

# แก้ทีละไฟล์, อ่านก่อนแก้
```

### 6. Validate — พิสูจน์ว่าครบ

```bash
# 6.1 reproduce ต้อง pass หลังแก้
node /tmp/reproduce.js
python3 /tmp/reproduce.py

# 6.2 rg ต้องไม่เจอ pattern เก่าเหลือ
rg -n "127\.0\.0\.1" --type js --type ts --type py
rg -n "buggyPattern" --type js --type ts --type py

# 6.3 test เดิมต้องผ่าน
npm test 2>&1 | tail -30
pytest -q 2>&1 | tail -30

# 6.4 plugin validate ถ้าเป็น repo นี้
claude plugin validate .
python3 -m compileall skills/ -q

# 6.5 test install ถ้าเป็น plugin repo
tmp=$(mktemp -d); cd $tmp; mkdir t; cd t
claude plugin marketplace add /home/user/ulltimate-skills --force 2>&1 | tail -3
claude plugin install ulltimate-skills@ulltimate-skills 2>&1 | tail -3
cd /; rm -rf $tmp
```

### 7. Regression Guard — เพิ่ม test กันกลับมาเป็นอีก

```bash
# JS/TS: เพิ่ม test
cat >> tests/utils.test.ts <<'TS'
test('buggyFunc regression', () => {
  expect(buggyFunc('test')).toBe('expected');
});
TS

# Python: เพิ่ม test
cat >> tests/test_utils.py <<'PY'
def test_buggy_func_regression():
    assert buggy_func('test') == 'expected'
PY

npm test 2>&1 | tail -10
pytest -q 2>&1 | tail -10
```

## Stack Generic Cheat Sheet

| เป้าหมาย | JS/TS | Python |
|---------|-------|--------|
| หา usage | `rg -n "funcName" -t js -t ts` | `rg -n "func_name" -t py` |
| หา import | `rg "from.*file|import.*file"` | `rg "from.*file import|import.*file"` |
| Dep graph | `npx madge --circular src/` | `rg "^import|^from" -t py src/` |
| Reproduce | `node /tmp/reproduce.js` | `python3 /tmp/reproduce.py` |
| Test | `npm test` | `pytest -q` |

## Example — Bug ที่แก้ไฟล์เดียวแล้วพังไฟล์อื่น

**Scenario:** `src/utils/formatDate.ts` คืน format ผิด, มี 3 ไฟล์ import มัน

**Without this skill:** agent แก้ `formatDate.ts` อย่างเดียว → 3 ไฟล์ที่เรียกยังส่ง arg แบบเก่า → bug ต่อ

**With this skill:**
1. Reproduce → `/tmp/reproduce.js` แสดง date ผิด
2. Root Cause → format string ผิด + signature เปลี่ยน
3. Search → `rg "formatDate"` เจอ 4 ไฟล์ (1 ต้น + 3 ใช้)
4. Fix Root → แก้ `formatDate.ts`
5. Fix All → แก้ 3 ไฟล์ที่เรียกให้ส่ง arg ใหม่
6. Validate → reproduce pass + `npm test` pass + `rg` ไม่เจอ pattern เก่า
7. Regression → เพิ่ม test `formatDate('2026-09-24') === '24/09/2026'`

## Closing Checklist (บังคับ)

- [ ] Reproduce script มี + fail ก่อนแก้ + pass หลังแก้ (`/tmp/reproduce.*`)
- [ ] `bug-analysis.md` หรือสรุป root cause 1 ย่อหน้าเขียนไว้
- [ ] Impacted Files list มี (`/tmp/impacted.txt` หรือใน plan) + แก้ครบทุกไฟล์ ไม่ใช่แค่ไฟล์เดียว
- [ ] `rg` / `ast-grep` พิสูจน์ว่าไม่มี pattern เก่าเหลือ
- [ ] Validate ผ่าน: reproduce pass + existing tests pass + `claude plugin validate` ถ้าเป็น plugin repo + `compileall` ถ้ามี Python
- [ ] Regression test เพิ่มแล้ว + รันผ่าน
- [ ] Commit message มี root cause + list ไฟล์ที่แก้เพราะ dependency
- [ ] ไม่มีไฟล์ชั่วคราวค้างนอก `/tmp` ที่ควร gitignore
