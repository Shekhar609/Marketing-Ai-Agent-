"""
RAG Knowledge Base Tool — MCP-Compatible Tool for Agent Access to Knowledge Base
Corresponds to Master Specification Section 22 & 24.
"""

from typing import Any, Dict, Optional

from app.models.audit import RiskLevel
from app.tools.base import BaseTool


class SearchKnowledgeBaseTool(BaseTool):
    """
    Searches the enterprise marketing knowledge base using hybrid search.
    Agents invoke this tool to retrieve grounded organizational context
    rather than hallucinating information.
    """
    name = "search_knowledge_base"
    description = (
        "Searches the enterprise marketing knowledge base for relevant documents, "
        "brand guidelines, product info, case studies, competitor reports, "
        "and historical campaign data. Returns contextual passages with citations."
    )
    risk_level = RiskLevel.LOW
    requires_approval = False

    async def execute(
        self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Any:
        query = params.get("query", "")
        top_k = params.get("top_k", 5)
        document_type = params.get("document_type")
        product = params.get("product")

        # In a real execution context, the agent service would pass db and org_id
        # via the context dict. For standalone tool testing, return mock results.
        if context and context.get("db") and context.get("organization_id"):
            from app.services.rag_service import rag_service
            from app.schemas.document import SearchRequest

            search_req = SearchRequest(
                query=query,
                top_k=top_k,
                document_type=document_type,
                product=product,
                search_mode="hybrid",
                rerank=True,
            )
            result = await rag_service.search(
                db=context["db"],
                organization_id=context["organization_id"],
                request=search_req,
            )
            return {
                "query": query,
                "results": [
                    {
                        "content": r.content[:500],
                        "document_title": r.document_title,
                        "source": r.source,
                        "score": r.score,
                    }
                    for r in result.results
                ],
                "total_results": result.total_results,
            }

        # Mock response for standalone testing
        return {
            "query": query,
            "results": [
                {
                    "content": f"Relevant knowledge base passage for: {query}",
                    "document_title": "AIPNT Marketing Knowledge Base",
                    "source": "internal_kb",
                    "score": 0.92,
                }
            ],
            "total_results": 1,
        }
