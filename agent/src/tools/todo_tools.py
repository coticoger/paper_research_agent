from pathlib import Path
from langgraph.types import Command
from graph.state import MainAgentState
from schemas.todo import Todo
from langchain.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from tools.description import WRITE_TODOS_DESCRIPTION
from typing_extensions import Annotated
from langchain_core.tools import tool, InjectedToolCallId

WORKSPACE_DIR = Path(__file__).parent.parent / "memory"

#----------------
# Todo 관리  도구
#----------------
@tool(description=WRITE_TODOS_DESCRIPTION)
def write_todos(todos : list[Todo], tool_call_id : Annotated[str, InjectedToolCallId]) -> Command:
    """TODO 목록을 업데이트 합니다."""
    return Command(
        update = {
            "todos" : todos,
            "messages" : [
                ToolMessage(f"TODO 업데이트됨 : {todos}", tool_call_id = tool_call_id)
            ]
        }
    )

@tool
def read_todos(state: Annotated[MainAgentState, InjectedState]) -> str:
    """현재 TODO 목록을 읽습니다."""
    todos = state.get("todos",[])
    if not todos:
        return "[Warning] TODO가 없습니다"
    
    result = "현재 TODO\n"
    for i, todo in enumerate(todos, 1):
        emoji = {"pending" : "🟡", "in_progress" : "🟢", "completed" : "🔵", "fail" : "🔴"}.get(todo["status"], "🔴")
        result += f"{i}. {emoji}({todo['status']}) {todo['content']}\n"
    return result.strip()
