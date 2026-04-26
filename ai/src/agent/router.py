# agent/router.py
from langgraph.types import Command
from schemas.agent_state import AgentState


def router(state: AgentState) -> Command:
   
    task = state.get("task")

    print(f"✅ Router - 현재 받은 task : {task}\n\n")

    if task == "paper_search":
        return Command(goto="paper_search_agent")

    if task == "paper_analysis":
        return Command(goto="paper_analysis")

    if task == "task_paper_search":
        return Command(goto="task_paper_search")

    return Command(goto="fail")
