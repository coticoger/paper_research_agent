import json
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from prompts.commit_prompt import COMMIT_PROMPT, SEARCH_COMMIT_PROMPT, ANALYSIS_COMMIT_PROMPT
from config import COMMIT_MODELS
from langgraph.types import Command
from schemas.agent_state import AgentState


model = COMMIT_MODELS["commit-agent"]["model"]
temperature = COMMIT_MODELS["commit-agent"]["temperature"]

llm = init_chat_model(
    model=model,
    temperature=temperature,
)


def commit_agent(state: AgentState) :
    messages = state["messages"]
    user_message = messages[-1].content
    human_feedback = state.get("human_feedback","")

    if human_feedback:
        new_messages = state.get("new_messages","")
        task = state.get("task","")

        if task == "paper_search":
            topics = state.get("topics",[])
            agent = create_agent(
                llm,
                system_prompt=SEARCH_COMMIT_PROMPT.format(message=user_message, topics = topics, new_messages = new_messages,human_feedback = human_feedback),
            )
        elif task == "paper_analysis":
            plans = state.get("plans",[])
            agent = create_agent(
                llm,
                system_prompt= ANALYSIS_COMMIT_PROMPT.format(human_feedback = human_feedback, plans = plans)
            )
        elif task == "task_paper_search":
            pass

        next_node = "router"
    else:
        agent = create_agent(
            llm,
            system_prompt=COMMIT_PROMPT.format(message=user_message),
        )
        
        next_node = "human_review"

    result = agent.invoke({
        "messages": messages
    })

    content = result["messages"][-1].content
    parsed = json.loads(content)
    
    print(f"✅ CommitAgent 실행 완료\n")
    print(f"{content}\n\n")

    if human_feedback:
        task = state.get("task", "")

        if task == "paper_search":
            return Command(
                update={
                    "messages" : result["messages"],
                    "task" : "paper_search",
                    "new_messages" : parsed["new_messages"],
                    "topics" : parsed["topics"],
                    "human_feedback" : "",
                },
                goto = next_node
            )
        if task == "paper_analysis":
            return Command(
                update = {
                    "messages" : result["messages"],
                    "task" : "paper_analysis",
                    "new_messages" : state.get("new_messages",""),
                    "plans" : parsed["plans"],
                    "human_feedback" : "",
                },
                goto = next_node
            )
        
    parsed_task = parsed["task"]

    if parsed_task == "paper_search":
            return Command(
                update={
                    "messages": result["messages"],
                    "task": parsed_task,
                    "new_messages": parsed["new_messages"],
                    "topics": parsed["topics"],
                },
                goto=next_node,
            )

    if parsed_task == "paper_analysis":
        return Command(
            update={
                "messages": result["messages"],
                "task": parsed_task,
                "new_messages": parsed["new_messages"],
                "pdf_path": parsed["pdf_path"],
                "plans": parsed["plans"],
            },
            goto=next_node,
        )

