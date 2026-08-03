from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.config import get_settings
from src.logging_config import configure_logging
import logging
import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logging.getLogger(__name__).info("Starting %s in %s mode",settings.app_name,settings.app_env)
    yield
    logging.getLogger(__name__).info("Shutting down")


app = FastAPI(
    title="AI20K Agent",
    description="AI Agent built with LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_logging(request,call_next):
    started=time.perf_counter()
    try:
        response=await call_next(request)
        logging.getLogger("http").info("%s %s -> %s %.1fms",request.method,request.url.path,response.status_code,(time.perf_counter()-started)*1000)
        return response
    except Exception:
        logging.getLogger("http").exception("Unhandled error: %s %s",request.method,request.url.path)
        raise

app.include_router(router, prefix="/api/v1")

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

