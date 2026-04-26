import json
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from config import PAPER_SEARCH_MODELS 

from tools.file_tools import ls, read_file, write_file
from prompts.paper_search_prompt import RELEVANCE_PROMPT
from schemas.agent_state import AgentState
from langgraph.types import Command
from utils import filter_papers_by_relevance

model = PAPER_SEARCH_MODELS ["relevance-agent"]["model"]
temperature = PAPER_SEARCH_MODELS ["relevance-agent"]["temperature"]

llm = init_chat_model(model = model, temperature = temperature)

# 추가! commit_agent의 search_paper 정보 가져와서 format해야함

agent = create_agent(
    llm,
    tools = [ls, read_file, write_file],
    system_prompt=(
        "You are a relevance ranking agent. Your job is to evaluate how well each paper "
        "matches the user's research intent, assign calibrated relevance scores, and "
        "preserve the original paper information while adding clear scoring rationale. "
        "Be selective, concept-focused, and consistent across all candidates."
    )
)

def relevance_agent(state:AgentState) -> Command:
    print(f"✅ relevance agent로 관련도 높은 논문을 추출합니다.\n")

    instruction = state.get("new_messages","")
    topics = state.get("topics",[])
    papers = state.get("papers",[])
    path = state.get("path","")

    result = agent.invoke({
        "messages" : [{"role":"user", "content" : RELEVANCE_PROMPT.format(instruction=instruction, topics = topics, papers=papers, path = path)}]
    })

    content = result["messages"][-1].content
    parsed = json.loads(content)

    scored_papers = parsed.get("scored_papers",[])

    relevant_papers = filter_papers_by_relevance(scored_papers, threshold = 0.7)

    return Command(
        update = {
            "relevant_papers" : relevant_papers
        },
        goto = "summary_agent"
    )


