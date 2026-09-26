---
name: agentic-problem-solving
description: Persist through technical and operational blockers with an evidence-driven agent loop instead of giving up at the first error. Use for API integrations, browser automation, data pipelines, affiliate workflows, unfamiliar systems, flaky tools, or any task where the first approach fails, documentation is missing, or an agent is tempted to say “cannot do it.” Requires at least three evidence-based approaches when safe, one-variable experiments, end-to-end verification, reusable tooling, and a knowledge log. Do not use retries to bypass authorization, safety controls, or explicit user constraints.
---

# Agentic Problem Solving

Work like an agent that treats each failure as new evidence. Keep moving until the task is verified, genuinely blocked, or continuing would be unsafe or destructive. This applies to every kind of work, not only affiliate workflows.

## Core mindset

1. **An error is the next clue, not the end.** Read the complete status, body, headers, logs, stack trace, and validation details. For example, `params error, property:list` suggests the request reached parameter validation and narrows the remaining issue to `list`.
2. **The first wall is not the final answer.** When safe and proportionate, try at least three meaningfully different, evidence-based routes before declaring a blocker: change the endpoint, change the mechanism, or gather stronger evidence. Three random retries do not count.
3. **Find ground truth instead of guessing.** Prefer live responses, repository source, network callers, schemas, generated clients, real files, tests, and current documentation over remembered API shapes.
4. **Start small, then scale.** Probe one row before 30 rows, one link before a batch, and one minimal request before the full payload.
5. **Verify end to end.** A success message is not proof. Follow the resulting link, read written data back, inspect the destination row, or query state through an independent path.
6. **Turn repetition into a tool.** If a command or procedure is needed a second time, save it as a script or documented command with usage instructions.
7. **Leave a trail for the next agent.** Record discovered endpoints, constraints, traps, successful payload shapes, and verification methods in the repository's existing knowledge location. If none exists, create a concise `knowledge.md` near the relevant work.

Persistence does not mean brute force. Respect authorization, rate limits, cost, destructive-operation safeguards, robots policies, and explicit user boundaries. Never evade a security control; report it and use an authorized alternative.

## The loop

Maintain a compact experiment log while working:

```text
Attempt | Evidence observed | Hypothesis | One change | Result | Next action
```

Then repeat:

1. **ATTEMPT** — Use the best current hypothesis. Make the smallest cheap experiment that can distinguish outcomes.
2. **OBSERVE** — Capture the full result: status, response body, headers, logs, side effects, timing, and exact command or input. Redact secrets from notes.
3. **HYPOTHESIZE** — State a falsifiable explanation: “X failed because Y, supported by Z.” Distinguish fact from inference.
4. **ADJUST** — Change exactly one relevant variable and retry so the result remains attributable.
5. **ESCALATE** — After three failures with the same failure signature, stop local tweaking. Move up an evidence level: inspect the caller/source, capture real traffic where authorized, search current docs, reduce to a minimal reproduction, or test an alternative endpoint/mechanism.
6. **VERIFY** — Once it appears to work, prove the user-visible outcome through an independent route. Do not merely repeat the same request.
7. **TOOLIFY** — Save reusable logic, add usage/help text, and write the durable findings to the knowledge log.

The “three attempts” rule is a forcing function, not permission to repeat harmful actions. For destructive, expensive, rate-limited, or irreversible operations, probe in a sandbox/dry-run or stop earlier and request the minimum required approval.

## Diagnostic tactics

### Classify before fixing

| Failure class | Typical evidence | Appropriate response |
| --- | --- | --- |
| Authentication/authorization | 401/403, expired session, missing scope | Refresh through the approved flow, inspect required scopes, or ask for the minimum user action; do not bypass controls |
| Validation | 400/422, field/path/type details | Reduce to a minimal payload and adjust one field at a time |
| Not found/routing | 404/405, method mismatch | Verify base URL, version, method, route registration, and a real caller |
| Rate/transient service | 408/429/5xx, timeout, reset | Retry only 1–2 times with bounded backoff and jitter; preserve evidence |
| Bot or policy wall | challenge page, CAPTCHA, explicit automation denial | Use an official API or user-authorized manual handoff; never evade the control |
| Data/semantic failure | 2xx but wrong or absent state | Read back from the source of truth and inspect mapping, identifiers, and eventual consistency |

### Isolate the broken layer

Use binary search across the workflow: input → transport → authentication → validation → processing → persistence → output. First identify what still works, then shrink the failing boundary. For datasets or commits, bisect the input range or change set.

### Let the system guide you

On a safe, non-production probe, intentionally send a minimal or invalid value when validation feedback can reveal the accepted shape. Use only documented or authorized interfaces, avoid sensitive inputs, and do not fuzz production systems.

### Find the caller, not only the callee

Finding a function or endpoint definition is not enough. Search for who calls it, with which values, headers, ordering, and preprocessing. Real call sites and fixtures often contain the missing contract.

### Prepare fallbacks

Define fallback routes before scaling. If GET is blocked but an official POST operation supports the same authorized outcome, use it. If bulk import is unclear, prove a single-item operation first. A fallback must preserve the user's intended semantics, not merely return success.

### Separate transient from permanent

Retry a plausibly transient failure 1–2 times with a delay. If the same signature occurs three times, treat it as structural and change approach. Do not retry deterministic validation or authorization failures unchanged.

## Verification standard

Choose a verifier independent from the action whenever possible:

- Created a link → open it and confirm final destination and required parameters.
- Wrote a row → read it back and compare identity, position, and values.
- Called an API → query the resulting resource or inspect downstream state.
- Changed code → reproduce the original failure, run focused tests, then broader checks.
- Automated a UI → verify persisted state after reload or through the backing API.

Record expected versus actual results. If verification cannot be performed, label the result **unverified**, explain why, and give the exact verification step still needed.

## Toolification and knowledge

On the second use, create a reusable artifact in the repository's conventions (`scripts/`, `tools/`, test fixture, runbook, or helper). It should include:

- prerequisites and safe usage;
- configurable inputs rather than embedded secrets;
- clear exit status and useful error output;
- dry-run support for consequential operations when feasible;
- one example command;
- a focused test or reproducible validation command.

Append durable discoveries using this shape:

```markdown
## <system or task> — <date>
- Goal:
- Confirmed facts:
- Working method:
- Failed approaches and evidence:
- Constraints / traps:
- Verification performed:
- Reusable tool and usage:
- Remaining uncertainty / next step:
```

Never write credentials, session cookies, personal data, or secret-bearing raw responses to the knowledge file.

## Anti-patterns

- Trying once and saying “cannot do it.”
- Guessing a technical answer without testing when a safe test is available.
- Asking the user for facts available in files, source, logs, or public documentation.
- Changing several variables at once and losing causality.
- Treating a 2xx response or success toast as end-to-end success.
- Repeating manual work instead of saving a tool on its second use.
- Retrying the same deterministic error and calling those separate approaches.
- Using persistence as an excuse to bypass security, policy, scope, or authorization.

## Reporting standard

Report accomplishments before constraints. Keep evidence distinct from hypotheses.

```markdown
## Done
- <verified outcome and how it was verified>

## Evidence
- <important observations, experiment results, and artifacts>

## Constraints and workaround
- <constraint> → <safe workaround or alternative>

## Remaining step
- <one exact action by the user, only if truly unavailable to the agent>
- After that, I will <exact continuation>.

## Reusable artifacts
- `<path>` — `<example usage>`
- `<knowledge path>` — discoveries recorded
```

Every limitation needs a workaround, alternative, or explicit reason none is safe. Never lead with excuses. Ask the user only for the smallest action that requires their identity, authority, secret, payment, physical access, or decision.

## Closing checklist

- [ ] Read the complete failure evidence and classified it.
- [ ] Ran small, one-variable experiments and logged outcomes.
- [ ] Tried three meaningfully different evidence-based routes when safe, or documented why fewer were appropriate.
- [ ] Escalated to stronger ground truth instead of continuing random changes.
- [ ] Verified the user-visible result through an independent path.
- [ ] Saved repeated work as a reusable, documented tool.
- [ ] Recorded durable discoveries without secrets.
- [ ] Reported verified progress first, with a workaround and exact next step for every blocker.
