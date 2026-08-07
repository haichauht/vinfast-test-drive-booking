import logging
import time
import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.api.site_routes import router as site_router
from src.config import get_settings
from src.dependencies import booking_service, database, zalo_client
from src.logging_config import configure_logging
from src.services.zalo_bot import ZaloPollingService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logging.getLogger(__name__).info("Starting %s in %s mode", settings.app_name, settings.app_env)
    polling_task = None
    notification_task = None
    if settings.zalo_bot_enabled and settings.zalo_bot_polling_enabled and zalo_client:
        polling_task = asyncio.create_task(
            ZaloPollingService(database, zalo_client, settings.zalo_bot_poll_timeout_seconds).run()
        )
        logging.getLogger(__name__).info("Zalo Bot polling enabled")
    async def dispatch_notifications() -> None:
        while True:
            try:
                await asyncio.to_thread(booking_service.dispatch_due_notifications)
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.getLogger(__name__).exception("Notification dispatch failed")
            await asyncio.sleep(5)

    notification_task = asyncio.create_task(dispatch_notifications())
    yield
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
    if notification_task:
        notification_task.cancel()
        try:
            await notification_task
        except asyncio.CancelledError:
            pass
    logging.getLogger(__name__).info("Shutting down")


app = FastAPI(
    title="AI20K Agent",
    description="AI Agent built with LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
media_root = Path(settings.media_root).resolve()
media_root.mkdir(parents=True, exist_ok=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging(request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
        logging.getLogger("http").info(
            "%s %s -> %s %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - started) * 1000,
        )
        return response
    except Exception:
        logging.getLogger("http").exception("Unhandled error: %s %s", request.method, request.url.path)
        raise


app.include_router(router, prefix="/api/v1")
app.include_router(site_router, prefix="/api/v1")
app.mount("/media", StaticFiles(directory=media_root), name="media")


@app.get("/api/v1/echo")
async def echo(text: str = "Hello") -> dict[str, str]:
    return {
        "status": "ok",
        "echo": text,
        "time": datetime.now(UTC).isoformat(),
    }


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}
