"""
Vector store service.
Handles embedding generation and all Qdrant operations.
"""
import uuid
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue, ScoredPoint
)
from app.core.config import settings
from app.services.parser import Clause


client = AsyncOpenAI(api_key=settings.openai_api_key)
qdrant = AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

VECTOR_SIZE = 1536  # text-embedding-3-small output size


async def ensure_collection():
    """Create Qdrant collection if it doesn't exist."""
    collections = await qdrant.get_collections()
    names = [c.name for c in collections.collections]
    if settings.qdrant_collection not in names:
        await qdrant.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


async def embed_text(text: str) -> list[float]:
    """Generate embedding for a single text."""
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=text,
    )
    return response.data[0].embedding


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts (more efficient)."""
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


async def index_document(document_id: str, clauses: list[Clause]) -> int:
    """
    Embed all clauses and store them in Qdrant with metadata.
    Returns number of chunks indexed.
    """
    await ensure_collection()

    texts = [clause.text for clause in clauses]
    embeddings = await embed_batch(texts)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "document_id": document_id,
                "text": clause.text,
                "page": clause.page,
                "clause_number": clause.clause_number,
                "section_title": clause.section_title,
            }
        )
        for clause, embedding in zip(clauses, embeddings)
    ]

    # Upsert in batches of 100 to avoid memory issues with large docs
    batch_size = 100
    for i in range(0, len(points), batch_size):
        await qdrant.upsert(
            collection_name=settings.qdrant_collection,
            points=points[i:i + batch_size],
        )

    return len(points)


async def search(document_id: str, query: str, top_k: int = 6) -> list[ScoredPoint]:
    """
    Semantic search within a specific document.
    Filters by document_id so queries don't bleed across documents.
    """
    query_embedding = await embed_text(query)

    results = await qdrant.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_embedding,
        query_filter=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
        limit=top_k,
        with_payload=True,
        score_threshold=0.3,  # Filter out very low quality matches
    )

    return results


async def get_all_clauses(document_id: str) -> list[dict]:
    """
    Retrieve all stored clauses for a document (used by risk analyzer).
    """
    results, _ = await qdrant.scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
        limit=500,
        with_payload=True,
        with_vectors=False,
    )
    return [point.payload for point in results]


async def delete_document(document_id: str):
    """Remove all vectors for a document from Qdrant."""
    await qdrant.delete(
        collection_name=settings.qdrant_collection,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
    )
