from typing import TypedDict
from typing_extensions import NotRequired

from schemas.paper import SummarizedPaper

class Result(TypedDict):
    topic: str
    summary: str
    papers: list[SummarizedPaper]
    tags: NotRequired[list[str]]
    status: NotRequired[str]
