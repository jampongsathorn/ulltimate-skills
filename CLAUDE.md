# Repo notes for Claude Code

This repo is a personal library of Claude Code skills, published as a single installable plugin.
It also works in Arena AI via root `AGENTS.md` index — Arena has no auto-load, so it reads `AGENTS.md` then `skills/<name>/SKILL.md`.

## Skills in this repo (Group 1 — systematic work)

- `agentic-code-workflow` — 6-step systematic workflow (Scan → Grill → Plan → Implement → Validate → Document) for code agentic agents, dual-mode Claude Code + Arena
- `bugfix-systematic` — 7-step bug fixing (Reproduce → Root Cause → Dep Search → Fix Root → Fix All → Validate → Regression), stack generic JS/TS + Python
- `trading-stats-mindset` — professor-level statistical mindset for time series trading: 5 checks (Distribution, Stationarity, Randomness, Sample size, Bias) + 4 priorities (Regime shift, Overfitting, Tail risk, Win rate illusion), decision tree, Python script generating report+memo
- `grilling` / `domain-modeling` — direct live-interview as design tree, frontier rounds, plus docs (ADRs, glossary) — vendored from mattpocock/skills. Not the same as "grill me" (reserved elsewhere for a subagent-critique loop that only interrupts the user once, at the end).
- `skill-creator` — create/improve skills, evals, benchmarks (vendored from anthropics/claude-plugins-official)

See `AGENTS.md` for Arena usage and full catalog.

## Adding a skill

- New skills go in `skills/<kebab-case-name>/SKILL.md`. The plugin scans `skills/` by default, so nothing else
  in the repo needs editing — no need to touch `.claude-plugin/marketplace.json` or `plugin.json`.
- Prefer the `skill-creator` skill for anything non-trivial: it runs the draft → test → review → benchmark loop,
  and it can optimise the `description` for triggering at the end.
- For systematic work, use `agentic-code-workflow` and `bugfix-systematic` as playbooks — they enforce concrete commands + closing checklist.
- Quick scaffold: `tools/new-skill.sh <name>`, or copy `templates/skill-template/`.
- Keep `SKILL.md` under ~500 lines. Push detail into `references/`, deterministic code into `scripts/`,
  output templates into `assets/`, and say when to read each one.
- The frontmatter `description` is the trigger and the only always-loaded text — make it cover both the
  capability and the situations that should invoke it.

## Before committing

```bash
claude plugin validate .
```

It reports one warning about the missing `version` in `plugin.json`. That's intentional — without a version,
Claude Code versions the plugin by git commit, so installed copies pick up new skills on the next marketplace
update. Don't "fix" it by adding a version unless you also plan to bump it on every change (see README).

Never edit `skills/skill-creator/` in place: it's vendored from `anthropics/claude-plugins-official`
(Apache-2.0). To update it, follow `skills/skill-creator/UPSTREAM.md` so the next sync stays clean.

Skill workspaces (`*-workspace/`, `feedback.json`) are generated eval output and are gitignored — don't commit
them.
