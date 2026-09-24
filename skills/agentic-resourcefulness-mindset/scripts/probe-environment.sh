#!/usr/bin/env bash
# probe-environment.sh — build a capability matrix BEFORE you plan.
#
# Answers three questions in one shot:
#   1. which binaries exist here?
#   2. which hosts can this sandbox actually reach (TLS handshake)?
#   3. which package registries / python modules work?
#
# Usage:
#   scripts/probe-environment.sh                                  # markdown to stdout
#   scripts/probe-environment.sh --out probe/capability-matrix.md
#   scripts/probe-environment.sh --hosts "api.github.com,pypi.org" --timeout 2
#   scripts/probe-environment.sh --quiet                          # summary lines only
#
# Exit code is always 0: this is an information tool, not a gate.
# No dependencies beyond bash + (python3 or openssl).

set -uo pipefail

HOSTS_DEFAULT="github.com api.github.com codeload.github.com raw.githubusercontent.com objects.githubusercontent.com pypi.org files.pythonhosted.org registry.npmjs.org huggingface.co cdn.jsdelivr.net unpkg.com video.twimg.com pbs.twimg.com x.com api.fxtwitter.com deb.debian.org archive.ubuntu.com"
TOOLS_DEFAULT="git curl wget jq rg ffmpeg ffprobe python3 pip3 node npm tesseract gh docker unzip tar openssl sqlite3 pandoc pdftotext claude"
PYMODS_DEFAULT="requests numpy pandas PIL yaml bs4 faster_whisper torch cv2"

HOSTS="$HOSTS_DEFAULT"
TOOLS="$TOOLS_DEFAULT"
PYMODS="$PYMODS_DEFAULT"
TIMEOUT=3
OUT=""
QUIET=0

while [ $# -gt 0 ]; do
  case "$1" in
    --hosts)   HOSTS="${2//,/ }"; shift 2 ;;
    --tools)   TOOLS="${2//,/ }"; shift 2 ;;
    --pymods)  PYMODS="${2//,/ }"; shift 2 ;;
    --timeout) TIMEOUT="${2:-3}"; shift 2 ;;
    --out)     OUT="${2:-}"; shift 2 ;;
    --quiet)   QUIET=1; shift ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 0 ;;
  esac
done

# ---------------------------------------------------------------- helpers
have() { command -v "$1" >/dev/null 2>&1; }
tmo()  { if have timeout; then timeout "$@"; else "$@"; fi; }

version_of() {
  case "$1" in
    ffmpeg|ffprobe) tmo 5 "$1" -version 2>/dev/null | head -1 ;;
    python3)        tmo 5 python3 --version 2>&1 | head -1 ;;
    openssl)        tmo 5 openssl version 2>&1 | head -1 ;;
    unzip)          tmo 5 unzip -v 2>/dev/null | head -1 ;;
    gh)             tmo 5 gh --version 2>&1 | head -1 ;;
    *)              tmo 5 "$1" --version 2>&1 | head -1 ;;
  esac
}

# probe one host; prints "ALLOWED" or "BLOCKED:<reason>"
probe_host() {
  local host="$1"
  if have python3; then
    python3 - "$host" "$TIMEOUT" <<'PY' 2>/dev/null
import socket, ssl, sys
host, t = sys.argv[1], float(sys.argv[2])
try:
    ctx = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=t) as s:
        with ctx.wrap_socket(s, server_hostname=host):
            print("ALLOWED")
except Exception as e:
    print("BLOCKED:" + type(e).__name__)
PY
  elif have openssl; then
    if tmo "$TIMEOUT" openssl s_client -connect "${host}:443" -servername "$host" </dev/null >/dev/null 2>&1; then
      echo "ALLOWED"
    else
      echo "BLOCKED:openssl"
    fi
  else
    echo "UNKNOWN:no-probe-tool"
  fi
}

now="$(date -u '+%Y-%m-%d %H:%M UTC')"

# ---------------------------------------------------------------- collect
tools_present=""; tools_missing=""
for t in $TOOLS; do
  if have "$t"; then tools_present="$tools_present $t"; else tools_missing="$tools_missing $t"; fi
done

pymods_present=""; pymods_missing=""
if have python3; then
  for m in $PYMODS; do
    # find_spec avoids import side effects and is fast
    if tmo 5 python3 -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('$m') else 1)" >/dev/null 2>&1; then
      pymods_present="$pymods_present $m"
    else
      pymods_missing="$pymods_missing $m"
    fi
  done
fi

allowed=""; blocked=""
for h in $HOSTS; do
  res="$(probe_host "$h")"
  case "$res" in
    ALLOWED) allowed="$allowed $h" ;;
    *)       blocked="$blocked $h" ;;
  esac
done

# egress profile
n_allowed=$(printf '%s' "$allowed" | wc -w | tr -d ' ')
n_blocked=$(printf '%s' "$blocked" | wc -w | tr -d ' ')

registry_only=1
for h in $allowed; do
  case "$h" in
    pypi.org|registry.npmjs.org|files.pythonhosted.org|github.com|api.github.com|codeload.github.com) ;;
    *) registry_only=0 ;;
  esac
done

if [ "$n_blocked" -eq 0 ]; then
  profile="open — you can fetch directly; still record the matrix"
elif [ "$registry_only" -eq 1 ] && [ "$n_allowed" -gt 0 ]; then
  profile="registry-only allowlist — download via pip/npm, and relay anything else through remote compute (see references/escalation-ladder.md)"
else
  profile="mixed — some hosts reachable; route per host, prefer the cheapest reachable one"
fi

# ---------------------------------------------------------------- render
render() {
  echo "# Capability matrix"
  echo
  echo "Probed: ${now} · timeout ${TIMEOUT}s"
  echo
  echo "## Egress (TLS 443)"
  echo
  echo "| host | reachable |"
  echo "| --- | --- |"
  for h in $HOSTS; do
    if printf '%s' "$allowed" | grep -qw "$h"; then echo "| $h | yes |"; else echo "| $h | NO |"; fi
  done
  echo
  echo "**Profile:** $profile"
  echo
  echo "## Binaries"
  echo
  echo "| tool | present | version |"
  echo "| --- | --- | --- |"
  for t in $TOOLS; do
    if have "$t"; then
      v="$(version_of "$t" | cut -c1-60)"
      echo "| $t | yes | ${v:-?} |"
    else
      echo "| $t | NO | — |"
    fi
  done
  echo
  echo "## Python modules"
  echo
  echo "present:${pymods_present:- none}"
  echo
  echo "missing:${pymods_missing:- none}"
  echo
  echo "## Read this as"
  echo
  echo "- Missing binary that a package registry can ship (ffmpeg → \`pip install imageio-ffmpeg\`, tesseract → remote compute)"
  echo "- Blocked host that matters → climb the escalation ladder, don't retry the same call"
  echo "- Everything blocked → ask the user for the artifact; say exactly what you tried"
  echo "- Installs made with \`pip install --user\` / \`npm -g\` live outside the repo and **can vanish on a workspace reset** — re-run this probe after any reset, and put anything reproducible into git instead"
}

if [ "$QUIET" -eq 0 ]; then
  if [ -n "$OUT" ]; then
    mkdir -p "$(dirname "$OUT")"
    render | tee "$OUT"
    echo >&2
    echo "written: $OUT" >&2
  else
    render
  fi
fi

{
  echo "---"
  echo "tools present:$(printf '%s' "$tools_present" | sed 's/ / /g')"
  echo "tools missing:$(printf '%s' "$tools_missing" | sed 's/ / /g')"
  echo "hosts allowed:$allowed"
  echo "hosts blocked:$blocked"
  echo "profile: $profile"
} >&2

exit 0
