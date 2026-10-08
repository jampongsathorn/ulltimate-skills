# FACTS LEDGER — <project name>

> **Files beat memory.** This ledger is the source of truth for load-bearing facts.
> HANDOFF/state files say *what is happening*; this file says *what is true*.
> Supersede, never silently overwrite. Validate after every edit:
> `python3 skills/templates/validate_facts_ledger.py facts-ledger.md`
>
> Field contract:
> - `fact` — the claim, specific and verbatim (exact ids, numbers, formats). No paraphrase.
> - `provenance` — `agent-observed` | `user-reported` | `documented` | `inferred` | `hypothesis`
> - `as_of` — YYYY-MM-DD when last verified true
> - `decay` — `immutable` (cannot change: past events, files on disk, safety rules) |
>   `stable-until-change` (holds until named files/conditions change) |
>   `decaying` (real-world state: prices, API behavior, stock — re-verify before load-bearing use) |
>   `volatile` (auth, quota, rate limits — verify now, every time)
> - `re-verify` — the exact one-liner command that re-verifies it, or
>   `gated: <who/what must authorize>` or `never: <safety reason>`
> - `status` — `active` | `superseded` | `retired`
> - `supersedes` / `superseded_by` — `—` or an F-id; both sides must agree

### F-001 · <short title — what the fact is>
- fact: <the specific claim, with exact values/ids/paths>
- provenance: agent-observed
- as_of: 2026-10-08
- decay: decaying
- re-verify: `<exact command that prints the ground truth>`
- status: active
- supersedes: —
- superseded_by: —
- note: <optional: claim boundary — what this fact does NOT imply>

### F-002 · <an example of superseding>
- fact: <newer measurement replacing F-001, e.g. re-measured price>
- provenance: agent-observed
- as_of: 2026-10-09
- decay: decaying
- re-verify: `<command>`
- status: active
- supersedes: F-001
- superseded_by: —
- note: supersedes F-001 because <reason + evidence>
