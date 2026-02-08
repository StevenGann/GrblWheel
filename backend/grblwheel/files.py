"""G-code file storage: upload directory, safe filenames, list/read/delete."""

from __future__ import annotations

import re
from pathlib import Path


# Disallow path traversal and only allow safe chars for filenames
SAFE_NAME = re.compile(r"^[a-zA-Z0-9_.\-]+$")


def get_upload_dir(config: dict) -> Path:
    path = config.get("paths", {}).get("upload_dir", "gcode")
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_filename(name: str) -> str | None:
    """Return basename if safe, else None."""
    base = Path(name).name
    if not base or not SAFE_NAME.match(base):
        return None
    return base


def list_files(upload_dir: Path) -> list[dict]:
    """List G-code files with name and size."""
    if not upload_dir.exists():
        return []
    out = []
    for f in sorted(upload_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in (".gcode", ".nc", ".ngc", ".txt", ""):
            out.append({"name": f.name, "size": f.stat().st_size})
    return out


def _resolve_path(upload_dir: Path, name: str) -> Path | None:
    """Resolve safe path under upload_dir; None if invalid."""
    safe = safe_filename(name)
    if not safe:
        return None
    p = (upload_dir / safe).resolve()
    try:
        p.relative_to(upload_dir.resolve())
    except ValueError:
        return None
    return p


def get_file_path(upload_dir: Path, name: str) -> Path | None:
    """Resolve safe path for a stored file if it exists; None otherwise."""
    p = _resolve_path(upload_dir, name)
    return p if p and p.exists() else None


def read_lines(upload_dir: Path, name: str) -> list[str] | None:
    """Read file lines (UTF-8); None if not found or invalid."""
    p = get_file_path(upload_dir, name)
    if not p:
        return None
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return None


def delete_file(upload_dir: Path, name: str) -> bool:
    """Delete file if safe and exists. Return True if deleted."""
    p = _resolve_path(upload_dir, name)
    if not p or not p.exists():
        return False
    try:
        p.unlink()
        return True
    except Exception:
        return False


def save_upload(upload_dir: Path, name: str, content: bytes, max_size: int = 50 * 1024 * 1024) -> str | None:
    """Save uploaded content. Return None on success, else error message."""
    path = _resolve_path(upload_dir, name)
    if not path:
        return "Invalid filename"
    if len(content) > max_size:
        return "File too large"
    upload_dir.mkdir(parents=True, exist_ok=True)
    try:
        path.write_bytes(content)
        return None
    except Exception as e:
        return str(e)
