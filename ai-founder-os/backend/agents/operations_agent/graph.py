"""
Operations Agent — LangGraph Subgraph

Implements the ReAct-style operations workflow as a directed state graph,
including MCP tool execution and approval flow.
"""

from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage

from db.models import Task
from llm.provider import get_model
from guardrails.approval_gate import ApprovalPending
from .prompts import OPERATIONS_SYSTEM_PROMPT
from .tools import get_tool_definitions, execute_tool
from db.repository import outcome_repository, task_repository


class OpsState(TypedDict):
    db: AsyncSession
    task: Task
    messages: list[BaseMessage]
    status: str
    summary: str


async def reason_node(state: OpsState) -> dict:
    """Invoke the LLM to decide on tools or produce a final response."""
    tool_definitions = await get_tool_definitions()
    model = get_model()
    if tool_definitions:
        model = model.bind_tools(tool_definitions)

    response = await model.ainvoke(state["messages"])
    
    status = "running"
    summary = ""
    
    if hasattr(response, 'tool_calls') and not response.tool_calls:
        # If no tool calls, the model decided it's finished
        status = "completed"
        summary = response.content or "Task completed."

    return {"messages": state["messages"] + [response], "status": status, "summary": summary}


async def execute_tool_node(state: OpsState) -> dict:
    """Execute the tools requested by the LLM."""
    last_message = state["messages"][-1]
    
    new_messages = []
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            try:
                result = await execute_tool(state["db"], state["task"].id, tool_call["name"], tool_call["args"])
                new_messages.append(ToolMessage(
                    tool_call_id=tool_call["id"],
                    name=tool_call["name"],
                    content=str(result)
                ))
            except ApprovalPending as e:
                # If approval is pending, we halt the tool execution and wait
                return {
                    "status": "awaiting_approval",
                    "summary": f"Blocked: {e.tool_name} requires approval (ID: {e.approval_id})"
                }
                
    return {"messages": state["messages"] + new_messages}


async def record_outcome_node(state: OpsState) -> dict:
    """Record the final result in the database."""
    # We only log outcome on successful completion in the old flow
    if state["status"] == "completed":
        pass # The parent orchestration (or agent.py wrapper) handles persistence now, 
             # but we can do it here for completeness or just return state.
             
    return state


def route_after_reason(state: OpsState) -> str:
    if state["status"] == "completed":
        return "record_outcome"
    return "execute_tool"


def route_after_tool(state: OpsState) -> str:
    if state["status"] == "awaiting_approval":
        return "record_outcome"
    return "reason"


def build_ops_graph() -> StateGraph:
    """Compile the Operations state graph."""
    graph = StateGraph(OpsState)

    graph.add_node("reason", reason_node)
    graph.add_node("execute_tool", execute_tool_node)
    graph.add_node("record_outcome", record_outcome_node)

    graph.set_entry_point("reason")
    
    graph.add_conditional_edges("reason", route_after_reason)
    graph.add_conditional_edges("execute_tool", route_after_tool)
    
    graph.add_edge("record_outcome", END)

    return graph.compile()
