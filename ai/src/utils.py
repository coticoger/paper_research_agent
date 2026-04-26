import re
from datetime import datetime
from typing import Any

def today():
    return datetime.now().strftime(f'%Y-%m-%d')

def file_dir():
    return datetime.now().strftime(f'%Y-%m-%d_%H-%M-%S')

def normalize_title(title: str) -> str:
    title = title.lower().strip()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title)
    return title


def deduplicate_papers(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    deduped = []

    for paper in papers:
        doi = paper.get("doi")
        arxiv_id = paper.get("arxiv_id")
        pubmed_id = paper.get("pubmed_id") or paper.get("pmid")
        title = paper.get("title", "")

        if doi:
            key = f"doi:{doi.lower().strip()}"
        elif arxiv_id:
            key = f"arxiv:{arxiv_id.lower().strip()}"
        elif pubmed_id:
            key = f"pmid:{str(pubmed_id).strip()}"
        else:
            key = f"title:{normalize_title(title)}"

        if key in seen:
            continue

        seen.add(key)
        deduped.append(paper)

    return deduped

def filter_papers_by_relevance( scored_papers: list[dict], threshold: float = 0.7) -> list[dict]:
    return [
        paper for paper in scored_papers
        if float(paper.get("relevance_score", 0.0)) >= threshold
    ]