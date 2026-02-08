"""Raspberry Pi GPIO hardware controller using pigpio (optional dependency).

Requires the pigpio daemon (sudo pigpiod). Encoder pins (clk, dt) and button/switch
pins are read from config.hardware. Encoder uses a background thread for polling.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Callable, Awaitable

from grblwheel.hardware.base import HardwareController, JogMode


class GpioHardwareController(HardwareController):
    """Pi GPIO: KY-040 style rotary encoder (jog), optional buttons and mode switch. Requires pigpiod."""

    def __init__(self, config: dict):
        self._config = config
        self._jog_callback: Callable[[int, JogMode], Awaitable[None]] | None = None
        self._button_callback: Callable[[str], Awaitable[None]] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._pi = None
        self._mode_index = 0
        self._modes: list[JogMode] = ["x", "y", "z", "feedrate"]
        self._running = False
        self._encoder_thread: threading.Thread | None = None
        self._btn_map: dict = {}
        self._clk_pin = None
        self._dt_pin = None

    def start(self) -> None:
        try:
            import pigpio
        except ImportError:
            raise ImportError("Install optional dependency: pip install 'grblwheel[gpio]'")
        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError("pigpio daemon not running. On Pi run: sudo pigpiod")
        hw = self._config.get("hardware") or {}
        enc_cfg = hw.get("encoder") or {}
        self._btn_map = hw.get("buttons") or {}
        switch_pins = hw.get("jog_mode_switch") or []
        self._modes = ["x", "y", "z", "feedrate"][: max(1, len(switch_pins) + 1)]
        self._running = True

        for pin in list(self._btn_map.keys()) + switch_pins:
            self._pi.set_mode(pin, pigpio.INPUT)
            self._pi.set_pull_up_down(pin, pigpio.PUD_UP)

        clk, dt = enc_cfg.get("clk"), enc_cfg.get("dt")
        if clk is not None and dt is not None:
            self._clk_pin = int(clk)
            self._dt_pin = int(dt)
            self._pi.set_mode(self._clk_pin, pigpio.INPUT)
            self._pi.set_pull_up_down(self._clk_pin, pigpio.PUD_UP)
            self._pi.set_mode(self._dt_pin, pigpio.INPUT)
            self._pi.set_pull_up_down(self._dt_pin, pigpio.PUD_UP)
            self._encoder_thread = threading.Thread(target=self._encoder_poll, daemon=True)
            self._encoder_thread.start()

    def _encoder_poll(self) -> None:
        """Simple KY-040 encoder polling: CLK/DT, report delta."""
        last = None
        while self._running and self._pi and self._clk_pin is not None:
            try:
                clk = self._pi.read(self._clk_pin)
                dt = self._pi.read(self._dt_pin)
                state = (clk, dt)
                if last is not None and state != last:
                    if last == (0, 0) and clk == 1:
                        delta = 1 if dt == 0 else -1
                        if self._jog_callback and self._loop:
                            mode = self._modes[self._mode_index] if self._mode_index < len(self._modes) else "x"
                            asyncio.run_coroutine_threadsafe(
                                self._jog_callback(delta, mode), self._loop
                            )
                last = state
            except Exception:
                break
            import time
            time.sleep(0.001)

    def stop(self) -> None:
        self._running = False
        if self._encoder_thread and self._encoder_thread.is_alive():
            self._encoder_thread.join(timeout=1.0)
        if self._pi is not None:
            try:
                self._pi.stop()
            except Exception:
                pass
            self._pi = None

    def on_jog(self, callback: Callable[[int, JogMode], Awaitable[None]] | None) -> None:
        self._jog_callback = callback
        if callback:
            self._loop = asyncio.get_event_loop()

    def on_button(self, callback: Callable[[str], Awaitable[None]] | None) -> None:
        self._button_callback = callback
