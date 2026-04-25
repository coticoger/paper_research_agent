import argparse
import json
from pathlib import Path
import sys
import time

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.types import Command


CURRENT_DIR = Path(__file__).resolve().parent
AGENT_DIR = CURRENT_DIR.parent
load_dotenv(AGENT_DIR / ".env")

if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from config import GRAPH_RECURSION_LIMIT  # noqa: E402
from graph.workflow import display_workflow_graph, workflow  # noqa: E402


def _parse_args():
    parser = argparse.ArgumentParser(description="AI Office workflow runner")
    parser.add_argument(
        "query",
        nargs="?",
        default="Genomics와 AI 관련 논문 찾아줘",
        help="workflow에 전달할 사용자 질의",
    )
    parser.add_argument(
        "--graph",
        action="store_true",
        help="워크플로우 그래프만 출력합니다.",
    )
    parser.add_argument(
        "--recursion-limit",
        type=int,
        default=GRAPH_RECURSION_LIMIT,
        help="Outer workflow recursion limit",
    )
    return parser.parse_args()


def _print_result(result):
    print("\n=== Workflow Result ===")

    summary = {
        "user_query": result.get("user_query"),
        "approved_topics": result.get("approved_topics"),
        "todos": result.get("todos"),
        "final_results_count": len(result.get("final_results", [])),
        "messages_count": len(result.get("messages", [])),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))

    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        content = getattr(last_message, "content", None)
        print("\n=== Last Message ===")
        print(content if content is not None else str(last_message))


def _print_topic_selection(interrupt_value):
    candidates = interrupt_value.get("candidate_topics", [])
    question = interrupt_value.get("clarification_question")
    print("\n=== Topic Candidates ===")
    if question:
        print(question)
    for index, topic in enumerate(candidates, start=1):
        keywords = ", ".join(topic.get("keywords", []))
        print(f"{index}. {topic.get('topic', 'Untitled')}")
        if topic.get("query"):
            print(f"   query: {topic['query']}")
        if keywords:
            print(f"   keywords: {keywords}")
    print("\nSelect numbers like '1,3', type 'all', or type a new request to regenerate topics.")


def _resume_workflow(result, config):
    while result.get("__interrupt__"):
        interrupt_obj = result["__interrupt__"][0]
        interrupt_value = getattr(interrupt_obj, "value", interrupt_obj)
        if isinstance(interrupt_value, dict) and interrupt_value.get("type") == "topic_selection":
            _print_topic_selection(interrupt_value)
            selection = input("\nYour topic choice: ").strip()
            result = workflow.invoke(Command(resume={"action": "select", "selection": selection}), config=config)
            continue

        print("\n=== Workflow Paused ===")
        print(interrupt_value)
        selection = input("\nResume value: ").strip()
        result = workflow.invoke(Command(resume=selection), config=config)
    return result


def main():
    args = _parse_args()
    print("[run] starting workflow runner", flush=True)
    print(f"[run] query={args.query}", flush=True)
    print(f"[run] recursion_limit={args.recursion_limit}", flush=True)

    if args.graph:
        print("[run] graph mode enabled", flush=True)
        display_workflow_graph(workflow)
        return

    initial_state = {
        "user_query": args.query,
        "run_started_at": time.time(),
        "messages": [HumanMessage(content=args.query)],
    }
    config = {
        "recursion_limit": args.recursion_limit,
        "configurable": {"thread_id": f"cli-{int(time.time())}"},
    }

    print("[run] invoking workflow...", flush=True)
    result = workflow.invoke(initial_state, config=config)
    result = _resume_workflow(result, config)
    print("[run] workflow finished", flush=True)
    _print_result(result)


if __name__ == "__main__":
    main()
