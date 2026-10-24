"""
Memory System Service — Three-Layer Cognitive Architecture
Corresponds to Master Specification Section 23 (Memory System).

Layers:
1. Short-Term Memory: Active task/workflow context
2. Long-Term Memory: Persistent organization preferences, brand rules, past campaigns
3. Episodic Memory: Action, reason, outcome, what worked, what failed for continuous optimization
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.autonomous import EpisodicMemory, MemoryItem


class MemoryService:
    """Three-tier cognitive memory architecture for autonomous marketing operations."""

    def __init__(self):
        # Short-term active working memory (in-memory per session)
        self._short_term_store: Dict[str, Dict[str, Any]] = {}

    # --------------------------------------------------------------------------
    # 1. Short-Term Memory (Session / Task Context)
    # --------------------------------------------------------------------------
    def set_short_term(self, session_id: str, key: str, value: Any) -> None:
        """Store working state in short-term memory."""
        if session_id not in self._short_term_store:
            self._short_term_store[session_id] = {}
        self._short_term_store[session_id][key] = value

    def get_short_term(self, session_id: str, key: str, default: Any = None) -> Any:
        """Retrieve working state from short-term memory."""
        return self._short_term_store.get(session_id, {}).get(key, default)

    def clear_short_term(self, session_id: str) -> None:
        """Flush working memory for a session."""
        self._short_term_store.pop(session_id, None)

    # --------------------------------------------------------------------------
    # 2. Long-Term Memory (Persistent Organizational Knowledge)
    # --------------------------------------------------------------------------
    async def save_long_term(
        self,
        db: AsyncSession,
        organization_id: str,
        memory_type: str,
        key: str,
        value: Dict[str, Any],
        confidence: float = 1.0,
        context: Optional[str] = None,
    ) -> MemoryItem:
        """Persist verified preference, brand rule, or past campaign insight."""
        # Upsert if exists
        existing = await db.scalar(
            select(MemoryItem).where(
                MemoryItem.organization_id == organization_id,
                MemoryItem.key == key,
            )
        )
        if existing:
            existing.value = value
            existing.confidence = confidence
            existing.context = context
            existing.memory_type = memory_type
            await db.commit()
            return existing

        item = MemoryItem(
            organization_id=organization_id,
            memory_type=memory_type,
            key=key,
            value=value,
            confidence=confidence,
            context=context,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def get_long_term(
        self,
        db: AsyncSession,
        organization_id: str,
        key: Optional[str] = None,
        memory_type: Optional[str] = None,
    ) -> List[MemoryItem]:
        """Query long-term organizational memory items."""
        query = select(MemoryItem).where(MemoryItem.organization_id == organization_id)
        if key:
            query = query.where(MemoryItem.key == key)
        if memory_type:
            query = query.where(MemoryItem.memory_type == memory_type)
        results = await db.scalars(query)
        return list(results.all())

    # --------------------------------------------------------------------------
    # 3. Episodic Memory (Experiences, Outcomes, Learnings)
    # --------------------------------------------------------------------------
    async def record_episode(
        self,
        db: AsyncSession,
        organization_id: str,
        task_name: str,
        action_taken: str,
        reason: str,
        outcome: str,
        what_worked: List[str],
        what_failed: List[str],
        impact_score: float = 0.8,
    ) -> EpisodicMemory:
        """Record an action episode with reflection for future learning."""
        episode = EpisodicMemory(
            organization_id=organization_id,
            task_name=task_name,
            action_taken=action_taken,
            reason=reason,
            outcome=outcome,
            what_worked=what_worked,
            what_failed=what_failed,
            impact_score=impact_score,
        )
        db.add(episode)
        await db.commit()
        await db.refresh(episode)
        return episode

    async def retrieve_episodes(
        self,
        db: AsyncSession,
        organization_id: str,
        task_name: Optional[str] = None,
        limit: int = 10,
    ) -> List[EpisodicMemory]:
        """Fetch past episodes to guide future autonomous decisions."""
        query = select(EpisodicMemory).where(EpisodicMemory.organization_id == organization_id)
        if task_name:
            query = query.where(EpisodicMemory.task_name == task_name)
        query = query.order_by(EpisodicMemory.created_at.desc()).limit(limit)
        results = await db.scalars(query)
        return list(results.all())


memory_service = MemoryService()
