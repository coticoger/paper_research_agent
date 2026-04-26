import json
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from config import PAPER_SEARCH_MODELS 

from tools.file_tools import ls, read_file, write_file
from tools.pdf_tools import get_pdf_metadata, download_pdf, extract_pdf_text, find_pdf_section_headings, extract_pdf_key_sections
from prompts.paper_search_prompt import SUMMARIZER_PROMPT
from schemas.agent_state import AgentState
from langgraph.types import Command

model = PAPER_SEARCH_MODELS ["summarizer-agent"]["model"]
temperature = PAPER_SEARCH_MODELS ["summarizer-agent"]["temperature"]

llm = init_chat_model(model = model, temperature = temperature)

agent = create_agent(
    llm,
    tools = [ls, read_file, write_file, download_pdf, extract_pdf_key_sections],
    system_prompt=(
        "You are a paper summarization agent. Your job is to inspect the most relevant "
        "papers, use the PDF tools when possible, extract evidence from the paper itself, "
        "and produce concise but faithful summaries of the problem, method, key findings, "
        "limitations, and user relevance. Prefer evidence-based summaries over guesses, "
        "and be explicit when information is missing or uncertain."
    )
)

def select_top_papers(papers: list[dict], top_k : int = 5) -> list[dict]:
    return sorted(
        papers,
        key=lambda x : float(x.get("relevance_score", 0)),
        reverse = True
    )[:min(len(papers),top_k)]

def summary_agent(state : AgentState)-> Command:
    print(f"✅ summary agent로 관련도 높은 논문을 요약해서 정리합니다.")

    relevant_papers = state.get("relevant_papers",[])
    path = state.get("path","")
    papers_json = json.dumps(relevant_papers, ensure_ascii=False, indent=2)

    result = agent.invoke({
        "messages":[{"role":"user","content":SUMMARIZER_PROMPT.format(papers=papers_json, path=path)}]
    })

    content = result["messages"][-1].content
    parsed = json.loads(content)

    print(f"✅ summary agent 논문 요약 완료")

    return Command(
        update = {
            "summaries" : parsed.get("summaries",[])
        },
        goto = "validation_agent"
    )
