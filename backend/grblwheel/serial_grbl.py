"""Serial connection to GRBL: port discovery, connect, send line and wait for ok.

GRBL expects 115200 baud (configurable) and CR line ending. send_line() is blocking;
call it from a thread or run_in_executor in async code.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterator

import serial
import serial.tools.list_ports


LINE_ENDING = "\r"
DEFAULT_BAUD = 115200


@dataclass
class SerialState:
    """Current serial connection state; read by API and UI."""
    connected: bool = False
    port: str | None = None
    baud: int = DEFAULT_BAUD
    last_response: str = ""
    last_error: str = ""


def list_ports() -> list[dict[str, str]]:
    """Return list of available serial ports with description."""
    return [
        {"port": p.device, "description": p.description or p.device}
        for p in serial.tools.list_ports.comports()
    ]


class GrblSerial:
    """Synchronous serial wrapper for GRBL. Use from async via run_in_executor or a thread."""

    def __init__(self, baud: int = DEFAULT_BAUD):
        """Optional baud rate (default 115200). Connection is via connect()."""
        self._ser: serial.Serial | None = None
        self._baud = baud
        self._state = SerialState(baud=baud)
        self._lock = asyncio.Lock()

    @property
    def state(self) -> SerialState:
        return self._state

    def connect(self, port: str, baud: int | None = None) -> str | None:
        """Connect to the given port. Returns None on success, or an error message string."""
        if self._ser and self._ser.is_open:
            self.disconnect()
        try:
            self._ser = serial.Serial(
                port=port,
                baudrate=baud or self._baud,
                timeout=0.1,
                write_timeout=2.0,
            )
            self._ser.reset_input_buffer()
            self._ser.reset_output_buffer()
            self._state.connected = True
            self._state.port = port
            self._state.baud = self._ser.baudrate
            self._state.last_error = ""
            return None
        except Exception as e:
            self._state.last_error = str(e)
            return str(e)

    def disconnect(self) -> None:
        """Close the serial port and clear connection state."""
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
        self._state.connected = False
        self._state.port = None

    def send_line(self, line: str) -> tuple[bool, str]:
        """
        Send one line (with CR) and wait for 'ok' or 'error'. Blocking.
        Returns (success, response_text).
        """
        if not self._ser or not self._ser.is_open:
            return False, "Not connected"
        line = line.strip()
        if not line:
            return True, ""
        try:
            self._ser.write((line + LINE_ENDING).encode("ascii"))
            self._ser.flush()
            # Read until we get ok or error (GRBL sends one line per response)
            while True:
                raw = self._ser.readline()
                if not raw:
                    continue
                try:
                    text = raw.decode("ascii", errors="replace").strip()
                except Exception:
                    text = raw.decode("utf-8", errors="replace").strip()
                if not text:
                    continue
                self._state.last_response = text
                if text.strip().upper().startswith("OK"):
                    return True, text
                if "error" in text.lower():
                    self._state.last_error = text
                    return False, text
                # Status reports etc.: keep reading
        except serial.SerialException as e:
            self._state.last_error = str(e)
            return False, str(e)
        except Exception as e:
            self._state.last_error = str(e)
            return False, str(e)

    def read_lines(self) -> Iterator[str]:
        """Non-blocking read of available lines (for status streaming)."""
        if not self._ser or not self._ser.is_open:
            return
        while self._ser.in_waiting:
            raw = self._ser.readline()
            if not raw:
                break
            try:
                text = raw.decode("ascii", errors="replace").strip()
            except Exception:
                text = raw.decode("utf-8", errors="replace").strip()
            if text:
                yield text
