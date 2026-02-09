"""FastAPI application entry and static file serving.

Creates the app with config from load_config(), mounts /api routes, and serves
the Vue SPA from frontend/dist when present. Lifespan sets up and tears down
the hardware controller (GPIO on Pi when enabled).
"""

from __future__ import annotations

import os
from pathlib import Path

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from grblwheel.config import load_config

# SPA build output; backend serves it when present (e.g. after npm run build).
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init hardware controller if gpio_enabled. Shutdown: stop controller."""
    from grblwheel.hardware_integration import setup_hardware, teardown_hardware
    setup_hardware(app)
    yield
    teardown_hardware(app)


def create_app(config_path: str | None = None) -> FastAPI:
    """Build the FastAPI app: config, CORS, /api router, optional SPA static + catch-all."""
    config = load_config(config_path)
    app = FastAPI(
        title="GrblWheel",
        description="GRBL jog wheel and G-code sender",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.config = config

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes will be included by routers
    from grblwheel.api import router as api_router
    app.include_router(api_router, prefix="/api", tags=["api"])

    @app.get("/")
    def root():
        if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
            from fastapi.responses import FileResponse
            return FileResponse(FRONTEND_DIST / "index.html")
        return {"message": "GrblWheel API", "docs": "/docs", "health": "/api/health"}

    # Serve SPA static assets and fallback for client-side routing
    if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

        @app.get("/{full_path:path}")
        def serve_spa(full_path: str):
            from fastapi.responses import FileResponse
            path = FRONTEND_DIST / full_path
            if path.is_file():
                return FileResponse(path)
            return FileResponse(FRONTEND_DIST / "index.html")

    return app


app = create_app(os.environ.get("GRBLWHEEL_CONFIG"))


if __name__ == "__main__":
    import uvicorn
    cfg = app.state.config
    port = int(os.environ.get("GRBLWHEEL_PORT", cfg["server"]["port"]))
    try:
        uvicorn.run(
            "grblwheel.main:app",
            host=cfg["server"]["host"],
            port=port,
            reload=os.environ.get("GRBLWHEEL_RELOAD", "0") == "1",
        )
    except OSError as e:
        if "10048" in str(e) or "address already in use" in str(e).lower() or "Errno 98" in str(e):
            print(f"Port {port} is already in use. Stop the other process or use a different port:")
            print(f"  PowerShell: $env:GRBLWHEEL_PORT=8766; py -m grblwheel.main")
            print(f"  Cmd:        set GRBLWHEEL_PORT=8766 && py -m grblwheel.main")
        raise
