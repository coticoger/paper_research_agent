from schemas.agent_state import AgentState
from langgraph.types import Command

def human_review(state:AgentState) -> Command:
    task = state.get("task")

    if task == "paper_search":
        return paper_search_review(state)
    
    if task == "paper_analysis":
        return paper_analysis_review(state)

    if task == "task_paper_search":
        return task_paper_search_review(state)

def paper_search_review(state : AgentState) -> Command:
    print(f'"✅ 현재 topics" : {state["topics"]}')

    choice = input("""
1. 수정하기
2. topic 제거
3. 그대로 진행
""").strip()
    
    if choice == str(1):
        feedback = input("어떻게 수정할까요?: ").strip()

        return Command(
            update = {"human_feedback" : feedback},
            goto="commit_agent"
            )

    if choice == str(2):
        remove = input("제거할 topic 입력 :")
        remove_topics = {x.strip() for x in remove.split(",") if x.strip()}

        return Command(
            update={
                "topics" : [ t for t in state["topics"] if t not in remove_topics]
            },
            goto = "router"
        )
    
    if choice == str(3):
        return Command(
            goto="router"
        )

    return Command(goto="fail")

def paper_analysis_review(state : AgentState) -> Command:
    print(f"현재 분석 계획\n {state["plans"]}")
    
    choice = input(""" 1. 수정하기 \n 2. plan 제거 \n 3. 그대로 진행\n""").strip()

    if choice == str(1):
        feedback = input("어떤 부분을 수정할까요?: ").strip()

        return Command(
            update = {"human_feedback":feedback},
            goto = "commit_agent"
        )

    if choice == str(2):
        remove = input("제거할 plan 입력: ")
        remove_plans = {x.strip() for x in remove.split(",") if x.strip()}

        return Command(
            update = {"plans" : [t for t in state["plans"] if t not in remove_plans]},
            goto = "router"
        )
    
    if choice == str(3):
        return Command(
            goto = "router"
        )
    
    return Command(goto="fail")

def task_paper_search_review(state) -> Command:
    return 