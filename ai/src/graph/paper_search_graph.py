from langgraph.graph import StateGraph, START, END
from schemas.agent_state import AgentState


from agent.paper_search.search_agent import search_agent
from agent.paper_search.relevance_judge import relevance_agent
from agent.paper_search.summary_agent import summary_agent
from agent.paper_search.valid_agent import validation_agent


def build_paper_search_graph():
    graph = StateGraph(AgentState)

    graph.add_node("search_agent", search_agent)
    graph.add_node("relevance_agent", relevance_agent)
    graph.add_node("summary_agent", summary_agent)
    graph.add_node("validation_agent", validation_agent)

    graph.add_edge(START, "search_agent")
    graph.add_edge("search_agent", "relevance_agent")
    graph.add_edge("relevance_agent", "summary_agent")
    graph.add_edge("summary_agent", "validation_agent")
    graph.add_edge("validation_agent", END)

    return graph.compile()