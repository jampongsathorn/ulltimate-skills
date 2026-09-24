---
name: agentic-resourcefulness-mindset
description: >-
  Think like a resourceful senior operator when the environment fights back — blocked network egress,
  missing binaries, expired credentials, sandboxes that reset and delete work, or outputs you cannot
  verify directly. Use whenever a step fails with SSLZeroReturnError, "Empty reply from server",
  "command not found", "Permission denied", 401, 403, 429 or non-fast-forward; whenever a host is
  blocked or unpredictable; whenever a tool must be obtained; whenever work has to survive between
  turns or hand off to another session; and especially whenever you are about to tell the user
  "I can't" or "it's not possible". Forces Probe, Cheapest path, Escalate, Triangulate, then Persist
  and hand off. Dual-mode — Claude Code and Arena.
---

# Agentic Resourcefulness Mindset

Most agent failures are not knowledge failures — they are **environment failures mistaken for capability limits**.
The sandbox blocks a host, a binary is missing, a token expired, the workspace got reset, and the agent
concludes "impossible" after one attempt. The fix is not more cleverness; it is a repeatable posture:

> **The environment is a variable, not a verdict.**
> And its counterweight: **resourcefulness without honesty is just confident nonsense** — so every routed,
> inferred, or unverifiable result gets labelled as such.

## When to use

- Any command failed with an environment-shaped error: `SSLZeroReturnError`, `Empty reply from server`,
  `command not found`, `Permission denied`, `401`, `403`, `429`, `Killed`, `No space left`, `non-fast-forward`
- A host is blocked, or the sandbox has an allowlist you have not mapped
- You need a tool that is not installed, and the package manager cannot reach its mirror
- Work must survive between turns (resets happen) or be handed to another session or agent
- The output cannot be verified directly (video, PDF, image, audio, remote state, someone else's API)
- You are about to write "I can't fetch/install/access…" or to hand the user a confident summary built on one source

## When NOT to use

- Routine code edits, refactors, new features → `agentic-code-workflow`
- A logic bug that reproduces locally → `bugfix-systematic`
- Statistical claims about time series → `trading-stats-mindset`
- **A requirements question, not a technical block.** If the user must choose what "good" means, ask —
  resourcefulness is about routing around *technical* constraints, not about guessing intent.

## Core Mindset — 5 Mandatory Moves

Each move has Theory / Heuristic / Trap. Skipping move 4 or 5 is how a resourceful agent turns into a
dangerous one.

### 1. Probe, don't presume

**Theory:** A plan is only valid inside a known capability envelope. Every assumed capability is a
deferred failure that costs a whole cycle when it lands.

**Heuristic:** Before any multi-step plan, spend one minute building a capability matrix:
which binaries exist, which hosts answer a TLS handshake, which registries work.

```bash
skills/agentic-resourcefulness-mindset/scripts/probe-environment.sh --out probe/capability-matrix.md --timeout 2
# stdout = markdown matrix; stderr = one-line summary (allowed/blocked hosts, missing tools, profile)
```

**Trap:** "The docs say it works." Docs describe the upstream world. A CI runner without ffmpeg,
a sandbox whose Debian mirror is blocked, an `SSLZeroReturnError` that looks like a network outage
but is actually an allowlist — all invisible until probed. One real case: a whole CI run died because
the workflow assumed the runner shipped `ffmpeg` and had `set -e` on every line.

### 2. Cheapest path first

**Theory:** Information per unit of time is the real currency. A 1-second probe beats a 10-minute
pipeline, even if the pipeline is the "proper" solution — because the probe decides *whether* the
pipeline is needed and *which* one.

**Heuristic — the cost ladder.** Climb only until the question is answered:

| Rung | Move | Cost |
| --- | --- | --- |
| 0 | Look in the workspace / ask for a path you already have | seconds |
| 1 | Metadata endpoint (oEmbed, syndication, `HEAD`, `--dry-run`, `--list-formats`) | seconds |
| 2 | A parameter change (higher bitrate variant, different flag, retry with UA, `?tag=`) | seconds |
| 3 | A library that ships the asset (`pip install imageio-ffmpeg` brings a static ffmpeg) | ~1 min |
| 4 | Local full pipeline (transcribe/OCR/render everything) | minutes–hours |
| 5 | Remote compute relay | minutes + cleanup duty |

**Trap:** Building the pipeline before the probe (CI job to fetch a file that one `curl` could have
fetched), or running a heavyweight model on the whole input when 15 seconds of it settles the question
(`large-v3` on 100s of audio: 40 minutes and a cancelled run; `medium`: 90 seconds and enough).

### 3. Escalate, don't surrender

**Theory:** For almost any data-transfer or compute task there are ≥3 independent routes. Blocks are
usually scoped (one host, one binary, one path) — so a global "impossible" conclusion is almost always
a category error.

**Heuristic — the escalation ladder.** Climb in order, and *tell the user which rung you used*:

1. **Retry with variation** — user-agent, `?tag=`, alternate URL variant, IPv4, backoff on 429
2. **Alternate tool** — `wget` vs `curl`, `git archive` vs API, `openssl s_client` vs python TLS, `find` vs `rg`
3. **Package registry as transport** — `pip`/`npm` reach places your `curl` cannot:
   `imageio-ffmpeg` (static ffmpeg), `faster-whisper` (models still need HF — check first), CLI wrappers
4. **Alternate remote surface** — push through a host you *can* reach (e.g. `github.com`) instead of the one you cannot
5. **Remote compute relay** — run the blocked step on a CI runner that has full internet, then fetch the
   artifacts back through git. Recipe: [`references/escalation-ladder.md`](references/escalation-ladder.md)
   → "Rung 5". Full worked YAML: repo runbook `understanding-video.md` PART 3
6. **Ask the user** — but only after 1–5, and with an exact ask: "upload the .mp4/.mp3/number, or reconnect
   GitHub; here is what I already tried and why each route failed"

**Trap (both directions):** Stopping at rung 1 and reporting "can't" — or jumping to rung 5 (using the
user's repo, their CI minutes, their data) without telling them, without a cleanup contract, and without
logging what would need deleting if the session died mid-flight. Both happened in the same session.

### 4. Triangulate, label, and never launder uncertainty

**Theory:** Every single-source conclusion inherits that source's failure modes. Independent streams
disagreeing is *signal* — the disagreement is usually the most important sentence in the report.

**Heuristic:** For any claim that matters, collect **2+ independent evidence streams**, then write down
which stream supports which claim, and keep "fact" and "inference" in separate columns.

Example from a real video analysis — four independent streams, one report:

| Stream | Tool | What it proved |
| --- | --- | --- |
| Pixels | ffmpeg frames + contact sheets | shot order, on-screen labels, no cart banner visible |
| Burned-in text | tesseract (caption band, 2× upscaled) | the same caption repeated 17×, and nothing else |
| Audio character | FFT → RMS / flatness / ZCR | *no silence anywhere* → ASMR bed + music, not a talking head |
| Words | whisper no-VAD + VAD + demucs-separated vocals | the actual narration, cross-checked across models |

**Trap:** Smoothing contradictions into a confident narrative. Real examples worth copying as anti-patterns:
the on-camera person was male but the narration was female; the caption advertised a product that never
appears in the footage; two model runs disagreed on a number ("18 days" vs "15 days"). All three were
reported **as contradictions**, with timestamps — not resolved by guessing. Print `(?)` where a word is
uncertain; a marked unknown costs nothing, an unmarked fabrication costs trust.

### 5. Persist, then hand off

**Theory:** In an ephemeral sandbox, uncommitted work does not exist. Two resets in one day deleted a
report, a video, 50 frames and five transcripts; a third nearly destroyed the only copy when the
scratch branch holding the artifacts was deleted *before* the text output was committed.

**Heuristic:**

- **Commit and push early and often.** Safety is `origin`, not the working tree. Two reset shapes show up in
  practice: a *full wipe* (untracked/ignored files vanish — recover only from pushed commits) and a *git ref
  reset* (`git log` falls back to `main` while working-tree files survive). For the second kind, keep the work:

```bash
git fetch origin '+refs/heads/*:refs/remotes/origin/*'   # a fresh clone may only track main
git reset --soft origin/<BRANCH>                          # move the ref, leave index + working tree alone
git add -A && git diff --cached --diff-filter=D --name-only   # must be empty before you commit
```
- **Two artifact tiers:**
  - *must survive* → small text (report, transcripts, logs, evidence) committed to a tracked folder,
    e.g. `analyses/<date>-<slug>/`
  - *best-effort* → heavy media (video, audio, frame dumps) in a gitignored `*-workspace/`, with the
    runbook to re-fetch it if it disappears
- **Reversibility contract for anything you borrow** (someone else's repo, CI, API quota): announce it,
  make it easy to delete, delete it when done, and report what is left over if you could not.
- **Before deleting anything, log its recoverable ID.** Deleted git branches stay fetchable by SHA for a
  while — which is how the wiped artifacts above were recovered:

```bash
git ls-remote --heads origin | grep tmp          # note the SHAs BEFORE deleting
git fetch origin <SHA>                           # later: recover a deleted branch
git archive FETCH_HEAD out | tar -x -C /tmp/art --strip-components=1
```

- **End with an explicit leftovers list** — see [`assets/handoff-template.md`](assets/handoff-template.md).
  "Done" without "what remains" is how the next session loses an hour.

**Trap:** "I'll commit at the end." Accepting "it's in a gitignored folder, so it's safe" as a durability
story. Cleaning up so thoroughly that the user cannot reproduce or verify the work.

## Priority Behaviors — what to check first

### P1. Hostile egress → route, then verify the routed artifact
A route is only real if the result is intact. After any relay or alternate download, verify
size/hash/duration (`sha256sum`, `ffprobe -show_format`, `wc -l`) — a 302 HTML error page saved as `.mp4`
looks like success to a careless script.

### P2. Missing binary → registry transport or remote compute
`command -v` first. Prefer a package that ships the binary (`pip install imageio-ffmpeg`) over building
from source; prefer remote compute over both when the binary needs system libs (tesseract, ffprobe in
some images). Record which route you took — it belongs in the handoff.

### P3. Destructive resets → durability tiers + recoverable IDs
Assume the working tree and gitignored folders can vanish between turns. Assume `pip install --user`
installs vanish too. Anything the user would be annoyed to lose belongs in a commit.

### P4. Unverifiable output → triangulate or admit it
If two independent streams cannot confirm the claim, the honest deliverable is the *raw artifact plus a
labelled caveat* ("I could not verify X; here is the audio, listen at 0:12"). Do not substitute fluency
for evidence.

## Decision Tree

```text
Something failed
│
├─ Is the failure environment-shaped? (blocked / missing / expired / reset)
│    ├─ no  → it's a logic bug: bugfix-systematic
│    └─ yes → continue
│
├─ Step 0: probe. Which hosts answer, which tools exist, which registries work?
│
├─ Blocked host?
│    ├─ need bytes from it → climb ladder 1→5 (references/escalation-ladder.md)
│    └─ need only facts (title, size, duration) → rung 1 metadata endpoint first
│
├─ Missing binary?
│    ├─ registry ships it → pip/npm install (rung 3)
│    └─ needs system libs → remote compute (rung 5) or ask the user
│
├─ Credentials expired (401 / auth failed)?
│    ├─ local git only → tell the user to reconnect; keep working locally, commit early
│    └─ required to finish → say exactly which capability is missing and what still works
│
├─ Output unverifiable by construction?
│    └─ triangulate ≥2 streams; label facts vs inference; attach raw artifacts
│
└─ Any long or borrowed-compute path?
     └─ declare the cleanup contract BEFORE starting, log recoverable IDs, end with leftovers
```

## Workflow — how an agent actually runs this skill

1. **Scan** (`agentic-code-workflow` step 1) — know the repo and the task.
2. **Probe** — run `scripts/probe-environment.sh`; save the matrix next to the work.
3. **Route** — pick the cheapest rung that answers the question; write the route down.
4. **Execute** — keep it re-runnable: a script or a workflow file in git, not a one-off shell line you
   cannot reproduce after a reset.
5. **Verify** — integrity of every fetched artifact; triangulate any claim that matters.
6. **Persist** — commit text artifacts; push; keep heavy media where the runbook can re-fetch it.
7. **Hand off** — status, evidence, leftovers, next actions (`assets/handoff-template.md`).

## Bundled resources

- `scripts/probe-environment.sh` — capability matrix (binaries, egress, python modules) with a
  registry-only/allowlist/mixed profile verdict. Run it before planning.
- `references/escalation-ladder.md` — read when blocked: the six rungs with concrete recipes,
  verification steps, cleanup contract, and the CI-relay skeleton.
- `assets/handoff-template.md` — copy into the final message when the work involved a workaround.

## Worked example (this repo, 2026-09-24)

Task: explain what is inside an X video, from a link only.
Blockers hit, in order: egress to `video.twimg.com`/`x.com` blocked (`SSLZeroReturnError`); no ffmpeg;
tesseract unavailable; HuggingFace blocked (so no local whisper/demucs); the workspace reset **twice**,
deleting local commits and a gitignored artifact folder; a temp branch was deleted before its contents
were committed elsewhere.
What the mindset produced: metadata endpoints for facts → GitHub Actions runner as remote compute
(declared, branch-per-run) → artifacts pushed to throwaway branches → `git archive` fetch back →
4-stream triangulation → report with contradictions and `(?)` markers → cleanup, plus an honest note
that one shortcut (a "safe" gitignored folder) did **not** survive a reset, and recovery of the deleted
branches by SHA.
Artifacts: `understanding-video.md` (runbook), `analyses/2026-09-24-jessievariety13-2102770102517309525/`
(committed report + transcripts + evidence).

## Closing Checklist

- [ ] Capability matrix produced and saved before the plan (not after the failure)
- [ ] Cheapest rung that answered the question was used (and I can name why heavier rungs were skipped)
- [ ] Every workaround is written down: which host/tool failed, which route replaced it
- [ ] If I borrowed compute (CI, API quota, user's repo): announced, reversible, cleaned up, leftovers listed
- [ ] Borrowed-compute artifacts: recoverable IDs (branch, SHA, run number) logged before deletion
- [ ] Any claim that matters has ≥2 independent streams; facts and inferences are separated
- [ ] Uncertain text marked `(?)`; contradictions reported instead of smoothed
- [ ] Text artifacts committed and pushed; heavy media has a documented re-fetch path
- [ ] Final message contains status, evidence pointers, and an explicit "what remains" section
