import logging

from fastapi import APIRouter
from qdrant_client import QdrantClient
from redis import Redis

from app.core.config import settings
from app.db import engine
from app.services.index import qdrant

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    result = {"status": "ok", "database": "unknown", "qdrant": "unknown", "redis": "not_configured"}
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        result["database"] = "ok"
    except Exception:
        result["database"] = "unavailable"
        logger.exception("Database health check failed")

    try:
        if settings.qdrant_mode.lower() == "local":
            qdrant().get_collections()
        else:
            QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key).get_collections()
        result["qdrant"] = "ok"
    except Exception:
        result["qdrant"] = "unavailable"
        logger.exception("Qdrant health check failed")

    if settings.redis_url:
        try:
            Redis.from_url(settings.redis_url, socket_timeout=1).ping()
            result["redis"] = "ok"
        except Exception:
            result["redis"] = "unavailable"
            logger.exception("Redis health check failed")

    result["status"] = "ok" if result["database"] == result["qdrant"] == "ok" else "degraded"
    return result
