#!/usr/bin/env bash
# Run at boot by grblwheel-update.service. Check GrblWheel repo for updates;
# if we are behind origin/main, pull, re-run setup-pi.sh, and reboot.
set -e

REPO_ROOT="${GRBLWHEEL_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$REPO_ROOT"

# Default branch to track (main or master)
BRANCH="main"
git show-ref -q "refs/heads/master" 2>/dev/null && BRANCH="master" || true

REMOTE="${GRBLWHEEL_REMOTE:-origin}"
REMOTE_URL="${GRBLWHEEL_REPO:-https://github.com/StevenGann/GrblWheel}"

# Ensure remote is set
if ! git remote get-url "$REMOTE" &>/dev/null; then
  git remote add "$REMOTE" "$REMOTE_URL" 2>/dev/null || true
fi

git fetch "$REMOTE" "$BRANCH" 2>/dev/null || { echo "GrblWheel update check: fetch failed (no network?)." >&2; exit 0; }
LOCAL=$(git rev-parse "refs/heads/$BRANCH" 2>/dev/null || echo "none")
REMOTE_REF=$(git rev-parse "refs/remotes/$REMOTE/$BRANCH" 2>/dev/null || echo "none")

if [[ "$LOCAL" != "none" && "$REMOTE_REF" != "none" && "$LOCAL" != "$REMOTE_REF" ]]; then
  echo "GrblWheel: new version available; updating and rebooting..."
  git pull "$REMOTE" "$BRANCH" --no-edit
  "$REPO_ROOT/scripts/setup-pi.sh"
  echo "GrblWheel: re-running setup complete; rebooting..."
  sudo reboot
fi
exit 0
