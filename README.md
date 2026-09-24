# ulltimate-skills

A personal library of reusable [Claude Code](https://code.claude.com/docs/en/plugins) skills, packaged as one
installable plugin. Install it once, and every skill added to `skills/` shows up automatically after an update.

## What's in here

| Skill | What it does | Origin |
| --- | --- | --- |
| [`skill-creator`](skills/skill-creator/SKILL.md) | Build a new skill from scratch, improve an existing one, write test cases, run evals, benchmark with/without the skill, and optimise the description so it triggers reliably. | Vendored from [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) (Apache-2.0) — see [`UPSTREAM.md`](skills/skill-creator/UPSTREAM.md) |
| [`agentic-code-workflow`](skills/agentic-code-workflow/SKILL.md) | Systematic 6-step workflow (Scan → Grill → Plan → Implement → Validate → Document) for code agentic agents to work like a senior engineer. Dual-mode Claude Code + Arena. Forces concrete commands, dependency search, and closing checklist. | Original — for Claude Code + Arena |
| [`bugfix-systematic`](skills/bugfix-systematic/SKILL.md) | Systematic bug fixing that fixes root cause + all dependent files, not just one file. Enforces Reproduce → Root Cause Tree → Dependency Search → Fix Root → Fix All Impacted → Validate → Regression Guard. Stack generic JS/TS + Python. | Original — for Claude Code + Arena |
| [`grilling`](skills/grilling/SKILL.md) | Grill the user relentlessly about a plan, decision, or idea. Maps as design tree, asks frontier in rounds, waits for answers. Use before any non-trivial task. | Vendored from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT) — see [`UPSTREAM.md`](skills/grilling/UPSTREAM.md) |
| [`grill-me`](skills/grill-me/SKILL.md) | Alias for grilling — trigger phrase users remember. Calls grilling skill. | Vendored from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT) — see [`UPSTREAM.md`](skills/grill-me/UPSTREAM.md) |

## Install

```bash
claude plugin marketplace add jampongsathorn/ulltimate-skills
claude plugin install ulltimate-skills@ulltimate-skills
```

Or from inside a running session, with `/plugin`:

```text
/plugin marketplace add jampongsathorn/ulltimate-skills
/plugin install ulltimate-skills@ulltimate-skills
```

Then restart Claude Code. Skills are namespaced by the plugin name:

- Invoke one directly: `/ulltimate-skills:skill-creator`
- Or just describe your task — Claude reads each skill's `description` and pulls the skill in when it fits,
  e.g. *"turn this workflow we just did into a skill"*.

### Try the repo without installing

```bash
claude --plugin-dir /path/to/ulltimate-skills   # loads the plugin in place; /reload-plugins to re-read
```

## Updating

After you push new skills, pull them into any machine that has the plugin installed:

```bash
claude plugin marketplace update ulltimate-skills   # or `/plugin marketplace update ulltimate-skills`
```

There's deliberately **no `version` field** in `.claude-plugin/plugin.json`, so Claude Code versions the plugin
by the git commit it fetched and updates land on the next marketplace refresh. If you ever want pinned releases,
add `"version": "1.0.0"` to `plugin.json` and bump it whenever you want users to receive a change.

## Adding a new skill

Three ways, easiest first.

1. **Ask Claude to do it.** With this plugin installed: *"Use the skill-creator skill to make a skill for X."*
   That walks the full loop — draft → test prompts → human review of outputs → benchmark vs. baseline →
   rewrite → repeat — and finishes by optimising the description for triggering. This is the recommended path
   for anything you'll use often.

2. **Scaffold, then edit.**

   ```bash
   tools/new-skill.sh my-skill-name     # creates skills/my-skill-name/SKILL.md from templates/skill-template
   ```

3. **By hand.** Copy `templates/skill-template/` to `skills/<name>/` and fill in `SKILL.md`.

Then validate and commit:

```bash
claude plugin validate .        # catches manifest and frontmatter mistakes
git add -A && git commit -m "Add my-skill-name skill" && git push
```

One caveat while developing: skill changes are only picked up on reload. Use `claude --plugin-dir .` and
`/reload-plugins`, or restart the session.

## Layout

```text
.claude-plugin/
├── marketplace.json     # makes this repo addable as a marketplace
└── plugin.json          # the single plugin's manifest (name = skill namespace)
skills/                  # ← every skill lives here; this folder is what Claude Code scans
└── skill-creator/
    ├── SKILL.md         # frontmatter (name, description) + instructions
    ├── agents/          # subagent prompts used by the skill
    ├── references/      # docs loaded only when needed
    ├── scripts/         # Python helpers invoked by the skill
    ├── assets/          # templates used by the skill
    └── eval-viewer/     # HTML reviewer generator
templates/
└── skill-template/      # starting point for a new skill (outside skills/ on purpose)
tools/
└── new-skill.sh         # scaffolder
```

## Conventions

- **One skill per directory** under `skills/`, named in kebab-case, each containing a `SKILL.md`.
- **The `description` in the frontmatter is the trigger.** It is the only part always loaded into context
  (~100 words), so write both *what it does* and *when to use it*, and lean slightly pushy — models tend to
  under-trigger skills. Put "when to use" information there, not in the body.
- **Keep `SKILL.md` under ~500 lines.** Beyond that, move detail into `references/` and point at it explicitly;
  bundled scripts can run without ever being read.
- **Bundle repeated work.** If a skill keeps writing the same helper script, commit it to the skill's `scripts/`.
- **Only `SKILL.md` goes at the root of a skill directory.** Anything inside `skills/` that lacks a valid
  `SKILL.md` is ignored at best, so templates and scratch work live outside it.
- **Eval runs land in `<skill-name>-workspace/`** (that's what skill-creator writes) and are gitignored.

## Requirements

- Claude Code (any recent version; `plugin validate` used here is from 2.1.x).
- Python 3 for the bundled scripts — standard library only, except `scripts/quick_validate.py`, which needs
  PyYAML (`pip install pyyaml`).
- The description-optimisation loop (`scripts/run_eval.py`, `scripts/run_loop.py`) shells out to `claude -p`,
  so it needs the Claude Code CLI on `PATH`.

## Credits

`skills/skill-creator` is vendored unmodified from Anthropic's official plugin marketplace and is licensed
under Apache-2.0 — see [`skills/skill-creator/LICENSE.txt`](skills/skill-creator/LICENSE.txt). Everything else
here is personal configuration.
