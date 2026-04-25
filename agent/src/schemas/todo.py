from typing_extensions import NotRequired, TypedDict

from schemas.plan import TodoStatus

class Todo(TypedDict):
    content: str
    status: TodoStatus
    reason: NotRequired[str]
