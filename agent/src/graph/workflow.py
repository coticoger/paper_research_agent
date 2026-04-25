from IPython.display import Image, display
from langgraph.graph import END, START, StateGraph

from graph.state import MainAgentState


def run_topic_agent(state: MainAgentState):
    from agents.topic_agent import topic_agent

    return topic_agent.invoke(state)


def run_main_agent(state: MainAgentState):
    from agents.main_agent import main_agent

    return main_agent.invoke(state)


def run_final_validator(state: MainAgentState):
    from agents.final_validator import final_validator

    return final_validator.invoke(state)


def route_after_validation(state: MainAgentState) -> str:
    if state.get("final_results"):
        return END
    return "main_agent"


def build_workflow():
    graph = StateGraph(MainAgentState)

    graph.add_node("topic_agent", run_topic_agent)
    graph.add_node("main_agent", run_main_agent)
    graph.add_node("final_validator", run_final_validator)

    graph.add_edge(START, "topic_agent")
    graph.add_edge("topic_agent", "main_agent")
    graph.add_edge("main_agent", "final_validator")
    graph.add_conditional_edges(
        "final_validator",
        route_after_validation,
        {
            "main_agent": "main_agent",
            END: END,
        },
    )

    return graph.compile()


def display_workflow_graph(app=None):
    app = app or build_workflow()
    try:
        display(Image(app.get_graph().draw_mermaid_png()))
    except Exception:
        print(app.get_graph().draw_mermaid())
    return app


workflow = build_workflow()


if __name__ == "__main__":
    display_workflow_graph(workflow)
