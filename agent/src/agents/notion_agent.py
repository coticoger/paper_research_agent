from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from graph.state import DedupAgentState
from prompts.sub_agent_prompt import NOTION_PROMPT
from tools.file_tools import ls, read_file, write_file
from tools.reasoning_tools import think_tool

from config import SUBAGENT_MODELS


notion_model = init_chat_model(
    model=SUBAGENT_MODELS["notion-agent"]["model"],
    temperature=SUBAGENT_MODELS["notion-agent"]["temperature"],
)

notion_agent_tools = [write_file, read_file, ls]

notion_agent = create_agent(
    notion_model,
    tools = notion_agent_tools,
    system_prompt=NOTION_PROMPT,
    state_schema= DedupAgentState
)