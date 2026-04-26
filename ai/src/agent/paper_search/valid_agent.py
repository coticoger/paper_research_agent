import json
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from config import PAPER_SEARCH_MODELS 

from tools.file_tools import ls, read_file, write_file
from schemas.agent_state import AgentState
from langgraph.types import Command
from prompts.paper_search_prompt import VALIDATOR_PROMPT
from config import PAPER_SEARCH_CONFIG

model = PAPER_SEARCH_MODELS ["validator-agent"]["model"]
temperature = PAPER_SEARCH_MODELS ["validator-agent"]["temperature"]

llm = init_chat_model(model = model, temperature = temperature)

agent = create_agent(
    llm,
    tools = [ls, read_file, write_file],
    system_prompt=(
        "You are a final validation agent for paper search results. Your job is to review "
        "the summarized candidates, decide which papers truly satisfy the user's request, "
        "reject weak or off-target candidates, and determine whether another search round "
        "is necessary. Be strict about user intent, transparent about rejection reasons, "
        "and only approve papers that are genuinely useful for the request."
    )
)

def validation_agent(state:AgentState)->Command:
    print(f"✅ validation agent로 찾은 논문이 사용자의 요구와 맞는지 다시한번 확인합니다.")

    instruction = state.get("new_messages","")
    topics = state.get("topics",[])
    summaries = state.get("summaries",[])
    path = state.get("path","")

    result = agent.invoke({
        "messages":[{"role":"user","content":VALIDATOR_PROMPT.format(papers = summaries, path = path, instruction = instruction, topics = topics)}]
    })

    content = result["messages"][-1].content
    parsed = json.loads(content)

    validated_papers = parsed.get("validated_papers", [])
    rejected_papers = parsed.get("rejected_papers", [])
    needs_retry = parsed.get("needs_research_retry", False)  
    retry_iter = PAPER_SEARCH_CONFIG["max_iter"] 
    retry_count = state.get("retry_count",0)


    if (needs_retry or len(validated_papers) == 0) and (retry_count < retry_iter):
        print("⚠️ 적합한 논문 없음 → search_agent 재실행")
        retry_count += 1

        return Command(
            update={
                "validated_papers": [],
                "rejected_papers": rejected_papers,
                "retry_reason": parsed.get("retry_reason", "적합한 논문 없음"),
                "retry_count": retry_count,
            },
            goto="search_agent",
        )

    print("✅ 검증 완료 Finish")

    return Command(
        update={
            "validated_papers": validated_papers,
            "rejected_papers": rejected_papers,
            "retry_reason": None,
            "retry_count": retry_count,
        },
        goto="__end__",
    )
