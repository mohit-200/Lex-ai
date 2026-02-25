from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.schemas import QueryRequest, QueryResponse
from app.models.db import Document, QueryLog
from app.services.rag_engine import query_document
from app.api.deps import get_db

router = APIRouter(prefix="/documents", tags=["Query"])


@router.post("/{document_id}/query", response_model=QueryResponse)
async def query(
    document_id: str,
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ask a natural language question about a document.

    Returns:
    - answer: grounded answer with clause references
    - confidence: 0.0-1.0 retrieval confidence score
    - is_confident: False means you should verify manually
    - sources: exact clauses used to generate the answer
    - latency_ms: total response time
    """
    # Verify document exists and is ready
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.status != "ready":
        raise HTTPException(status_code=400, detail=f"Document is not ready yet. Status: {doc.status}")

    response = await query_document(
        document_id=document_id,
        query=request.query,
        top_k=request.top_k,
    )

    # Log the query for later RAGAS evaluation
    log = QueryLog(
        document_id=document_id,
        query=request.query,
        answer=response.answer,
        confidence=response.confidence,
        sources_count=len(response.sources),
        latency_ms=response.latency_ms,
    )
    db.add(log)
    await db.commit()

    return response
