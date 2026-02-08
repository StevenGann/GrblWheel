"""API routes: health, serial, macros, files, job. All mounted under /api."""

from fastapi import APIRouter

from grblwheel.api.health import router as health_router
from grblwheel.api.serial_api import router as serial_router
from grblwheel.api.macros_api import router as macros_router
from grblwheel.api.files_api import router as files_router
from grblwheel.api.job_api import router as job_router

router = APIRouter()
router.include_router(health_router)
router.include_router(serial_router)
router.include_router(macros_router)
router.include_router(files_router)
router.include_router(job_router)
