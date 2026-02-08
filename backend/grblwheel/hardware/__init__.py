"""Hardware abstraction: GPIO jog wheel, buttons, mode switch. No-op on Windows.

Use create_hardware_controller(config) to get either GpioHardwareController (Pi, when
gpio_enabled and pigpio available) or MockHardwareController (Windows or GPIO disabled).
"""

from __future__ import annotations

from grblwheel.hardware.base import HardwareController

__all__ = ["HardwareController", "create_hardware_controller"]


def create_hardware_controller(config: dict) -> HardwareController:
    """Return a hardware controller: GPIO on Pi when config.gpio_enabled, else mock (no-op)."""
    if not config.get("gpio_enabled", False):
        from grblwheel.hardware.mock_controller import MockHardwareController
        return MockHardwareController(config)
    try:
        from grblwheel.hardware.gpio_controller import GpioHardwareController
        return GpioHardwareController(config)
    except ImportError:
        from grblwheel.hardware.mock_controller import MockHardwareController
        return MockHardwareController(config)
