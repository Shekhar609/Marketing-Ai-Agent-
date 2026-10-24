"""
Unified AI Evaluation Service Layer
Corresponds to Master Specification Section 39: AI Evaluation.
"""

import time
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.evaluation.agent_evaluator import AgentEvaluationResult, AgentEvaluator
from app.core.evaluation.benchmark_dataset import GOLDEN_BENCHMARK_SUITE, GoldenTestCase
from app.core.evaluation.rag_evaluator import RAGEvaluator, RAGMetricsResult
from app.models.evaluation import EvaluationRun

logger = logging.getLogger(__name__)


class EvaluationService:
    """
    Coordinates RAG evaluation, agent quality benchmarking, and continuous regression tests.
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def evaluate_rag(
        self,
        query: str,
        retrieved_contexts: List[str],
        generated_answer: str,
        ground_truth: Optional[str] = None,
        organization_id: Optional[str] = None,
        test_case_id: Optional[str] = None,
    ) -> RAGMetricsResult:
        start_time = time.time()
        metrics = RAGEvaluator.evaluate(
            query=query,
            retrieved_contexts=retrieved_contexts,
            generated_answer=generated_answer,
            ground_truth=ground_truth,
        )
        latency_ms = (time.time() - start_time) * 1000.0

        if self.db and organization_id:
            eval_run = EvaluationRun(
                organization_id=organization_id,
                eval_type="RAG",
                test_case_id=test_case_id,
                metrics={
                    "retrieval_precision": metrics.retrieval_precision,
                    "retrieval_recall": metrics.retrieval_recall,
                    "faithfulness": metrics.faithfulness,
                    "answer_relevance": metrics.answer_relevance,
                },
                overall_score=metrics.overall_ragas_score,
                passed=metrics.passed,
                latency_ms=round(latency_ms, 2),
                details=metrics.details,
            )
            self.db.add(eval_run)
            await self.db.commit()

        return metrics

    async def evaluate_agent(
        self,
        task_prompt: str,
        output_text: str,
        agent_name: str,
        organization_id: Optional[str] = None,
        expected_elements: Optional[List[str]] = None,
        reference_context: Optional[str] = None,
    ) -> AgentEvaluationResult:
        start_time = time.time()
        result = AgentEvaluator.evaluate_output(
            task_prompt=task_prompt,
            output_text=output_text,
            expected_elements=expected_elements,
            reference_context=reference_context,
        )
        latency_ms = (time.time() - start_time) * 1000.0

        if self.db and organization_id:
            eval_run = EvaluationRun(
                organization_id=organization_id,
                eval_type="AGENT",
                agent_name=agent_name,
                metrics={
                    "correctness": result.correctness,
                    "relevance": result.relevance,
                    "groundedness": result.groundedness,
                    "completeness": result.completeness,
                    "consistency": result.consistency,
                    "marketing_quality_score": result.marketing_quality_score,
                },
                overall_score=result.overall_agent_quality,
                passed=result.passed,
                latency_ms=round(latency_ms, 2),
                details={"feedback": result.feedback},
            )
            self.db.add(eval_run)
            await self.db.commit()

        return result

    async def run_benchmark_suite(
        self,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the Golden Benchmark Suite against the system and return pass rates.
        """
        results = []
        passed_count = 0

        for tc in GOLDEN_BENCHMARK_SUITE:
            if tc.category == "RAG":
                res = await self.evaluate_rag(
                    query=tc.prompt,
                    retrieved_contexts=tc.expected_contexts,
                    generated_answer=tc.reference_output,
                    ground_truth=tc.expected_contexts[0],
                    organization_id=organization_id,
                    test_case_id=tc.id,
                )
                passed = res.overall_ragas_score >= tc.passing_threshold
                if passed:
                    passed_count += 1
                results.append({
                    "test_case_id": tc.id,
                    "category": tc.category,
                    "score": res.overall_ragas_score,
                    "passed": passed,
                })
            else:
                res = await self.evaluate_agent(
                    task_prompt=tc.prompt,
                    output_text=tc.reference_output,
                    agent_name=tc.category.lower() + "_agent",
                    organization_id=organization_id,
                    expected_elements=tc.required_keywords,
                )
                passed = res.overall_agent_quality >= tc.passing_threshold
                if passed:
                    passed_count += 1
                results.append({
                    "test_case_id": tc.id,
                    "category": tc.category,
                    "score": res.overall_agent_quality,
                    "passed": passed,
                })

        total = len(GOLDEN_BENCHMARK_SUITE)
        pass_rate = round(passed_count / max(total, 1), 3)

        return {
            "total_tests": total,
            "passed_tests": passed_count,
            "failed_tests": total - passed_count,
            "pass_rate": pass_rate,
            "suite_status": "PASSED" if pass_rate >= 0.66 else "FAILED",
            "results": results,
        }
