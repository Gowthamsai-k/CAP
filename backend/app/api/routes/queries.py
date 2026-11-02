import logging

from fastapi import APIRouter, HTTPException

from app.schemas import QueryIn, QueryOut
from app.services.qa import answer_question

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=QueryOut)
def query(request: QueryIn):
    try:
        return answer_question(request.question, request.top_k, request.jurisdiction)
    except Exception as exc:
        logger.exception("Question-answering request failed")
        raise HTTPException(503, "Legal retrieval is temporarily unavailable.") from exc
