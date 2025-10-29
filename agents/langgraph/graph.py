"""
LangGraph controller skeleton — single stack, no specific model vendor baked in.

This models a minimal spec lifecycle graph:
- env_provision -> plan -> implement -> test -> ready_for_pr

Plug in your preferred LLM (e.g., GLM 4.x) by providing a `call_llm(messages)` function.
"""
from __future__ import annotations

from typing import Any, Dict, List
from langgraph.graph import StateGraph, END


class SpecState(dict):
    """State container passed between nodes."""
    pass


def env_provision(state: SpecState) -> SpecState:
    # Placeholder: orchestrator already created worktrees/branches.
    state["env"] = "provisioned"
    return state


def plan(state: SpecState) -> SpecState:
    # TODO: call LLM to outline tasks based on spec text
    state["plan"] = ["edit code", "run tests", "iterate"]
    return state


def implement(state: SpecState) -> SpecState:
    # TODO: drive edits via tasks/commands; today this is human/IDE assisted
    state["changes"] = True
    return state


def test(state: SpecState) -> SpecState:
    # TODO: run `task test` in each repo worktree and collect results
    state["tests"] = "passing"
    return state


def build_graph():
    g = StateGraph(SpecState)
    g.add_node("env_provision", env_provision)
    g.add_node("plan", plan)
    g.add_node("implement", implement)
    g.add_node("test", test)

    g.set_entry_point("env_provision")
    g.add_edge("env_provision", "plan")
    g.add_edge("plan", "implement")
    g.add_edge("implement", "test")
    g.add_edge("test", END)
    return g.compile()


if __name__ == "__main__":
    graph = build_graph()
    out = graph.invoke({"spec_id": "123", "slug": "example"})
    print(out)
