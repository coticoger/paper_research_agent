from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from graph.state import DedupAgentState
from prompts.sub_agent_prompt import SUMMARIZE_PROMPT
from tools.file_tools import ls, read_file, write_file
from tools.reasoning_tools import think_tool

from config import SUBAGENT_MODELS


summarizer_model = init_chat_model(
    model=SUBAGENT_MODELS["summarizer-agent"]["model"],
    temperature=SUBAGENT_MODELS["summarizer-agent"]["temperature"],
)

summarizer_agent_tools = [write_file, read_file, ls]

summarizer_agent = create_agent(
    summarizer_model,
    tools = summarizer_agent_tools,
    system_prompt=SUMMARIZE_PROMPT,
    state_schema= DedupAgentState
)