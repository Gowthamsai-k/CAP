from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Prepare local storage before serving requests."""
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.company_upload_path.mkdir(parents=True, exist_ok=True)
    settings.qdrant_local_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.3.0",
    description="Source-grounded legal research with an isolated local G Inc demo workspace.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(health_router, tags=["health"])
app.include_router(api_router, prefix=settings.api_prefix)
