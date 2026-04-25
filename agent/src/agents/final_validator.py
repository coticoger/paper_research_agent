from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from config import VALID_MODELS
from graph.state import MainAgentState
from prompts.final_valid_agent_prompt import VALID_AGENT_PROMPT


valid_model = init_chat_model(
    model=VALID_MODELS["valid-agent"]["model"],
    temperature=VALID_MODELS["valid-agent"]["temperature"],
)

final_validator = create_agent(
    valid_model,
    tools=[],
    system_prompt=VALID_AGENT_PROMPT,
    state_schema=MainAgentState,
)

valid_agent = final_validator
