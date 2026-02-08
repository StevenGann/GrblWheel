"""Hardware abstraction: GPIO jog wheel, buttons, mode switch. No-op on Windows."""

from __future__ import annotations

from typing import Callable, Awaitable

from grblwheel.hardware.base import HardwareController

__all__ = ["HardwareController", "create_hardware_controller"]


def create_hardware_controller(config: dict) -> HardwareController:
    """Create the appropriate controller: GPIO on Pi when enabled, else no-op."""
    if not config.get("gpio_enabled", False):
        from grblwheel.hardware.mock_controller import MockHardwareController
        return MockHardwareController(config)
    try:
        from grblwheel.hardware.gpio_controller import GpioHardwareController
        return GpioHardwareController(config)
    except ImportError:
        from grblwheel.hardware.mock_controller import MockHardwareController
        return MockHardwareController(config)
