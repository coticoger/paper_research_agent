# 그래프 확인하는 코드

from pathlib import Path
import sys


AGENT_SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = AGENT_SRC_DIR.parent.parent

if str(AGENT_SRC_DIR) not in sys.path:
    sys.path.append(str(AGENT_SRC_DIR))

try:
    from graph.workflow import workflow  # noqa: E402
except ModuleNotFoundError as e:
    if e.name == "langgraph":
        print("langgraph 패키지가 설치되지 않았습니다.")
        print("다음 명령으로 설치하세요:")
        print("python -m pip install -r agent/requirement.txt")
        raise SystemExit(1)
    raise


def main():
    graph = workflow.get_graph()

    png_path = ROOT_DIR / "workflow_graph.png"
    mermaid_path = ROOT_DIR / "workflow_graph.mmd"

    try:
        png_bytes = graph.draw_mermaid_png()
        png_path.write_bytes(png_bytes)
        print(f"workflow graph image saved: {png_path}")
    except Exception:
        mermaid = graph.draw_mermaid()
        mermaid_path.write_text(mermaid, encoding="utf-8")
        print(f"PNG rendering failed. Mermaid text saved: {mermaid_path}")
        print(mermaid)


if __name__ == "__main__":
    main()
