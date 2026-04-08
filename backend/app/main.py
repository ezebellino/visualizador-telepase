from __future__ import annotations

import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .observability import configure_logging, log_event
from .schemas import DashboardResponse
from .services import build_dashboard_response

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
logger = configure_logging()

app = FastAPI(
    title="Telepase Control Center API",
    version="2.0.0",
    summary="Backend para dashboards operativos Telepase con FastAPI.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_observability(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        log_event(
            logger,
            "request_failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query=str(request.url.query),
            duration_ms=duration_ms,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        raise

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers["x-request-id"] = request_id
    log_event(
        logger,
        "request_completed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/dashboard/analyze", response_model=DashboardResponse)
async def analyze_dashboard(
    request: Request,
    file: UploadFile = File(...),
    vias: str | None = Form(default=None),
    sentidos: str | None = Form(default=None),
    patente: str | None = Form(default=None),
    start_time: str | None = Form(default=None),
    end_time: str | None = Form(default=None),
) -> DashboardResponse:
    selected_vias = [item.strip() for item in vias.split(",")] if vias else None
    selected_sentidos = [item.strip() for item in sentidos.split(",")] if sentidos else None
    return await build_dashboard_response(
        request_id=request.state.request_id,
        uploaded_file=file,
        vias=selected_vias,
        sentidos=selected_sentidos,
        patente=patente,
        start_time=start_time,
        end_time=end_time,
    )


if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/")
    def frontend_index() -> FileResponse:
        return FileResponse(FRONTEND_DIST / "index.html")


    @app.get("/{full_path:path}")
    def frontend_spa_fallback(full_path: str) -> FileResponse:
        target = FRONTEND_DIST / full_path
        if full_path and target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(FRONTEND_DIST / "index.html")
