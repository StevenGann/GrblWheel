#!/bin/bash
# Pull latest GrblWheel from GitHub and run the install script.
# Run from repo root: ./scripts/update-pi.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [ ! -d .git ]; then
  echo "Not a git repo. Clone GrblWheel first, then run this script." >&2
  exit 1
fi

echo "=== GrblWheel update ==="
echo "Repo: $REPO_ROOT"
git pull
echo ""
echo "Running install script..."
exec "$REPO_ROOT/scripts/install-pi.sh"
