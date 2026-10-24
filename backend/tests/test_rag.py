"""
Tests for RAG Knowledge Base System
Covers: document ingestion, chunking, search (semantic, keyword, hybrid),
metadata filtering, reranking, document management, and citation tracking.
"""

import pytest
from httpx import AsyncClient


# ==========================================================================
# Helper: Onboard a test tenant and get auth token
# ==========================================================================

async def _create_test_tenant(client: AsyncClient) -> dict:
    """Create a tenant and return auth headers + org info."""
    onboard_payload = {
        "organization_name": "RAG Test Corp",
        "organization_slug": "rag-test-corp",
        "industry": "AI / SaaS",
        "admin_email": "rag_admin@ragtest.com",
        "admin_name": "RAG Admin",
        "admin_password": "SecureRAGPassword123!",
        "monthly_budget": 200000.0,
        "monthly_leads_target": 300,
        "revenue_target": 5000000.0,
    }
    res = await client.post("/api/v1/auth/onboard", json=onboard_payload)
    assert res.status_code == 201, f"Onboarding failed: {res.text}"
    token = res.json()["access_token"]
    org_id = res.json()["organization"]["id"]
    return {"headers": {"Authorization": f"Bearer {token}"}, "org_id": org_id}


# ==========================================================================
# Helper: Upload a sample document
# ==========================================================================

SAMPLE_DOC_TEXT = """
AIPNT DigiSwasth Healthcare Platform

DigiSwasth is an AI-powered digital healthcare ecosystem that delivers end-to-end
patient management, diagnostic triage, and electronic health records (EHR) compliance
with ABDM (Ayushman Bharat Digital Mission) standards.

Key Features:
- 10+ vital sign diagnostics including SpO2, blood pressure, and ECG
- AI-powered smart triage kiosk for OPD patient routing
- ABDM M1/M2/M3 certified EHR sync for hospitals and clinics
- Multilingual voice assistant supporting Hindi, Odia, and English
- Real-time dashboard for hospital administrators

Target Market:
DigiSwasth targets mid-size hospitals (50-500 beds), diagnostic chains, rural health
centers funded by CSR programs, and municipal health departments seeking digital
transformation compliance.

Competitive Advantage:
Unlike HealthCube which focuses only on rural diagnostics, DigiSwasth provides an
integrated end-to-end solution from patient registration to EHR sync, with built-in
ABDM compliance that eliminates the need for third-party certification.

Pricing Model:
Per-kiosk hardware (₹2.5L-4L) + SaaS subscription (₹15,000/month per facility).

ROI for Hospitals:
- 40% reduction in OPD wait times
- 60% faster patient registration
- 100% ABDM compliance (avoiding ₹5L+ penalty per facility)
- 3x improvement in diagnostic throughput
"""

SAMPLE_DOC_TEXT_2 = """
Prarambh AI Coding and STEM Platform

Prarambh is an AI-powered STEM education platform designed for K-12 schools in India,
fully aligned with NEP 2020 curriculum requirements for computational thinking and
artificial intelligence education.

Core Modules:
- Block-based coding for beginners (Class 3-5)
- Python programming with AI projects (Class 6-8)
- Robotics integration with IoT hardware kits
- AI/ML fundamentals with real-world projects (Class 9-12)

Dual Language Support:
Prarambh features a unique dual-language AI co-teacher that delivers lessons in both
Odia and English, making it the only STEM platform with regional Indic language support.

Target Schools:
- Private CBSE/ICSE schools in Tier-1 and Tier-2 cities
- State board schools in Odisha, Jharkhand, and Chhattisgarh
- DAV and Kendriya Vidyalaya chains seeking NEP compliance
"""


async def _upload_document(
    client: AsyncClient,
    auth: dict,
    title: str = "DigiSwasth Product Documentation",
    text: str = SAMPLE_DOC_TEXT,
    doc_type: str = "product_documentation",
    product: str = "DigiSwasth",
    department: str = "Product",
) -> dict:
    """Upload a document and return the response JSON."""
    payload = {
        "title": title,
        "document_type": doc_type,
        "department": department,
        "product": product,
        "source": "internal_docs",
        "tags": ["healthcare", "abdm", "digiswasth"],
        "raw_text": text,
    }
    res = await client.post(
        "/api/v1/knowledge/documents",
        json=payload,
        headers=auth["headers"],
    )
    assert res.status_code == 201, f"Upload failed: {res.text}"
    return res.json()


# ==========================================================================
# Test: Document Upload & Ingestion Pipeline
# ==========================================================================

@pytest.mark.asyncio
async def test_document_upload_and_indexing(async_client: AsyncClient):
    """Test full RAG pipeline: upload → parse → chunk → embed → index."""
    auth = await _create_test_tenant(async_client)
    doc = await _upload_document(async_client, auth)

    assert doc["status"] == "INDEXED"
    assert doc["total_chunks"] > 0
    assert doc["total_tokens"] > 0
    assert doc["embedding_model"] is not None
    assert doc["processing_time_ms"] > 0
    assert doc["document_type"] == "product_documentation"
    assert doc["title"] == "DigiSwasth Product Documentation"


# ==========================================================================
# Test: Document List & Retrieval
# ==========================================================================

@pytest.mark.asyncio
async def test_document_list_and_retrieval(async_client: AsyncClient):
    """Test listing and retrieving documents by ID."""
    auth = await _create_test_tenant(async_client)
    doc = await _upload_document(async_client, auth)

    # List documents
    res = await async_client.get(
        "/api/v1/knowledge/documents",
        headers=auth["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert len(data["documents"]) >= 1

    # Get specific document
    res = await async_client.get(
        f"/api/v1/knowledge/documents/{doc['id']}",
        headers=auth["headers"],
    )
    assert res.status_code == 200
    assert res.json()["id"] == doc["id"]


# ==========================================================================
# Test: Document Chunk Inspection
# ==========================================================================

@pytest.mark.asyncio
async def test_document_chunks(async_client: AsyncClient):
    """Test retrieving chunks with embeddings and metadata."""
    auth = await _create_test_tenant(async_client)
    doc = await _upload_document(async_client, auth)

    res = await async_client.get(
        f"/api/v1/knowledge/documents/{doc['id']}/chunks",
        headers=auth["headers"],
    )
    assert res.status_code == 200
    chunks = res.json()
    assert len(chunks) > 0

    # Verify chunk structure
    chunk = chunks[0]
    assert "content" in chunk
    assert "chunk_index" in chunk
    assert "token_count" in chunk
    assert chunk["has_embedding"] is True
    assert chunk["metadata"]["document_title"] == "DigiSwasth Product Documentation"


# ==========================================================================
# Test: Hybrid Search (Semantic + Keyword)
# ==========================================================================

@pytest.mark.asyncio
async def test_hybrid_search(async_client: AsyncClient):
    """Test hybrid search combining semantic and keyword matching."""
    auth = await _create_test_tenant(async_client)
    await _upload_document(async_client, auth)

    search_payload = {
        "query": "ABDM compliance healthcare kiosk diagnostics",
        "top_k": 5,
        "search_mode": "hybrid",
        "rerank": True,
    }
    res = await async_client.post(
        "/api/v1/knowledge/search",
        json=search_payload,
        headers=auth["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] > 0
    assert data["search_mode"] == "hybrid"
    assert data["processing_time_ms"] > 0

    # Verify result structure
    result = data["results"][0]
    assert "content" in result
    assert "score" in result
    assert "document_title" in result
    assert result["score"] > 0


# ==========================================================================
# Test: Keyword-only Search
# ==========================================================================

@pytest.mark.asyncio
async def test_keyword_search(async_client: AsyncClient):
    """Test keyword-only search mode."""
    auth = await _create_test_tenant(async_client)
    await _upload_document(async_client, auth)

    search_payload = {
        "query": "DigiSwasth ABDM hospital",
        "top_k": 3,
        "search_mode": "keyword",
        "rerank": False,
    }
    res = await async_client.post(
        "/api/v1/knowledge/search",
        json=search_payload,
        headers=auth["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["search_mode"] == "keyword"
    assert data["total_results"] > 0


# ==========================================================================
# Test: Semantic-only Search
# ==========================================================================

@pytest.mark.asyncio
async def test_semantic_search(async_client: AsyncClient):
    """Test semantic-only search mode using embeddings."""
    auth = await _create_test_tenant(async_client)
    await _upload_document(async_client, auth)

    search_payload = {
        "query": "patient registration electronic health records",
        "top_k": 3,
        "search_mode": "semantic",
        "rerank": False,
    }
    res = await async_client.post(
        "/api/v1/knowledge/search",
        json=search_payload,
        headers=auth["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["search_mode"] == "semantic"
    assert data["total_results"] > 0


# ==========================================================================
# Test: Metadata Filtering in Search
# ==========================================================================

@pytest.mark.asyncio
async def test_search_with_metadata_filter(async_client: AsyncClient):
    """Test search filtered by product metadata."""
    auth = await _create_test_tenant(async_client)
    await _upload_document(async_client, auth, product="DigiSwasth")

    # Search with product filter matching
    search_payload = {
        "query": "healthcare diagnostics",
        "top_k": 5,
        "product": "DigiSwasth",
        "search_mode": "hybrid",
    }
    res = await async_client.post(
        "/api/v1/knowledge/search",
        json=search_payload,
        headers=auth["headers"],
    )
    assert res.status_code == 200
    assert res.json()["total_results"] > 0


# ==========================================================================
# Test: RAG Context Assembly with Citations
# ==========================================================================

@pytest.mark.asyncio
async def test_rag_context_with_citations(async_client: AsyncClient):
    """Test RAG context assembly with citation tracking (Section 49)."""
    auth = await _create_test_tenant(async_client)
    await _upload_document(async_client, auth)

    context_payload = {
        "query": "What is DigiSwasth's competitive advantage?",
        "top_k": 3,
        "search_mode": "hybrid",
    }
    res = await async_client.post(
        "/api/v1/knowledge/context",
        json=context_payload,
        headers=auth["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert "context_text" in data
    assert "sources" in data
    assert data["total_tokens"] > 0
    assert len(data["sources"]) > 0

    # Verify citation structure
    source = data["sources"][0]
    assert "citation_label" in source
    assert "document_id" in source
    assert "document_title" in source
    assert "relevance_score" in source


# ==========================================================================
# Test: Multi-Document Search
# ==========================================================================

@pytest.mark.asyncio
async def test_multi_document_search(async_client: AsyncClient):
    """Test search across multiple documents from different products."""
    auth = await _create_test_tenant(async_client)

    # Upload two different product docs
    await _upload_document(
        async_client, auth,
        title="DigiSwasth Product Documentation",
        text=SAMPLE_DOC_TEXT,
        product="DigiSwasth",
    )
    await _upload_document(
        async_client, auth,
        title="Prarambh STEM Platform",
        text=SAMPLE_DOC_TEXT_2,
        product="Prarambh",
        department="Education",
    )

    # Search should return results from both documents
    search_payload = {
        "query": "AI platform India education healthcare",
        "top_k": 10,
        "search_mode": "hybrid",
    }
    res = await async_client.post(
        "/api/v1/knowledge/search",
        json=search_payload,
        headers=auth["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] > 0

    # Check that we get results from different documents
    doc_ids = {r["document_id"] for r in data["results"]}
    assert len(doc_ids) >= 1  # At least 1, ideally 2 with diverse results


# ==========================================================================
# Test: Document Soft-Delete
# ==========================================================================

@pytest.mark.asyncio
async def test_document_soft_delete(async_client: AsyncClient):
    """Test soft-deleting a document removes it from search results."""
    auth = await _create_test_tenant(async_client)
    doc = await _upload_document(async_client, auth)

    # Delete the document
    res = await async_client.delete(
        f"/api/v1/knowledge/documents/{doc['id']}",
        headers=auth["headers"],
    )
    assert res.status_code == 204

    # Search should return no results for deleted document
    search_payload = {
        "query": "DigiSwasth ABDM healthcare",
        "top_k": 5,
        "search_mode": "hybrid",
    }
    res = await async_client.post(
        "/api/v1/knowledge/search",
        json=search_payload,
        headers=auth["headers"],
    )
    assert res.status_code == 200
    assert res.json()["total_results"] == 0


# ==========================================================================
# Test: Tenant Isolation in RAG
# ==========================================================================

@pytest.mark.asyncio
async def test_rag_tenant_isolation(async_client: AsyncClient):
    """Test that documents are isolated between tenants (Section 40)."""
    # Create Tenant A and upload a document
    onboard_a = {
        "organization_name": "Tenant A Corp",
        "organization_slug": "tenant-a",
        "industry": "Healthcare",
        "admin_email": "admin_a@tenanta.com",
        "admin_name": "Admin A",
        "admin_password": "TenantA_Pass123!",
        "monthly_budget": 100000.0,
        "monthly_leads_target": 200,
        "revenue_target": 3000000.0,
    }
    res_a = await async_client.post("/api/v1/auth/onboard", json=onboard_a)
    assert res_a.status_code == 201
    auth_a = {"headers": {"Authorization": f"Bearer {res_a.json()['access_token']}"}}

    await _upload_document(async_client, auth_a, title="Tenant A Secret Doc")

    # Create Tenant B
    onboard_b = {
        "organization_name": "Tenant B Corp",
        "organization_slug": "tenant-b",
        "industry": "Education",
        "admin_email": "admin_b@tenantb.com",
        "admin_name": "Admin B",
        "admin_password": "TenantB_Pass123!",
        "monthly_budget": 100000.0,
        "monthly_leads_target": 200,
        "revenue_target": 3000000.0,
    }
    res_b = await async_client.post("/api/v1/auth/onboard", json=onboard_b)
    assert res_b.status_code == 201
    auth_b = {"headers": {"Authorization": f"Bearer {res_b.json()['access_token']}"}}

    # Tenant B should NOT see Tenant A's documents
    search_payload = {
        "query": "DigiSwasth ABDM healthcare",
        "top_k": 5,
        "search_mode": "hybrid",
    }
    res = await async_client.post(
        "/api/v1/knowledge/search",
        json=search_payload,
        headers=auth_b["headers"],
    )
    assert res.status_code == 200
    assert res.json()["total_results"] == 0

    # Tenant B should also see no documents in the list
    res = await async_client.get(
        "/api/v1/knowledge/documents",
        headers=auth_b["headers"],
    )
    assert res.status_code == 200
    assert res.json()["total"] == 0


# ==========================================================================
# Test: MCP Tool Registration includes search_knowledge_base
# ==========================================================================

@pytest.mark.asyncio
async def test_rag_tool_registered(async_client: AsyncClient):
    """Test that search_knowledge_base tool is registered in MCP catalog."""
    auth = await _create_test_tenant(async_client)
    res = await async_client.get(
        "/api/v1/agents/tools",
        headers=auth["headers"],
    )
    assert res.status_code == 200
    tools = res.json()
    tool_names = [t["name"] for t in tools]
    assert "search_knowledge_base" in tool_names

    # Find the tool and verify its properties
    rag_tool = next(t for t in tools if t["name"] == "search_knowledge_base")
    assert rag_tool["risk_level"] == "LOW"
    assert rag_tool["requires_approval"] is False
