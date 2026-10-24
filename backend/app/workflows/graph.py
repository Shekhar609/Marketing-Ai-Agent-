"""
LangGraph Multi-Agent Workflow State Machine
Corresponds to Master Specification Section 21 & Section 55.
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.workflows.nodes import (
    analytics_evaluation_node,
    approval_gate_node,
    content_creation_node,
    execution_node,
    optimization_report_node,
    persona_analysis_node,
    research_node,
    strategy_node,
    understand_objective_node,
)
from app.workflows.state import MarketingState


def build_marketing_graph():
    """
    Constructs and compiles the end-to-end multi-agent state graph.
    """
    builder = StateGraph(MarketingState)

    # 1. Add Agent Nodes
    builder.add_node("understand_objective", understand_objective_node)
    builder.add_node("research", research_node)
    builder.add_node("persona_analysis", persona_analysis_node)
    builder.add_node("strategy", strategy_node)
    builder.add_node("content_creation", content_creation_node)
    builder.add_node("approval_gate", approval_gate_node)
    builder.add_node("execution", execution_node)
    builder.add_node("analytics_evaluation", analytics_evaluation_node)
    builder.add_node("optimization_report", optimization_report_node)

    # 2. Add Sequential Edges
    builder.add_edge(START, "understand_objective")
    builder.add_edge("understand_objective", "research")
    builder.add_edge("research", "persona_analysis")
    builder.add_edge("persona_analysis", "strategy")
    builder.add_edge("strategy", "content_creation")
    builder.add_edge("content_creation", "approval_gate")
    builder.add_edge("approval_gate", "execution")
    builder.add_edge("execution", "analytics_evaluation")
    builder.add_edge("analytics_evaluation", "optimization_report")
    builder.add_edge("optimization_report", END)

    # 3. Compile with Checkpointing
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    return graph


marketing_workflow_engine = build_marketing_graph()
