"""
RAG Quality Evaluator (RAGAS-Style Metrics)
Corresponds to Master Specification Section 39:
Retrieval Precision, Retrieval Recall, Faithfulness, Answer Relevance.
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RAGMetricsResult(BaseModel):
    retrieval_precision: float
    retrieval_recall: float
    faithfulness: float
    answer_relevance: float
    overall_ragas_score: float
    passed: bool
    details: Dict[str, Any] = {}


class RAGEvaluator:
    """
    Computes rigorous evaluation metrics for Retrieval-Augmented Generation.
    """

    @classmethod
    def evaluate(
        cls,
        query: str,
        retrieved_contexts: List[str],
        generated_answer: str,
        ground_truth: Optional[str] = None,
        threshold: float = 0.70,
    ) -> RAGMetricsResult:
        query_words = set(re.findall(r"\b\w{3,}\b", query.lower()))
        answer_words = set(re.findall(r"\b\w{3,}\b", generated_answer.lower()))

        combined_context = " ".join(retrieved_contexts).lower()
        context_words = set(re.findall(r"\b\w{3,}\b", combined_context))

        # 1. Retrieval Precision: proportion of retrieved chunks that contain query intent
        relevant_chunks = 0
        for chunk in retrieved_contexts:
            chunk_words = set(re.findall(r"\b\w{3,}\b", chunk.lower()))
            if len(query_words.intersection(chunk_words)) > 0:
                relevant_chunks += 1
        retrieval_precision = (
            relevant_chunks / max(len(retrieved_contexts), 1) if retrieved_contexts else 0.0
        )

        # 2. Retrieval Recall: coverage of ground truth (or query words if ground truth absent)
        target_reference_words = (
            set(re.findall(r"\b\w{3,}\b", ground_truth.lower()))
            if ground_truth
            else query_words
        )
        if target_reference_words:
            overlap = len(context_words.intersection(target_reference_words))
            retrieval_recall = min(overlap / len(target_reference_words), 1.0)
        else:
            retrieval_recall = 1.0

        # 3. Faithfulness: is the generated answer supported by retrieved context?
        if answer_words:
            faithful_words = len(answer_words.intersection(context_words))
            faithfulness = min(faithful_words / len(answer_words), 1.0)
        else:
            faithfulness = 0.0

        # 4. Answer Relevance: does the generated answer directly address the user query?
        if query_words and answer_words:
            relevance_matches = sum(
                1 for qw in query_words if any(qw in aw or aw in qw for aw in answer_words)
            )
            answer_relevance = min((relevance_matches + 1) / (len(query_words) + 1), 1.0)
        else:
            answer_relevance = 0.0

        # Overall harmonic mean / composite RAGAS score
        overall_score = (
            retrieval_precision * 0.25
            + retrieval_recall * 0.25
            + faithfulness * 0.30
            + answer_relevance * 0.20
        )

        return RAGMetricsResult(
            retrieval_precision=round(retrieval_precision, 3),
            retrieval_recall=round(retrieval_recall, 3),
            faithfulness=round(faithfulness, 3),
            answer_relevance=round(answer_relevance, 3),
            overall_ragas_score=round(overall_score, 3),
            passed=overall_score >= threshold,
            details={
                "retrieved_chunk_count": len(retrieved_contexts),
                "threshold": threshold,
            },
        )
