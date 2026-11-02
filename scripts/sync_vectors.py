#!/usr/bin/env python3
"""Syncs existing chunks from SQLite compliance.db into local Qdrant if empty."""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db import SessionLocal
from app.models import LegalDocument, LegalChunk, CompanyDocument, CompanyChunk
from app.services.index import (
    qdrant,
    ensure_collection,
    index_chunks,
    index_company_chunks,
    COLLECTION,
    COMPANY_COLLECTION,
)


def sync():
    db = SessionLocal()
    client = qdrant()
    ensure_collection()

    # 1. Sync legal knowledge
    try:
        legal_count = client.count(COLLECTION).count
    except Exception:
        legal_count = 0

    if legal_count == 0:
        docs = db.query(LegalDocument).all()
        for doc in docs:
            chunks = db.query(LegalChunk).filter(LegalChunk.document_id == doc.id).all()
            if not chunks:
                continue
            records = []
            for c in chunks:
                records.append({
                    "id": c.id,
                    "text": c.text,
                    "section": c.section,
                    "document_title": doc.title,
                    "jurisdiction": doc.jurisdiction,
                    "country": doc.country,
                    "domain": doc.domain,
                    "source_url": doc.source_url,
                })
            print(f"Indexing {len(records)} legal sections for: {doc.title}...")
            index_chunks(doc.id, records)
        print("Legal vector index is up to date.")
    else:
        print(f"Legal vector collection already has {legal_count} points.")

    # 2. Sync company knowledge
    try:
        company_count = client.count(COMPANY_COLLECTION).count
    except Exception:
        company_count = 0

    if company_count == 0:
        cdocs = db.query(CompanyDocument).all()
        for cdoc in cdocs:
            cchunks = db.query(CompanyChunk).filter(CompanyChunk.company_document_id == cdoc.id).all()
            if not cchunks:
                continue
            records = []
            for c in cchunks:
                records.append({
                    "id": c.id,
                    "text": c.text,
                    "section": c.section,
                    "document_title": cdoc.title,
                })
            print(f"Indexing {len(records)} company sections for: {cdoc.title}...")
            index_company_chunks(cdoc.company_id, cdoc.id, records)
        if cdocs:
            print("Company vector index is up to date.")

    db.close()


if __name__ == "__main__":
    sync()
