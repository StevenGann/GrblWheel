"""No-op hardware controller for Windows or when GPIO is disabled.

Used whenever gpio_enabled is false or pigpio cannot be imported (e.g. on non-Pi).
"""

from __future__ import annotations

from grblwheel.hardware.base import HardwareController


class MockHardwareController(HardwareController):
    """Stub that does nothing; satisfies the HardwareController interface."""

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass
