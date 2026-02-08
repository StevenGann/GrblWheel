#!/bin/bash
# GrblWheel Pi install script. Run from repo root: ./scripts/install-pi.sh
# Or from anywhere: /path/to/GrblWheel/scripts/install-pi.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== GrblWheel install (Pi) ==="
echo "Repo: $REPO_ROOT"

# Python venv and package
echo ""
echo "--- Python ---"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "Created .venv"
fi
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -e ".[gpio]"
echo "Python deps installed (with GPIO support)."

# Config
echo ""
echo "--- Config ---"
if [ ! -f "config/config.yaml" ]; then
  cp config/config.example.yaml config/config.yaml
  echo "Created config/config.yaml (edit as needed)."
else
  echo "config/config.yaml already exists."
fi

# Frontend (optional if npm available)
echo ""
echo "--- Frontend ---"
if command -v npm >/dev/null 2>&1; then
  cd frontend
  npm install --silent
  npm run build
  cd "$REPO_ROOT"
  echo "Frontend built."
else
  echo "npm not found; skipping frontend build. Copy frontend/dist from another machine or install Node.js."
fi

# systemd: substitute repo path and install
echo ""
echo "--- systemd ---"
SED_EXPR="s|/home/pi/GrblWheel|$REPO_ROOT|g"
mkdir -p /tmp/grblwheel-systemd
sed "$SED_EXPR" systemd/grblwheel.service > /tmp/grblwheel-systemd/grblwheel.service
sed "$SED_EXPR" systemd/grblwheel-kiosk.service > /tmp/grblwheel-systemd/grblwheel-kiosk.service
sudo cp /tmp/grblwheel-systemd/grblwheel.service /tmp/grblwheel-systemd/grblwheel-kiosk.service /etc/systemd/system/
rm -rf /tmp/grblwheel-systemd
chmod +x systemd/kiosk.sh
echo "systemd units installed (path set to $REPO_ROOT)."

sudo systemctl daemon-reload
sudo systemctl enable grblwheel
sudo systemctl enable grblwheel-kiosk
sudo systemctl start grblwheel
echo "Backend enabled and started."

# Kiosk only starts if graphical.target is active
if [ -n "$DISPLAY" ] || systemctl is-active graphical.target >/dev/null 2>&1; then
  sudo systemctl start grblwheel-kiosk 2>/dev/null || true
  echo "Kiosk started (if display available)."
else
  echo "To start kiosk after booting to desktop: sudo systemctl start grblwheel-kiosk"
fi

echo ""
echo "=== Install done ==="
echo "  Backend: http://$(hostname -I | awk '{print $1}'):8765"
echo "  Config:  $REPO_ROOT/config/config.yaml"
echo "  For GPIO jog wheel: sudo pigpiod   (or enable pigpiod on boot)"
echo "  Update:  $REPO_ROOT/scripts/update-pi.sh"
