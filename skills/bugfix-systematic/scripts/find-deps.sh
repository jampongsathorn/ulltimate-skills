#!/usr/bin/env bash
# find-deps.sh — Find all files that depend on a given file or symbol
# Usage: ./find-deps.sh <file-or-symbol> [root]
# Example: ./find-deps.sh utils.ts src/
#          ./find-deps.sh buggyFunc

set -e
TARGET="${1:?Usage: $0 <file-or-symbol> [root]}"
ROOT="${2:-.}"

echo "=== Searching for usages of: $TARGET in $ROOT ==="
echo

echo "--- rg search (generic) ---"
rg -n "$TARGET" --type js --type ts --type tsx --type jsx --type py "$ROOT" 2>/dev/null | head -100 || echo "rg not found or no matches"

echo
echo "--- import search (JS/TS) ---"
rg -n "from ['\"].*$TARGET|import.*$TARGET|require.*$TARGET" --type js --type ts --type tsx "$ROOT" 2>/dev/null | head -100 || true

echo
echo "--- import search (Python) ---"
rg -n "from.*$TARGET import|import.*$TARGET" --type py "$ROOT" 2>/dev/null | head -100 || true

echo
echo "--- circular deps (JS/TS) if madge available ---"
if command -v npx >/dev/null 2>&1; then
  npx --yes madge --circular --extensions js,ts,tsx,jsx "$ROOT" 2>&1 | head -50 || echo "madge check failed or no circular deps"
else
  echo "npx not available, skipping madge"
fi

echo
echo "=== Done. Write impacted files to /tmp/impacted.txt ==="
echo "Tip: rg -n \"$TARGET\" | cut -d: -f1 | sort -u > /tmp/impacted.txt"
