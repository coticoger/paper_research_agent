WRITE_TODOS_DESCRIPTION = """
복잡한 워크플로우를 추적하기 위한 구조화된 작업 목록을 생성합니다.

## 언제 사용
- 여러 단계가 필요한 복잡한 작업
- 사용자가 여러 작업을 요청했을 때

## 구조
- 상태는 pending, in_progress, completed, fail 중 하나
- 한 번에 하나의 in_progress 작업만
"""

#-----------------------------

TASK_DESCRIPTION_PREFIX = """
특화된 서브 에이전트에게 작업을 위임합니다.
각 서브 에이전트는 격리된 컨텍스트에서 실행됩니다.

## 사용 가능한 서브 에이전트:
{other_agents}
"""

