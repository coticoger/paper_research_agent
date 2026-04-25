from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from graph.state import DedupAgentState
from prompts.sub_agent_prompt import RELEVANCE_PROMPT
from tools.file_tools import ls, read_file, write_file
from tools.reasoning_tools import think_tool

from config import SUBAGENT_MODELS


relevance_model = init_chat_model(
    model=SUBAGENT_MODELS["relevance-agent"]["model"],
    temperature=SUBAGENT_MODELS["relevance-agent"]["temperature"],
)

relevance_agent_tools = [write_file, read_file, ls]

relevance_agent = create_agent(
    relevance_model,
    tools = relevance_agent_tools,
    system_prompt=RELEVANCE_PROMPT,
    state_schema= DedupAgentState
)