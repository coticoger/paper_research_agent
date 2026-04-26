import json
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from config import PAPER_SEARCH_MODELS 

from tools.file_tools import ls, read_file, write_file
from tools.research_tools import search_arxiv, search_pubmed
from prompts.paper_search_prompt import SEARCH_PROMPT
from utils import deduplicate_papers
from schemas.agent_state import AgentState
from langgraph.types import Command
from utils import file_dir

model = PAPER_SEARCH_MODELS ["search-agent"]["model"]
temperature = PAPER_SEARCH_MODELS ["search-agent"]["temperature"]

llm = init_chat_model(model = model, temperature = temperature)

agent = create_agent(
    llm,
    tools = [ls, read_file, write_file, search_arxiv, search_pubmed],
    system_prompt=(
        "You are a paper discovery agent. Your job is to find relevant academic papers "
        "for the user's research request by using the available search tools carefully "
        "and efficiently. Search broadly enough to cover the main topics, prefer papers "
        "that are genuinely relevant over papers that merely share keywords, and return "
        "structured results that are easy for downstream agents to evaluate."
    )
)

def search_agent(state: AgentState) -> Command:
    print(f"✅ search agent로 논문 찾기를 시작합니다\n")
    instruction = state.get("new_messages", "")
    topics = state.get("topics", [])
    path = file_dir()

    result = agent.invoke({
        "messages" : [{"role":"user", "content":SEARCH_PROMPT.format(instruction=instruction, topics=topics, path = path)}]
    })

    content = result["messages"][-1].content
    parsed = json.loads(content)
    papers = parsed.get("papers", [])
    papers = deduplicate_papers(papers)

    paper_search_payload = {
        "instruction": instruction,
        "topics": topics,
        "generated_at": path,
        "total_papers": len(papers),
        "papers": papers,
    }

    print(f"✅ search agent로 논문 찾기를 완료했습니다\n\n")


    return Command(
        update ={
            "papers":papers,
            "path":path,
        },
        goto = "relevance_agent"
    )
