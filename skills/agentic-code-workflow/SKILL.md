---
name: agentic-code-workflow
description: Systematic workflow for code agentic agents to work like a senior engineer. Use whenever you need to build features, fix bugs, refactor, or create new skills in a repo — especially when previous attempts were slow, incomplete, or fixed only one file while breaking dependencies. Forces Scan → Grill → Plan → Implement → Validate → Document every time. Works dual-mode in Claude Code and Arena.
---

# Agentic Code Workflow

ทำให้ code agent ทำงานเป็นระบบ ไม่ใช่ debug ไปเรื่อยๆ

## When to use

- สร้าง feature ใหม่, แก้ bug, refactor, สร้าง skill ใหม่
- Agent แก้ไฟล์เดียวแล้วพังไฟล์อื่น (dependency bug)
- งานที่เคยทำช้าเพราะไม่มี workflow ชัดเจนก่อนลงมือ
- ทุกครั้งที่เริ่ม session ใหม่ใน Arena หรือ Claude Code และอยากให้เป็นระบบตั้งแต่ต้น

ถ้าเป็นงานแก้ bug โดยเฉพาะ ให้เรียก `bugfix-systematic` ต่อจาก skill นี้ — skill นี้คือกรอบใหญ่, `bugfix-systematic` คือกรอบย่อยสำหรับ bug

## Core Principle

**หาข้อเท็จจริงเอง อย่าถาม user ถ้าหาได้จากเครื่องมือ** — นี่คือกฎจาก `grilling`

## Workflow (6 ขั้นบังคับ)

### 1. Scan — หาข้อเท็จจริงก่อน

รันคำสั่งเหล่านี้ก่อนถามอะไรทั้งสิ้น:

```bash
# โครงสร้าง repo 20-30 ไฟล์แรก
find . -type f -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/dist/*" -not -path "*/__pycache__/*" | head -30

# ดูว่ามี AGENTS.md / CLAUDE.md / README.md ไหม
ls -la | head -30
cat AGENTS.md 2>/dev/null | head -100
cat CLAUDE.md 2>/dev/null | head -100

# ถ้าเป็น Claude Code plugin
cat .claude-plugin/plugin.json
cat .claude-plugin/marketplace.json
claude plugin validate . 2>&1 | tail -20

# ถ้ามี package.json / pyproject.toml
cat package.json 2>/dev/null | head -50
cat pyproject.toml 2>/dev/null | head -50
```

ทำไมต้อง scan? เพราะ bug แบบ "แก้ไฟล์เดียวแต่พังไฟล์อื่น" เกิดจากการไม่อ่าน dependency ก่อน

### 2. Grill — สร้าง design tree

เรียก `grilling` skill:

- ใน Claude Code: `/ulltimate-skills:grilling`
- ใน Arena: `read_file skills/grilling/SKILL.md` แล้วทำตาม

แมปเป็น tree, ถาม frontier เป็นรอบๆ จนหมดสมมติฐาน อย่าเริ่ม code จนกว่าจะได้ `confirm`

### 3. Plan — เขียนแผนสั้นที่รันได้

สร้าง `plan.md` หรือ `task.md` ที่มี:

```markdown
## Goal
## Root Cause Hypothesis
## Impacted Files (from rg / import trace)
## Steps (1..n)
## Validation (how to know it's done)
```

### 4. Implement — minimal diff

กฎ:
- อ่านไฟล์ก่อนแก้เสมอ (`read_file`)
- แก้ทีละไฟล์, diff เล็ก
- ถ้าแก้ function ที่มีคน import ให้ `rg` หาทุกที่ที่ใช้ก่อน:

```bash
# JS/TS generic
rg -n "functionName|import.*from.*fileName" --type js --type ts --type tsx
rg -n "from ['\"].*fileName|import.*fileName" --type js --type ts

# Python generic
rg -n "def functionName|from.*fileName import|import.*fileName" --type py

# ใช้ ast-grep ถ้าติดตั้ง
ast-grep --pattern 'function $FUNC($$$ARGS) { $$$BODY }' -l js,ts
ast-grep --pattern 'def $FUNC($$$ARGS):' -l python
```

### 5. Validate — พิสูจน์ว่าครบ

```bash
# JS/TS
npm run build 2>&1 | tail -30
npm test 2>&1 | tail -50

# Python
python3 -m compileall skills/
pytest -q 2>&1 | tail -50

# Claude Code plugin (repo นี้)
claude plugin validate .
# test install จริง
tmp=$(mktemp -d); cd $tmp; mkdir test; cd test
claude plugin marketplace add /path/to/ulltimate-skills --force 2>&1 | tail -5
claude plugin install ulltimate-skills@ulltimate-skills 2>&1 | tail -5
claude plugin details ulltimate-skills@ulltimate-skills 2>&1 | tail -20
cd /; rm -rf $tmp

# Arena preview (ถ้ามี web server)
# ต้อง bind 0.0.0.0, ใช้ relative URL, allowedHosts, ไม่มี X-Frame-Options
```

### 6. Document — ปิดงานแบบเป็นระบบ

- อัพเดต `AGENTS.md` ถ้ามี skill ใหม่
- อัพเดต `README.md` / `CLAUDE.md` ถ้ามี workflow ใหม่
- เขียนสรุป root cause 1 ย่อหน้าใน commit message
- ลบไฟล์ชั่วคราวใน `/tmp`

## Stack Generic Support

Skill นี้รองรับทั้ง JS/TS และ Python:

| Task | JS/TS | Python |
|------|-------|--------|
| Find usages | `rg -n "func" --type ts` | `rg -n "def func" --type py` |
| Dep graph | `npx madge --circular src/` | `pydeps --show-deps` / `rg "import"` |
| Build | `npm run build` | `python -m compileall` |
| Test | `npm test` | `pytest -q` |

## Example

**Input:** "แก้ bug ที่แก้ไฟล์เดียวแล้วพังอีกไฟล์"

**Output ของ skill:**
1. Scan → เจอว่า `utils.ts` ถูก import โดย 5 ไฟล์
2. Grill → ถามว่าแก้แบบไหน, ครอบคลุมแค่ไหน, stack อะไร
3. Plan → เขียน `plan.md` ว่ามี 5 ไฟล์โดน impact
4. Implement → แก้ `utils.ts` + 5 ไฟล์ที่ import
5. Validate → `npm test` pass + `rg` ไม่เจอ pattern เก่าเหลือ
6. Document → อัพเดต AGENTS.md + commit

## Closing Checklist (บังคับ)

- [ ] Scan ครบ (find + read AGENTS.md/CLAUDE.md + validate)
- [ ] Grill จน frontier หมด + ได้ confirm
- [ ] Plan เขียนไว้ (มี Impacted Files list)
- [ ] Implement แบบ minimal diff + อ่านไฟล์ก่อนแก้ + rg หา usage ครบ
- [ ] Validate ผ่าน (build + test + plugin validate + test install ถ้าเป็น plugin repo)
- [ ] Document อัพเดต (AGENTS.md / README / commit message มี root cause)
- [ ] ไม่มีไฟล์ชั่วคราวค้างใน /tmp หรือ workspace ที่ควร gitignore
