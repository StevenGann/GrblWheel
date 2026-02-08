"""Serial and GRBL API: list ports, connect, disconnect, send command."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

from grblwheel.serial_grbl import GrblSerial, list_ports

router = APIRouter()


def get_grbl(request: Request) -> GrblSerial:
    if not hasattr(request.app.state, "grbl"):
        request.app.state.grbl = GrblSerial()
    return request.app.state.grbl


@router.get("/serial/ports")
def serial_ports():
    """List available serial ports."""
    return {"ports": list_ports()}


@router.get("/serial/state")
def serial_state(request: Request):
    """Current connection state."""
    grbl = get_grbl(request)
    s = grbl.state
    return {
        "connected": s.connected,
        "port": s.port,
        "baud": s.baud,
        "last_response": s.last_response,
        "last_error": s.last_error,
    }


@router.post("/serial/connect")
async def serial_connect(request: Request, body: dict[str, Any] | None = None):
    """Connect to a serial port. Body: { \"port\": \"COM3\", \"baud\": 115200 }."""
    body = body or {}
    port = body.get("port")
    if not port:
        return {"ok": False, "error": "port required"}
    grbl = get_grbl(request)
    baud = body.get("baud") or request.app.state.config.get("serial", {}).get("baud", 115200)
    loop = asyncio.get_event_loop()
    err = await loop.run_in_executor(None, lambda: grbl.connect(port, int(baud)))
    if err:
        return {"ok": False, "error": err}
    return {"ok": True}


@router.post("/serial/disconnect")
def serial_disconnect(request: Request):
    """Disconnect from serial."""
    grbl = get_grbl(request)
    grbl.disconnect()
    return {"ok": True}


@router.post("/serial/send")
async def serial_send(request: Request, body: dict[str, Any] | None = None):
    """Send one G-code line. Body: { \"command\": \"G0 X10\" }. Waits for ok."""
    body = body or {}
    command = (body.get("command") or "").strip()
    if not command:
        return {"ok": False, "error": "command required"}
    grbl = get_grbl(request)
    loop = asyncio.get_event_loop()
    success, response = await loop.run_in_executor(None, lambda: grbl.send_line(command))
    return {"ok": success, "response": response}


@router.websocket("/serial/ws")
async def serial_ws(websocket: WebSocket):
    """WebSocket: receive commands to send, broadcast status/responses to all subscribers."""
    await websocket.accept()
    # For now we just keep connection open; job progress and status can be pushed here later
    try:
        while True:
            msg = await websocket.receive_text()
            # Optional: accept {"type":"send","command":"..."} and run send_line, then echo response
            await websocket.send_json({"type": "info", "message": "Use POST /api/serial/send for commands"})
    except WebSocketDisconnect:
        pass
