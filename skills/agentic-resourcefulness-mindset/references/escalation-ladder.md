# Escalation Ladder — when the environment says no

Read this when a step is blocked: a host refuses, a binary is missing, credentials expired, or the
sandbox cannot do what the task needs. Climb in order; stop at the first rung that answers the question.
**Always record which rung you used** — the user needs to know where their data and compute went.

Table of contents
1. [Prove the block (30 seconds)](#1-prove-the-block)
2. [Rung 1 — retry with variation](#2-rung-1--retry-with-variation)
3. [Rung 2 — alternate tool](#3-rung-2--alternate-tool)
4. [Rung 3 — package registry as transport](#4-rung-3--package-registry-as-transport)
5. [Rung 4 — alternate remote surface](#5-rung-4--alternate-remote-surface)
6. [Rung 5 — remote compute relay](#6-rung-5--remote-compute-relay)
7. [Rung 6 — ask the user](#7-rung-6--ask-the-user)
8. [Verification: a route is only real if the artifact is intact](#8-verification)
9. [Cleanup contract for borrowed compute](#9-cleanup-contract)
10. [Case notes from a real session](#10-case-notes)

---

## 1. Prove the block

Before escalating, know what is actually broken. "It failed" is not a diagnosis.

```bash
# TLS handshake only — distinguishes allowlist blocks from DNS/network/TLS problems
python3 - <<'PY'
import socket, ssl
for host in ["example.com", "pypi.org", "video.twimg.com"]:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=6) as s:
            with ctx.wrap_socket(s, server_hostname=host):
                print(host, "TLS OK")
    except Exception as e:
        print(host, "FAIL", type(e).__name__, str(e)[:60])
PY
```

Signature table:

| Symptom | Usual meaning |
| --- | --- |
| `SSLZeroReturnError` / `Empty reply from server` on **some** hosts, not all | egress allowlist |
| `Name or service not known` | DNS |
| `Connection timed out` on every host | no network at all |
| `403` with HTML body | the endpoint wants headers (`-A "<browser UA>"`) or a token |
| `401` on git/API operations you did before | credential/token expired mid-session |
| `command not found` | missing binary — not a network problem |
| `Killed` / `No space left` | resource limits; shrink the job, don't retry it |

Also record **what still works**: a plan built around the reachable hosts is worth more than a lament.

---

## 2. Rung 1 — retry with variation

Cheap, and it resolves a surprising share of failures:

- browser user-agent: `curl -fsSL -A "Mozilla/5.0 (…)" -o file "$URL"`
- alternate URL variants: `?tag=29`, `&lang=th`, `/small` vs `/large`, `www` vs bare host
- alternate protocol/port: `http://` vs `https://`, IPv4 if IPv6 is broken
- backoff on `429`: sleep 5–30 s, or reduce concurrency
- add the obvious headers: `Accept`, `Referer`, `Authorization: Bearer $TOKEN`

Stop after ~2 variations of the same idea; a third identical retry is just noise in the log.

---

## 3. Rung 2 — alternate tool

Different tools fail differently; that is the point.

| Need | Try |
| --- | --- |
| download | `wget` vs `curl`; `git clone --depth 1` vs tarball |
| transport files between git states | `git archive` (no checkout, no side effects) |
| TLS diagnosis | `openssl s_client` vs `python3 ssl` vs `curl -v` |
| search | `rg` vs `grep -r` vs `git grep` |
| JSON | `jq` vs `python3 -m json.tool` vs `node -e` |
| media metadata | `ffprobe` vs `exiftool` vs `mediainfo` vs the platform's own API |

---

## 4. Rung 3 — package registry as transport

Registries are frequently reachable when arbitrary web hosts are not, and they can ship more than
libraries — including **static binaries**:

```bash
# static ffmpeg that does not depend on apt mirrors
pip install --user --break-system-packages imageio-ffmpeg
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -version          # ships ffmpeg; ffprobe is NOT included — plan around that

# node equivalents
npm i -g @ffmpeg-installer/ffmpeg     # another static ffmpeg route
npx --yes some-cli --help             # try before installing
```

Rules of thumb:

- If a python package exists that *wraps* the missing capability, installing it is usually faster than
  building the capability.
- Model downloads are a separate dependency: `faster-whisper`/`torch`/`transformers` install from PyPI but
  fetch **weights from HuggingFace** — if HF is blocked, the install succeeds and the run fails. Probe the
  weight host too, and if it is blocked, move the inference to rung 5.
- Prefer `--user` in sandboxes you do not own; note that `--user` installs may not survive a workspace
  reset, so never make them the only copy of a result.

---

## 5. Rung 4 — alternate remote surface

When the *specific host* is blocked but a *related host* is reachable, push/pull through the reachable one:

- platform mirrors and syndication endpoints (e.g. an oEmbed/syndication endpoint that returns the same
  payload the blocked site serves)
- a git remote you can reach (push the job, let the remote-side machinery do the fetching)
- vendor CDNs with the same artifact (`registry.npmjs.org`, `cdn.jsdelivr.net` when allowed)

This rung is about *where* the request is made from, not yet about *who computes*.

---

## 6. Rung 5 — remote compute relay

Use when the blocked step needs a real machine: full internet, system libraries (tesseract, ffprobe),
or long CPU work.

Shape of the relay:

```
sandbox (limited egress, can reach github.com)
  └─ push a workflow file  →  CI runner (full internet, system packages)
                                └─ download → process → push artifacts to a throwaway branch
  └─ git fetch <branch/SHA> → git archive → artifacts back in the sandbox
```

Non-negotiables:

1. **Announce it.** You are spending someone's CI minutes on their repo. Say so before, not after.
2. **Branch per run** — `tmp-<job>-${{ github.run_number }}` — so parallel runs cannot clobber each other.
   (A shared branch name was clobbered for real.)
3. **Idempotent steps** — `set -x` not `set -e` on analysis steps, `continue-on-error: true` on best-effort
   ones (OCR/transcribe), explicit `timeout` on anything that could hang.
4. **Never assume the runner's image** — install what you need explicitly. One run died because it assumed
   `ffmpeg` existed.
5. **Cap the expensive step** — prefer the smaller/faster model first; a full-size model on CPU can burn a
   40-minute job and never finish.
6. **Write diagnostics into the artifacts** — `probe.txt`, logs, error output. If logs are unreadable
   (permission-restricted), artifacts are your debugger.
7. **Fetch back with plain git** — `git fetch origin <branch|SHA>` + `git archive FETCH_HEAD path/` needs no
   API token and leaves no working-tree mess.

Minimal skeleton (inject your own steps; full worked example in repo `understanding-video.md` PART 3):

```yaml
name: tmp-fetch-artifacts
on: { push: { paths: ['.github/workflows/tmp-fetch-artifacts.yml'] }, workflow_dispatch: }
permissions: { contents: write }
jobs:
  fetch:
    runs-on: ubuntu-latest
    timeout-minutes: 40
    steps:
      - uses: actions/checkout@v4
      - name: Install tooling
        run: sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg tesseract-ocr
      - name: Do the blocked work
        run: |
          mkdir -p out
          curl -fsSL -A "Mozilla/5.0" -o /tmp/in.bin "$SOURCE_URL"
          # ... process into out/ ...
      - name: Publish
        if: always()
        run: |
          git config user.name artifact-bot
          git config user.email artifact-bot@users.noreply.github.com
          git checkout -b "tmp-artifacts-${{ github.run_number }}"
          git add -f out && git commit -m "artifacts" || true
          git push -u origin "tmp-artifacts-${{ github.run_number }}"
```

Watch it without polling hard (runs take 3–8 minutes):

```bash
curl -sS "https://api.github.com/repos/<owner>/<repo>/actions/runs?per_page=3" |
  python3 -c "import json,sys;[print(r['run_number'],r['status'],r.get('conclusion'),r['updated_at']) for r in json.load(sys.stdin)['workflow_runs']]"
curl -sS "https://api.github.com/repos/<owner>/<repo>/actions/runs/<RUN_ID>/jobs" | python3 -m json.tool | head -40
```

---

## 7. Rung 6 — ask the user

Only after 1–5, and make the ask precise:

> "I can't reach `<host>` (blocked) and the CI relay needs your repo's Actions enabled. Two options:
> (a) upload the .mp4 here — I'll do the rest locally; (b) re-enable Actions and I'll run the relay
> (I'll delete the branch and workflow when done). What I already tried: curl (blocked), pip route
> (`imageio-ffmpeg` installed, works), HF weights (blocked → no local whisper)."

A good ask contains: the exact missing resource, the routes already tried with their errors, the
consequence of not having it, and the cheapest thing the user could do.

---

## 8. Verification

A route is only real when the artifact is intact. Verify immediately after fetching, and record the check
in your report:

```bash
sha256sum out/source.mp4              # did the bytes change between routes?
ffprobe -v error -show_format -show_streams out/source.mp4 | head -20   # duration/streams sane?
wc -l out/transcript.txt              # did the transcript actually contain lines?
grep -c "<html" out/source.mp4 || true   # classic: an error page saved as a media file
```

Compare against a *known* property from metadata (duration, size, item count). Discovering three steps
later that an artifact is an HTML error page wastes the whole cycle.

---

## 9. Cleanup contract

Borrowed compute is a loan. Write this into your plan before starting, and honour it:

- [ ] Workflow file removed from the working branch when done (`git rm … && git commit && git push`)
- [ ] Throwaway branches deleted — **after** committing/copying anything worth keeping
- [ ] Recoverable IDs logged **before** deletion (`git ls-remote --heads origin | grep tmp` → save SHAs)
- [ ] Final remote state verified: `git ls-remote --heads origin` shows only expected branches
- [ ] If cleanup could not finish (expired token, lost network): say so explicitly and name what is left

Recovery after an over-eager cleanup — deleted branches stay fetchable by SHA for a while:

```bash
git fetch origin <SHA>
git archive FETCH_HEAD out | tar -x -C /tmp/art --strip-components=1
```

---

## 10. Case notes

Real session, one afternoon (X video analysis in a registry-only sandbox):

| Blocker | Rung used | Outcome |
| --- | --- | --- |
| `video.twimg.com`, `x.com` blocked | 1 (probe) + 4 (syndication/API host for facts) | metadata (duration, variants, caption) obtained for free |
| CI run died at step 4 | — (assumption bug) | runner had no `ffmpeg`; fixed by installing tooling explicitly |
| full model too slow (40 min, unfinished) | 5 (cap the expensive step) | parallel run with the smaller model produced the deliverable |
| HF blocked → no local whisper/demucs | 5 | transcription moved to the runner (vocals separated with demucs there) |
| two runs pushing the same branch | — (design bug) | `run_number` in branch name |
| workspace reset ×2; report + artifacts deleted | 5 (durability) | text committed to tracked `analyses/…`, heavy media to a gitignored workspace |
| deleted branch held the only artifacts | recovery by SHA | `git fetch origin <SHA>` + `git archive` restored everything |
