#!/usr/bin/env bash
# Scaffold a new skill in this repo: tools/new-skill.sh my-skill
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ $# -ne 1 ]; then
  echo "Usage: $(basename "$0") <skill-name>" >&2
  echo "Example: $(basename "$0") pdf-invoice-parser" >&2
  exit 1
fi

name="$1"
if ! printf '%s' "$name" | grep -Eq '^[a-z0-9]+(-[a-z0-9]+)*$'; then
  echo "Skill names must be kebab-case (lowercase letters, digits, single hyphens): $name" >&2
  exit 1
fi

dest="$repo_root/skills/$name"
if [ -e "$dest" ]; then
  echo "skills/$name already exists — pick another name or edit it in place." >&2
  exit 1
fi

mkdir -p "$dest"
sed "s/^name: my-skill$/name: $name/" \
  "$repo_root/templates/skill-template/SKILL.md" > "$dest/SKILL.md"

echo "Created skills/$name/SKILL.md"
echo
echo "Next steps:"
echo "  1. Fill in the frontmatter description (this is what makes the skill trigger)."
echo "  2. Write the body, and add scripts/ references/ assets/ only if you need them."
echo "  3. Test locally:  claude --plugin-dir \"$repo_root\""
echo "     For a full build-test-improve loop, ask Claude to use the skill-creator skill."
