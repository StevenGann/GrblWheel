#!/bin/sh
# Disable screen blanking and start Chromium in kiosk mode for GrblWheel UI.
# Run after X is up (graphical.target). Assumes backend is at http://127.0.0.1:8765

export DISPLAY=${DISPLAY:-:0}

# Disable screen blanking and power management
xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true
xset s noblank 2>/dev/null || true

# Optional: hide cursor (uncomment if desired)
# which unclutter >/dev/null 2>&1 && unclutter -idle 1 &

URL="http://127.0.0.1:8765/"

# Chromium kiosk: no decorations, fullscreen, app mode
exec chromium-browser \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --no-first-run \
  --start-fullscreen \
  --app="$URL"
