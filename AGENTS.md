# AGENTS.md — Index for Arena AI and other code agents

This repo is a Claude Code plugin **and** an Arena AI skill library. Claude Code auto-discovers `skills/` via `.claude-plugin/plugin.json`. Arena has no auto-load — **read this file first, then read the specific `skills/<name>/SKILL.md` you need**.

## How to use in Arena

1. **Scan** repo structure:
```bash
find . -type f -not -path "*/node_modules/*" -not -path "*/.git/*" | head -30
ls -la
cat .claude-plugin/plugin.json
```

2. **Pick a skill** from the catalog below and read it:
```
read_file skills/<skill-name>/SKILL.md
```

3. **Follow its workflow** — every skill in this repo has concrete bash commands and a Closing Checklist. Don't skip steps.

4. **Validate** before finishing:
```bash
claude plugin validate .
python3 -m compileall skills/ -q
```

## Runbooks (step-by-step guides, not skills)

- **[`understanding-video.md`](understanding-video.md)** — user sends a video link and asks what's in it.
  Full runbook: environment probe → metadata without crawling → frames/contact sheets → caption OCR →
  audio (speech vs ASMR bed) → demucs + faster-whisper transcript → cross-validation → report → cleanup.
  Includes the working GitHub Actions relay YAML for when sandbox egress is blocked, plus a gotchas list
  (VAD drops half the clip, large-v3 hangs, per-run branch names, cleanup contract) and **PART 7 on durability**
  (the workspace can be reset between turns: commit text artifacts to tracked `analyses/<date>-<slug>/`, keep heavy
  media in the gitignored `<name>-workspace/`, log tmp-branch SHAs before deleting so they stay recoverable).
  **Read this before improvising.** Worked example: [`analyses/2026-09-24-jessievariety13-2102770102517309525/report.md`](analyses/2026-09-24-jessievariety13-2102770102517309525/report.md)

## Skill Catalog (Group 1 — Systematic Work)

### Core Workflow (use first)

- **`agentic-code-workflow`** — Systematic 6-step workflow for any code task (Scan → Grill → Plan → Implement → Validate → Document). Forces concrete commands, dependency search, and closing checklist. Use for feature, refactor, or new skill creation.
  - Path: `skills/agentic-code-workflow/SKILL.md`
  - Triggers: building features, slow work, incomplete fixes, new skills

- **`grilling`** / **`grill-me`** / **`grill-with-docs`** / **`domain-modeling`** — Relentless interview to sharpen a plan or design. Maps decisions as a design tree, asks frontier in rounds, waits for answers. `grill-with-docs` also creates ADRs and glossary via `domain-modeling`. Use before any non-trivial task to reach shared understanding.
  - Path: `skills/grilling/SKILL.md` (core), `skills/grill-me/SKILL.md` (alias), `skills/grill-with-docs/SKILL.md` (grilling + docs), `skills/domain-modeling/SKILL.md` (glossary + ADRs)
  - Upstream: `mattpocock/skills` MIT, commit `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`
  - Triggers: "grill me", "stress test", planning, design, CONTEXT.md, ADR

### Bug Fixing

- **`bugfix-systematic`** — Systematic bug fixing that fixes root cause + all dependent files, not just one file. Enforces Reproduce → Root Cause Tree → Dependency Search → Fix Root → Fix All Impacted → Validate → Regression Guard. Stack generic JS/TS + Python. Use when bug fix is slow, incomplete, or fixes one file but breaks others.
  - Path: `skills/bugfix-systematic/SKILL.md`
  - Key commands: `rg -n "func"`, `npx madge --circular`, `python3 /tmp/reproduce.py`, `npm test`, `pytest`
  - Triggers: bug fix, dependency bug, incomplete fix, debugging endlessly

### Trading & Statistics (Professor Level)

- **`trading-stats-mindset`** — Think like a 10-year stats professor for time series trading strategy analysis. Forces Distribution > Point, Stationarity, Randomness, Sample size, Bias checks. Detects regime shifts, overfitting/walk-forward degradation, tail risk/drawdown clustering, win rate illusion. Includes decision tree (Theory/Heuristic/Trap), data mixing strategy, and Python script generating report + memo.
  - Path: `skills/trading-stats-mindset/SKILL.md`
  - Script: `skills/trading-stats-mindset/scripts/trading_stats_check.py --input data.csv --output report/`
  - References: `references/professor-decision-tree.md`, `assets/report-template.md`
  - Triggers: trading strategy analysis, time series behavior, statistical mindset, regime shift, overfitting, tail risk

### Skill Building

- **`skill-creator`** — Create new skills, modify existing ones, run evals and benchmarks, optimize descriptions. Use when creating a skill from scratch or improving one.
  - Path: `skills/skill-creator/SKILL.md`
  - Upstream: `anthropics/claude-plugins-official` Apache-2.0, commit `6bfd4e0c6d3da6050984fa5ed8281d915fa7ed69`
  - Triggers: create skill, edit skill, eval skill

## Quick Start for Bug Fixing (most common pain)

```bash
# 1. Read the systematic workflow
read_file skills/agentic-code-workflow/SKILL.md
read_file skills/bugfix-systematic/SKILL.md

# 2. Scan
find . -type f -not -path "*/node_modules/*" -not -path "*/.git/*" | head -30
rg -n "buggyFunction" --type js --type ts --type py

# 3. Grill (if needed)
read_file skills/grilling/SKILL.md
# → run rounds until confirm

# 4. Follow bugfix-systematic 7 steps
# → reproduce, root cause, impacted list, fix root, fix all, validate, regression
```

## Quick Start for Trading Stats Analysis (professor level)

```bash
# 1. Read professor mindset
read_file skills/trading-stats-mindset/SKILL.md
read_file skills/trading-stats-mindset/references/professor-decision-tree.md

# 2. Run professor script on your data
python3 skills/trading-stats-mindset/scripts/trading_stats_check.py --input trades.csv --pnl-col pnl --returns-col returns --output report/
# Generates report/analysis-report.md + report/decision-memo.md

# 3. Follow decision tree: Observation → Question → Test → Interpretation → Trading Decision
```

## Arena-Specific Rules (from experience)

- **Web preview**: bind `0.0.0.0`, not `127.0.0.1`; use relative URLs + `/api` proxy; set `allowedHosts: all` or allow preview host; avoid `X-Frame-Options` / CSP `frame-ancestors` blocking iframe
- **Processes**: use `start_process` for dev servers, not `bash` (bash times out); `get_process_output` to wait for port
- **Sandbox egress is limited**: in some sessions only `github.com` + package registries (pypi/npm) are reachable;
  everything else (`video.twimg.com`, `huggingface.co`, `raw.githubusercontent.com`, `r.jina.ai`, …) returns
  `SSLZeroReturnError` / empty reply. **Probe with one TLS line before planning** — then either use `pip`
  (e.g. `imageio-ffmpeg` for a static ffmpeg) or relay the work through a GitHub Actions runner (see
  [`understanding-video.md`](understanding-video.md) PART 3) and fetch results back via `git archive`.
  Note: HF-blocked means `faster-whisper` / `demucs` can't download models locally — transcribe in CI.
- **Snapshots**: files in `node_modules/`, `dist/`, `__pycache__/`, `.next/`, `build/`, `out/`, `target/`, `.cache/` are NOT persisted — don't write important files there
- **Tools available**: `bash`, `read_file`, `write_file`, `edit_file`, `web_search`, `image_search`, `generate_image`, `generate_speech`, `start_process`, `get_process_output`, `stop_process`

## Adding a New Skill

```bash
tools/new-skill.sh <kebab-case-name>
# Edit skills/<name>/SKILL.md — keep <500 lines, concrete commands, closing checklist
claude plugin validate .
```

No need to edit `.claude-plugin/marketplace.json` or `plugin.json` — `skills/` is auto-scanned.

## Validation

```bash
claude plugin validate .   # should warn only about missing version (intentional)
python3 -m compileall skills/ -q
```

Missing `version` in `plugin.json` is intentional — version comes from git commit SHA.
