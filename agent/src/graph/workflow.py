import json
import re
from pathlib import Path
from typing import Any

from IPython.display import Image, display
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from config import (
    AGENT_RECURSION_LIMIT,
    MAX_ITER,
    SEARCH_MAX_RESULTS_PER_SOURCE,
    SUMMARY_MAX_PAPERS,
    SUMMARY_RELEVANCE_THRESHOLD,
)
from graph.state import MainAgentState

WORKSPACE_DIR = Path(__file__).parent.parent / "memory"


def _resolve_run_dir(run_started_at: float | None) -> Path:
    if run_started_at is None:
        return WORKSPACE_DIR
    from datetime import datetime
    folder = datetime.fromtimestamp(run_started_at).strftime("%Y-%m-%d_%H-%M-%S")
    return WORKSPACE_DIR / folder


def _debug(message: str):
    print(f"[workflow] {message}", flush=True)


def _extract_message_content(message) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content)


def _extract_json_payload(result: dict[str, Any]) -> dict[str, Any] | None:
    messages = result.get("messages", [])
    if not messages:
        return None

    content = _extract_message_content(messages[-1]).strip()
    candidates = [content]
    if "```json" in content:
        candidates.extend(
            block.split("```", 1)[0].strip()
            for block in content.split("```json")[1:]
            if block.strip()
        )

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            continue
    return None


def _select_topics(candidates: list[dict[str, Any]], selection: Any) -> tuple[list[dict[str, Any]], bool, str | None]:
    if isinstance(selection, dict):
        action = str(selection.get("action", "select")).lower()
        if action in {"retry", "regenerate"}:
            return [], True, selection.get("query") or selection.get("message")
        selection = selection.get("selection") or selection.get("choice") or selection.get("selected")

    if isinstance(selection, list):
        selected = [
            topic
            for index, topic in enumerate(candidates, start=1)
            if index in selection or str(index) in selection
        ]
        return selected, False, None

    selection_text = str(selection or "").strip()
    if not selection_text:
        return [], True, None
    if selection_text.lower() in {"all", "a", "전체"}:
        return candidates, False, None
    if selection_text.lower().startswith(("retry", "again", "다시")):
        return [], True, selection_text

    indices = [int(value) for value in re.findall(r"\d+", selection_text)]
    selected = [
        topic
        for index, topic in enumerate(candidates, start=1)
        if index in indices
    ]
    if selected:
        return selected, False, None
    return [], True, selection_text



def _read_jsonl(path: str, run_started_at: float | None = None) -> list[dict[str, Any]]:
    target = _resolve_run_dir(run_started_at) / path
    if not target.exists():
        return []
    rows = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _read_json(path: str, run_started_at: float | None = None):
    target = _resolve_run_dir(run_started_at) / path
    if not target.exists():
        return None
    return json.loads(target.read_text(encoding="utf-8"))


def _count_jsonl(path: str, run_started_at: float | None = None) -> int:
    target = _resolve_run_dir(run_started_at) / path
    if not target.exists():
        return 0
    return sum(1 for line in target.read_text(encoding="utf-8").splitlines() if line.strip())


def _load_pipeline_outputs(state: MainAgentState) -> dict[str, Any]:
    run_started_at = state.get("run_started_at")
    pipeline_status = {
        "raw_papers_count": _count_jsonl("raw_papers.jsonl", run_started_at),
        "dedup_papers_count": _count_jsonl("dedup_papers.jsonl", run_started_at),
        "scored_papers_count": _count_jsonl("scored_papers.jsonl", run_started_at),
        "summarized_papers_count": _count_jsonl("summaries.jsonl", run_started_at),
    }

    update: dict[str, Any] = {"pipeline_status": pipeline_status}

    summaries = _read_jsonl("summaries.jsonl", run_started_at)
    if summaries:
        update["summarized_papers"] = summaries

    final_results = _read_json("final_results.json", run_started_at)
    if final_results:
        update["final_results"] = final_results

    dedup_result = _read_json("dedup_result.json", run_started_at)
    if dedup_result:
        update["dedup_result"] = dedup_result
    return update


def _build_todos() -> list[dict[str, str]]:
    return [
        {"content": "Search approved topics", "status": "pending"},
        {"content": "Deduplicate papers", "status": "pending"},
        {"content": "Score relevance", "status": "pending"},
        {"content": "Summarize papers with relevance_score >= 0.7", "status": "pending"},
        {"content": "Build final_results.json", "status": "pending"},
    ]


def _completed_todos() -> list[dict[str, str]]:
    return [
        {**todo, "status": "completed"}
        for todo in _build_todos()
    ]


def run_topic_agent(state: MainAgentState):
    _debug("enter topic_agent")
    from agents.topic_agent import topic_agent

    result = topic_agent.invoke(state)
    payload = _extract_json_payload(result)
    if payload:
        result["topic_expansion"] = payload
        result["topics"] = payload.get("candidate_topics", [])
        result["topic_retry_requested"] = False
    _debug(f"exit topic_agent | keys={sorted(result.keys())}")
    return result


def run_topic_selection(state: MainAgentState):
    _debug("enter topic_selection")
    if state.get("approved_topics"):
        _debug("exit topic_selection | approved_topics already present")
        return {"topic_retry_requested": False}

    topic_expansion = state.get("topic_expansion", {})
    candidates = topic_expansion.get("candidate_topics") or state.get("topics", [])
    selection = interrupt(
        {
            "type": "topic_selection",
            "message": "Select topic numbers, type 'all', or type a new request to regenerate topics.",
            "candidate_topics": candidates,
            "clarification_question": topic_expansion.get("clarification_question"),
        }
    )
    selected_topics, retry_requested, retry_query = _select_topics(candidates, selection)
    if retry_requested:
        update: dict[str, Any] = {"topic_retry_requested": True}
        if retry_query:
            update["user_query"] = retry_query
            update["messages"] = [HumanMessage(content=retry_query)]
        _debug("exit topic_selection | retry requested")
        return update

    _debug(f"exit topic_selection | selected={len(selected_topics)}")
    return {
        "approved_topics": selected_topics,
        "topics": selected_topics,
        "topic_retry_requested": False,
        "messages": [
            HumanMessage(
                content="Selected topics: "
                + json.dumps(selected_topics, ensure_ascii=False)
            )
        ],
    }


def run_main_agent(state: MainAgentState):
    _debug("enter main_agent")

    approved_topics = state.get("approved_topics", [])
    plan = {
        "domains": [topic.get("topic", "research topic") for topic in approved_topics],
        "search_scope": state.get("search_scope", "default"),
        "min_papers": state.get("min_papers", 0),
        "todos": [todo["content"] for todo in _build_todos()],
    }
    result = {
        "todos": _build_todos(),
        "plan": plan,
        "validation_iter": 0,
        "final_results": [],
        "summarized_papers": [],
        "messages": [
            AIMessage(
                content=(
                    "Planned low-token pipeline execution. Large JSONL files will be processed "
                    "by deterministic tools instead of being read into the agent context."
                )
            )
        ],
    }
    _debug(f"exit main_agent | keys={sorted(result.keys())}")
    return result


def run_paper_pipeline(state: MainAgentState):
    _debug("enter paper_pipeline")
    from tools.paper_pipeline_tools import (
        build_final_results_file,
        deduplicate_papers_file,
        score_papers_file,
        search_papers_file,
        set_run_dir,
        summarize_papers_file,
    )

    set_run_dir(state.get("run_started_at") or __import__("time").time())

    approved_topics = state.get("approved_topics", [])
    if not approved_topics:
        return {
            "pipeline_status": {"error": "approved_topics is empty"},
            "messages": [AIMessage(content="[Warning] approved_topics is empty")],
        }

    max_total_results = SEARCH_MAX_RESULTS_PER_SOURCE * 2 * len(approved_topics)
    logs = [
        search_papers_file.invoke(
            {
                "topics": approved_topics,
                "max_results_per_source": SEARCH_MAX_RESULTS_PER_SOURCE,
                "max_total_results": max_total_results,
            }
        ),
        deduplicate_papers_file.invoke({}),
        score_papers_file.invoke({"topics": approved_topics}),
        summarize_papers_file.invoke(
            {
                "relevance_threshold": SUMMARY_RELEVANCE_THRESHOLD,
                "max_papers": SUMMARY_MAX_PAPERS,
            }
        ),
        build_final_results_file.invoke({}),
    ]

    result = _load_pipeline_outputs(state)
    result["todos"] = _completed_todos()
    result["messages"] = [AIMessage(content="\n".join(logs))]
    _debug(f"exit paper_pipeline | status={result.get('pipeline_status')}")
    return result


def route_after_topic_selection(state: MainAgentState) -> str:
    if state.get("topic_retry_requested"):
        _debug("route_after_topic_selection -> topic_agent")
        return "topic_agent"
    _debug("route_after_topic_selection -> main_agent")
    return "main_agent"


def run_final_validator(state: MainAgentState):
    _debug("enter final_validator")
    from agents.final_validator import final_validator

    result = final_validator.invoke(
        state,
        config={"recursion_limit": AGENT_RECURSION_LIMIT},
    )
    result["validation_iter"] = state.get("validation_iter", 0) + 1
    _debug(
        f"exit final_validator | validation_iter={result['validation_iter']} "
        f"| final_results={len(result.get('final_results', []))}"
    )
    return result


def route_after_validation(state: MainAgentState) -> str:
    if state.get("validation_iter", 0) >= MAX_ITER:
        _debug(f"route_after_validation -> END (validation_iter={state.get('validation_iter', 0)})")
        return END
    if state.get("final_results"):
        _debug("route_after_validation -> END (final_results present)")
        return END
    _debug("route_after_validation -> main_agent")
    return "main_agent"


def build_workflow():
    graph = StateGraph(MainAgentState)

    graph.add_node("topic_agent", run_topic_agent)
    graph.add_node("topic_selection", run_topic_selection)
    graph.add_node("main_agent", run_main_agent)
    graph.add_node("paper_pipeline", run_paper_pipeline)
    graph.add_node("final_validator", run_final_validator)

    graph.add_edge(START, "topic_agent")
    graph.add_edge("topic_agent", "topic_selection")
    graph.add_conditional_edges(
        "topic_selection",
        route_after_topic_selection,
        {
            "topic_agent": "topic_agent",
            "main_agent": "main_agent",
        },
    )
    graph.add_edge("main_agent", "paper_pipeline")
    graph.add_edge("paper_pipeline", "final_validator")
    graph.add_conditional_edges(
        "final_validator",
        route_after_validation,
        {
            "main_agent": "main_agent",
            END: END,
        },
    )

    return graph.compile(checkpointer=MemorySaver())


def display_workflow_graph(app=None):
    app = app or build_workflow()
    try:
        display(Image(app.get_graph().draw_mermaid_png()))
    except Exception:
        print(app.get_graph().draw_mermaid())
    return app


workflow = build_workflow()


if __name__ == "__main__":
    display_workflow_graph(workflow)
