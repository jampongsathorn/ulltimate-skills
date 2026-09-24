# Upstream

`skill-creator` is vendored from Anthropic's official plugin marketplace, not written here.
Keep it in sync occasionally; don't edit it in place unless you intend to fork it.

| | |
|---|---|
| Source | https://github.com/anthropics/claude-plugins-official |
| Path | `plugins/skill-creator/skills/skill-creator` |
| Commit | `6bfd4e0c6d3da6050984fa5ed8281d915fa7ed69` (2026-09-23) |
| License | Apache-2.0 — see `LICENSE.txt` |

## Pulling upstream changes

```bash
# from the repo root
tmp=$(mktemp -d)
git clone --filter=blob:none --sparse --depth 1 https://github.com/anthropics/claude-plugins-official.git "$tmp"
git -C "$tmp" sparse-checkout set plugins/skill-creator

rsync -a --delete \
  "$tmp/plugins/skill-creator/skills/skill-creator/" \
  skills/skill-creator/

# then update the commit hash above
git -C "$tmp" log -1 --format=%H
rm -rf "$tmp"
```

Or just ask Claude Code: *"sync skills/skill-creator from anthropics/claude-plugins-official and show me the diff."*

## Local modifications

None. Keep it that way if possible so future syncs are clean.

## Runtime notes

- All scripts use the Python standard library only, except `scripts/quick_validate.py`, which imports
  PyYAML (`pip install pyyaml`) for frontmatter parsing.
- Description optimisation (`scripts/run_eval.py`, `scripts/run_loop.py`) shells out to `claude -p`,
  so it needs the Claude Code CLI on `PATH`.
