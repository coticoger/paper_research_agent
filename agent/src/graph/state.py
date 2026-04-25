from typing import Annotated, Literal, TypeAlias, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from schemas.dedup import DedupResult
from schemas.paper import Paper, ScoredPaper, SummarizedPaper
from schemas.plan import ExecutionPlan
from schemas.notion import NotionWriteResult
from schemas.result import Result
from schemas.topic import Topic
from schemas.topic_expansion import TopicExpansionResult
from schemas.todo import Todo

class MainAgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    user_query: str
    topic_expansion: TopicExpansionResult
    approved_topics: list[Topic]
    search_scope: str
    min_papers: int
    year_range: str
    preferred_sources: list[str]
    todos: list[Todo]
    plan: ExecutionPlan
    topics: list[Topic]
    raw_papers: list[Paper]
    dedup_result: DedupResult
    dedup_papers: list[Paper]
    scored_papers: list[ScoredPaper]
    summarized_papers: list[SummarizedPaper]
    final_results: list[Result]
    notion_result: NotionWriteResult

SubAgentStatus = Literal["pending", "in_progress", "complete", "fail"]
SubAgentType = Literal[
    "research-agent",
    "dedup-agent",
    "relevance-agent",
    "summarizer-agent",
    "notion-agent",
]


class BaseSubAgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    task_id: str
    subagent_type: SubAgentType
    user_query: str
    instruction: str
    input_path: str
    output_path: str
    status: SubAgentStatus
    error: str


class ResearchAgentState(BaseSubAgentState, total=False):
    subagent_type: Literal["research-agent"]
    topics: list[Topic]
    raw_papers: list[Paper]
    search_scope: str
    min_papers: int
    preferred_sources: list[str]


class DedupAgentState(BaseSubAgentState, total=False):
    subagent_type: Literal["dedup-agent"]
    raw_papers: list[Paper]
    dedup_result: DedupResult
    dedup_papers: list[Paper]


class RelevanceAgentState(BaseSubAgentState, total=False):
    subagent_type: Literal["relevance-agent"]
    topics: list[Topic]
    dedup_papers: list[Paper]
    scored_papers: list[ScoredPaper]
    relevance_threshold: float


class SummarizerAgentState(BaseSubAgentState, total=False):
    subagent_type: Literal["summarizer-agent"]
    topics: list[Topic]
    scored_papers: list[ScoredPaper]
    summarized_papers: list[SummarizedPaper]
    summary_threshold: float


class NotionAgentState(BaseSubAgentState, total=False):
    subagent_type: Literal["notion-agent"]
    summarized_papers: list[SummarizedPaper]
    final_results: list[Result]
    notion_result: NotionWriteResult


SubAgentState: TypeAlias = (
    ResearchAgentState
    | DedupAgentState
    | RelevanceAgentState
    | SummarizerAgentState
    | NotionAgentState
)
