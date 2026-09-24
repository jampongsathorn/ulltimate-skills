#!/usr/bin/env bash
# scan-repo.sh — Systematic repo scan for agentic-code-workflow step 1
set -e
ROOT="${1:-.}"

echo "=== Repo Scan: $ROOT ==="
echo
echo "--- top files ---"
find "$ROOT" -type f -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/dist/*" -not -path "*/__pycache__/*" -not -path "*/.next/*" | head -40

echo
echo "--- root ls ---"
ls -la "$ROOT" | head -40

echo
echo "--- AGENTS.md / CLAUDE.md / README ---"
for f in AGENTS.md CLAUDE.md README.md; do
  if [ -f "$ROOT/$f" ]; then
    echo "== $f (first 50 lines) =="
    head -50 "$ROOT/$f"
    echo
  fi
done

echo "--- plugin manifests ---"
cat "$ROOT/.claude-plugin/plugin.json" 2>/dev/null || echo "no plugin.json"
echo
cat "$ROOT/.claude-plugin/marketplace.json" 2>/dev/null | head -50 || echo "no marketplace.json"

echo
echo "--- package / python ---"
cat "$ROOT/package.json" 2>/dev/null | head -30 || echo "no package.json"
cat "$ROOT/pyproject.toml" 2>/dev/null | head -30 || echo "no pyproject.toml"

echo
echo "--- validate (if claude available) ---"
if command -v claude >/dev/null 2>&1; then
  claude plugin validate "$ROOT" 2>&1 | tail -20
else
  echo "claude CLI not found"
fi
