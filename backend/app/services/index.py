from functools import lru_cache
from uuid import uuid5, NAMESPACE_URL

from qdrant_client import QdrantClient, models

from app.core.config import settings

COLLECTION = "legal_knowledge"
COMPANY_COLLECTION = "company_knowledge"


@lru_cache
def embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


@lru_cache
def qdrant() -> QdrantClient:
    if settings.qdrant_mode.lower() == "local":
        settings.qdrant_local_path.parent.mkdir(parents=True, exist_ok=True)
        return QdrantClient(path=str(settings.qdrant_local_path))
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def ensure_collection() -> None:
    _ensure_collection(COLLECTION, indexes={"jurisdiction": models.PayloadSchemaType.KEYWORD})


def _ensure_collection(name: str, indexes: dict[str, models.PayloadSchemaType]) -> None:
    client = qdrant()
    if not client.collection_exists(name):
        client.create_collection(name, vectors_config=models.VectorParams(size=settings.embedding_dimension, distance=models.Distance.COSINE))
    for field, schema in indexes.items():
        client.create_payload_index(name, field, schema)


def index_chunks(document_id: str, chunks: list[dict]) -> None:
    ensure_collection()
    vectors = embedder().encode([c["text"] for c in chunks], normalize_embeddings=True).tolist()
    points = []
    for chunk, vector in zip(chunks, vectors):
        point_id = str(uuid5(NAMESPACE_URL, chunk["id"]))
        points.append(models.PointStruct(id=point_id, vector=vector, payload={**chunk, "document_id": document_id}))
    qdrant().upsert(collection_name=COLLECTION, points=points, wait=True)


def delete_document_vectors(collection_name: str, document_id: str, id_field: str = "document_id") -> None:
    if not qdrant().collection_exists(collection_name):
        return
    qdrant().delete(
        collection_name=collection_name,
        points_selector=models.FilterSelector(
            filter=models.Filter(must=[models.FieldCondition(key=id_field, match=models.MatchValue(value=document_id))])
        ),
        wait=True,
    )


def search(question: str, top_k: int, jurisdiction: str | None = None):
    ensure_collection()
    vector = embedder().encode(question, normalize_embeddings=True).tolist()
    query_filter = None
    if jurisdiction:
        query_filter = models.Filter(must=[models.FieldCondition(key="jurisdiction", match=models.MatchValue(value=jurisdiction.upper()))])
    return qdrant().query_points(collection_name=COLLECTION, query=vector, query_filter=query_filter, limit=top_k, with_payload=True).points


def index_company_chunks(company_id: str, document_id: str, chunks: list[dict]) -> None:
    _ensure_collection(COMPANY_COLLECTION, indexes={"company_id": models.PayloadSchemaType.KEYWORD})
    vectors = embedder().encode([c["text"] for c in chunks], normalize_embeddings=True).tolist()
    points = []
    for chunk, vector in zip(chunks, vectors):
        point_id = str(uuid5(NAMESPACE_URL, chunk["id"]))
        points.append(models.PointStruct(id=point_id, vector=vector, payload={**chunk, "company_id": company_id, "company_document_id": document_id}))
    qdrant().upsert(collection_name=COMPANY_COLLECTION, points=points, wait=True)


def delete_company_document_vectors(document_id: str) -> None:
    delete_document_vectors(COMPANY_COLLECTION, document_id, id_field="company_document_id")


def search_company(question: str, top_k: int, company_id: str):
    _ensure_collection(COMPANY_COLLECTION, indexes={"company_id": models.PayloadSchemaType.KEYWORD})
    vector = embedder().encode(question, normalize_embeddings=True).tolist()
    query_filter = models.Filter(must=[models.FieldCondition(key="company_id", match=models.MatchValue(value=company_id))])
    return qdrant().query_points(collection_name=COMPANY_COLLECTION, query=vector, query_filter=query_filter, limit=top_k, with_payload=True).points
