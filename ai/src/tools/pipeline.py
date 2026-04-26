from agent.paper_research.research_agent import research_agnet
from langchain.tools import tool

@tool
def research_topic() -> str:
    """
    지시사항과 관련 단어 정보를 바탕으로
    """