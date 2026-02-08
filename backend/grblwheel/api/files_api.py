"""File API: list uploaded G-code files, upload, get lines (for job start-at-line), delete."""

from __future__ import annotations

from fastapi import APIRouter, Request, UploadFile, File, HTTPException

from grblwheel.files import get_upload_dir, list_files, delete_file, save_upload, read_lines

router = APIRouter()


@router.get("/files")
def files_list(request: Request):
    """List uploaded G-code files."""
    config = request.app.state.config
    upload_dir = get_upload_dir(config)
    return {"files": list_files(upload_dir)}


@router.post("/files/upload")
async def files_upload(request: Request, file: UploadFile = File(...)):
    """Upload a G-code file."""
    config = request.app.state.config
    upload_dir = get_upload_dir(config)
    name = file.filename or "upload.gcode"
    content = await file.read()
    err = save_upload(upload_dir, name, content)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"ok": True, "name": name}


@router.get("/files/{name}/lines")
def files_get_lines(request: Request, name: str):
    """Get line count and optional content for a file (for job start-at-line)."""
    config = request.app.state.config
    upload_dir = get_upload_dir(config)
    lines = read_lines(upload_dir, name)
    if lines is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"name": name, "lines": lines, "count": len(lines)}


@router.delete("/files/{name}")
def files_delete(request: Request, name: str):
    """Delete an uploaded file."""
    config = request.app.state.config
    upload_dir = get_upload_dir(config)
    if not delete_file(upload_dir, name):
        raise HTTPException(status_code=404, detail="File not found or invalid")
    return {"ok": True}
