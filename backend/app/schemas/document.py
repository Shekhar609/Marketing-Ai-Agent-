"""
RAG Document Schemas - Request/Response Models
Corresponds to Master Specification Section 22 & 36.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Document Schemas
# --------------------------------------------------------------------------

class DocumentUploadRequest(BaseModel):
    """Request body for uploading a document to the knowledge base."""
    title: str = Field(..., min_length=1, max_length=500)
    document_type: str = Field(default="other")
    department: Optional[str] = None
    product: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    raw_text: str = Field(..., min_length=1, description="The text content of the document")


class DocumentResponse(BaseModel):
    """Response schema for a document record."""
    id: str
    organization_id: str
    title: str
    filename: str
    content_type: str
    document_type: str
    status: str
    department: Optional[str] = None
    product: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    total_chunks: int = 0
    total_tokens: int = 0
    embedding_model: Optional[str] = None
    processing_time_ms: float = 0.0
    error_message: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""
    documents: List[DocumentResponse]
    total: int
    skip: int
    limit: int


# --------------------------------------------------------------------------
# Search Schemas
# --------------------------------------------------------------------------

class SearchRequest(BaseModel):
    """Hybrid search request combining semantic and keyword search."""
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=50)
    # Metadata filters (Section 22)
    document_type: Optional[str] = None
    department: Optional[str] = None
    product: Optional[str] = None
    tags: Optional[List[str]] = None
    # Search mode
    search_mode: str = Field(
        default="hybrid",
        description="Search mode: 'semantic', 'keyword', or 'hybrid'"
    )
    # Reranking
    rerank: bool = Field(default=True, description="Apply LLM-based reranking to results")


class SearchResultItem(BaseModel):
    """A single search result from the knowledge base."""
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    score: float = Field(description="Relevance score (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Citation tracking (Section 49)
    source: Optional[str] = None
    document_type: Optional[str] = None
    chunk_index: int = 0


class SearchResponse(BaseModel):
    """Response from a knowledge base search."""
    query: str
    results: List[SearchResultItem]
    total_results: int
    search_mode: str
    reranked: bool = False
    processing_time_ms: float = 0.0


# --------------------------------------------------------------------------
# Chunk Schemas
# --------------------------------------------------------------------------

class ChunkResponse(BaseModel):
    """Response schema for a document chunk."""
    id: str
    document_id: str
    chunk_index: int
    content: str
    token_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    has_embedding: bool = False

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------
# RAG Context Schemas (for agent consumption)
# --------------------------------------------------------------------------

class RAGContext(BaseModel):
    """Assembled RAG context for agent consumption with citation tracking."""
    context_text: str = Field(description="Assembled context passages")
    sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Citation sources with document references"
    )
    total_tokens: int = 0
    query: str = ""
