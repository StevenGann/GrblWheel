# Systemd

The **grblwheel-update** service is installed by `scripts/setup-pi.sh` (not from a file in this folder). It:

- Runs once at boot after network is available
- Checks this repo (StevenGann/GrblWheel) for new commits on `main`/`master`
- If behind: `git pull`, re-runs `setup-pi.sh`, then reboots

The service runs as the user who ran setup (e.g. `pi`). Candle is started by the desktop **autostart** entry (`~/.config/autostart/candle-grblwheel.desktop`), not by systemd, so it starts after the user logs in (e.g. auto-login).
