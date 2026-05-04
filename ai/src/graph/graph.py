from langgraph.graph import StateGraph, START, END

from schemas.agent_state import AgentState
from agent.commit_agent import commit_agent
from agent.human_review import human_review
from agent.router import router
from graph.paper_search_graph import build_paper_search_graph
from graph.paper_analysis_graph import build_paper_analysis_graph


def build_graph():
    graph = StateGraph(AgentState)

    paper_search_agent = build_paper_search_graph()
    paper_analysis_agent = build_paper_analysis_graph()

    graph.add_node("commit_agent", commit_agent)
    graph.add_node("human_review", human_review)
    graph.add_node("router", router)
    graph.add_node("paper_search_agent", paper_search_agent)
    graph.add_node("paper_anlaysis_agent", paper_analysis_agent)
    #graph.add_node("task_paper_search_agent", task_paper_search_agent)

    graph.add_edge(START, "commit_agent")

    # Command(goto=...)로 실제 이동하더라도
    # 시각화/branch 등록을 위해 가능한 edge를 명시
    graph.add_edge("commit_agent", "human_review")
    graph.add_edge("commit_agent", "router")

    graph.add_edge("human_review", "commit_agent")
    graph.add_edge("human_review", "router")

    graph.add_edge("router", "paper_search_agent")

    graph.add_edge("paper_search_agent", END)
    graph.add_edge("paper_anlaysis_agent", END)
    #graph.add_edge("task_paper_search_agent", END)

    return graph.compile()