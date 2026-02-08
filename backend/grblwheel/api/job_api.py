"""Job API: start/pause/resume/stop file run; WebSocket for progress."""

from __future__ import annotations

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

from grblwheel.job_runner import JobProgress, JobRunner, JobState

router = APIRouter()

_ws_clients: list[WebSocket] = []


async def _broadcast_progress(progress: JobProgress) -> None:
    msg = {
        "type": "progress",
        "state": progress.state.value,
        "current_line": progress.current_line,
        "total_lines": progress.total_lines,
        "filename": progress.filename,
        "error_message": progress.error_message,
    }
    dead = []
    for ws in _ws_clients:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _ws_clients:
            _ws_clients.remove(ws)


def get_runner(request: Request) -> JobRunner:
    app = request.app
    if not hasattr(app.state, "job_runner"):
        grbl = app.state.grbl if hasattr(app.state, "grbl") else None
        if grbl is None:
            from grblwheel.serial_grbl import GrblSerial
            app.state.grbl = GrblSerial()
            grbl = app.state.grbl
        runner = JobRunner(grbl, app.state.config)
        runner.set_progress_callback(_broadcast_progress)
        app.state.job_runner = runner
    return app.state.job_runner


def get_runner_from_app(app) -> JobRunner:
    if not hasattr(app.state, "job_runner"):
        grbl = app.state.grbl if hasattr(app.state, "grbl") else None
        if grbl is None:
            from grblwheel.serial_grbl import GrblSerial
            app.state.grbl = GrblSerial()
            grbl = app.state.grbl
        runner = JobRunner(grbl, app.state.config)
        runner.set_progress_callback(_broadcast_progress)
        app.state.job_runner = runner
    return app.state.job_runner


def progress_to_dict(p: JobProgress) -> dict:
    return {
        "state": p.state.value,
        "current_line": p.current_line,
        "total_lines": p.total_lines,
        "filename": p.filename,
        "error_message": p.error_message,
    }


@router.post("/job/start")
async def job_start(request: Request, body: dict | None = None):
    """Start running a file. Body: { \"filename\": \"x.gcode\", \"start_line\": 1 }."""
    body = body or {}
    filename = body.get("filename")
    if not filename:
        return {"ok": False, "error": "filename required"}
    start_line = max(1, int(body.get("start_line", 1)))
    runner = get_runner(request)
    if runner.progress.state == JobState.RUNNING or runner.progress.state == JobState.PAUSED:
        return {"ok": False, "error": "Job already running"}
    import asyncio
    asyncio.create_task(runner.run(filename, start_line=start_line))
    return {"ok": True}


@router.get("/job/status")
def job_status(request: Request):
    """Current job progress."""
    runner = get_runner(request)
    return progress_to_dict(runner.progress)


@router.post("/job/pause")
def job_pause(request: Request):
    runner = get_runner(request)
    runner.pause()
    return {"ok": True}


@router.post("/job/resume")
def job_resume(request: Request):
    runner = get_runner(request)
    runner.resume()
    return {"ok": True}


@router.post("/job/stop")
def job_stop(request: Request):
    runner = get_runner(request)
    runner.stop()
    return {"ok": True}


@router.websocket("/job/ws")
async def job_ws(websocket: WebSocket):
    """WebSocket: receive start/pause/resume/stop; server pushes progress updates."""
    await websocket.accept()
    _ws_clients.append(websocket)
    app = websocket.app
    try:
        runner = get_runner_from_app(app)
        await websocket.send_json({"type": "progress", **progress_to_dict(runner.progress)})
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            runner = get_runner_from_app(app)
            if action == "start":
                filename = data.get("filename")
                if filename:
                    import asyncio
                    start_line = max(1, int(data.get("start_line", 1)))
                    asyncio.create_task(runner.run(filename, start_line=start_line))
            elif action == "pause":
                runner.pause()
            elif action == "resume":
                runner.resume()
            elif action == "stop":
                runner.stop()
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)
