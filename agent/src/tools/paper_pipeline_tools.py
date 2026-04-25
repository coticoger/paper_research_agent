import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

from config import RELEVANCE_LLM_TOP_K, SUBAGENT_MODELS
from schemas.paper import Paper, ScoredPaper, SummarizedPaper
from services.dedup import deduplicate_papers
from tools.research_tools import PUB_MED_KEY, search_arxiv, search_pubmed


_relevance_model = None
_summarizer_model = None
_current_run_dir: Path | None = None


def _get_relevance_model():
    global _relevance_model
    if _relevance_model is None:
        cfg = SUBAGENT_MODELS["relevance-agent"]
        _relevance_model = init_chat_model(model=cfg["model"], temperature=cfg["temperature"])
    return _relevance_model


def _get_summarizer_model():
    global _summarizer_model
    if _summarizer_model is None:
        cfg = SUBAGENT_MODELS["summarizer-agent"]
        _summarizer_model = init_chat_model(model=cfg["model"], temperature=cfg["temperature"])
    return _summarizer_model


WORKSPACE_DIR = Path(__file__).parent.parent / "memory"


def _run_dir_name(run_started_at: float) -> str:
    return datetime.fromtimestamp(run_started_at).strftime("%Y-%m-%d_%H-%M-%S")


def set_run_dir(run_started_at: float) -> Path:
    global _current_run_dir
    _current_run_dir = WORKSPACE_DIR / _run_dir_name(run_started_at)
    _current_run_dir.mkdir(parents=True, exist_ok=True)
    return _current_run_dir


def get_run_dir() -> Path:
    return _current_run_dir if _current_run_dir is not None else WORKSPACE_DIR


def _memory_path(path: str) -> Path:
    base = get_run_dir()
    target = (base / path).resolve()
    if not str(target).startswith(str(WORKSPACE_DIR.resolve())):
        raise ValueError("workspace outside access is not allowed")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _read_jsonl(path: str) -> list[dict[str, Any]]:
    target = _memory_path(path)
    if not target.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: str, rows: list[dict[str, Any]]) -> None:
    target = _memory_path(path)
    content = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    target.write_text(content + ("\n" if content else ""), encoding="utf-8")


def _write_json(path: str, payload: Any) -> None:
    _memory_path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _parse_search_response(response: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(response)
    except json.JSONDecodeError:
        return []
    papers = payload.get("raw_papers", [])
    return papers if isinstance(papers, list) else []


def _topic_query(topic: dict[str, Any]) -> str:
    query = topic.get("query") or topic.get("topic")
    if query:
        return str(query)
    keywords = topic.get("keywords") or []
    return " ".join(str(keyword) for keyword in keywords)


def _topic_name(topic: dict[str, Any]) -> str:
    return str(topic.get("topic") or topic.get("query") or "research topic")


def _paper_key(paper: dict[str, Any]) -> str:
    return str(paper.get("paper_id") or paper.get("doi") or paper.get("title") or "")


@tool
def search_papers_file(
    topics: list[dict[str, Any]],
    output_path: str = "raw_papers.jsonl",
    max_results_per_source: int = 5,
    max_total_results: int = 100,
) -> str:
    """Search PubMed and arXiv for approved topics and save raw papers as JSONL."""
    raw_papers: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for topic in topics:
        query = _topic_query(topic)
        if not query:
            continue

        topic_name = _topic_name(topic)
        for search_tool in [search_pubmed, search_arxiv]:
            response = search_tool.invoke(
                {"query": query, "max_results": max_results_per_source}
            )
            for paper in _parse_search_response(response):
                key = _paper_key(paper)
                if key and key in seen_keys:
                    continue
                if key:
                    seen_keys.add(key)
                paper["matched_topic"] = topic_name
                raw_papers.append(paper)
                if len(raw_papers) >= max_total_results:
                    _write_jsonl(output_path, raw_papers)
                    return (
                        f"[Info] saved {len(raw_papers)} raw papers to {output_path} "
                        f"(capped at {max_total_results})"
                    )

    _write_jsonl(output_path, raw_papers)
    return f"[Info] saved {len(raw_papers)} raw papers to {output_path}"


@tool
def deduplicate_papers_file(
    input_path: str = "raw_papers.jsonl",
    output_path: str = "dedup_papers.jsonl",
    summary_path: str = "dedup_result.json",
) -> str:
    """Read raw paper JSONL, remove duplicates, and save deduplicated papers."""
    raw_papers = _read_jsonl(input_path)
    if not raw_papers:
        return f"[Warning] {input_path} has no papers"

    topic_by_key = {
        _paper_key(paper): paper.get("matched_topic")
        for paper in raw_papers
        if paper.get("matched_topic")
    }
    dedup_result = deduplicate_papers(raw_papers)
    dedup_papers = []
    for paper in dedup_result["deduplicated_papers"]:
        paper_data = paper.model_dump()
        matched_topic = topic_by_key.get(_paper_key(paper_data))
        if matched_topic:
            paper_data["matched_topic"] = matched_topic
        dedup_papers.append(paper_data)

    summary = {
        "total_raw_papers": len(raw_papers),
        "total_deduplicated": dedup_result["total_deduplicated"],
        "duplicates_removed": dedup_result["duplicates_removed"],
    }
    _write_jsonl(output_path, dedup_papers)
    _write_json(summary_path, summary)
    return (
        f"[Info] saved {len(dedup_papers)} deduplicated papers to {output_path}; "
        f"removed {summary['duplicates_removed']} duplicates"
    )


def _keyword_score(paper: dict[str, Any], topics: list[dict[str, Any]]) -> tuple[float, str]:
    text = " ".join(
        str(paper.get(field) or "")
        for field in ["title", "abstract"]
    ).lower()
    best_score = 0.0
    best_topic = str(paper.get("matched_topic") or "")

    for topic in topics:
        keywords = [str(keyword).lower() for keyword in topic.get("keywords", [])]
        keywords.extend(str(topic.get("topic") or "").lower().split())
        keywords = [keyword for keyword in keywords if len(keyword) > 2]
        if not keywords:
            continue
        hits = sum(1 for keyword in keywords if keyword in text)
        score = min(1.0, hits / max(3, len(set(keywords))))
        if score > best_score:
            best_score = score
            best_topic = _topic_name(topic)

    return best_score, best_topic or "research topic"


def _llm_rescore_paper(paper: dict[str, Any], topics: list[dict[str, Any]]) -> tuple[float, str]:
    topic_list = ", ".join(_topic_name(t) for t in topics)
    title = str(paper.get("title") or "")
    abstract = str(paper.get("abstract") or "")[:1000]
    prompt = (
        f"Rate the relevance of this academic paper to the given research topics.\n"
        f"Topics: {topic_list}\n\n"
        f"Title: {title}\nAbstract: {abstract}\n\n"
        'Return JSON only: {"relevance_score": <float 0.0-1.0>, "reason": "<brief reason>"}'
    )
    try:
        model = _get_relevance_model()
        response = model.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        payload = json.loads(content)
        score = min(1.0, max(0.0, float(payload.get("relevance_score", 0.0))))
        reason = str(payload.get("reason", "LLM relevance evaluation"))
        return score, reason
    except Exception:
        return float(paper.get("relevance_score", 0.0)), "keyword score (LLM failed)"


@tool
def score_papers_file(
    topics: list[dict[str, Any]],
    input_path: str = "dedup_papers.jsonl",
    output_path: str = "scored_papers.jsonl",
) -> str:
    """Score papers with keyword filter (all) then LLM re-rank (top 30) and save JSONL."""
    papers = _read_jsonl(input_path)
    if not papers:
        return f"[Warning] {input_path} has no papers"

    # 1차: keyword score 전체 필터링
    for paper in papers:
        score, matched_topic = _keyword_score(paper, topics)
        paper["relevance_score"] = round(score, 3)
        paper["relevance_reason"] = "keyword overlap"
        paper["matched_topic"] = matched_topic

    papers.sort(key=lambda p: float(p.get("relevance_score") or 0.0), reverse=True)

    # 2차: 상위 RELEVANCE_LLM_TOP_K개만 LLM으로 재평가
    llm_rescored = 0
    for paper in papers[:RELEVANCE_LLM_TOP_K]:
        score, reason = _llm_rescore_paper(paper, topics)
        paper["relevance_score"] = round(score, 3)
        paper["relevance_reason"] = reason
        llm_rescored += 1

    papers.sort(key=lambda p: float(p.get("relevance_score") or 0.0), reverse=True)

    scored_papers: list[dict[str, Any]] = []
    for paper in papers:
        matched_topic = paper.get("matched_topic", "research topic")
        scored = ScoredPaper.model_validate(paper).model_dump()
        scored["matched_topic"] = matched_topic
        scored_papers.append(scored)

    _write_jsonl(output_path, scored_papers)
    return (
        f"[Info] saved {len(scored_papers)} scored papers to {output_path} "
        f"(keyword scored all, LLM re-scored top {llm_rescored})"
    )


def _truncate(value: str, max_length: int = 4000) -> str:
    value = " ".join(value.split())
    if len(value) <= max_length:
        return value
    return value[:max_length].rstrip() + "..."


def _first_sentences(value: str | None, max_sentences: int = 3) -> str:
    if not value:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", value.strip())
    selected = " ".join(sentence for sentence in sentences[:max_sentences] if sentence)
    return selected or value[:600]


def _extract_pmid(paper: dict[str, Any]) -> str | None:
    if paper.get("pmid"):
        return str(paper["pmid"])
    paper_id = str(paper.get("paper_id") or "")
    if paper_id.startswith("pubmed_"):
        return paper_id.removeprefix("pubmed_")
    url = str(paper.get("url") or "")
    match = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", url)
    return match.group(1) if match else None


def _resolve_pmcid(pmid: str) -> str | None:
    params = {"ids": pmid, "format": "json"}
    if PUB_MED_KEY:
        params["api_key"] = PUB_MED_KEY
    try:
        response = requests.get(
            "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        records = response.json().get("records", [])
    except Exception:
        return None
    if not records:
        return None
    return records[0].get("pmcid")


def _node_text(node) -> str:
    if node is None:
        return ""
    return _truncate(" ".join(node.itertext()))


def _section_kind(title: str) -> str | None:
    normalized = title.lower()
    if any(keyword in normalized for keyword in ["introduction", "background"]):
        return "introduction"
    if any(keyword in normalized for keyword in ["method", "materials", "experimental", "implementation"]):
        return "method"
    if "discussion" in normalized:
        return "discussion"
    return None


def _fetch_pmc_sections(pmid: str | None) -> dict[str, str]:
    if not pmid:
        return {}

    pmcid = _resolve_pmcid(pmid)
    if not pmcid:
        return {}

    params = {
        "db": "pmc",
        "id": pmcid.removeprefix("PMC"),
        "retmode": "xml",
    }
    if PUB_MED_KEY:
        params["api_key"] = PUB_MED_KEY

    try:
        response = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except Exception:
        return {}

    sections: dict[str, str] = {}
    abstract = root.find(".//abstract")
    if abstract is not None:
        sections["abstract"] = _node_text(abstract)

    for sec in root.findall(".//body//sec"):
        title = _node_text(sec.find("title"))
        kind = _section_kind(title)
        if not kind or kind in sections:
            continue
        paragraphs = [_node_text(paragraph) for paragraph in sec.findall(".//p")]
        text = _truncate(" ".join(paragraph for paragraph in paragraphs if paragraph))
        if text:
            sections[kind] = text
    return sections


def _llm_summarize_paper(paper: dict[str, Any], sections: dict[str, str]) -> str:
    introduction = sections.get("introduction", "")[:2000]
    method = sections.get("method", "")[:2000]
    discussion = sections.get("discussion", "")[:2000]

    # introduction/method/discussion이 없으면 abstract로 fallback
    if not any([introduction, method, discussion]):
        fallback = sections.get("abstract") or str(paper.get("abstract") or "")
        if not fallback:
            return "No content available for summarization."
        introduction = fallback[:2000]

    parts = []
    if introduction:
        parts.append(f"Introduction:\n{introduction}")
    if method:
        parts.append(f"Methods:\n{method}")
    if discussion:
        parts.append(f"Discussion:\n{discussion}")

    prompt = (
        "Summarize this academic paper in 3-5 sentences.\n"
        "Focus on: research objective, methodology, and key findings/contributions.\n"
        "Use only the provided sections. Do not hallucinate.\n\n"
        f"Title: {paper.get('title', '')}\n\n"
        + "\n\n".join(parts)
        + "\n\nSummary:"
    )
    try:
        model = _get_summarizer_model()
        response = model.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        return content.strip()
    except Exception:
        # fallback: 섹션 텍스트 앞부분만 반환
        return _first_sentences(introduction or method or discussion, 3)


@tool
def summarize_papers_file(
    input_path: str = "scored_papers.jsonl",
    output_path: str = "summaries.jsonl",
    relevance_threshold: float = 0.7,
    max_papers: int = 20,
) -> str:
    """Summarize top papers using LLM with introduction/method/discussion sections."""
    papers = _read_jsonl(input_path)
    if not papers:
        return f"[Warning] {input_path} has no papers"

    candidates = [
        paper for paper in papers
        if float(paper.get("relevance_score") or 0.0) >= relevance_threshold
    ]
    candidates.sort(key=lambda p: float(p.get("relevance_score") or 0.0), reverse=True)

    summarized_papers: list[dict[str, Any]] = []
    for paper in candidates[:max_papers]:
        sections = _fetch_pmc_sections(_extract_pmid(paper))
        # abstract는 fallback 용도로만 sections에 보관, 요약엔 intro/method/discussion만 우선
        if "abstract" not in sections and paper.get("abstract"):
            sections["abstract"] = str(paper["abstract"])

        paper["summary"] = _llm_summarize_paper(paper, sections)
        summarized = SummarizedPaper.model_validate(paper).model_dump()
        if paper.get("matched_topic"):
            summarized["matched_topic"] = paper["matched_topic"]
        summarized["summary_source_sections"] = sorted(
            k for k in sections if k in {"introduction", "method", "discussion"}
        )
        summarized["section_availability"] = {
            "introduction": bool(sections.get("introduction")),
            "method": bool(sections.get("method")),
            "discussion": bool(sections.get("discussion")),
        }
        summarized_papers.append(summarized)

    _write_jsonl(output_path, summarized_papers)
    return (
        f"[Info] saved {len(summarized_papers)} LLM summaries to {output_path} "
        f"from top {max_papers} papers with relevance_score >= {relevance_threshold}"
    )


@tool
def build_final_results_file(
    input_path: str = "summaries.jsonl",
    output_path: str = "final_results.json",
) -> str:
    """Group summarized papers by matched topic and save final results JSON."""
    summarized_papers = _read_jsonl(input_path)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for paper in summarized_papers:
        topic = str(paper.get("matched_topic") or "Selected papers")
        grouped.setdefault(topic, []).append(paper)

    final_results = [
        {
            "topic": topic,
            "summary": "\n\n".join(
                f"- {paper.get('title')}: {paper.get('summary')}"
                for paper in papers
            ),
            "papers": papers,
            "tags": [topic],
            "status": "ready",
        }
        for topic, papers in grouped.items()
    ]
    _write_json(output_path, final_results)
    return f"[Info] saved {len(final_results)} final result groups to {output_path}"
