from typing_extensions import TypedDict, Annotated, Optional, NotRequired
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages : list[BaseMessage]

    path : NotRequired[str]

    topics : NotRequired[list[str]]
    new_messages : NotRequired[str]
    task : NotRequired[str]
    humman_feedback : NotRequired[str]

    papers : NotRequired[list[dict]]
    relevant_papers : NotRequired[list[dict]]
    summaries : NotRequired[list[dict]]
    validation_result : NotRequired[dict]

    validated_papers : list[dict]
    rejected_papers : list[dict]
    needs_retry : bool

    retry_count : NotRequired[int]

    final_result : NotRequired[str]
