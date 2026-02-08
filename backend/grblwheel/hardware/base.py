"""Base interface for hardware controller.

Implementations: MockHardwareController (no-op on Windows or when GPIO disabled),
GpioHardwareController (Raspberry Pi with pigpio for encoder and buttons).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Awaitable

# Jog mode selects which axis or parameter the encoder controls.
JogMode = str  # e.g. "x", "y", "z", "feedrate", "spindle"


class HardwareController(ABC):
    """Abstract: rotary encoder (jog), multi-position switch (mode), buttons."""

    @abstractmethod
    def start(self) -> None:
        """Start reading hardware (start background thread or pigpio callbacks)."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop and release resources."""
        pass

    def on_jog(self, callback: Callable[[int, JogMode], Awaitable[None]] | None) -> None:
        """Set callback(delta, mode). Delta is encoder steps (+/-), mode from switch."""
        pass

    def on_button(self, callback: Callable[[str], Awaitable[None]] | None) -> None:
        """Set callback(action). Action is macro name or 'start','stop', etc."""
        pass
