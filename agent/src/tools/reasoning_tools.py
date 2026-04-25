from pathlib import Path
from langchain_core.tools import tool

WORKSPACE_DIR = Path(__file__).parent.parent / "memory"

#----------------
# think_tool : 에이전트가 리서치 진행 상황을 성찰하고 다음 단계를 계획하는 데 사용
#----------------
@tool
def think_tool(reflection : str) -> str:
    """
    리서치 진행 상황에 대한 전략적 성찰 도구.

    각 검색 후에 이 도구를 사용하여 결과를 분석하고 다음 단계를 체계적으로 계획하세요.

    성찰 시 다루어야 할 내용:
    1. 현재 발견한 정보 분석 - 어떤 구체적인 정보를 수집했는가?
    2. 갭 평가 - 아직 부족한 핵심 정보는 무엇인가?
    3. 품질 평가 - 좋은 답변을 위한 충분한 근거 / 예시가 있는가?
    4. 전략적 결정 - 계속 검색할 것인가, 답변을 제공할 것인가?

    Args:
        reflection : 리서치 진행, 발견, 갭, 다음 단계에 대한 상세한 성찰

    Returns:
        의사결정을 위해 성찰이 기록되었음을 확인
    """
    return f"[Reflection]\n {reflection[:200]}..."
