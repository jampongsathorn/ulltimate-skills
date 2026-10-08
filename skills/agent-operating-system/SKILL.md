---
name: agent-operating-system
description: The repo-level discipline layer that keeps a long-running agent from drifting across sessions, context resets, and real-world data. Build a GOAL.md lock (North Star, Definition of Done, non-goals, pre-written drift warnings), a numbered CHECKPOINT_LOG ritual, fail-closed validators whose error messages teach the contract, evidence refs + claim boundaries on every artifact, human-literal write gates, and a test-false-first self-healing loop where real data disconfirms wrong assumptions and every fix ships with a regression test. Use when starting or inheriting any multi-session agent mission, when an agent keeps "getting lost" or re-doing finished work, when a pipeline must survive contact with real API data, or when reviewing/adopting a repo like this. Complements agentic-code-workflow (one task), agentic-problem-solving (one blocker), bugfix-systematic (one bug), and handoff (state file) — this skill is the mission-level system underneath all of them.
---

# Agent Operating System (goal-locked, fail-closed, self-healing)

## The core insight

A long-running agent does not stay on track through willpower or model quality. It stays on track because **the discipline lives in files and code, not in the agent's memory**:

1. The goal is **re-read from disk every session** — amnesia-proof.
2. The rules are **enforced by validators and gates** — the agent cannot "forget" to behave; wrong input physically fails.
3. Every step **leaves durable state** (checkpoints, run manifests, evidence files) — progress survives context loss.
4. Wrong assumptions are **detected automatically** when reality hits a fail-closed gate, then fixed with a regression test — the system disconfirms itself.

A context-reset agent that lands in this repo inherits all of it for free. That is why it doesn't get lost: getting lost requires forgetting, and the system is designed so forgetting costs one file read, not the mission.

Reference implementation: `codex_review/Shopee - Video Factory/` (GOAL.md, AGENTS.md "Start here every session" + "Hard rules", CHECKPOINT_LOG.md, `src/shopee_video_factory/`, `evidence/`). All examples below are real mechanisms from that repo, several verified live during an end-to-end run.

---

## Layer 1 — Goal lock (GOAL.md)

One small file, written **before** work starts, with these fixed sections:

- **North Star** — a single sentence describing the finished mission ("Jam can issue one short instruction … and the agent autonomously … and proves each video is visible"). One sentence, not a paragraph: it must be re-readable in seconds and unarguable.
- **Definition of Done** — a checkbox list of externally observable outcomes. Anything not on the list is not "done", and the list itself is never declared complete while a box is unchecked.
- **Non-goals** — explicit anti-scope ("Guaranteeing revenue, CTR, or CVR"; "Bulk publishing beyond the requested five"). Non-goals are how you say no fast when the mission tempts you to expand.
- **Constraints** — invariants that must hold at every step (secrets never printed; `uncertain` writes never blindly retried; a receipt is not proof of publication).
- **Drift warnings** — a pre-written list of the *specific ways this agent will predictably go wrong* ("Spending time polishing architecture before proving the basket-attachment path"; "Treating upload success or a local receipt as completion"). You write these on day one, naming the temptations in advance, because at hour 40 you will not recognize them as temptations.
- **Changelog** — dated, with a Reason column. Changing the goal is allowed but never silent.

Why it prevents drift: every later artifact (checkpoints, plans, PRs) justifies itself against this file. When you can't articulate how today's work moves the North Star, that is the drift alarm.

## Layer 2 — Session ritual (AGENTS.md "Start here")

The first thing every session does, in order:

1. Read `GOAL.md`, `PLAN.md`, and **the newest checkpoint entry**.
2. Run the cheap health checks (`doctor --lane …`, test suite) *before* touching external-write paths.
3. Inspect the durable run manifest. **Resume it; never start a duplicate run because context was lost.**

Rule 3 is the anti-amnesia rule: resumable state means a context reset costs you one `status` command, not a re-run of expensive or irreversible work. Every expensive action is idempotent or manifest-guarded (e.g. "never generate Clip 2 before Clip 1 has a hash-bound stage receipt").

## Layer 3 — Checkpoint ritual (CHECKPOINT_LOG.md)

After every meaningful work block, append a **numbered entry** with fixed fields. The format matters; do not improvise it:

- **North Star (re-read from GOAL.md)** — quote/restate it first. This one line is why the log works: you cannot write the checkpoint without re-anchoring.
- **Result** — what was actually achieved, with artifact paths.
- **Negative/partial evidence** — what failed, what stayed unknown. *Required field.* Systems that only record wins teach the next session nothing about minefields.
- **Claim boundaries** — what the result does NOT prove ("one hashtag snapshot is not momentum"; "Insight data describes only the supplied page").
- **Safety outcome** — what gates held, what was never attempted.
- **Validation** — test counts, compile, secrets scan.
- **Next action + why next** — the next step must justify itself against the North Star, not against momentum.
- **Goal status** — which DoD boxes this moved, stated plainly.

The checkpoint is written *while tired*, at the end of a block, precisely so the *next* session (which may be a different model with zero memory) can cold-start correctly. It is a handoff to a stranger: you.

## Layer 4 — Fail-closed validators (the code enforces the rules)

Every ingestion or normalization step validates and **raises on anything unexpected** rather than guessing. Unknown shape, missing field, stale timestamp, malformed identifier → `ValueError`, not best-effort parsing. Two properties make this discipline instead of pedantry:

1. **The error message teaches the contract.** Real example from `research.py`:

   ```
   affiliate.evidence_ref must be a query-free http(s) URL, an evidence/ path,
   or a capture: identifier
   ```

   An agent that hits this error self-corrects in **one step** — the message lists exactly the accepted formats. Verify this property in your own validators: an error message that says "invalid" forces guessing; one that says "must be one of A, B, C" repairs the caller.

2. **Fail-closed beats fail-open under real data.** The pipeline was built before real data arrived; when 20 real feed pages hit it, the ingest crashed on live cards the author never imagined (`biz_type=2`, no `meta`). That crash was the system *working* — it refused to silently mis-ingest, and the failure pointed at the exact assumption to fix.

Companion rules that make validators safe to trust:

- **Freshness limits** (`max_product_age_hours=24`, mandatory `observed_at`) — stale evidence cannot pass as current.
- **Identity exactness** — product identity requires exact `item_id + shop_id`; title-substring matching is banned.
- **Deterministic versioned formulas** — scoring is `"observable-proxy-v1"`, a named, versioned function. Results are reproducible and auditable; changing the formula is a version bump, not a silent tweak.

## Layer 5 — Evidence contract (provenance and honesty in the data itself)

- Every observation carries an **`evidence_ref`** restricted to three forms: a `capture:<id>` ( sanitized snapshot), an `evidence/<path>` file, or a query-free http(s) URL. No observation enters the pipeline without provenance. Data that cannot name its source does not exist.
- Every scored/ranked output carries a **`claim_boundary`** string baked into the artifact: *"Scores are computed opportunity proxies. They are not observed CTR or CVR."* The anti-overclaim travels **with the data**, so a downstream agent consuming the JSON cannot miss it.
- **Semantic verdict vocabulary** is fixed: `verified` / `HTTP-schema verified; semantic success unknown` / `rejected`. An HTTP 200 with an unreadable success marker is recorded as *unknown*, never rounded up to success. ("The values of `code` and `msg` were not retained" → verdict unknown, and the unknown was later resolved only by new authorized evidence.)
- **Negative evidence is first-class and permanent.** A 403 risk response on an endpoint produces a written rule: excluded, never retried, no header rotation — recorded in the evidence file and the checkpoint. And a result on one endpoint is permission-information about **that endpoint only**; it never leaks conclusions to sibling endpoints.
- **Separation of powers:** sanitizers/ingesters make **zero network calls** — they accept supplied bodies only; acquisition (network + credentials) lives outside; raw bodies and secrets stay under gitignored `.private/` / in-memory only.

## Layer 6 — Write gates and state machines

- **Dry-run is the default.** Planning, ranking, and staging produce durable state but perform no external write.
- **Human-literal gate:** publishing requires the exact string `+submit` **in the current human message** plus an env flag plus a frozen-intent token. No paraphrase, no "user seemed to approve earlier", no remembering.
- **Jobs are a state machine** (`planned → … → approval_required → publishing → published_unverified|uncertain → verified`) and transitions are validated in code. Asking for an approval token for a job still in `planned` state returns `{"ok": false, "error": "job must be in approval_required state"}` — verified by probing it live.
- **`uncertain` is a terminal-enough state:** an external write whose outcome is unknown is never blindly retried; you reconcile (read back ground truth) before any further action. A UI transition, a draft response, or an upload receipt is **not success** — only independent read-back of the exact post + exact `item_id + shop_id` is.

## Layer 7 — The self-healing loop (test-false-first)

This is the mechanism behind "มันแก้บั๊กตัวเองได้" — the pipeline treats its own expectations as hypotheses:

1. **Expectations are encoded as validators/tests *before* real data arrives.** The regex `PUBLIC_POST_ID_RE = [1-9][0-9]*` was an *assumption written as code*.
2. **Real data arrives and fails the gate.** Live post-detail sanitization failed: real public post ids are base64-style (`rsLSgeIDCgDwwVoEAAAAAA==`), not numeric.
3. **The failure is investigated as a question: is the data wrong, or is the expectation wrong?** Evidence gathering: all 38 post ids observed across 20 real feed pages matched `[A-Za-z0-9+/_-]{20,28}={0,2}`; the Insight `encodePostId` field uses the same format. Verdict: **the code's assumption was wrong.**
4. **Write the regression test that reproduces the false first** (real-format fixture passes, the old wrong format is *kept as a deliberate reject-case*), then fix the code, then run the full suite.
5. **Document the correction in evidence + checkpoint** — including updating any earlier statement the correction invalidates (the previous evidence file's "semantic success unknown" verdict for the mix endpoint was explicitly superseded once real envelopes proved `code=0, msg=""`).

The loop, in one line: **assume you are wrong, make reality the referee, and turn every disconfirmation into a test.** A validator failure is never noise to route around — it is the cheapest possible moment to learn that a belief encoded in code is false.

## Layer 8 — Validation before "done" (every checkpoint, no exceptions)

The exit checklist for every work block: full test suite green (state the count), compilation passes, CLI renders, secrets scan of the repo clean, and — if anything external was touched — what exactly was and was not written. A checkpoint that says "done" without these lines is not a checkpoint.

---

## Installing this in a new project (minimal kit)

```
GOAL.md            # North Star, DoD checkboxes, non-goals, constraints, drift warnings, changelog
AGENTS.md          # "Start here every session" ritual + hard rules + write-gate sequence
CHECKPOINT_LOG.md  # numbered entries, fixed fields, newest last
evidence/          # one dated markdown file per verification, fixed table: timestamp,
                   # request class, HTTP/schema observation, semantic verdict, recommendation
.private/          # gitignored: raw bodies, snapshots, current working state
runs/              # gitignored: durable run manifests for resume-never-duplicate
```

Plus, in code: one validator module whose every raise message lists the accepted formats; evidence_ref + claim_boundary + observed_at required on artifacts that cross a stage boundary; a job state machine with validated transitions; dry-run default; and a literal human gate for irreversible writes.

## Session checklist (when operating under this skill)

- [ ] Read GOAL.md + newest checkpoint. Say the North Star back before doing anything.
- [ ] Run the cheap checks (tests, doctor, status) before touching anything expensive or irreversible.
- [ ] Resume the manifest; never re-run finished work. Check what is already done *before* planning.
- [ ] Before each external or expensive action: which DoD box does this move? If none — stop, it's drift.
- [ ] After each block: checkpoint entry with all fixed fields, including negative evidence and claim boundaries.
- [ ] When a validator rejects real data: investigate, don't bypass. Write the regression test first, then fix, then full suite, then document the correction.
- [ ] Before claiming done: validation checklist, and say precisely what remains gated/blocked — a blocked path is reported as blocked, never papered over.

## Drift tells (stop immediately if you notice these)

- You are polishing or refactoring something that no DoD box depends on.
- You are about to re-run an acquisition, query, or build "to be sure" without checking the manifest/snapshots first.
- You are interpreting a 200, a receipt, or a UI change as success without read-back.
- You are filling a gap with plausible data instead of recording it as a gap.
- You are retrying or routing around a risk/stop response instead of honoring the recorded permanent rule.
- You are about to write a checkpoint entry that has no "negative evidence" line because "everything worked".
- You changed the goal (scope, definition of done) without a GOAL.md changelog entry.

## Relationship to other skills

- `handoff` maintains the state file; this skill defines **what the state is for** and the ritual around it (GOAL/checkpoint/manifests).
- `agentic-code-workflow` governs a single task (Scan→Grill→Plan→Implement→Validate→Document); this skill is the mission-level frame that task runs inside.
- `agentic-problem-solving` is the evidence loop for a blocker; this skill's Layer 7 is that loop applied to *the code's own assumptions*.
- `bugfix-systematic` fixes a known bug root-and-branch; Layer 7 is how the bug gets *discovered* by the pipeline in the first place.
