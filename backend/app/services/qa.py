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
    if not settings.is_llm_available:
        answer = "Retrieved source excerpts are provided below. Configure Ollama or OPENAI_API_KEY to generate a concise answer grounded in these excerpts."
        return QueryOut(answer=answer, citations=citations, evidence_sufficient=True)
    from openai import OpenAI
    evidence = "\n\n".join(f"[{i+1}] {c.document_title} — {c.section or 'unlabelled section'}\n{c.excerpt}" for i, c in enumerate(citations))
    client_kwargs = {"api_key": settings.openai_api_key or "ollama"}
    if settings.active_llm_base_url:
        client_kwargs["base_url"] = settings.active_llm_base_url
    try:
        response = OpenAI(**client_kwargs).chat.completions.create(
            model=settings.active_llm_model,
            messages=[
                {"role": "system", "content": "Answer only from supplied legal evidence. Clearly state uncertainty and avoid legal advice. Cite claims using [1], [2] matching evidence order. If evidence is insufficient, say so."},
                {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{evidence}"},
            ], temperature=0.1,
        )
        return QueryOut(answer=response.choices[0].message.content or "Insufficient evidence to answer.", citations=citations, evidence_sufficient=True)
    except Exception as exc:
        return QueryOut(
            answer=f"Note: Local LLM ({settings.active_llm_model}) is currently offline or unreachable at {settings.active_llm_base_url or 'OpenAI'}. Verified legal excerpts are displayed below.",
            citations=citations,
            evidence_sufficient=True,
        )
