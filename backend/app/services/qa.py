from app.core.config import settings
from app.schemas import Citation, QueryOut
from app.services.index import search


def answer_question(question: str, top_k: int, jurisdiction: str | None = None) -> QueryOut:
    hits = search(question, top_k, jurisdiction)
    citations = []
    for hit in hits:
        p = hit.payload or {}
        citations.append(Citation(
            document_id=p.get("document_id", ""), document_title=p.get("document_title", "Unknown document"),
            section=p.get("section"), source_url=p.get("source_url"), excerpt=p.get("text", ""), score=float(hit.score or 0),
        ))
    if not citations:
        return QueryOut(answer="No indexed legal evidence was found for this question. Add a validated legal document, then try again.", citations=[], evidence_sufficient=False)
    if citations[0].score < settings.retrieval_similarity_threshold:
        return QueryOut(answer="The indexed documents returned only weakly related excerpts. There is not enough evidence to answer this question reliably.", citations=citations, evidence_sufficient=False)
    if not settings.openai_api_key:
        answer = "Retrieved source excerpts are provided below. Configure OPENAI_API_KEY to generate a concise answer grounded in these excerpts."
        return QueryOut(answer=answer, citations=citations, evidence_sufficient=True)
    from openai import OpenAI
    evidence = "\n\n".join(f"[{i+1}] {c.document_title} — {c.section or 'unlabelled section'}\n{c.excerpt}" for i, c in enumerate(citations))
    response = OpenAI(api_key=settings.openai_api_key).chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "Answer only from supplied legal evidence. Clearly state uncertainty and avoid legal advice. Cite claims using [1], [2] matching evidence order. If evidence is insufficient, say so."},
            {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{evidence}"},
        ], temperature=0.1,
    )
    return QueryOut(answer=response.choices[0].message.content or "Insufficient evidence to answer.", citations=citations, evidence_sufficient=True)
