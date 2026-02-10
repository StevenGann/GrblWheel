#!/usr/bin/env bash
# GrblWheel Pi setup: install Candle, configure autostart (fullscreen), and update-on-boot.
# Run from repo root or from scripts/:
#   ./scripts/setup-pi.sh   OR   cd GrblWheel && ./scripts/setup-pi.sh
set -e

# Repo root (directory that contains scripts/ and config/)
if [[ -n "$GRBLWHEEL_ROOT" ]]; then
  REPO_ROOT="$GRBLWHEEL_ROOT"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
cd "$REPO_ROOT"

CONFIG_DIR="${CONFIG_DIR:-$REPO_ROOT/config}"
CANDLE_SRC="${CANDLE_SRC:-$HOME/Candle}"
CANDLE_INSTALL="${CANDLE_INSTALL:-$HOME/programs/Candle}"
GRBLWHEEL_REPO="${GRBLWHEEL_REPO:-https://github.com/StevenGann/GrblWheel}"

echo "GrblWheel setup: repo=$REPO_ROOT, Candle install=$CANDLE_INSTALL"

# --- System packages for building Candle (Raspberry Pi OS / Ubuntu) ---
echo "Installing build and Qt dependencies..."
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
  cmake build-essential git \
  qtbase5-dev libqt5serialport5-dev qtscript5-dev \
  qttools5-dev libqt5websockets5-dev qtmultimedia5-dev

# --- Build and install Candle ---
if [[ ! -d "$CANDLE_SRC" ]]; then
  echo "Cloning Candle..."
  git clone --depth 1 https://github.com/Denvi/Candle.git "$CANDLE_SRC"
fi
cd "$CANDLE_SRC"
git fetch --tags 2>/dev/null || true
# Build in a build dir
BUILD_DIR="$CANDLE_SRC/build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"
echo "Building Candle (this may take a while)..."
cmake .. -DCMAKE_INSTALL_PREFIX="$CANDLE_INSTALL"
cmake --build . --config Release -j"$(nproc 2>/dev/null || echo 2)"
cmake --install .
echo "Candle installed to $CANDLE_INSTALL"

# --- GrblWheel config ---
mkdir -p "$CONFIG_DIR"
if [[ ! -f "$CONFIG_DIR/grblwheel.conf" ]]; then
  if [[ -f "$CONFIG_DIR/grblwheel.example.conf" ]]; then
    cp "$CONFIG_DIR/grblwheel.example.conf" "$CONFIG_DIR/grblwheel.conf"
    echo "Created $CONFIG_DIR/grblwheel.conf from example; edit to set serial port if needed."
  else
    echo "Warning: no config/grblwheel.example.conf found; create $CONFIG_DIR/grblwheel.conf if you need to customize."
  fi
fi

# --- Launcher and autostart (Candle on login, fullscreen) ---
LAUNCHER="$REPO_ROOT/scripts/launch-candle.sh"
chmod +x "$LAUNCHER"
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
DESKTOP="$AUTOSTART_DIR/candle-grblwheel.desktop"
cat > "$DESKTOP" << EOF
[Desktop Entry]
Type=Application
Name=Candle (GrblWheel)
Comment=GRBL controller fullscreen
Exec=env GRBLWHEEL_ROOT=$REPO_ROOT GRBLWHEEL_CONFIG=$CONFIG_DIR/grblwheel.conf CANDLE_INSTALL=$CANDLE_INSTALL $LAUNCHER
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
echo "Autostart entry: $DESKTOP"

# --- Update checker: systemd one-shot at boot ---
SERVICE_NAME="grblwheel-update"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=GrblWheel: check for updates and reboot if new version
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$REPO_ROOT
Environment=GRBLWHEEL_ROOT=$REPO_ROOT
ExecStart=$REPO_ROOT/scripts/check-update-and-reboot.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
echo "Update service enabled: $SERVICE_NAME"

echo ""
echo "Setup complete."
echo "  1. Edit $CONFIG_DIR/grblwheel.conf to set serial_port (optional; you can also set it once in Candle Settings)."
echo "  2. Ensure auto-login to desktop is enabled so Candle starts on boot."
echo "  3. On each boot, this repo is checked for updates; if found, setup is re-run and the Pi reboots."
echo "  4. To start Candle now (after next login): log out and back in, or run: $LAUNCHER"
