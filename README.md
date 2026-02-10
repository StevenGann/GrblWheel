# GrblWheel

Bootstrap and configuration to run **[Candle](https://github.com/Denvi/Candle)** (GRBL controller with G-code visualizer) on a Raspberry Pi: install Candle, start it fullscreen on boot, and keep this repo up to date by checking for new versions at startup and re-running setup + reboot when needed.

## What this repo does

- **Uses Candle** for the GUI and control logic ([Denvi/Candle](https://github.com/Denvi/Candle) — Qt-based GRBL controller and G-code visualizer).
- **Pi setup script** (`scripts/setup-pi.sh`):
  - Installs build deps and **builds Candle** from source.
  - Configures **autostart** so Candle runs **fullscreen** when the user logs in (e.g. after auto-login to desktop).
  - Installs a **boot-time update checker** that looks at this repo for new commits and, if found, pulls, re-runs the setup script, and reboots.
- **Serial port**: Candle does not accept the serial port on the command line. Configure it once in **Candle → Settings**; the Pi will remember it across reboots. If the launcher’s `-fullscreen` flag is not supported by your Candle build, you can edit `scripts/launch-candle.sh` and remove it; Candle will still start normally.

## Requirements

- **Raspberry Pi** running Raspberry Pi OS (Raspbian) with desktop (for Candle’s GUI). Candle’s docs mention [Raspberry Pi OS Trixie](https://github.com/Denvi/Candle); the same build steps typically work on Bookworm.
- Network for the update check and for building (apt, git clone of Candle).

## Quick start (Raspberry Pi)

1. Clone this repo (e.g. to `/home/pi/GrblWheel`):

   ```bash
   git clone https://github.com/StevenGann/GrblWheel.git
   cd GrblWheel
   ```

2. Run the setup script (installs Candle, autostart, and update service):

   ```bash
   chmod +x scripts/setup-pi.sh scripts/launch-candle.sh scripts/check-update-and-reboot.sh
   ./scripts/setup-pi.sh
   ```

3. Enable **auto-login to desktop** (Raspberry Pi OS: **Preferences → Raspberry Pi Configuration → System → Boot → Auto Login** set to “Desktop auto-login” or “Desktop”).

4. Optionally edit `config/grblwheel.conf` (created from `config/grblwheel.example.conf`) for any future options. Serial port is still set in Candle’s Settings.

5. Reboot. After boot:
   - The **update checker** runs (checks this repo; if there’s a new version, it pulls, re-runs setup, and reboots).
   - Once the desktop starts, **Candle** launches fullscreen. Set the serial port once in Candle’s Settings if needed.

## Project structure

```
GrblWheel/
├── config/
│   └── grblwheel.example.conf   # Example config (serial_port, etc.)
├── scripts/
│   ├── setup-pi.sh              # Main Pi setup: install Candle, autostart, update service
│   ├── launch-candle.sh         # Launches Candle fullscreen (used by autostart)
│   └── check-update-and-reboot.sh  # Boot: check repo, pull + setup + reboot if new version
├── systemd/
│   └── README.md                # Notes on grblwheel-update service
└── README.md
```

## What runs when

1. **Boot** → network comes up → **grblwheel-update.service** runs once:
   - Fetches `origin/main` (or `origin/master`) for this repo.
   - If the Pi’s branch is behind: `git pull`, then `./scripts/setup-pi.sh`, then **reboot**.
   - If up to date: exits; boot continues.
2. **Desktop session** (e.g. auto-login) → **Candle** is started via `~/.config/autostart/candle-grblwheel.desktop` → runs `scripts/launch-candle.sh` → Candle in fullscreen.

## Config

- **config/grblwheel.conf** (copy from `config/grblwheel.example.conf`): used by the launcher; currently holds optional settings (e.g. serial port for reference). Candle’s own serial/baud settings are configured in **Candle → Settings** and stored by Candle.
- **Candle**: set serial port and baud once in the app; they persist.

## Manual update (without reboot)

From the repo directory:

```bash
git pull origin main   # or master
./scripts/setup-pi.sh
```

Then restart Candle (log out and back in, or run `./scripts/launch-candle.sh`).

## Customizing paths

You can override paths when running setup:

- `GRBLWHEEL_ROOT` – path to this repo (default: inferred from script location).
- `CANDLE_SRC` – where to clone Candle source (default: `$HOME/Candle`).
- `CANDLE_INSTALL` – where to install Candle (default: `$HOME/programs/Candle`).
- `CONFIG_DIR` – directory for `grblwheel.conf` (default: `$REPO_ROOT/config`).

Example:

```bash
CANDLE_INSTALL=/opt/candle ./scripts/setup-pi.sh
```

## License

MIT
