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

    # commit_agent, human_review, router가 이미 Command(goto=...)로 다음 노드를 지정하는데, 동시에 일반 add_edge()도 연결돼 있어서 LangGraph가 의도보다 여러 경로를 병렬 실행했습니다.
    graph.add_node(
        "commit_agent",
        commit_agent,
        destinations=("human_review", "router"),
    )
    graph.add_node(
        "human_review",
        human_review,
        destinations=("commit_agent", "router"),
    )
    graph.add_node(
        "router",
        router,
        destinations=("paper_search_agent", "paper_analysis_agent"),
    )
    graph.add_node("paper_search_agent", paper_search_agent)
    graph.add_node("paper_analysis_agent", paper_analysis_agent)
    #graph.add_node("task_paper_search_agent", task_paper_search_agent)

    graph.add_edge(START, "commit_agent")

    graph.add_edge("paper_search_agent", END)
    graph.add_edge("paper_analysis_agent", END)
    #graph.add_edge("task_paper_search_agent", END)

    return graph.compile()
