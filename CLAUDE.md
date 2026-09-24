# Repo notes for Claude Code

This repo is a personal library of Claude Code skills, published as a single installable plugin.

## Adding a skill

- New skills go in `skills/<kebab-case-name>/SKILL.md`. The plugin scans `skills/` by default, so nothing else
  in the repo needs editing — no need to touch `.claude-plugin/marketplace.json` or `plugin.json`.
- Prefer the `skill-creator` skill for anything non-trivial: it runs the draft → test → review → benchmark loop,
  and it can optimise the `description` for triggering at the end.
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
