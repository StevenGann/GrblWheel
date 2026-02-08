# GrblWheel

GRBL jog wheel and G-code sender for Raspberry Pi (and Windows for development). Fullscreen touch UI + web interface, file upload, macros, and optional GPIO hardware (rotary encoder, buttons).

## Requirements

- Python 3.10+
- On Pi: optional `pigpio` for GPIO (jog wheel, buttons)

## Setup

```bash
# Create venv and install (Windows: use py instead of python3)
py -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Pi
pip install -e .
```

Optional GPIO on Pi:
```bash
pip install -e ".[gpio]"
```

Copy and edit config:
```bash
copy config\config.example.yaml config\config.yaml
```

## Windows (testing)

Quick install and update scripts (PowerShell, run from repo root). If scripts are blocked, run once: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.

```powershell
.\scripts\install-win.ps1
```

This creates `.venv`, installs the package, copies config if missing, and builds the frontend if `npm` is available. Then run:

```powershell
py -m grblwheel.main
```

To pull latest and re-run install:

```powershell
.\scripts\update-win.ps1
```

## Run (development)

From the project root (GrblWheel):

```bash
py -m grblwheel.main
# Or: uvicorn grblwheel.main:app --reload --host 0.0.0.0 --port 8765
```

Then open http://localhost:8765 (after frontend is built, or use API at http://localhost:8765/api/health). Config is read from `config/config.yaml` or `config.yaml` in the current directory.

## Frontend

```bash
cd frontend
npm install
npm run build
```

Backend serves the built files from `frontend/dist` when present.

## Testing

```bash
pip install -e ".[dev]"
pytest -v
```

CI runs the same tests and a frontend build on push/PR to `main` or `master` (see [.github/workflows/test.yml](.github/workflows/test.yml)).

## Raspberry Pi (appliance mode)

**Quick install (after cloning):**
```bash
cd GrblWheel
chmod +x scripts/install-pi.sh scripts/update-pi.sh
./scripts/install-pi.sh
```
This creates the venv, installs Python deps (with GPIO), copies config if missing, builds the frontend if `npm` is available, and installs/enables the systemd units (paths are set automatically).

**Update from GitHub:**
```bash
./scripts/update-pi.sh
```
Pulls the latest code and runs the install script again.

**Manual steps** (if not using the install script):
1. Clone the project to the Pi (e.g. `/home/pi/GrblWheel`).
2. Create a venv and install: `python3 -m venv .venv && .venv/bin/pip install -e ".[gpio]"`.
3. Copy and edit config: `cp config/config.example.yaml config/config.yaml`. Set `gpio_enabled: true` and hardware pins if using GPIO.
4. Build frontend on Pi or copy `frontend/dist` from your PC: `cd frontend && npm install && npm run build`.
5. Install systemd units (adjust paths in the service files if needed), then `sudo systemctl daemon-reload && sudo systemctl enable grblwheel grblwheel-kiosk && sudo systemctl start grblwheel`.
6. For GPIO (jog wheel): run pigpio daemon: `sudo pigpiod` (or enable on boot).

## License

MIT
