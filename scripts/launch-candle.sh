#!/usr/bin/env bash
# Launch Candle in fullscreen. Reads GRBLWHEEL_CONFIG (grblwheel.conf) for optional settings.
# Called by autostart after user login. Candle does not support serial port on CLI; set it once in Candle Settings.
set -e

CONFIG="${GRBLWHEEL_CONFIG:-}"
CANDLE_INSTALL="${CANDLE_INSTALL:-$HOME/programs/Candle}"
REPO_ROOT="${GRBLWHEEL_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

if [[ -n "$CONFIG" && -f "$CONFIG" ]]; then
  # Source key=value style config (serial_port, fullscreen)
  while IFS= read -r line; do
    [[ "$line" =~ ^#.*$ ]] && continue
    if [[ "$line" =~ ^([a-zA-Z_][a-zA-Z0-9_]*)=(.*)$ ]]; then
      export "${BASH_REMATCH[1]}=${BASH_REMATCH[2]}"
    fi
  done < "$CONFIG"
fi

CANDLE_BIN=""
for d in "$CANDLE_INSTALL/bin" "$CANDLE_INSTALL"; do
  if [[ -x "$d/candle" ]]; then
    CANDLE_BIN="$d/candle"
    break
  fi
done
if [[ -z "$CANDLE_BIN" ]]; then
  echo "Candle not found under $CANDLE_INSTALL. Run scripts/setup-pi.sh first." >&2
  exit 1
fi

# Qt / Candle: try fullscreen (many Qt apps support -fullscreen or -f)
exec "$CANDLE_BIN" -fullscreen "$@"
