import hashlib
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import CompanyChunk, CompanyDocument
from app.schemas import CompanyDocumentOut, ReviewIn, ReviewOut
from app.services.compliance import review_g_inc
from app.services.index import delete_company_document_vectors, index_company_chunks
from app.services.parsing import company_chunks

logger = logging.getLogger(__name__)
router = APIRouter()


def require_local_demo() -> None:
    if settings.is_production:
        raise HTTPException(404, "The single-company demo workspace is disabled in production.")


@router.get("/documents", response_model=list[CompanyDocumentOut])
def list_company_documents(db: Session = Depends(get_db)):
    require_local_demo()
    statement = (
        select(CompanyDocument)
        .where(CompanyDocument.company_id == settings.demo_company_id)
        .order_by(CompanyDocument.created_at.desc())
    )
    return db.scalars(statement).all()


@router.post("/documents/upload", response_model=CompanyDocumentOut)
async def upload_company_document(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    db: Session = Depends(get_db),
):
    require_local_demo()
    if Path(file.filename or "").suffix.lower() != ".md":
        raise HTTPException(415, "The G Inc demo accepts Markdown policy drafts (.md) only.")

    contents = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Maximum upload size is {settings.max_upload_mb} MB.")

    digest = hashlib.sha256(contents).hexdigest()
    duplicate = db.scalar(select(CompanyDocument).where(
        CompanyDocument.company_id == settings.demo_company_id,
        CompanyDocument.content_hash == digest,
    ))
    if duplicate:
        raise HTTPException(409, f"This G Inc file is already registered as document {duplicate.id}.")

    document_id = str(uuid4())
    path = settings.company_upload_path / f"{document_id}.md"
    path.write_bytes(contents)
    try:
        pieces = company_chunks(contents.decode("utf-8-sig"))
        if not pieces:
            raise ValueError("No text chunks could be created.")

        document = CompanyDocument(
            id=document_id,
            company_id=settings.demo_company_id,
            title=title or Path(file.filename or "G Inc policy").stem,
            filename=file.filename or path.name,
            content_hash=digest,
            document_type="internal_policy_draft",
            chunks_count=len(pieces),
        )
        db.add(document)
        db.flush()

        records = []
        for index, (section, chunk_text) in enumerate(pieces):
            chunk = CompanyChunk(
                id=str(uuid4()),
                company_document_id=document_id,
                company_id=settings.demo_company_id,
                section=section,
                text=chunk_text,
                chunk_index=index,
                payload={"document_title": document.title, "source_type": "company", "company_id": settings.demo_company_id},
            )
            db.add(chunk)
            records.append({"id": chunk.id, "text": chunk_text, "section": section, "document_title": document.title})

        index_company_chunks(settings.demo_company_id, document_id, records)
        db.commit()
        return document
    except Exception as exc:
        db.rollback()
        try:
            delete_company_document_vectors(document_id)
        except Exception:
            logger.exception("Could not roll back vector points for failed G Inc ingestion")
        path.unlink(missing_ok=True)
        logger.exception("G Inc demo policy ingestion failed")
        if isinstance(exc, (ValueError, UnicodeDecodeError)):
            raise HTTPException(422, f"Company document ingestion failed: {exc}") from exc
        raise HTTPException(503, "G Inc policy indexing is temporarily unavailable.") from exc


@router.post("/review", response_model=ReviewOut)
def company_review(request: ReviewIn):
    require_local_demo()
    try:
        return review_g_inc(request.question, request.top_k)
    except Exception as exc:
        logger.exception("G Inc demo compliance review failed")
        raise HTTPException(503, "Company review is temporarily unavailable.") from exc
