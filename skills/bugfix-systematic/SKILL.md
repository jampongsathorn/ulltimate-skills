---
name: bugfix-systematic
description: Systematic bug fixing for code agentic agents that fixes root cause and all dependent files, not just one file. Use when bug fixes are slow, incomplete, fix one file but break others, or when agent debugs endlessly without a clear workflow. Enforces Reproduce → Root Cause Tree → Dependency Search → Fix Root → Fix All Impacted → Validate → Regression Guard. Works dual-mode Claude Code + Arena, stack generic JS/TS + Python.
---

# Bugfix Systematic

Fix bugs systematically, completely, with no leftover bugs.

## When to use

- Bug still exists after fix, or appears in another file (dependency bug)
- Fixing one file but the function is imported in many places
- Agent is slow because it debugs endlessly with no clear workflow before coding
- You want a measurable definition of "complete": reproduce + root cause + fix all + test

If you don't have a plan yet, call `agentic-code-workflow` first, then this skill for the bug-specific phase, or call `grilling` to clear the design tree.

## Definition of Done (Complete = 4 items)

1. **Reproducible** — there is a script that fails before fix and passes after
2. **Root cause + all places using same pattern** — `rg` + `ast-grep` + import graph
3. **Fix as minimal diff at root** — fix the root cause, not the symptom
4. **Tests + rerun** — existing tests pass + new regression test

## Workflow — 7 steps (do not skip)

### 1. Reproduce — Prove the bug exists

```bash
# Create a direct reproduce file, don't guess
# JS/TS
cat > /tmp/reproduce.js <<'JS'
const { buggyFunc } = require('./src/utils');
console.log(buggyFunc('test')); // should be X but got Y
JS
node /tmp/reproduce.js

# Python
cat > /tmp/reproduce.py <<'PY'
from src.utils import buggy_func
print(buggy_func('test'))  # should be X but got Y
PY
python3 /tmp/reproduce.py

# Web bug
cat > reproduce.sh <<'SH'
curl -s http://localhost:3000/api/test | jq .
SH
bash reproduce.sh
```

You must see a failure before moving on. If you can't reproduce, you don't understand the bug yet.

### 2. Root Cause Tree — Why did this happen?

Use `grilling` to ask yourself:

```
Root: Why does buggyFunc return wrong value?
├── Branch A: logic inside the function itself wrong?
├── Branch B: dependency it calls wrong?
│   ├── B1: config wrong?
│   └── B2: another file it imports changed signature?
└── Branch C: same pattern copy-pasted in many places?
```

Write to `bug-analysis.md`:

```markdown
## Bug: ...
## Reproduce: /tmp/reproduce.py → fails with ...
## Root Cause: ...
## Why fixing one file fails: ...
```

### 3. Dependency & Similar Search — Find all impacted files

This step solves "fix one file, break another".

```bash
# 3.1 Find all usages of same function/name
rg -n "buggyFunc|buggy_func" --type js --type ts --type py --type tsx --type jsx

# 3.2 Find all places importing the file you will change
# JS/TS
rg -n "from ['\"].*utils|import.*utils|require.*utils" --type js --type ts --type tsx
npx madge --circular --extensions js,ts,tsx src/ 2>&1 | head -100
npx madge --image /tmp/dep.png src/ 2>&1 | tail -5

# Python
rg -n "from.*utils import|import.*utils" --type py
# Use pydeps if available
pip install pydeps -q && pydeps src/ --show-deps 2>&1 | head -100 || rg -n "^import|^from" --type py src/ | head -50

# 3.3 Find same pattern with ast-grep (if installed)
# Example: find all places binding 127.0.0.1 instead of 0.0.0.0
rg -n "127\.0\.0\.1" --type js --type ts --type py
ast-grep --pattern 'app.listen($$$ARGS, "127.0.0.1")' -l js,ts,tsx
ast-grep --pattern 'def $FUNC($$$):' -l python

# 3.4 Build Impacted Files list
cat > /tmp/impacted.txt <<'TXT'
src/utils.ts
src/api/handler.ts (imports utils.ts)
src/components/Widget.tsx (imports utils.ts)
tests/utils.test.ts
TXT
cat /tmp/impacted.txt
```

### 4. Fix Root — Minimal diff at root

Rules:
- Read file before editing every time
- Fix root cause, not symptom
- Keep diff as small as possible

```bash
# Before editing, read
read_file src/utils.ts  # In Arena use read_file tool
# In bash
cat src/utils.ts | head -100
```

### 5. Fix All Impacted — Don't stop at one file

Open `/tmp/impacted.txt` and fix every file:

```bash
# Example: if function signature changed, fix all call sites
rg -n "buggyFunc\(" --type js --type ts | while read line; do echo "$line"; done

# Fix one by one, read before edit
```

### 6. Validate — Prove it's complete

```bash
# 6.1 Reproduce must pass after fix
node /tmp/reproduce.js
python3 /tmp/reproduce.py

# 6.2 rg must find no old pattern left
rg -n "127\.0\.0\.1" --type js --type ts --type py
rg -n "buggyPattern" --type js --type ts --type py

# 6.3 Existing tests must pass
npm test 2>&1 | tail -30
pytest -q 2>&1 | tail -30

# 6.4 Plugin validate if this repo
claude plugin validate .
python3 -m compileall skills/ -q

# 6.5 Test install if plugin repo
tmp=$(mktemp -d); cd $tmp; mkdir t; cd t
claude plugin marketplace add /home/user/ulltimate-skills 2>&1 | tail -3
claude plugin install ulltimate-skills@ulltimate-skills 2>&1 | tail -3
cd /; rm -rf $tmp
```

### 7. Regression Guard — Add test to prevent return

```bash
# JS/TS: add test
cat >> tests/utils.test.ts <<'TS'
test('buggyFunc regression', () => {
  expect(buggyFunc('test')).toBe('expected');
});
TS

# Python: add test
cat >> tests/test_utils.py <<'PY'
def test_buggy_func_regression():
    assert buggy_func('test') == 'expected'
PY

npm test 2>&1 | tail -10
pytest -q 2>&1 | tail -10
```

## Stack Generic Cheat Sheet

| Goal | JS/TS | Python |
|------|-------|--------|
| Find usages | `rg -n "funcName" -t js -t ts` | `rg -n "func_name" -t py` |
| Find imports | `rg "from.*file|import.*file"` | `rg "from.*file import|import.*file"` |
| Dep graph | `npx madge --circular src/` | `rg "^import|^from" -t py src/` |
| Reproduce | `node /tmp/reproduce.js` | `python3 /tmp/reproduce.py` |
| Test | `npm test` | `pytest -q` |

## Example — Bug where fixing one file breaks another

**Scenario:** `src/utils/formatDate.ts` returns wrong format, 3 files import it.

**Without this skill:** agent fixes `formatDate.ts` only → 3 callers still pass old args → bug continues.

**With this skill:**
1. Reproduce → `/tmp/reproduce.js` shows wrong date
2. Root Cause → format string wrong + signature changed
3. Search → `rg "formatDate"` finds 4 files (1 source + 3 users)
4. Fix Root → fix `formatDate.ts`
5. Fix All → fix 3 callers to pass new args
6. Validate → reproduce passes + `npm test` passes + `rg` finds no old pattern
7. Regression → add test `formatDate('2026-09-24') === '24/09/2026'`

## Closing Checklist (mandatory)

- [ ] Reproduce script exists + fails before fix + passes after (`/tmp/reproduce.*`)
- [ ] `bug-analysis.md` or 1-paragraph root cause summary written
- [ ] Impacted Files list exists (`/tmp/impacted.txt` or in plan) + all files fixed, not just one
- [ ] `rg` / `ast-grep` proves no old pattern remains
- [ ] Validate passed: reproduce passes + existing tests pass + `claude plugin validate` if plugin repo + `compileall` if Python
- [ ] Regression test added + passes
- [ ] Commit message includes root cause + list of files fixed due to dependency
- [ ] No temp files left outside `/tmp` that should be gitignored
