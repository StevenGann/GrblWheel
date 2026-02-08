"""No-op hardware controller for Windows or when GPIO is disabled."""

from __future__ import annotations

from grblwheel.hardware.base import HardwareController


class MockHardwareController(HardwareController):
    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass
