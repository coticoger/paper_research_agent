from langgraph.graph import StateGraph, START, END
from schemas.agent_state import AgentState

from agent.paper_analysis.pdf_inspector_agent import inspector_agent


def build_paper_analysis_graph():
    graph = StateGraph(AgentState)

    graph.add_node("inspector_agent", inspector_agent)

    graph.add_edge(START, "inspector_agent")

    graph.add_edge("inspector_agent",END)

    return graph.compile()