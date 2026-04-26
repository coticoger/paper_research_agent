import json
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from prompts.commit_prompt import COMMIT_PROMPT, RE_COMMIT_PROMPT
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
        topics = state.get("topics",[])
        new_messages = state.get("new_messages","")
        agent = create_agent(
            llm,
            system_prompt=RE_COMMIT_PROMPT.format(message=user_message, topics = topics, new_messages = new_messages,human_feedback = human_feedback),
        )

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

    return Command(
        update={
            "messages" : result["messages"],
            "task" : parsed["task"],
            "new_messages" : parsed["new_messages"],
            "topics" : parsed["topics"],
        },
        goto = next_node
    )