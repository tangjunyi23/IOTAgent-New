from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, ensure_directories, get_settings
from app.manager import ManagerAgentService
from app.realtime import AuditEventBroker
from app.repository import JsonRepository
from app.routes import router


def create_app(settings_override: Settings | None = None) -> FastAPI:
    settings = settings_override or get_settings()
    ensure_directories(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository = JsonRepository(settings)
        broker = AuditEventBroker()
        app.state.settings = settings
        app.state.repository = repository
        app.state.broker = broker
        app.state.manager = ManagerAgentService(settings, repository, broker)
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(router, prefix=settings.api_prefix)

    static_dir = settings.frontend_dir / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def frontend_index() -> FileResponse:
        return FileResponse(settings.frontend_dir / "index.html")

    return app


app = create_app()
