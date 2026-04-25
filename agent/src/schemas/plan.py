from typing import Literal, TypedDict


TodoStatus = Literal["pending", "in_progress", "completed"]


class ExecutionPlan(TypedDict):
    domains: list[str]
    search_scope: str
    min_papers: int
    todos: list[str]
