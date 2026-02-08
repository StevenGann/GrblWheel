# GrblWheel

GRBL jog wheel and G-code sender for Raspberry Pi (and Windows for development). Fullscreen touch UI + web interface, file upload, macros, and optional GPIO hardware (rotary encoder, buttons).

## Overview

GrblWheel lets you control a GRBL-based CNC mill from a Raspberry Pi with an optional physical jog wheel, or from any machine (including Windows) via the same web UI. It provides:

- **Web UI**: Connection to GRBL over USB serial, G-code command input, file upload and run (with optional start-at-line), job pause/resume/stop, Zero X/Y, Zero Z, Z probe macros.
- **Appliance mode (Pi)**: systemd services for auto-start and crash restart; Chromium kiosk for fullscreen touch on a small HDMI display.
- **Hardware (Pi, optional)**: Rotary encoder as jog wheel, multi-position switch for axis/mode, buttons mapped to macros. Uses pigpio; no GPIO on Windows.

**Architecture**: Python backend (FastAPI) serves REST and WebSocket APIs and (when built) the Vue 3 frontend. Serial communication with GRBL is synchronous and run in a thread pool. Job runner sends G-code files line-by-line (wait for `ok`). Config is YAML; macros and hardware pins are configured there.

## Project structure

```
GrblWheel/
├── backend/grblwheel/          # Python package
│   ├── main.py                 # FastAPI app, static serving, lifespan
│   ├── config.py               # YAML config load/merge
│   ├── serial_grbl.py          # Serial port list, connect, send line (GRBL)
│   ├── files.py                # G-code file storage (safe names, list/read/delete)
│   ├── job_runner.py           # Run file line-by-line, pause/resume/stop, progress
│   ├── hardware_integration.py # Wire GPIO jog/buttons to GRBL and macros
│   ├── api/                    # REST + WebSocket routes
│   │   ├── health.py, serial_api.py, macros_api.py, files_api.py, job_api.py
│   └── hardware/               # GPIO abstraction (mock on Windows, pigpio on Pi)
├── frontend/                   # Vue 3 + Vite SPA (built to frontend/dist)
├── config/config.example.yaml  # Example config (copy to config.yaml)
├── systemd/                    # Pi: grblwheel.service, grblwheel-kiosk.service, kiosk.sh
├── scripts/                    # install-pi.sh, update-pi.sh, install-win.ps1, update-win.ps1
└── tests/                      # Pytest (API and config)
```

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

## Config reference

Config file: `config/config.yaml` (copy from `config/config.example.yaml`). Key sections:

| Section    | Purpose |
|-----------|---------|
| `server`  | `host`, `port` for the HTTP server (default 8765). |
| `serial`  | `baud` (default 115200). `port` is usually left unset; selected in the UI. |
| `paths`   | `upload_dir`: directory for uploaded G-code (relative to config dir). |
| `gpio_enabled` | Set `true` on Pi to enable jog wheel/buttons; ignored on Windows. |
| `macros`  | Map macro name → list of G-code lines (e.g. `zero_xy`, `zero_z`, `z_probe`). |
| `hardware`| When `gpio_enabled`: `buttons` (pin → macro name), `encoder` (`clk`, `dt` GPIO), `jog_mode_switch` (list of pins for X/Y/Z/feedrate). |

Override config path with env: `GRBLWHEEL_CONFIG=/path/to/config.yaml`.

## API overview

All API routes are under `/api`. OpenAPI docs at `/docs` when the server is running.

- **Health**: `GET /api/health`
- **Serial**: `GET /api/serial/ports`, `GET /api/serial/state`, `POST /api/serial/connect`, `POST /api/serial/disconnect`, `POST /api/serial/send` (body: `{ "command": "G0 X10" }`)
- **Macros**: `GET /api/macros`, `POST /api/macros/{name}/run`
- **Files**: `GET /api/files`, `POST /api/files/upload`, `GET /api/files/{name}/lines`, `DELETE /api/files/{name}`
- **Job**: `POST /api/job/start` (body: `{ "filename", "start_line" }`), `GET /api/job/status`, `POST /api/job/pause`, `POST /api/job/resume`, `POST /api/job/stop`, `WebSocket /api/job/ws` (progress pushed to clients)

## For developers / handoff

- **Adding a new API route**: Add a router in `backend/grblwheel/api/` and include it in `api/__init__.py`.
- **Changing macros or default config**: Edit `config.py` `DEFAULT_CONFIG` and/or `config.example.yaml`.
- **Frontend**: Vue 3 Composition API in `frontend/src/App.vue`; build with `npm run build` in `frontend/`; backend serves `frontend/dist` when present.
- **Tests**: `pytest` with `tests/test_api.py` (FastAPI TestClient) and `tests/test_config.py`. Install dev deps: `pip install -e ".[dev]"`.
- **GRBL protocol**: 115200 baud, CR line ending; send one line, wait for `ok` or `error` before next (see `serial_grbl.py`).

## License

MIT
