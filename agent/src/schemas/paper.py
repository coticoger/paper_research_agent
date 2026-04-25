from pydantic import BaseModel, Field
from typing_extensions import Optional

class Paper(BaseModel):
    paper_id : str
    title : str
    authors : list[str]= Field(default_factory=list)
    year : Optional[int] = None
    published : Optional[str] = None
    abstract : Optional[str] = None
    doi : Optional[str] = None
    url : Optional[str] = None
    source : str
    pmid : Optional[str] = None
    arxiv_id : Optional[str] = None
    citation_count : Optional[int] = None

class ScoredPaper(Paper):
    relevance_score : float
    relevance_reason : Optional[str] = None

class SummarizedPaper(ScoredPaper):
    summary : str
