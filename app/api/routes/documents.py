import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.schemas import DocumentUploadResponse, DocumentStatusResponse, DocumentListItem
from app.models.db import Document, RiskAnalysis, User
from app.services.parser import parse_pdf, get_page_count
from app.services.vector_store import index_document
from app.services.risk_analyzer import analyze_document_risks
from app.core.config import settings
from app.api.deps import get_db, get_current_user

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=list[DocumentListItem])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(Document.user_id == current_user.id).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return [
        DocumentListItem(
            document_id=d.id,
            filename=d.filename,
            status=d.status,
            chunk_count=d.chunk_count,
            page_count=d.page_count,
            file_size_bytes=d.file_size_bytes,
            created_at=d.created_at,
        )
        for d in docs
    ]


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB.")

    document_id = str(uuid.uuid4())

    clauses = parse_pdf(file_bytes)
    page_count = get_page_count(file_bytes)

    if not clauses:
        raise HTTPException(status_code=422, detail="Could not extract text from PDF. Is it scanned?")

    doc = Document(
        id=document_id,
        user_id=current_user.id,
        filename=file.filename,
        file_size_bytes=len(file_bytes),
        page_count=page_count,
        chunk_count=len(clauses),
        status="indexing",
    )
    db.add(doc)

    risk = RiskAnalysis(document_id=document_id, status="pending")
    db.add(risk)
    await db.commit()

    chunk_count = await index_document(document_id, clauses)

    doc.status = "ready"
    doc.chunk_count = chunk_count
    await db.commit()

    analyze_document_risks.delay(document_id)

    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        page_count=page_count,
        chunk_count=chunk_count,
        status="ready",
        message="Document indexed. Risk analysis running in background.",
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentStatusResponse(
        document_id=doc.id,
        filename=doc.filename,
        status=doc.status,
        chunk_count=doc.chunk_count,
        page_count=doc.page_count,
        file_size_bytes=doc.file_size_bytes,
        created_at=doc.created_at,
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    from app.services.vector_store import delete_document as qdrant_delete
    await qdrant_delete(document_id)

    await db.delete(doc)
    await db.commit()

    return {"message": f"Document {document_id} deleted."}
