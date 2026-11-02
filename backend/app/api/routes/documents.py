import hashlib
import logging
from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import LegalChunk, LegalDocument
from app.schemas import DocumentOut
from app.services.index import delete_document_vectors, index_chunks, COLLECTION
from app.services.parsing import extract_text, legal_chunks

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    statement = select(LegalDocument).order_by(LegalDocument.created_at.desc())
    return db.scalars(statement).all()


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    jurisdiction: str | None = Form(None),
    country: str | None = Form(None),
    domain: str | None = Form(None),
    industry: str | None = Form(None),
    authority: str | None = Form(None),
    document_type: str | None = Form(None),
    source_url: str | None = Form(None),
    version: str | None = Form(None),
    publication_date: date | None = Form(None),
    effective_from: date | None = Form(None),
    effective_to: date | None = Form(None),
    document_status: str = Form("unknown"),
    db: Session = Depends(get_db),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(415, "Upload a PDF or DOCX legal document.")

    contents = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Maximum upload size is {settings.max_upload_mb} MB.")

    digest = hashlib.sha256(contents).hexdigest()
    duplicate = db.scalar(select(LegalDocument).where(LegalDocument.content_hash == digest))
    if duplicate:
        raise HTTPException(409, f"This file is already registered as document {duplicate.id}.")

    document_id = str(uuid4())
    path = settings.upload_path / f"{document_id}{suffix}"
    path.write_bytes(contents)
    try:
        pieces = legal_chunks(extract_text(path))
        if not pieces:
            raise ValueError("No text chunks could be created.")

        document = LegalDocument(
            id=document_id,
            title=title or Path(file.filename or "Legal document").stem,
            filename=file.filename or path.name,
            content_hash=digest,
            jurisdiction=jurisdiction.upper() if jurisdiction else None,
            country=country,
            domain=domain,
            authority=authority,
            document_type=document_type,
            industry=industry,
            source_url=source_url,
            version=version,
            publication_date=publication_date,
            effective_from=effective_from,
            effective_to=effective_to,
            document_status=document_status,
            chunks_count=len(pieces),
            metadata_json={"source_classification": "user_supplied_legal", "status_was_user_supplied": True},
        )
        db.add(document)
        db.flush()

        records = []
        for index, (section, chunk_text) in enumerate(pieces):
            chunk = LegalChunk(
                id=str(uuid4()),
                document_id=document_id,
                section=section,
                text=chunk_text,
                chunk_index=index,
                payload={"document_title": document.title, "jurisdiction": document.jurisdiction, "country": country,
                         "domain": domain, "source_url": source_url},
            )
            db.add(chunk)
            records.append({
                "id": chunk.id,
                "text": chunk_text,
                "section": section,
                "document_title": document.title,
                "jurisdiction": document.jurisdiction,
                "country": country,
                "domain": domain,
                "source_url": source_url,
            })

        index_chunks(document_id, records)
        db.commit()
        return document
    except Exception as exc:
        db.rollback()
        try:
            delete_document_vectors(COLLECTION, document_id)
        except Exception:
            logger.exception("Could not roll back vector points for failed ingestion")
        path.unlink(missing_ok=True)
        logger.exception("Legal document ingestion failed")
        if isinstance(exc, ValueError):
            raise HTTPException(422, f"Ingestion failed: {exc}") from exc
        raise HTTPException(503, "Legal document indexing is temporarily unavailable.") from exc
