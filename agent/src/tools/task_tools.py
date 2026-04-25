from typing import Any, TypedDict

from langchain.agents import create_agent
from langchain_core.tools import BaseTool, tool

from config import AGENT_RECURSION_LIMIT
from graph.state import SubAgentType
from tools.description import TASK_DESCRIPTION_PREFIX


class SubAgentSpec(TypedDict, total=False):
    name: SubAgentType
    description: str
    prompt: str
    tools: list[str]
    state_schema: Any
    model: Any


DEFAULT_SUBAGENTS: list[SubAgentSpec] = [
    {"name": "research-agent", "description": "논문 검색과 raw_papers 산출"},
    {"name": "dedup-agent", "description": "중복 제거와 dedup_papers 산출"},
    {"name": "relevance-agent", "description": "관련도 점수화와 scored_papers 산출"},
    {"name": "summarizer-agent", "description": "논문 요약과 summaries 산출"},
]


def _subagent_listing(subagents: list[SubAgentSpec]) -> str:
    return "\n".join(
        f"- **{spec['name']}**: {spec['description']}"
        for spec in subagents
    )


def _extract_result_text(result: dict[str, Any]) -> str:
    messages = result.get("messages", [])
    if not messages:
        return "[Warning] 서브 에이전트가 메시지를 반환하지 않았습니다."

    last_message = messages[-1]
    content = getattr(last_message, "content", None)
    if isinstance(content, str):
        return content[:4000] + ("... [truncated]" if len(content) > 4000 else "")
    if isinstance(last_message, dict):
        text = str(last_message.get("content", last_message))
        return text[:4000] + ("... [truncated]" if len(text) > 4000 else "")
    text = str(last_message)
    return text[:4000] + ("... [truncated]" if len(text) > 4000 else "")


def create_task_tool(
    tools: list[Any],
    subagents: list[SubAgentSpec],
    model: Any | None = None,
    state_schema: Any | None = None,
):
    """서브 에이전트 구성에 맞는 task 도구를 생성합니다."""
    agents: dict[str, Any] = {}
    tools_by_name = {tool_.name: tool_ for tool_ in tools if isinstance(tool_, BaseTool)}

    for spec in subagents:
        missing_keys = [key for key in ["name", "description", "prompt"] if key not in spec]
        if missing_keys:
            raise ValueError(f"subagent spec 누락: {missing_keys}")

        selected_tools = tools
        if "tools" in spec:
            unknown_tools = [name for name in spec["tools"] if name not in tools_by_name]
            if unknown_tools:
                raise ValueError(f"{spec['name']}에 알 수 없는 tool 지정: {unknown_tools}")
            selected_tools = [tools_by_name[name] for name in spec["tools"]]

        agent_kwargs = {
            "model": spec.get("model", model),
            "tools": selected_tools,
            "system_prompt": spec["prompt"],
        }
        state_schema = spec.get("state_schema", state_schema)
        if state_schema is not None:
            agent_kwargs["state_schema"] = state_schema

        agents[spec["name"]] = create_agent(**agent_kwargs)

    other_agents_string = _subagent_listing(subagents)

    @tool(description=TASK_DESCRIPTION_PREFIX.format(other_agents=other_agents_string))
    def configured_task(description: str, subagent_type: SubAgentType) -> str:
        """
        서브 에이전트에 작업을 위임합니다.

        Note: 파일은 로컬 디스크에 저장되므로 서브 에이전트가 저장한 파일은
        메인 에이전트에서도 접근 가능합니다.
        """
        if subagent_type not in agents:
            return f"[Warning] {subagent_type} 없음.\n사용 가능: {list(agents.keys())}"

        sub_agent = agents[subagent_type]
        isolated_state = {
            "messages": [{"role": "user", "content": description}],
            "instruction": description,
            "subagent_type": subagent_type,
        }
        result = sub_agent.invoke(
            isolated_state,
            config={"recursion_limit": AGENT_RECURSION_LIMIT},
        )
        return _extract_result_text(result)

    return configured_task


@tool(description=TASK_DESCRIPTION_PREFIX.format(other_agents=_subagent_listing(DEFAULT_SUBAGENTS)))
def task(description: str, subagent_type: SubAgentType) -> str:
    """
    서브 에이전트 위임용 기본 task 도구.

    아직 런타임 서브 에이전트 구성이 연결되지 않은 환경에서도 메인 에이전트가
    import 단계에서 깨지지 않도록 기본 인터페이스를 제공합니다.
    """
    return (
        "[Delegation prepared]\n"
        f"subagent_type: {subagent_type}\n"
        f"description: {description}\n"
        "Note: 실제 서브 에이전트 실행은 create_task_tool(...)로 구성해야 합니다."
    )
