---
name: agent-memory-hygiene
description: Survive long sessions and context compaction without hallucinating details, repeating finished work, or inheriting flattened confidence. Use on ANY task that spans multiple sessions or long context — even without a mission repo — when exact values (ids, prices, flags, error messages, paths) matter, when a compaction/summary is about to happen or just happened, or when you catch yourself "remembering" a value you cannot see. Installs a facts-ledger.md (load-bearing facts with provenance, as_of, decay class, supersede pointers, and a one-command re-verify each) plus a fail-closed validator. Core law: files beat memory — recall is not verification. For the full mission-level system (GOAL lock, checkpoints, write gates), use agent-operating-system; this skill is its context-survival layer, usable standalone.
---

# Agent Memory Hygiene (facts ledger, files beat memory)

## The problem, stated once

Long missions outlive the context window. Compaction (or a new session) replaces lived memory with a summary, and summaries lose exactly the things that matter most to future work: exact strings (paraphrased away), certainty levels ("probably 7%" becomes "7%"), the rationale behind decisions (conclusions survive, reasons don't), and the order of corrections. Worst of all, the failure is silent — **reconstructing a plausible value feels identical to remembering a real one.** The handoff summary is written by the most context-saturated version of you, so anything not already written to disk by then is at risk.

The fix is not better memory. It is making forgetting cheap: every load-bearing fact lives in a file with a one-command re-verify, so the difference between "I remember" and "I know" is a single grep.

## Core laws

1. **Files beat memory.** When your context and a file disagree, the file wins. Your recall of a specific string, number, path, or flag is *unverified* until re-read from disk.
2. **Capture verbatim, immediately.** Error messages, regexes, ids, working commands — into a file the moment you see them. A paraphrased error message is operatively worthless.
3. **Write state early, never at compaction time.** Frequent small structured records beat one heroic summary written while degraded.
4. **Intent ≠ state.** Plans survive compaction better than completion status. A plan is what you meant; a manifest is what happened. Never claim completion from a plan.
5. **Provenance and certainty travel with the fact.** Who observed it (agent-observed / user-reported / documented / inferred / hypothesis), when, how confidently — written down *before* compression can flatten the hedge.
6. **Every fact has a decay class and a re-verify path.** A fact with no re-verify command is unverifiable and must be labeled as such.
7. **Supersede, never silently overwrite.** New evidence appends with a pointer to what it replaces; both sides of the pointer must agree.
8. **Re-anchor often.** Re-read the governing files before each new subtask, not just each session. Mid-context is where early instructions silently die.
9. **Beware interference.** Similar items held in memory cross-contaminate (shop A's rate attributed to shop B). Tables in files don't interfere; heads do.

## The facts ledger

One `facts-ledger.md` per workspace/project, sitting next to (and distinct from) the state/handoff file: the handoff says *what is happening*, the ledger says *what is true*. Copy the template from `skills/templates/facts-ledger.md`. Entry format:

```markdown
### F-001 · <short title>
- fact: <the specific claim — exact ids, numbers, formats. No paraphrase.>
- provenance: agent-observed | user-reported | documented | inferred | hypothesis
- as_of: YYYY-MM-DD          # when last verified true
- decay: immutable | stable-until-change | decaying | volatile
- re-verify: `<exact command>` | gated: <condition> | never: <safety reason>
- status: active | superseded | retired
- supersedes: — | F-###      # what this entry replaced
- superseded_by: — | F-###   # what replaced this entry (both sides must agree)
- note: <claim boundary — what this fact does NOT imply>
```

Decay classes, with the discipline each one demands:

| Class | Meaning | Discipline |
|---|---|---|
| `immutable` | Past events, files on disk, standing safety rules | Trust freely; re-verify by re-reading |
| `stable-until-change` | Test results, code contracts | Valid until the named files change |
| `decaying` | Real-world state: prices, stock, API behavior | Re-verify before load-bearing use |
| `volatile` | Auth, quota, rate limits | Verify now, every time |

`re-verify` is the heart of the ledger. Three acceptable forms, nothing else:

- `` `command` `` — a one-liner that prints the ground truth (tested, not imagined);
- `gated: <condition>` — re-verification exists but needs authorization/time (user request, owner cookie, cost);
- `never: <safety reason>` — for standing safety rules where probing *is* the hazard.

## The validator (fail-closed, like everything worth trusting)

`skills/templates/validate_facts_ledger.py` — pure stdlib, no dependencies:

```bash
python3 skills/templates/validate_facts_ledger.py facts-ledger.md        # human output
python3 skills/templates/validate_facts_ledger.py facts-ledger.md --json # machine output
```

It rejects: missing/empty fields, vocabulary violations ("ผมจำได้" is not a provenance), non-dates, placeholder re-verify values (`TODO`), duplicate ids, dangling supersedes pointers, one-sided supersede links, and active entries that claim to be superseded. Every error names the entry, the field, and the accepted fix — the error message teaches the contract. Run it after every ledger edit; wire it into the checkpoint/exit checklist (`agent-operating-system` Layer 8) or CI if the project has one.

## When to write ledger entries

- You just observed something load-bearing live (an API behavior, a real price, a bug, a working command).
- The user stated a constraint, decision, or correction that must outlive this session.
- You are about to rely on a fact whose `as_of` is old and whose decay class is `decaying` or worse.
- Before a handoff/compaction: every fact you are carrying only in context gets written down or explicitly dropped.
- When one fact replaces another — append, point, never delete.

## Hallucination tripwires (self-check before acting)

- You are *recalling* an exact value rather than *seeing* it on screen → stop, run the re-verify command.
- You are about to state a number/string not visible in any open file or recent quote → re-derive it, or label it unverified out loud.
- You can explain in confident detail why something works but cannot name the file/observation where you learned it → that is reconstruction, not memory.
- You "remember" completing a validation step but cannot point at its artifact/output → it did not happen yet.
- An inherited summary states something with full confidence that was originally hedged → re-check before building on it.
- Several similar values (rates, ids, prices) are involved → do not recall; read the table.

## Relationship to other skills

- `agent-operating-system` — the full mission system; this skill is its Layer 9, extracted for standalone use on any long task.
- `handoff` — maintains the *state* file (what is happening); the ledger holds *knowledge* (what is true). Both belong in a long mission; neither replaces the other.
- `agentic-problem-solving` — its evidence loop is for external blockers; this skill's loop is for the agent's own memory as the blocker.
- `bugfix-systematic` — write the regression test when reality disconfirms code; write the ledger entry when reality disconfirms a recorded fact.
