"""Job runner: send G-code file line-by-line with start-at-line, pause/resume/stop and progress.

Each line is sent over the shared GrblSerial and we wait for 'ok' before the next.
Empty lines and comments (;) are skipped. Progress is reported via an optional
async callback (e.g. to push to WebSocket clients).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Awaitable

from grblwheel.files import get_upload_dir, read_lines
from grblwheel.serial_grbl import GrblSerial


class JobState(str, Enum):
    """Current job execution state."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
    DONE = "done"


@dataclass
class JobProgress:
    """Snapshot of job progress for API and WebSocket."""
    state: JobState = JobState.IDLE
    current_line: int = 0
    total_lines: int = 0
    filename: str = ""
    error_message: str = ""


def _strip_line(line: str) -> str:
    s = line.strip()
    # Strip comments for length check
    if ";" in s:
        s = s.split(";", 1)[0].strip()
    return s


def _is_empty_or_comment(line: str) -> bool:
    s = line.strip()
    return not s or s.startswith(";")


class JobRunner:
    """Runs a G-code file through GrblSerial line-by-line with pause/resume/stop and progress callback."""

    def __init__(self, grbl: GrblSerial, config: dict):
        self._grbl = grbl
        self._config = config
        self._progress = JobProgress()
        self._task: asyncio.Task | None = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._stop_requested = False
        self._on_progress: Callable[[JobProgress], Awaitable[None]] | None = None

    @property
    def progress(self) -> JobProgress:
        return self._progress

    def set_progress_callback(self, cb: Callable[[JobProgress], Awaitable[None]] | None) -> None:
        """Register an async callback invoked with JobProgress on state/line changes."""
        self._on_progress = cb

    async def _notify_progress(self) -> None:
        if self._on_progress:
            await self._on_progress(self._progress)

    async def run(
        self,
        filename: str,
        start_line: int = 1,
    ) -> None:
        """Run a file: start_line is 1-based. Sends line-by-line, waiting for ok."""
        upload_dir = get_upload_dir(self._config)
        lines = read_lines(upload_dir, filename)
        if lines is None:
            self._progress.state = JobState.ERROR
            self._progress.error_message = "File not found"
            await self._notify_progress()
            return
        if not self._grbl.state.connected:
            self._progress.state = JobState.ERROR
            self._progress.error_message = "Not connected"
            await self._notify_progress()
            return

        self._progress = JobProgress(
            state=JobState.RUNNING,
            current_line=start_line - 1,
            total_lines=len(lines),
            filename=filename,
        )
        self._stop_requested = False
        self._pause_event.set()
        await self._notify_progress()

        loop = asyncio.get_event_loop()
        idx = max(0, start_line - 1)

        while idx < len(lines):
            if self._stop_requested:
                self._progress.state = JobState.DONE
                await self._notify_progress()
                return

            if not self._pause_event.is_set():
                self._progress.state = JobState.PAUSED
                await self._notify_progress()
                await self._pause_event.wait()
                self._progress.state = JobState.RUNNING
                await self._notify_progress()

            line = lines[idx]
            if _is_empty_or_comment(line):
                idx += 1
                self._progress.current_line = idx
                await self._notify_progress()
                continue

            stripped = _strip_line(line)
            if not stripped:
                idx += 1
                self._progress.current_line = idx
                await self._notify_progress()
                continue

            success, response = await loop.run_in_executor(
                None, lambda l=stripped: self._grbl.send_line(l)
            )
            if not success:
                self._progress.state = JobState.ERROR
                self._progress.error_message = response
                await self._notify_progress()
                return

            idx += 1
            self._progress.current_line = idx
            await self._notify_progress()

        self._progress.state = JobState.DONE
        await self._notify_progress()

    def pause(self) -> None:
        """Pause sending; run loop will wait until resume()."""
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume after pause."""
        self._pause_event.set()

    def stop(self) -> None:
        """Request job to stop after the current line."""
        self._stop_requested = True
