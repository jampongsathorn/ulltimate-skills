---
name: my-skill
description: One or two sentences covering BOTH what this skill does and the concrete situations it should fire in. This is the only text Claude sees before deciding whether to open the skill, so be specific and a little pushy about the triggers — name the file types, tools, phrasings, and contexts that should bring it to mind, and mention near-miss situations where it should NOT. Example: "Turn messy CSV exports into clean, typed datasets. Use whenever the user mentions CSV, Excel exports, sales data, survey dumps, or asks to clean/summarise tabular data — even if they never say 'CSV'."
---

# My Skill

One-paragraph summary of what this skill accomplishes and why someone would reach for it.

## Workflow

1. **Understand the input** — what the user handed you and what shape it's in.
2. **Do the core work** — the steps specific to this skill, in order.
3. **Produce the output** — the exact artifact the user cares about.

Explain *why* each step matters instead of writing rules in all caps; a model that understands the reason
generalises to cases this file never mentions.

## Output format

If the output has a fixed shape, spell it out. Templates beat prose:

```markdown
# <Title>
## Summary
## Details
```

## Bundled resources

Delete this section if the skill has no extra files, and keep SKILL.md itself under ~500 lines.

- `scripts/` — code for deterministic or repetitive work; run it instead of rewriting it each time.
- `references/` — deeper docs loaded only when needed (add a table of contents if longer than ~300 lines).
- `assets/` — files copied into the output (templates, fonts, icons).

Reference them from this file with a note on *when* to read them, e.g.
"See `references/schema.md` before writing the migration."

## Examples

**Example 1**
Input: <a realistic user request>
Output: <what the skill should produce>
