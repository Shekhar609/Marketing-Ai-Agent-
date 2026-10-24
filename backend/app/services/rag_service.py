"""
Enterprise RAG Service — Document Processing, Embedding, and Hybrid Search
Corresponds to Master Specification Section 22 (RAG System).

Pipeline: Document → Parser → Chunking → Metadata → Embedding → Vector Database
Search:   Query → Embedding → Semantic Search + Keyword Search → Reranking → Results
"""

import math
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document, DocumentChunk, DocumentStatus, DocumentType
from app.schemas.document import (
    ChunkResponse,
    DocumentResponse,
    RAGContext,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)


# --------------------------------------------------------------------------
# Text Chunking Engine
# --------------------------------------------------------------------------

class TextChunker:
    """
    Semantic-aware text chunking with configurable chunk sizes and overlap.
    Uses paragraph and sentence boundaries for intelligent splitting.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        min_chunk_size: int = 50,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 chars per token for English text."""
        return max(1, len(text) // 4)

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text by double newlines (paragraph boundaries)."""
        paragraphs = re.split(r"\n\s*\n", text.strip())
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex heuristic."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into semantic chunks with overlap.

        Returns list of dicts: [{"content": str, "token_count": int, "char_start": int, "char_end": int}]
        """
        if not text or not text.strip():
            return []

        paragraphs = self._split_into_paragraphs(text)
        chunks: List[Dict[str, Any]] = []
        current_chunk_parts: List[str] = []
        current_tokens = 0
        char_offset = 0

        for paragraph in paragraphs:
            para_tokens = self._estimate_tokens(paragraph)

            # If a single paragraph exceeds chunk size, split by sentences
            if para_tokens > self.chunk_size:
                # Flush current buffer first
                if current_chunk_parts:
                    chunk_text = "\n\n".join(current_chunk_parts)
                    if self._estimate_tokens(chunk_text) >= self.min_chunk_size:
                        chunks.append({
                            "content": chunk_text,
                            "token_count": self._estimate_tokens(chunk_text),
                            "char_start": char_offset,
                            "char_end": char_offset + len(chunk_text),
                        })
                    char_offset += len(chunk_text) + 2
                    current_chunk_parts = []
                    current_tokens = 0

                # Split large paragraph into sentence-level chunks
                sentences = self._split_into_sentences(paragraph)
                sent_buffer: List[str] = []
                sent_tokens = 0

                for sentence in sentences:
                    s_tokens = self._estimate_tokens(sentence)
                    if sent_tokens + s_tokens > self.chunk_size and sent_buffer:
                        chunk_text = " ".join(sent_buffer)
                        chunks.append({
                            "content": chunk_text,
                            "token_count": self._estimate_tokens(chunk_text),
                            "char_start": char_offset,
                            "char_end": char_offset + len(chunk_text),
                        })
                        # Apply overlap: keep last sentence(s) for continuity
                        overlap_parts = sent_buffer[-1:]
                        char_offset += len(chunk_text) + 1
                        sent_buffer = overlap_parts
                        sent_tokens = sum(self._estimate_tokens(s) for s in sent_buffer)
                    sent_buffer.append(sentence)
                    sent_tokens += s_tokens

                if sent_buffer:
                    chunk_text = " ".join(sent_buffer)
                    if self._estimate_tokens(chunk_text) >= self.min_chunk_size:
                        chunks.append({
                            "content": chunk_text,
                            "token_count": self._estimate_tokens(chunk_text),
                            "char_start": char_offset,
                            "char_end": char_offset + len(chunk_text),
                        })
                    char_offset += len(chunk_text) + 1
                continue

            # Normal paragraph: accumulate into current chunk
            if current_tokens + para_tokens > self.chunk_size and current_chunk_parts:
                chunk_text = "\n\n".join(current_chunk_parts)
                if self._estimate_tokens(chunk_text) >= self.min_chunk_size:
                    chunks.append({
                        "content": chunk_text,
                        "token_count": self._estimate_tokens(chunk_text),
                        "char_start": char_offset,
                        "char_end": char_offset + len(chunk_text),
                    })
                # Overlap: keep last paragraph
                overlap_parts = current_chunk_parts[-1:]
                char_offset += len(chunk_text) + 2
                current_chunk_parts = overlap_parts
                current_tokens = sum(self._estimate_tokens(p) for p in current_chunk_parts)

            current_chunk_parts.append(paragraph)
            current_tokens += para_tokens

        # Flush remaining buffer
        if current_chunk_parts:
            chunk_text = "\n\n".join(current_chunk_parts)
            if self._estimate_tokens(chunk_text) >= self.min_chunk_size:
                chunks.append({
                    "content": chunk_text,
                    "token_count": self._estimate_tokens(chunk_text),
                    "char_start": char_offset,
                    "char_end": char_offset + len(chunk_text),
                })

        return chunks


# --------------------------------------------------------------------------
# Embedding Engine (Mock for local dev, pluggable for production)
# --------------------------------------------------------------------------

class EmbeddingEngine:
    """
    Generates dense vector embeddings for text chunks.
    Uses a deterministic mock in development; can be swapped for
    OpenAI text-embedding-3-small, Gemini embedding, or local sentence-transformers.
    """

    EMBEDDING_DIM = 256  # Dimension of the embedding vectors

    def __init__(self):
        self.model_name = "mock-embedding-v1"

    def _mock_embed(self, text: str) -> List[float]:
        """
        Deterministic mock embedding: hash characters to produce a
        reproducible float vector. Same input always yields same vector.
        """
        vector = [0.0] * self.EMBEDDING_DIM
        for i, char in enumerate(text[:1024]):
            idx = (ord(char) * (i + 1)) % self.EMBEDDING_DIM
            vector[idx] += (ord(char) % 100) / 100.0
        # L2-normalize the vector
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        return vector

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        return self._mock_embed(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        return [self._mock_embed(t) for t in texts]


# --------------------------------------------------------------------------
# RAG Service
# --------------------------------------------------------------------------

class RAGService:
    """
    Enterprise RAG service managing the full document lifecycle:
    upload → parse → chunk → embed → index → search → retrieve.
    """

    def __init__(self):
        self.chunker = TextChunker(chunk_size=512, chunk_overlap=64)
        self.embedder = EmbeddingEngine()

    # ------------------------------------------------------------------
    # Document Ingestion
    # ------------------------------------------------------------------

    async def ingest_document(
        self,
        db: AsyncSession,
        organization_id: str,
        title: str,
        raw_text: str,
        filename: str = "uploaded.txt",
        content_type: str = "text/plain",
        document_type: str = "other",
        department: Optional[str] = None,
        product: Optional[str] = None,
        source: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Document:
        """
        Full RAG pipeline: create document record → chunk → embed → persist.
        """
        start_time = time.time()

        # 1. Create Document record in PENDING status
        doc = Document(
            organization_id=organization_id,
            title=title,
            filename=filename,
            content_type=content_type,
            document_type=DocumentType(document_type) if document_type in DocumentType.__members__.values() else DocumentType.OTHER,
            status=DocumentStatus.PARSING,
            department=department,
            product=product,
            source=source,
            tags=tags or [],
            raw_text=raw_text,
            file_size_bytes=len(raw_text.encode("utf-8")),
        )
        db.add(doc)
        await db.flush()
        await db.refresh(doc)

        try:
            # 2. Chunking stage
            doc.status = DocumentStatus.CHUNKING
            db.add(doc)
            await db.flush()

            chunk_data_list = self.chunker.chunk_text(raw_text)

            if not chunk_data_list:
                # Treat entire text as one chunk if no splits
                chunk_data_list = [{
                    "content": raw_text.strip(),
                    "token_count": len(raw_text) // 4,
                    "char_start": 0,
                    "char_end": len(raw_text),
                }]

            # 3. Embedding stage
            doc.status = DocumentStatus.EMBEDDING
            db.add(doc)
            await db.flush()

            texts = [c["content"] for c in chunk_data_list]
            embeddings = await self.embedder.embed_batch(texts)

            # 4. Persist chunks with embeddings
            total_tokens = 0
            for idx, (chunk_data, embedding) in enumerate(zip(chunk_data_list, embeddings)):
                chunk = DocumentChunk(
                    organization_id=organization_id,
                    document_id=doc.id,
                    chunk_index=idx,
                    content=chunk_data["content"],
                    token_count=chunk_data["token_count"],
                    chunk_metadata={
                        "document_title": title,
                        "document_type": document_type,
                        "department": department,
                        "product": product,
                        "source": source,
                        "tags": tags or [],
                        "char_start": chunk_data["char_start"],
                        "char_end": chunk_data["char_end"],
                    },
                    embedding=embedding,
                    embedding_model=self.embedder.model_name,
                )
                db.add(chunk)
                total_tokens += chunk_data["token_count"]

            # 5. Update document with processing telemetry
            processing_time_ms = (time.time() - start_time) * 1000
            doc.status = DocumentStatus.INDEXED
            doc.total_chunks = len(chunk_data_list)
            doc.total_tokens = total_tokens
            doc.embedding_model = self.embedder.model_name
            doc.processing_time_ms = processing_time_ms
            db.add(doc)
            await db.flush()
            await db.refresh(doc)

            return doc

        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            db.add(doc)
            await db.flush()
            await db.refresh(doc)
            raise

    # ------------------------------------------------------------------
    # Search (Hybrid: Semantic + Keyword with Metadata Filtering)
    # ------------------------------------------------------------------

    async def search(
        self,
        db: AsyncSession,
        organization_id: str,
        request: SearchRequest,
    ) -> SearchResponse:
        """
        Hybrid search across the knowledge base:
        1. Semantic search via cosine similarity on embeddings
        2. Keyword search via SQL LIKE on chunk content
        3. Score fusion and optional reranking
        """
        start_time = time.time()

        # Build base query with tenant isolation
        base_conditions = [
            DocumentChunk.organization_id == organization_id,
        ]

        # Metadata filters (Section 22)
        if request.document_type:
            # Join to Document table for type filtering
            base_conditions.append(
                DocumentChunk.document_id.in_(
                    select(Document.id).where(
                        Document.organization_id == organization_id,
                        Document.document_type == request.document_type,
                        Document.is_active == True,
                    )
                )
            )
        if request.department:
            base_conditions.append(
                DocumentChunk.chunk_metadata["department"].as_string() == request.department
            )
        if request.product:
            base_conditions.append(
                DocumentChunk.chunk_metadata["product"].as_string() == request.product
            )

        # Only search active documents
        active_doc_ids = select(Document.id).where(
            Document.organization_id == organization_id,
            Document.is_active == True,
            Document.status == DocumentStatus.INDEXED,
        )
        base_conditions.append(DocumentChunk.document_id.in_(active_doc_ids))

        results: List[SearchResultItem] = []

        if request.search_mode in ("semantic", "hybrid"):
            # Semantic search: embed query, then compute cosine similarity in Python
            # (In production with pgvector, this would use <=> operator directly)
            query_embedding = await self.embedder.embed_text(request.query)

            stmt = select(DocumentChunk).where(and_(*base_conditions))
            db_result = await db.execute(stmt)
            all_chunks = list(db_result.scalars().all())

            # Compute cosine similarity
            scored_chunks = []
            for chunk in all_chunks:
                if chunk.embedding:
                    sim = self._cosine_similarity(query_embedding, chunk.embedding)
                    scored_chunks.append((chunk, sim))

            # Sort by similarity descending
            scored_chunks.sort(key=lambda x: x[1], reverse=True)

            for chunk, score in scored_chunks[: request.top_k * 2]:
                doc_title = chunk.chunk_metadata.get("document_title", "") if chunk.chunk_metadata else ""
                results.append(SearchResultItem(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=doc_title,
                    content=chunk.content,
                    score=round(score, 4),
                    metadata=chunk.chunk_metadata or {},
                    source=chunk.chunk_metadata.get("source") if chunk.chunk_metadata else None,
                    document_type=chunk.chunk_metadata.get("document_type") if chunk.chunk_metadata else None,
                    chunk_index=chunk.chunk_index,
                ))

        if request.search_mode in ("keyword", "hybrid"):
            # Keyword search: case-insensitive LIKE matching
            keywords = request.query.lower().split()
            keyword_conditions = base_conditions.copy()

            # Match chunks containing any of the query keywords
            keyword_filters = []
            for kw in keywords[:10]:  # Limit to 10 keywords
                keyword_filters.append(
                    func.lower(DocumentChunk.content).contains(kw)
                )
            if keyword_filters:
                keyword_conditions.append(or_(*keyword_filters))

            stmt = select(DocumentChunk).where(and_(*keyword_conditions)).limit(request.top_k * 2)
            db_result = await db.execute(stmt)
            keyword_chunks = list(db_result.scalars().all())

            for chunk in keyword_chunks:
                # Calculate keyword relevance score
                content_lower = chunk.content.lower()
                keyword_hits = sum(1 for kw in keywords if kw in content_lower)
                kw_score = keyword_hits / max(len(keywords), 1)

                # Avoid duplicates from semantic search
                existing_ids = {r.chunk_id for r in results}
                if chunk.id not in existing_ids:
                    doc_title = chunk.chunk_metadata.get("document_title", "") if chunk.chunk_metadata else ""
                    results.append(SearchResultItem(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        document_title=doc_title,
                        content=chunk.content,
                        score=round(kw_score * 0.8, 4),  # Slightly lower weight than semantic
                        metadata=chunk.chunk_metadata or {},
                        source=chunk.chunk_metadata.get("source") if chunk.chunk_metadata else None,
                        document_type=chunk.chunk_metadata.get("document_type") if chunk.chunk_metadata else None,
                        chunk_index=chunk.chunk_index,
                    ))

        # Score fusion for hybrid results
        if request.search_mode == "hybrid":
            # Merge scores for chunks found by both methods
            chunk_scores: Dict[str, float] = {}
            for r in results:
                if r.chunk_id in chunk_scores:
                    chunk_scores[r.chunk_id] = max(chunk_scores[r.chunk_id], r.score)
                else:
                    chunk_scores[r.chunk_id] = r.score

            # Deduplicate and re-score
            seen = set()
            deduped: List[SearchResultItem] = []
            for r in results:
                if r.chunk_id not in seen:
                    seen.add(r.chunk_id)
                    r.score = chunk_scores[r.chunk_id]
                    deduped.append(r)
            results = deduped

        # Sort by score and truncate
        results.sort(key=lambda r: r.score, reverse=True)
        results = results[: request.top_k]

        # Reranking (Section 22) — LLM-based reranking placeholder
        reranked = False
        if request.rerank and len(results) > 1:
            results = await self._rerank_results(request.query, results)
            reranked = True

        processing_time_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_mode=request.search_mode,
            reranked=reranked,
            processing_time_ms=round(processing_time_ms, 2),
        )

    # ------------------------------------------------------------------
    # RAG Context Assembly (for agent consumption)
    # ------------------------------------------------------------------

    async def get_rag_context(
        self,
        db: AsyncSession,
        organization_id: str,
        query: str,
        top_k: int = 5,
        document_type: Optional[str] = None,
        product: Optional[str] = None,
    ) -> RAGContext:
        """
        Assemble RAG context with citation tracking for agent consumption.
        Returns assembled context text plus source citations.
        """
        search_req = SearchRequest(
            query=query,
            top_k=top_k,
            document_type=document_type,
            product=product,
            search_mode="hybrid",
            rerank=True,
        )
        search_result = await self.search(db, organization_id, search_req)

        # Assemble context passages with citations
        passages: List[str] = []
        sources: List[Dict[str, Any]] = []
        total_tokens = 0

        for i, item in enumerate(search_result.results):
            citation_label = f"[Source {i + 1}]"
            passages.append(f"{citation_label} {item.content}")
            sources.append({
                "citation_label": citation_label,
                "document_id": item.document_id,
                "document_title": item.document_title,
                "chunk_id": item.chunk_id,
                "chunk_index": item.chunk_index,
                "source": item.source,
                "document_type": item.document_type,
                "relevance_score": item.score,
            })
            total_tokens += len(item.content) // 4

        context_text = "\n\n".join(passages) if passages else "No relevant context found in the knowledge base."

        return RAGContext(
            context_text=context_text,
            sources=sources,
            total_tokens=total_tokens,
            query=query,
        )

    # ------------------------------------------------------------------
    # Document Management
    # ------------------------------------------------------------------

    async def list_documents(
        self,
        db: AsyncSession,
        organization_id: str,
        skip: int = 0,
        limit: int = 20,
        document_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[Document], int]:
        """List documents with optional filters and pagination."""
        conditions = [
            Document.organization_id == organization_id,
            Document.is_active == True,
        ]
        if document_type:
            conditions.append(Document.document_type == document_type)
        if status:
            conditions.append(Document.status == status)

        # Count total
        count_stmt = select(func.count(Document.id)).where(and_(*conditions))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Fetch page
        stmt = (
            select(Document)
            .where(and_(*conditions))
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        documents = list(result.scalars().all())

        return documents, total

    async def get_document(
        self,
        db: AsyncSession,
        document_id: str,
        organization_id: str,
    ) -> Optional[Document]:
        """Retrieve a single document by ID with tenant isolation."""
        stmt = select(Document).where(
            Document.id == document_id,
            Document.organization_id == organization_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_document_chunks(
        self,
        db: AsyncSession,
        document_id: str,
        organization_id: str,
    ) -> List[DocumentChunk]:
        """Retrieve all chunks for a document."""
        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.organization_id == organization_id,
            )
            .order_by(DocumentChunk.chunk_index)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def delete_document(
        self,
        db: AsyncSession,
        document_id: str,
        organization_id: str,
    ) -> bool:
        """Soft-delete a document (marks as inactive, chunks preserved for audit)."""
        doc = await self.get_document(db, document_id, organization_id)
        if not doc:
            return False
        doc.is_active = False
        db.add(doc)
        await db.flush()
        return True

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = math.sqrt(sum(a * a for a in vec_a))
        mag_b = math.sqrt(sum(b * b for b in vec_b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    async def _rerank_results(
        self,
        query: str,
        results: List[SearchResultItem],
    ) -> List[SearchResultItem]:
        """
        Rerank search results using relevance scoring heuristics.
        In production, this would call an LLM or cross-encoder model.
        """
        for result in results:
            query_terms = set(query.lower().split())
            content_terms = set(result.content.lower().split())
            term_overlap = len(query_terms & content_terms) / max(len(query_terms), 1)

            # Boost score based on term overlap and existing semantic score
            rerank_score = result.score * 0.7 + term_overlap * 0.3
            result.score = round(min(rerank_score, 1.0), 4)

        results.sort(key=lambda r: r.score, reverse=True)
        return results


# Singleton instance
rag_service = RAGService()
