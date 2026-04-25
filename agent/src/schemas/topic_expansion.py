from typing import TypedDict
from typing_extensions import NotRequired

from schemas.topic import Topic


class TopicExpansionResult(TypedDict):
    candidate_topics: list[Topic]
    ambiguity_score: float
    needs_user_clarification: bool
    clarification_question: NotRequired[str]
    approved_topics: NotRequired[list[Topic]]
