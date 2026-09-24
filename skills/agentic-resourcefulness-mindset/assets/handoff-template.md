# Handoff template

Copy this into the final message whenever the work involved a workaround, borrowed compute, routed
fetch, or anything you could not verify directly. Delete sections that genuinely do not apply — but
**never** delete *Leftovers* or *Verification*, and never present an inferred result as a fact.

---

## Status
One line: what is done and where it lives. Example:
"Draft report written and pushed to `analyses/2026-09-24-<slug>/report.md` (commit `abc1234`)."

## What I did (route taken)
- Blocked: `<host/tool>` failed with `<exact error>`.
- Route used: rung `<n>` — `<one-line description>` (e.g. "rung 5: CI relay on a runner with full internet").
- If compute was borrowed: state whose (repo/CI/API quota) and that it has been / will be cleaned up.

## Evidence
Pointers, not adjectives. Each claim gets a source the user can open:

| Claim | Evidence | Confidence |
| --- | --- | --- |
| `<claim>` | `path/to/file` (line/timestamp), or URL | verified / single-source / inferred |

- Independent streams used: `<e.g. pixels + OCR + spectrum + transcript>`
- Raw artifacts kept: `<paths>`
- Marked uncertainties: `<list of (?) spots, with timestamps>`

## Verification
- Integrity checks run: `<sha256 / duration / line counts / spot-check>` → result.
- What I could **not** verify, and why. Offer the cheapest way for the user to check it themselves
  (e.g. "listen at 0:12 of `media/audio.mp3`").

## Leftovers
Explicit, ordered, and honest:
- [ ] `<branch/tag/file still present>` — why, and whether it is safe to delete
- [ ] `<capability still missing>` (e.g. GitHub token expired → reconnect needed before I can clean up)
- [ ] `<decision the user must make>`

If nothing is left over, say "nothing outstanding" — do not leave it implicit.

## Next actions (optional)
Only if the user asked for a plan or the work naturally continues. Max 3 items, each one concrete.

---

### Anti-patterns this template exists to prevent

- "Done ✅" with no path, no commit, no evidence.
- A confident summary of something seen only through one unverified source.
- Silent use of someone's CI/repo/quota.
- Cleanup that removed the evidence, or leftovers that were never mentioned.
- Rounding a contradiction away instead of reporting it ("18 or 15 days" → pick one and move on).
