from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Literal


class DocumentOut(BaseModel):
    id: str
    title: str
    filename: str
    jurisdiction: str | None
    country: str | None
    domain: str | None
    authority: str | None
    document_type: str | None
    industry: str | None
    source_url: str | None
    version: str | None
    publication_date: date | None
    effective_from: date | None
    effective_to: date | None
    document_status: str
    chunks_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryIn(BaseModel):
    question: str = Field(min_length=5, max_length=4000)
    jurisdiction: str | None = Field(default=None, max_length=16)
    top_k: int = Field(default=5, ge=1, le=12)


class Citation(BaseModel):
    document_id: str
    document_title: str
    section: str | None
    source_url: str | None
    excerpt: str
    score: float


class QueryOut(BaseModel):
    answer: str
    citations: list[Citation]
    evidence_sufficient: bool
    disclaimer: str = "Research support only; this is not legal advice. Verify the cited source and applicability with qualified counsel."


class CompanyDocumentOut(BaseModel):
    id: str
    title: str
    filename: str
    document_type: str
    chunks_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewIn(BaseModel):
    question: str = Field(min_length=5, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=12)


class EvidenceRef(BaseModel):
    evidence_id: str
    title: str
    section: str | None
    excerpt: str
    source_url: str | None = None


class ReviewFinding(BaseModel):
    status: Literal["addressed_in_part", "potential_gap", "missing_company_evidence", "insufficient_legal_evidence"]
    issue: str
    analysis: str
    recommended_action: str
    legal_evidence_ids: list[str]
    company_evidence_ids: list[str]
    human_review_required: bool = True


class ReviewDraftFinding(BaseModel):
    status: Literal["addressed_in_part", "potential_gap", "missing_company_evidence", "insufficient_legal_evidence"]
    issue: str
    analysis: str
    recommended_action: str
    legal_evidence_ids: list[str]
    company_evidence_ids: list[str]


class ReviewDraft(BaseModel):
    summary: str
    findings: list[ReviewDraftFinding]


class ReviewOut(BaseModel):
    summary: str
    findings: list[ReviewFinding]
    legal_evidence: list[EvidenceRef]
    company_evidence: list[EvidenceRef]
    analysis_generated: bool
    disclaimer: str = "Demo research aid, not legal advice or a compliance certification. Verify every finding and the applicable legal dates with qualified counsel."
