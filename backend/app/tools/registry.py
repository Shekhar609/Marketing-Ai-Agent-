"""
Centralized Tool Registry, Execution Auditor, and Approval Gate
Corresponds to Master Specification Section 24, 25, 26.
"""

import time
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import ToolCallRecord, ToolCallStatus
from app.models.audit import ApprovalRequest, ApprovalStatus, RiskLevel
from app.tools.base import BaseTool, ToolResult
from app.tools.marketing_tools import (
    CalculateLeadScoreTool,
    CreateCampaignTool,
    GenerateContentTool,
    GetCRMLeadsTool,
    GetGA4TrafficTool,
    PostSlackAlertTool,
    SearchCompetitorTool,
    SearchWebTool,
    SendEmailTool,
    UpdateCRMLeadTool,
)
from app.tools.rag_tools import SearchKnowledgeBaseTool


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # Register default tools
        self.register(SearchWebTool())
        self.register(SearchCompetitorTool())
        self.register(CalculateLeadScoreTool())
        self.register(GenerateContentTool())
        self.register(SendEmailTool())
        self.register(CreateCampaignTool())
        self.register(SearchKnowledgeBaseTool())
        self.register(GetCRMLeadsTool())
        self.register(UpdateCRMLeadTool())
        self.register(PostSlackAlertTool())
        self.register(GetGA4TrafficTool())

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "risk_level": t.risk_level.value,
                "requires_approval": t.requires_approval,
            }
            for t in self._tools.values()
        ]

    async def execute(
        self,
        name: str,
        params: Dict[str, Any],
        organization_id: str,
        db: Optional[AsyncSession] = None,
        run_id: Optional[str] = None,
        task_id: Optional[str] = None,
        bypass_approval: bool = False,
    ) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                tool_name=name,
                error=f"Tool '{name}' is not registered in MCP catalog.",
            )

        # Enforce Human-in-the-Loop Risk Gate (Section 25 & 26)
        if tool.requires_approval and not bypass_approval:
            approval_id = None
            if db:
                approval = ApprovalRequest(
                    organization_id=organization_id,
                    agent_name="tool_dispatcher",
                    action_type=f"execute_tool_{name}",
                    risk_level=tool.risk_level,
                    payload={"tool_name": name, "params": params},
                    reason=f"High-impact action '{name}' requires human verification before execution.",
                    status=ApprovalStatus.PENDING,
                )
                db.add(approval)
                await db.flush()
                approval_id = approval.id

                # Record blocked tool call in audit log
                call_log = ToolCallRecord(
                    organization_id=organization_id,
                    run_id=run_id,
                    tool_name=name,
                    risk_level=tool.risk_level.value,
                    requires_approval=True,
                    input_params=params,
                    status=ToolCallStatus.BLOCKED_AWAITING_APPROVAL,
                )
                db.add(call_log)
                await db.flush()

            return ToolResult(
                success=False,
                tool_name=name,
                requires_approval=True,
                approval_request_id=approval_id,
                error="Action requires human approval before proceeding.",
            )

        # Execute Tool Logic
        start_time = time.time()
        try:
            res_data = await tool.execute(params)
            duration_ms = (time.time() - start_time) * 1000

            if db:
                call_log = ToolCallRecord(
                    organization_id=organization_id,
                    run_id=run_id,
                    tool_name=name,
                    risk_level=tool.risk_level.value,
                    requires_approval=tool.requires_approval,
                    input_params=params,
                    output_result=res_data,
                    status=ToolCallStatus.SUCCESS,
                    latency_ms=duration_ms,
                )
                db.add(call_log)
                await db.flush()

            return ToolResult(
                success=True,
                tool_name=name,
                result=res_data,
                execution_time_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            if db:
                call_log = ToolCallRecord(
                    organization_id=organization_id,
                    run_id=run_id,
                    tool_name=name,
                    risk_level=tool.risk_level.value,
                    requires_approval=tool.requires_approval,
                    input_params=params,
                    output_result={"error": str(e)},
                    status=ToolCallStatus.FAILED,
                    latency_ms=duration_ms,
                )
                db.add(call_log)
                await db.flush()

            return ToolResult(
                success=False,
                tool_name=name,
                error=str(e),
                execution_time_ms=duration_ms,
            )


tool_registry = ToolRegistry()
