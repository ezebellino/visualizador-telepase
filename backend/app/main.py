from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .schemas import DashboardResponse
from .services import build_dashboard_response

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

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


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/dashboard/analyze", response_model=DashboardResponse)
async def analyze_dashboard(
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
