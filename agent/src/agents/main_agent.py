from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from graph.state import MainAgentState
from prompts.main_agent_prompt import MAIN_AGENT_INSTRUCTIONS
from prompts.sub_agent_prompt import (
    DEDUP_PROMPT,
    RELEVANCE_PROMPT,
    RESEARCH_PROMPT,
    SUMMARIZE_PROMPT,
)
from tools.file_tools import ls, read_file, write_file
from tools.paper_pipeline_tools import (
    build_final_results_file,
    deduplicate_papers_file,
    score_papers_file,
    search_papers_file,
    summarize_papers_file,
)
from tools.reasoning_tools import think_tool
from tools.research_tools import search_arxiv, search_pubmed
from tools.task_tools import create_task_tool
from tools.todo_tools import read_todos, write_todos


model = init_chat_model(model="openai:gpt-5-mini", temperature=0.0)


research_agent = {
    "name": "research-agent",
    "description": "PubMed와 arXiv를 사용해 raw paper 메타데이터를 수집합니다.",
    "prompt": RESEARCH_PROMPT,
    "tools": ["search_papers_file", "search_pubmed", "search_arxiv", "write_file", "read_file", "ls"],
}

dedup_agent = {
    "name": "dedup-agent",
    "description": "수집된 raw paper 파일을 읽고 중복 제거 결과를 작성합니다.",
    "prompt": DEDUP_PROMPT,
    "tools": ["deduplicate_papers_file", "read_file", "write_file", "ls"],
}

relevance_agent = {
    "name": "relevance-agent",
    "description": "중복 제거된 논문을 읽고 관련도 평가 결과를 작성합니다.",
    "prompt": RELEVANCE_PROMPT,
    "tools": ["score_papers_file", "read_file", "write_file", "ls"],
}

summarize_agent = {
    "name": "summarizer-agent",
    "description": "점수화된 논문을 읽고 요약 및 최종 결과를 작성합니다.",
    "prompt": SUMMARIZE_PROMPT,
    "tools": ["summarize_papers_file", "build_final_results_file", "read_file", "write_file", "ls"],
}


all_subagents = [
    research_agent,
    dedup_agent,
    relevance_agent,
    summarize_agent,
]

all_tools = [
    ls,
    read_file,
    write_file,
    think_tool,
    write_todos,
    read_todos,
    search_pubmed,
    search_arxiv,
    search_papers_file,
    deduplicate_papers_file,
    score_papers_file,
    summarize_papers_file,
    build_final_results_file,
]


task_tool = create_task_tool(
    tools=all_tools,
    subagents=all_subagents,
    model=model,
    state_schema=MainAgentState,
)


main_agent_tools = [ls, read_file, write_file, think_tool, write_todos, read_todos, task_tool]


main_agent = create_agent(
    model,
    tools=main_agent_tools,
    system_prompt=MAIN_AGENT_INSTRUCTIONS,
    state_schema=MainAgentState,
)
