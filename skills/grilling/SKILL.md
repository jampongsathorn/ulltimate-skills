---
name: grilling
description: Interview the user directly and relentlessly about a plan, decision, or idea, in question rounds, waiting for their real answers each round. Use when the user explicitly asks to be interviewed live (not delegated to a subagent) — e.g. "interview me", "walk me through the questions". Also use when building new features or fixing bugs without a clear workflow — this skill forces systematic design-tree thinking before any code is written. Not for the phrase "grill me" alone: that phrase is reserved for a separate subagent-critique loop defined elsewhere, which drafts and refines a plan across subagent rounds and only interrupts the user once at the end — this skill is the direct live-interview alternative, for when that hand-off-free style is explicitly wanted instead.
---

# Grilling

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.

## Arena / Claude Code Adaptation

This skill is dual-mode:
- **Claude Code**: installed as `/ulltimate-skills:grilling`, auto-discovered via `skills/` scanning
- **Arena**: read this file directly via `read_file` — Arena has no auto-load, so you must explicitly point at `skills/grilling/SKILL.md`. Also listed in root `AGENTS.md`.

When using in Arena:
- Use `bash` to gather facts (`find`, `rg`, `ls`) before asking
- Never ask user for facts you can look up
- Keep language consistent with user's language (English if user writes English)
- End with a clear `Shared Understanding` summary and ask for `confirm`

## Closing Checklist

- [ ] Design tree mapped, frontier empty
- [ ] No silent assumptions left
- [ ] User confirmed shared understanding
- [ ] Next skill to invoke is clear (e.g., `bugfix-systematic`, `agentic-code-workflow`)
