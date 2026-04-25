from typing import TypedDict
from typing_extensions import NotRequired

class Topic(TypedDict):
    topic: str
    keywords: list[str]
    query: str
    reason: NotRequired[str]
