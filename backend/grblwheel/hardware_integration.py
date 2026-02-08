"""Wire hardware controller to GRBL serial and macros.

When GPIO is enabled (Pi only), jog events send G91 G0 axis moves; button
events run the configured macro (same as UI macro buttons). Uses app.state.grbl
and app.state.config; no-op if not connected.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from grblwheel.hardware import create_hardware_controller

if TYPE_CHECKING:
    from fastapi import FastAPI

# Per-axis/option step size for one encoder tick (mm or units).
JOG_STEPS = {"x": 0.1, "y": 0.1, "z": 0.01, "feedrate": 10, "spindle": 100}


async def _on_jog(delta: int, mode: str, app) -> None:
    """Send a relative jog move (G91 G0) for the given mode (x/y/z/feedrate)."""
    grbl = getattr(app.state, "grbl", None)
    if not grbl or not grbl.state.connected:
        return
    step = JOG_STEPS.get(mode, 0.1)
    amount = step * delta
    if mode in ("x", "y", "z"):
        axis = mode.upper()
        line = f"G91 G0 {axis}{amount:+.3f}"
    elif mode == "feedrate":
        # Relative F change: send F increase/decrease (GRBL may need current F first)
        line = f"G91 G0 F{amount:+.0f}" if delta != 0 else ""
    else:
        return
    if line:
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: grbl.send_line(line))


async def _on_button(action: str, app) -> None:
    """Run the macro named by action if it exists in config; sends lines via grbl."""
    if not action:
        return
    grbl = getattr(app.state, "grbl", None)
    config = getattr(app.state, "config", {})
    macros = config.get("macros") or {}
    if action in macros:
        # Run macro (same as API)
        from grblwheel.api.macros_api import get_runner_from_app
        runner = get_runner_from_app(app)
        # Run macro lines
        import asyncio
        if grbl and grbl.state.connected:
            for line in macros[action]:
                line = (line or "").strip()
                if line and not line.startswith(";"):
                    await asyncio.get_event_loop().run_in_executor(
                        None, lambda l=line: grbl.send_line(l)
                    )
    # Else could map to job start/stop etc. via app.state.job_runner


def setup_hardware(app: FastAPI) -> None:
    """Create hardware controller and register callbacks. No-op if GPIO disabled."""
    config = app.state.config
    if not config.get("gpio_enabled", False):
        return
    try:
        controller = create_hardware_controller(config)
        app.state.hardware_controller = controller

        async def on_jog(delta: int, mode: str):
            await _on_jog(delta, mode, app)

        async def on_btn(action: str):
            await _on_button(action, app)

        controller.on_jog(on_jog)
        controller.on_button(on_btn)
        controller.start()
    except Exception:
        app.state.hardware_controller = None


def teardown_hardware(app: FastAPI) -> None:
    """Stop and clear the hardware controller on app shutdown."""
    ctrl = getattr(app.state, "hardware_controller", None)
    if ctrl is not None:
        try:
            ctrl.stop()
        except Exception:
            pass
        app.state.hardware_controller = None
