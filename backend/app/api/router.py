from fastapi import APIRouter

from app.api.routes.company import router as company_router
from app.api.routes.documents import router as documents_router
from app.api.routes.queries import router as queries_router

api_router = APIRouter()
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(queries_router, prefix="/query", tags=["query"])
api_router.include_router(company_router, prefix="/company", tags=["company demo"])
