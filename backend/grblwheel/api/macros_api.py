"""Macros API: list macro names from config and run a macro (send each line, wait for ok)."""

from __future__ import annotations

from fastapi import APIRouter, Request

from grblwheel.serial_grbl import GrblSerial

router = APIRouter()


def get_grbl(request: Request) -> GrblSerial:
    """Return the app-scoped GrblSerial instance; create if missing."""
    if not hasattr(request.app.state, "grbl"):
        request.app.state.grbl = GrblSerial()
    return request.app.state.grbl


@router.get("/macros")
def list_macros(request: Request):
    """List configured macro names."""
    config = request.app.state.config
    macros = config.get("macros") or {}
    return {"macros": list(macros.keys())}


@router.post("/macros/{name}/run")
async def run_macro(request: Request, name: str):
    """Run a macro by name: send each G-code line and wait for ok."""
    import asyncio
    config = request.app.state.config
    macros = config.get("macros") or {}
    if name not in macros:
        return {"ok": False, "message": f"Unknown macro: {name}"}
    grbl = get_grbl(request)
    if not grbl.state.connected:
        return {"ok": False, "message": "Not connected"}
    lines = macros[name]
    if isinstance(lines, str):
        lines = [lines]
    loop = asyncio.get_event_loop()
    for line in lines:
        line = (line or "").strip()
        if not line or line.startswith(";"):
            continue
        success, response = await loop.run_in_executor(None, lambda l=line: grbl.send_line(l))
        if not success:
            return {"ok": False, "message": response}
    return {"ok": True, "message": "OK"}
