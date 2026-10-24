"""
RAG Knowledge Base API Router — Document Upload, Search, and Management
Corresponds to Master Specification Section 22 & 36.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_current_user, get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.document import (
    ChunkResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadRequest,
    RAGContext,
    SearchRequest,
    SearchResponse,
)
from app.services.rag_service import rag_service

router = APIRouter()


# --------------------------------------------------------------------------
# Document Ingestion
# --------------------------------------------------------------------------

@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    request: DocumentUploadRequest,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and process a document through the RAG pipeline:
    parse → chunk → embed → index.
    """
    try:
        doc = await rag_service.ingest_document(
            db=db,
            organization_id=tenant.id,
            title=request.title,
            raw_text=request.raw_text,
            filename=f"{request.title.lower().replace(' ', '_')}.txt",
            document_type=request.document_type,
            department=request.department,
            product=request.product,
            source=request.source,
            tags=request.tags,
        )
        return DocumentResponse.model_validate(doc)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document ingestion failed: {str(e)}",
        )


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------

@router.post("/search", response_model=SearchResponse)
async def search_knowledge_base(
    request: SearchRequest,
    tenant: Organization = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Hybrid search across the enterprise knowledge base.
    Supports semantic, keyword, and hybrid search modes
    with metadata filtering and optional reranking.
    """
    return await rag_service.search(db, tenant.id, request)


@router.post("/context", response_model=RAGContext)
async def get_rag_context(
    request: SearchRequest,
    tenant: Organization = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve assembled RAG context with citation tracking.
    Designed for agent consumption during workflow execution.
    """
    return await rag_service.get_rag_context(
        db=db,
        organization_id=tenant.id,
        query=request.query,
        top_k=request.top_k,
        document_type=request.document_type,
        product=request.product,
    )


# --------------------------------------------------------------------------
# Document Management
# --------------------------------------------------------------------------

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    document_type: Optional[str] = Query(default=None),
    doc_status: Optional[str] = Query(default=None, alias="status"),
    tenant: Organization = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List all documents in the organization's knowledge base."""
    documents, total = await rag_service.list_documents(
        db=db,
        organization_id=tenant.id,
        skip=skip,
        limit=limit,
        document_type=document_type,
        status=doc_status,
    )
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    tenant: Organization = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a document by ID."""
    doc = await rag_service.get_document(db, document_id, tenant.id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return DocumentResponse.model_validate(doc)


@router.get(
    "/documents/{document_id}/chunks",
    response_model=List[ChunkResponse],
)
async def get_document_chunks(
    document_id: str,
    tenant: Organization = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all chunks for a document with their metadata."""
    doc = await rag_service.get_document(db, document_id, tenant.id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    chunks = await rag_service.get_document_chunks(db, document_id, tenant.id)
    return [
        ChunkResponse(
            id=c.id,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            content=c.content,
            token_count=c.token_count,
            metadata=c.chunk_metadata or {},
            has_embedding=c.embedding is not None,
        )
        for c in chunks
    ]


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: str,
    tenant: Organization = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a document from the knowledge base."""
    success = await rag_service.delete_document(db, document_id, tenant.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return None
