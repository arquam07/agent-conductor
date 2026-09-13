"""The agent graph. This IS Diagram 2 (agent execution).
Reason -> (tool? -> loop) -> synthesize. A step guard prevents runaway loops."""
import logging
from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.agent.tools import TOOLS
from app.shared.config import settings
from app.shared.logging_setup import log_block

logger = logging.getLogger("agent")

SYSTEM_PROMPT = (
    "You are a capable task-running agent. Use tools when they help. "
    "When you have enough information, give a clear final answer."
)


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    steps: int  # reason-step counter, for the guard


def _build_llm():
    llm = ChatAnthropic(model=settings.llm_model, temperature=0)
    return llm.bind_tools(TOOLS)


def _reason(state: AgentState) -> dict:
    # Block: reason step (in: state -> out: next action)
    log_block(logger, "reason", f"step={state['steps']}")
    llm = _build_llm()
    response = llm.invoke(state["messages"])
    return {"messages": [response], "steps": state["steps"] + 1}


def _route(state: AgentState) -> str:
    # Block: tool call needed? + max steps guard
    last = state["messages"][-1]
    if state["steps"] >= settings.max_steps:
        log_block(logger, "guard", "step limit hit")
        return "halt"
    if getattr(last, "tool_calls", None):
        return "tools"
    return "done"


def build_agent():
    """Compile the graph once; reuse across jobs."""
    g = StateGraph(AgentState)
    g.add_node("reason", _reason)
    g.add_node("tools", ToolNode(TOOLS))  # executes tool calls, appends results
    g.add_edge(START, "reason")
    g.add_conditional_edges(
        "reason", _route, {"tools": "tools", "done": END, "halt": END}
    )
    g.add_edge("tools", "reason")  # loop back after a tool runs
    return g.compile()


_agent = None


def run_agent(task: str, params: dict | None = None) -> str:
    """Entry point the worker calls. in: task -> out: final answer text."""
    global _agent
    if _agent is None:
        _agent = build_agent()

    log_block(logger, "entry", f"task={task[:60]!r}")
    initial = {
        "messages": [SystemMessage(SYSTEM_PROMPT), HumanMessage(task)],
        "steps": 0,
    }
    final = _agent.invoke(initial)

    # Block: synthesize / return (in: final state -> out: result text)
    answer = final["messages"][-1].content
    log_block(logger, "return", f"steps={final['steps']}")
    return answer if isinstance(answer, str) else str(answer)