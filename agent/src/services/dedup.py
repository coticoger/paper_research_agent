import re
from difflib import SequenceMatcher

from schemas.dedup import DedupResult
from schemas.paper import Paper


SOURCE_PRIORITY = {
    "semantic_scholar": 0,
    "pubmed": 1,
    "arxiv": 2,
}


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().split())


def _normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    normalized = _normalize_text(doi).lower()
    normalized = normalized.removeprefix("https://doi.org/")
    normalized = normalized.removeprefix("http://doi.org/")
    normalized = normalized.removeprefix("doi:")
    return normalized or None


def _extract_arxiv_id(paper: Paper) -> str | None:
    if paper.arxiv_id:
        return _normalize_text(paper.arxiv_id).lower()

    if paper.paper_id.startswith("arxiv_"):
        return _normalize_text(paper.paper_id.removeprefix("arxiv_")).lower() or None

    if paper.url and "/abs/" in paper.url:
        tail = paper.url.split("/abs/")[-1]
        return tail.split("v")[0].strip().lower() or None

    return None


def _extract_pmid(paper: Paper) -> str | None:
    if paper.pmid:
        return _normalize_text(paper.pmid)

    if paper.paper_id.startswith("pubmed_"):
        return _normalize_text(paper.paper_id.removeprefix("pubmed_")) or None

    if paper.url and "pubmed.ncbi.nlm.nih.gov" in paper.url:
        match = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", paper.url)
        if match:
            return match.group(1)

    return None


def _normalize_title(title: str | None) -> str:
    normalized = _normalize_text(title).lower()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    return " ".join(normalized.split())


def _title_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0

    if left == right:
        return 1.0

    left_tokens = " ".join(sorted(set(left.split())))
    right_tokens = " ".join(sorted(set(right.split())))
    return SequenceMatcher(None, left_tokens, right_tokens).ratio()


def _paper_quality_score(paper: Paper) -> tuple[int, int, int, int, int]:
    return (
        -SOURCE_PRIORITY.get(paper.source, 999),
        len(paper.authors),
        1 if paper.abstract else 0,
        1 if paper.doi else 0,
        paper.citation_count or 0,
    )


def _pick_best_paper(papers: list[Paper]) -> Paper:
    return max(papers, key=_paper_quality_score)


def _merge_papers(papers: list[Paper]) -> Paper:
    best = _pick_best_paper(papers)
    merged = best.model_dump()

    for paper in papers:
        paper_data = paper.model_dump()

        for field in ["doi", "url", "published", "abstract", "pmid", "arxiv_id"]:
            if not merged.get(field) and paper_data.get(field):
                merged[field] = paper_data[field]

        if not merged.get("year") and paper_data.get("year") is not None:
            merged["year"] = paper_data["year"]

        if (merged.get("citation_count") or 0) < (paper_data.get("citation_count") or 0):
            merged["citation_count"] = paper_data["citation_count"]

        if len(merged.get("authors", [])) < len(paper_data.get("authors", [])):
            merged["authors"] = paper_data["authors"]

    return Paper.model_validate(merged)


def _bucket_by_exact_key(
    papers: list[Paper],
    key_fn,
) -> tuple[list[Paper], list[Paper]]:
    grouped: dict[str, list[Paper]] = {}
    remainder: list[Paper] = []

    for paper in papers:
        key = key_fn(paper)
        if key:
            grouped.setdefault(key, []).append(paper)
        else:
            remainder.append(paper)

    deduplicated = [_merge_papers(group) for group in grouped.values()]
    return deduplicated, remainder


def _dedup_by_title_similarity(
    papers: list[Paper],
    threshold: float,
    seed_papers: list[Paper] | None = None,
) -> list[Paper]:
    deduplicated: list[Paper] = list(seed_papers or [])
    normalized_titles: list[str] = [_normalize_title(paper.title) for paper in deduplicated]

    for paper in papers:
        normalized_title = _normalize_title(paper.title)
        matched_index: int | None = None

        for index, seen_title in enumerate(normalized_titles):
            if _title_similarity(normalized_title, seen_title) >= threshold:
                matched_index = index
                break

        if matched_index is None:
            deduplicated.append(paper)
            normalized_titles.append(normalized_title)
            continue

        deduplicated[matched_index] = _merge_papers([deduplicated[matched_index], paper])
        normalized_titles[matched_index] = _normalize_title(deduplicated[matched_index].title)

    return deduplicated


def deduplicate_papers(
    raw_papers: list[Paper | dict],
    title_similarity_threshold: float = 0.95,
) -> DedupResult:
    """DOI, arXiv ID, PMID, 제목 유사도 순서로 중복 논문을 제거한다."""
    validated_papers = [Paper.model_validate(paper) for paper in raw_papers]
    total_raw_papers = len(validated_papers)

    doi_deduped, remaining = _bucket_by_exact_key(
        validated_papers,
        lambda paper: _normalize_doi(paper.doi),
    )
    arxiv_deduped, remaining = _bucket_by_exact_key(remaining, _extract_arxiv_id)
    pmid_deduped, remaining = _bucket_by_exact_key(remaining, _extract_pmid)
    deduplicated_papers = _dedup_by_title_similarity(
        remaining,
        title_similarity_threshold,
        seed_papers=doi_deduped + arxiv_deduped + pmid_deduped,
    )

    return {
        "deduplicated_papers": deduplicated_papers,
        "total_deduplicated": len(deduplicated_papers),
        "duplicates_removed": total_raw_papers - len(deduplicated_papers),
    }


def dedup_papers(
    raw_papers: list[Paper | dict],
    title_similarity_threshold: float = 0.95,
) -> DedupResult:
    """호출부에서 짧은 이름을 선호할 때 사용하는 별칭."""
    return deduplicate_papers(raw_papers, title_similarity_threshold)
