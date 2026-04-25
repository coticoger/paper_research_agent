from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from graph.state import DedupAgentState
from prompts.sub_agent_prompt import DEDUP_PROMPT
from tools.file_tools import ls, read_file, write_file
from tools.reasoning_tools import think_tool

from config import SUBAGENT_MODELS


dedup_model = init_chat_model(
    model=SUBAGENT_MODELS["dedup-agent"]["model"],
    temperature=SUBAGENT_MODELS["dedup-agent"]["temperature"],
)

dedup_agent_tools = [write_file, read_file, ls]

dedup_agent = create_agent(
    dedup_model,
    tools = dedup_agent_tools,
    system_prompt=DEDUP_PROMPT,
    state_schema= DedupAgentState
)