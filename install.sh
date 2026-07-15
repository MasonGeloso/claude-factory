#!/usr/bin/env bash
# Install the Factory skill suite into your Claude Code user skills directory.
# Thin wrapper around the Factory CLI (bin/factory). For agents and updates use
# the CLI directly:  bin/factory update   |   bin/factory agents install ai-pm
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 is required to run the Factory CLI." >&2
  exit 1
fi

exec python3 "$HERE/bin/factory" install

# Tip: symlink the CLI onto your PATH so you can run `factory ...` anywhere:
#   ln -sf "$HERE/bin/factory" ~/.local/bin/factory
