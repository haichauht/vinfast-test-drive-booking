import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.config import get_settings
from src.observability import configure_langsmith

# Configure before importing graph/routes so LangChain and LangGraph see the
# canonical LANGSMITH_* variables during their initialization.
settings = get_settings()
configure_langsmith(settings)

from src.agents.graph import close_persistent_agent, initialize_persistent_agent
from src.api.routes import router
from src.api.site_routes import router as site_router
from src.bootstrap import initialize_database
from src.dependencies import booking_service, database, zalo_client
from src.internal_portal.errors import InternalPortalError
from src.internal_portal.routes import router as internal_router
from src.logging_config import configure_logging
from src.security.rate_limit import RateLimitMiddleware
from src.services.zalo_bot import ZaloPollingService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    initialize_database(database, settings)
    await initialize_persistent_agent(
        settings.database_url,
        required=settings.app_env == "production",
    )
    logging.getLogger(__name__).info("Starting %s in %s mode", settings.app_name, settings.app_env)
    polling_task = None
    notification_task = None
    if settings.zalo_bot_enabled and settings.zalo_bot_polling_enabled and zalo_client:
        polling_task = asyncio.create_task(
            ZaloPollingService(
                database,
                zalo_client,
                settings.zalo_bot_poll_timeout_seconds,
                settings.zalo_bot_processed_message_retention_days,
            ).run()
        )
        logging.getLogger(__name__).info("Zalo Bot polling enabled")

    async def dispatch_notifications() -> None:
        while True:
            try:
                await asyncio.to_thread(
                    booking_service.dispatch_due_notifications,
                    settings.notification_batch_size,
                    settings.notification_processing_timeout_seconds,
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.getLogger(__name__).exception("Notification dispatch failed")
            await asyncio.sleep(settings.notification_poll_interval_seconds)

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
    await close_persistent_agent()
    logging.getLogger(__name__).info("Shutting down")


app = FastAPI(
    title="AI20K Agent",
    description="AI Agent built with LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

media_root = Path(settings.media_root).resolve()
media_root.mkdir(parents=True, exist_ok=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, database=database, settings=settings)


@app.exception_handler(InternalPortalError)
async def internal_portal_error_handler(_request, exc: InternalPortalError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": {"code": exc.code, "message": str(exc)}},
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
app.include_router(internal_router, prefix="/api/v1")
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
