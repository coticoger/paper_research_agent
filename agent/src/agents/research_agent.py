from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from graph.state import ResearchAgentState
from prompts.sub_agent_prompt import RESEARCH_PROMPT
from tools.file_tools import ls, read_file, write_file
from tools.reasoning_tools import think_tool
from tools.research_tools import search_pubmed, search_arxiv

from config import SUBAGENT_MODELS


research_model = init_chat_model(
    model=SUBAGENT_MODELS["research-agent"]["model"],
    temperature=SUBAGENT_MODELS["research-agent"]["temperature"],
)

research_agent_tools = [search_arxiv, search_pubmed, write_file, read_file, ls]

research_agent = create_agent(
    research_model,
    tools = research_agent_tools,
    system_prompt=RESEARCH_PROMPT,
    state_schema=ResearchAgentState
)