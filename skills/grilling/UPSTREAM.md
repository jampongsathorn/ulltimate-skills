# Upstream

`grilling` is vendored from mattpocock/skills, not written here.
Keep it in sync occasionally; don't edit the core interview logic in place.

| | |
|---|---|
| Source | https://github.com/mattpocock/skills |
| Path | `skills/productivity/grilling` |
| Commit | `c55ee46073ed923f86ce59a5eb3b6d895095d1b7` (2026-09-18) |
| License | MIT — see source repo LICENSE |
| Local additions | Added `Arena / Claude Code adaptation` and `Closing Checklist` sections to make it dual-mode |

## Pulling upstream changes

```bash
tmp=$(mktemp -d)
git clone --filter=blob:none --sparse --depth 1 https://github.com/mattpocock/skills.git "$tmp"
git -C "$tmp" sparse-checkout set skills/productivity/grilling

rsync -a "$tmp/skills/productivity/grilling/" skills/grilling/
# restore local additions if overwritten, then update commit hash above
git -C "$tmp" log -1 --format=%H
rm -rf "$tmp"
```

## Local modifications

- Added dual-mode notes and closing checklist (see above)
- Original core prompt unchanged
