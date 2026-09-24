# Upstream

`domain-modeling` is vendored from mattpocock/skills.

| | |
|---|---|
| Source | https://github.com/mattpocock/skills |
| Path | `skills/engineering/domain-modeling` |
| Commit | `c55ee46073ed923f86ce59a5eb3b6d895095d1b7` (2026-09-18) |
| License | MIT |
| Includes | SKILL.md + CONTEXT-FORMAT.md + ADR-FORMAT.md + agents/openai.yaml |

## Pulling upstream

```bash
tmp=$(mktemp -d)
git clone --filter=blob:none --sparse --depth 1 https://github.com/mattpocock/skills.git "$tmp"
git -C "$tmp" sparse-checkout set skills/engineering/domain-modeling
rsync -a "$tmp/skills/engineering/domain-modeling/" skills/domain-modeling/
rm -rf "$tmp"
```

## Local modifications

None — kept original, added this UPSTREAM.md and kept references/ folder.
