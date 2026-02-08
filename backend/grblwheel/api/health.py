"""Health and status endpoint for liveness checks and API discovery."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    """Return service name and status; used by scripts and monitoring."""
    return {"status": "ok", "service": "grblwheel"}
