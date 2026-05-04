# pdf가 실제로 읽히는지 확인하고, 전체 구조를 파악
import json
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from config import PAPER_ANALYSIS_MODELS
from langgraph.types import Command
from schemas.agent_state import AgentState
from tools.inspector_tools import extract_blocks_tool, extract_figure_tables_tools, extract_metadata_tool, extract_text_tool
from tools.file_tools import ls, write_file
from utils import file_dir
from prompts.paper_analysis_prompt import INSPECTOR_PROMPT

model = PAPER_ANALYSIS_MODELS["inspector-agent"]["model"]
temperature = PAPER_ANALYSIS_MODELS["inspector-agent"]["temperature"]


llm = init_chat_model(model = model, temperature = temperature)

agent = create_agent(
    llm,
    tools = [ls, write_file, extract_blocks_tool, extract_figure_tables_tools, extract_metadata_tool, extract_text_tool],
    system_prompt = (
        "You are a PDF inspection agent. Your job is to inspect a paper PDF using "
        "the available tools, verify that the file is readable, and collect reliable "
        "structural context for downstream paper analysis agents. Use evidence from "
        "the PDF itself, avoid guessing when text is missing or unclear, and return "
        "structured JSON that is easy for later agents to consume."
    )
)

def inspector_agent(state : AgentState) -> Command:
    print(f"🔍 inspector agent로 논문 분석을 시작합니다\n")
    plans = state.get("plans","")
    path = file_dir()
    pdf_path = state.get("pdf_path","")

    result = agent.invoke({
        "messages" : [{"role":"user", "content":INSPECTOR_PROMPT.format(plans = plans, path = path, pdf_path = pdf_path)}]
    })

    content = result["messages"][-1].content
    parsed = json.loads(content)

    return Command(
        update = {
            "inspector" : parsed,
            "path" : path
        },
        goto = "__end__"
    )
