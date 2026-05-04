import argparse
from langchain_core.messages import HumanMessage

from pathlib import Path
from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent

load_dotenv(PROJECT_DIR / ".env")

from graph.graph import build_graph
from schemas.agent_state import AgentState


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="사용자 요청")
    parser.add_argument("--pdf", dest="pdf_path", default=None, help="PDF 파일 경로")
    return parser.parse_args()


def main():
    args = parse_args()

    state: AgentState = {
        "messages": [
            HumanMessage(content=args.query)
        ],
        "topics": [],
    }

    if args.pdf_path:
        state["pdf_path"] = str(Path(args.pdf_path).resolve())

    app = build_graph()
    graph = app.get_graph()
    graph_png_path = PROJECT_DIR / "paper_search_graph.png"
    graph_mermaid_path = PROJECT_DIR / "paper_search_graph.mmd"

    try:
        graph_png = graph.draw_mermaid_png()
        graph_png_path.write_bytes(graph_png)
        print(f"🖼️ 그래프 이미지를 저장했습니다: {graph_png_path}")
    except Exception:
        graph_mermaid = graph.draw_mermaid()
        graph_mermaid_path.write_text(graph_mermaid, encoding="utf-8")
        print(f"📝 그래프 PNG 저장에 실패해서 mermaid 텍스트를 저장했습니다: {graph_mermaid_path}")

    result = app.invoke(state)

    print("‼️ 최종 결과는 다음과 같습니다")
    print(result.get("validated_papers"))


if __name__ == "__main__":
    main()
