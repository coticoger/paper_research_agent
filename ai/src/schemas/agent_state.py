from typing_extensions import TypedDict, Annotated, Optional, NotRequired
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages : list[BaseMessage]
    final_result : NotRequired[str]

    path : NotRequired[str] # 저장공간 위치

    new_messages : NotRequired[str]
    task : NotRequired[str]
    human_feedback : NotRequired[str]

    topics : NotRequired[list[str]]
    papers : NotRequired[list[dict]]
    relevant_papers : NotRequired[list[dict]]
    summaries : NotRequired[list[dict]]
    validation_result : NotRequired[dict]
    validated_papers : list[dict]
    rejected_papers : list[dict]
    needs_retry : bool
    retry_count : NotRequired[int]
    
    pdf_path : str
    plans : list[str]
    insepctor : NotRequired[dict]



