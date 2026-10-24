"""
Cost Tracking, Token Budgeting & Model Routing Economics
Corresponds to Master Specification Section 41:
Tracks tokens, cost per run, cost per campaign, and enforces tenant budget limits.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models.evaluation import CostRecord

# Pricing in USD per 1,000,000 tokens
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gemini-1.5-flash": {"prompt": 0.075, "completion": 0.30},
    "gemini-1.5-pro": {"prompt": 1.25, "completion": 5.00},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
    "gpt-4o": {"prompt": 2.50, "completion": 10.00},
    "claude-3-5-sonnet": {"prompt": 3.00, "completion": 15.00},
    "default": {"prompt": 0.50, "completion": 2.00},
}

USD_TO_INR_RATE = 85.0


class CostCalculationResult(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    cost_inr: float
    model_name: str


class CostTracker:
    """
    Computes financial costs for LLM tokens and manages organization budget safety limits.
    """

    @classmethod
    def calculate_cost(
        cls,
        prompt_tokens: int,
        completion_tokens: int,
        model_name: str = "gemini-1.5-flash",
    ) -> CostCalculationResult:
        rates = MODEL_PRICING.get(model_name.lower(), MODEL_PRICING["default"])
        prompt_cost = (prompt_tokens / 1_000_000.0) * rates["prompt"]
        completion_cost = (completion_tokens / 1_000_000.0) * rates["completion"]
        total_usd = round(prompt_cost + completion_cost, 6)
        total_inr = round(total_usd * USD_TO_INR_RATE, 4)

        return CostCalculationResult(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=total_usd,
            cost_inr=total_inr,
            model_name=model_name,
        )

    @classmethod
    async def record_usage(
        cls,
        db: AsyncSession,
        organization_id: str,
        agent_name: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostRecord:
        """
        Record a token consumption ledger entry in database.
        """
        calc = cls.calculate_cost(prompt_tokens, completion_tokens, model_name)
        cost_record = CostRecord(
            organization_id=organization_id,
            run_id=run_id,
            agent_name=agent_name,
            model_name=model_name,
            prompt_tokens=calc.prompt_tokens,
            completion_tokens=calc.completion_tokens,
            total_tokens=calc.total_tokens,
            cost_usd=calc.cost_usd,
            cost_inr=calc.cost_inr,
            metadata_json=metadata or {},
        )
        db.add(cost_record)
        await db.commit()
        await db.refresh(cost_record)
        return cost_record

    @classmethod
    async def get_organization_spend_summary(
        cls,
        db: AsyncSession,
        organization_id: str,
    ) -> Dict[str, Any]:
        """
        Summarizes total tokens and cost spent for the tenant across all agents.
        """
        q = select(
            func.sum(CostRecord.prompt_tokens).label("total_prompt_tokens"),
            func.sum(CostRecord.completion_tokens).label("total_completion_tokens"),
            func.sum(CostRecord.total_tokens).label("total_tokens"),
            func.sum(CostRecord.cost_usd).label("total_usd"),
            func.sum(CostRecord.cost_inr).label("total_inr"),
            func.count(CostRecord.id).label("total_runs"),
        ).where(CostRecord.organization_id == organization_id)

        res = (await db.execute(q)).first()
        
        # Per-agent breakdown
        agent_q = (
            select(
                CostRecord.agent_name,
                func.sum(CostRecord.total_tokens).label("agent_tokens"),
                func.sum(CostRecord.cost_usd).label("agent_usd"),
                func.count(CostRecord.id).label("agent_runs"),
            )
            .where(CostRecord.organization_id == organization_id)
            .group_by(CostRecord.agent_name)
        )
        agent_rows = (await db.execute(agent_q)).all()

        return {
            "organization_id": organization_id,
            "total_tokens": res.total_tokens or 0,
            "total_prompt_tokens": res.total_prompt_tokens or 0,
            "total_completion_tokens": res.total_completion_tokens or 0,
            "total_cost_usd": round(res.total_usd or 0.0, 4),
            "total_cost_inr": round(res.total_inr or 0.0, 2),
            "total_runs": res.total_runs or 0,
            "agent_breakdown": [
                {
                    "agent_name": row.agent_name,
                    "tokens": row.agent_tokens or 0,
                    "cost_usd": round(row.agent_usd or 0.0, 4),
                    "runs": row.agent_runs or 0,
                }
                for row in agent_rows
            ],
        }
