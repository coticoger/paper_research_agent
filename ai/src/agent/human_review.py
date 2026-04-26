from schemas.agent_state import AgentState
from langgraph.types import Command

def human_review(state : AgentState) -> Command:
    print(f'"✅ 현재 topics" : {state["topics"]}')

    choice = input("""
1. 더 탐색
2. topic 제거
3. 그대로 진행
""").strip()
    
    if choice == str(1):
        feedback = input("잘못된 점을 알려주세요: ").strip()

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