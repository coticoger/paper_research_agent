from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from config import TOPIC_MODELS
from graph.state import MainAgentState
from prompts.topic_agent_prompt import TOPIC_AGENT_PROMPT


topic_model = init_chat_model(
    model=TOPIC_MODELS["topic-agent"]["model"],
    temperature=TOPIC_MODELS["topic-agent"]["temperature"],
)

topic_agent = create_agent(
    topic_model,
    tools=[],
    system_prompt=TOPIC_AGENT_PROMPT,
    state_schema=MainAgentState,
)
