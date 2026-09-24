---
name: agentic-code-workflow
description: Systematic workflow for code agentic agents to work like a senior engineer. Use whenever you need to build features, fix bugs, refactor, or create new skills in a repo — especially when previous attempts were slow, incomplete, or fixed only one file while breaking dependencies. Forces Scan → Grill → Plan → Implement → Validate → Document every time. Works dual-mode in Claude Code and Arena.
---

# Agentic Code Workflow

Make code agents work systematically, not debug endlessly.

## When to use

- Building a new feature, fixing a bug, refactoring, creating a new skill
- Agent fixes one file but breaks others (dependency bug)
- Work that was slow because there was no clear workflow before coding
- Every time you start a new session in Arena or Claude Code and want systematic behavior from the start

If it's specifically a bug fix, call `bugfix-systematic` after this skill — this one is the outer frame, `bugfix-systematic` is the inner frame for bugs.

## Core Principle

**Find facts yourself. Don't ask the user for anything you can look up with tools.** — This is the rule from `grilling`.

## Workflow (6 mandatory steps)

### 1. Scan — Gather facts first

Run these before asking anything:

```bash
# Repo structure, first 20-30 files
find . -type f -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/dist/*" -not -path "*/__pycache__/*" | head -30

# Check for AGENTS.md / CLAUDE.md / README.md
ls -la | head -30
cat AGENTS.md 2>/dev/null | head -100
cat CLAUDE.md 2>/dev/null | head -100

# If Claude Code plugin
cat .claude-plugin/plugin.json
cat .claude-plugin/marketplace.json
claude plugin validate . 2>&1 | tail -20

# If package.json / pyproject.toml exists
cat package.json 2>/dev/null | head -50
cat pyproject.toml 2>/dev/null | head -50
```

Why scan? Bugs like "fix one file, break another" happen because dependencies were never read.

### 2. Grill — Build a design tree

Invoke the `grilling` skill:

- In Claude Code: `/ulltimate-skills:grilling`
- In Arena: `read_file skills/grilling/SKILL.md` and follow it

Map as a tree, ask the frontier in rounds until no assumptions remain. Don't write code until you get `confirm`.

### 3. Plan — Write a short, runnable plan

Create `plan.md` or `task.md`:

```markdown
## Goal
## Root Cause Hypothesis
## Impacted Files (from rg / import trace)
## Steps (1..n)
## Validation (how to know it's done)
```

### 4. Implement — Minimal diff

Rules:
- Always read file before editing (`read_file`)
- Edit one file at a time, keep diffs small
- If you change a function that is imported elsewhere, `rg` for all usages first:

```bash
# JS/TS generic
rg -n "functionName|import.*from.*fileName" --type js --type ts --type tsx
rg -n "from ['\"].*fileName|import.*fileName" --type js --type ts

# Python generic
rg -n "def functionName|from.*fileName import|import.*fileName" --type py

# Use ast-grep if installed
ast-grep --pattern 'function $FUNC($$$ARGS) { $$$BODY }' -l js,ts
ast-grep --pattern 'def $FUNC($$$ARGS):' -l python
```

### 5. Validate — Prove it's complete

```bash
# JS/TS
npm run build 2>&1 | tail -30
npm test 2>&1 | tail -50

# Python
python3 -m compileall skills/
pytest -q 2>&1 | tail -50

# Claude Code plugin (this repo)
claude plugin validate .
# Real install test
tmp=$(mktemp -d); cd $tmp; mkdir test; cd test
claude plugin marketplace add /path/to/ulltimate-skills 2>&1 | tail -5
claude plugin install ulltimate-skills@ulltimate-skills 2>&1 | tail -5
claude plugin details ulltimate-skills@ulltimate-skills 2>&1 | tail -20
cd /; rm -rf $tmp

# Arena preview (if web server)
# Must bind 0.0.0.0, use relative URLs, allowedHosts, no X-Frame-Options
```

### 6. Document — Close systematically

- Update `AGENTS.md` if there's a new skill
- Update `README.md` / `CLAUDE.md` if workflow changed
- Write 1-paragraph root cause summary in commit message
- Clean up temp files in `/tmp`

## Stack Generic Support

| Task | JS/TS | Python |
|------|-------|--------|
| Find usages | `rg -n "func" --type ts` | `rg -n "def func" --type py` |
| Dep graph | `npx madge --circular src/` | `pydeps --show-deps` / `rg "import"` |
| Build | `npm run build` | `python -m compileall` |
| Test | `npm test` | `pytest -q` |

## Example

**Input:** "Fix a bug where fixing one file breaks another"

**Skill output:**
1. Scan → finds `utils.ts` is imported by 5 files
2. Grill → asks fix scope, coverage definition, stack
3. Plan → writes `plan.md` with 5 impacted files
4. Implement → fixes `utils.ts` + 5 importers
5. Validate → `npm test` passes + `rg` shows no old pattern left
6. Document → updates AGENTS.md + commits

## Closing Checklist (mandatory)

- [ ] Scan complete (find + read AGENTS.md/CLAUDE.md + validate)
- [ ] Grill until frontier empty + got confirm
- [ ] Plan written (includes Impacted Files list)
- [ ] Implement as minimal diff + read before edit + rg for usages complete
- [ ] Validate passed (build + test + plugin validate + test install if plugin repo)
- [ ] Document updated (AGENTS.md / README / commit message includes root cause)
- [ ] No temp files left in /tmp or workspace that should be gitignored
