#!/usr/bin/env bash
# Install the Factory skill suite into your Claude Code user skills directory.
set -euo pipefail

DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/skills" && pwd)"

echo "Installing Factory skills"
echo "  from: $SRC"
echo "  to:   $DEST"
mkdir -p "$DEST"

ts="$(date +%Y%m%d-%H%M%S)"
for skill in "$SRC"/*/; do
  name="$(basename "$skill")"
  target="$DEST/$name"
  if [ -e "$target" ]; then
    backup="$target.bak-$ts"
    echo "  • $name (existing → backed up to $(basename "$backup"))"
    mv "$target" "$backup"
  else
    echo "  • $name"
  fi
  cp -r "$skill" "$target"
done

echo
echo "Done. Installed: $(find "$SRC" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ') skills."
echo "Start in any repo with:  /factory-intake   (then later)  /goal /factory-execute <issue>"
