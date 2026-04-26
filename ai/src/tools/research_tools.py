import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from typing_extensions import Annotated, Optional
from langchain_core.tools import tool


load_dotenv(Path(__file__).resolve().parents[2] / ".env")
PUB_MED_KEY = os.getenv("PUB_MED_KEY")


WORKSPACE_DIR = Path(__file__).parent.parent / "memory"

# Research tool : PubMed / arXiv 

def _safe_text(value: Optional[str], default: str = "") -> str:
    """빈 값과 앞뒤 공백을 정리한 문자열을 반환."""
    if value is None:
        return default
    cleaned = " ".join(value.split())
    return cleaned if cleaned else default


def _truncate_text(text: str, max_length: int = 1000) -> str:
    """초록 길이를 제한해 tool 출력이 과도하게 커지는 것을 방지."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def _json_response(source: str, query: str, papers: list[dict], message: Optional[str] = None) -> str:
    """후속 단계에서 재사용하기 쉬운 일관된 JSON 문자열 응답."""
    payload = {
        "source": source,
        "query": query,
        "raw_papers": papers,
        "total_raw_papers": len(papers),
    }
    if message:
        payload["message"] = message
    return json.dumps(payload, ensure_ascii=False, indent=2)

def _batch_citation_counts(paper_ids: list[str]) -> dict[str, Optional[int]]:
    """Semantic Scholar 배치 API로 여러 논문의 인용 수를 한 번에 조회."""
    if not paper_ids:
        return {}
    try:
        resp = requests.post(
            "https://api.semanticscholar.org/graph/v1/paper/batch",
            params={"fields": "citationCount"},
            json={"ids": paper_ids},
            timeout=10,
        )
        if resp.status_code == 200:
            return {
                pid: (p.get("citationCount") if p else None)
                for pid, p in zip(paper_ids, resp.json())
            }
    except Exception:
        pass
    return {pid: None for pid in paper_ids}


@tool
def search_pubmed(query: str, max_results: int = 10) -> str:
    """
        PubMed API를 사용하여 논문 검색을 수행합니다..
        paper_id, title, authors, year, published, url, source, abstract 정보가 포함됩니다.

        Args:
            query : 검색할 쿼리
            num_reuslts : 반환할 결과 수 (기본값 : 10)
    """

    try:
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
        }
        if PUB_MED_KEY:
            search_params["api_key"] = PUB_MED_KEY

        search = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params=search_params,
            timeout=10,
        )
        search.raise_for_status()
        ids = search.json()["esearchresult"]["idlist"]
        if not ids:
            return _json_response("pubmed", query, [], f"'{query}' 검색 결과가 없습니다.")

        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "rettype": "abstract",
            "retmode": "xml",
        }
        if PUB_MED_KEY:
            fetch_params["api_key"] = PUB_MED_KEY

        fetch = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params=fetch_params,
            timeout=15,
        )
        fetch.raise_for_status()
        root = ET.fromstring(fetch.content)

        pmid_keys, papers = [], []
        for article in root.findall(".//PubmedArticle"):
            pmid = _safe_text(article.findtext(".//PMID"), "N/A")
            pmid_key = f"PMID:{pmid}"
            pmid_keys.append(pmid_key)

            title = _safe_text(article.findtext(".//ArticleTitle"), "N/A")

            abstract_els = article.findall(".//AbstractText")
            if abstract_els:
                parts = []
                for el in abstract_els:
                    label = el.get("Label") or el.get("NlmCategory", "")
                    text = _safe_text("".join(el.itertext()))
                    if text:
                        parts.append(f"{label}: {text}" if label else text)
                abstract = " ".join(parts) if parts else "초록 없음"
            else:
                abstract = "초록 없음"

            authors = []
            for author in article.findall(".//Author"):
                last_name = _safe_text(author.findtext("LastName"))
                fore_name = _safe_text(author.findtext("ForeName"))
                collective_name = _safe_text(author.findtext("CollectiveName"))
                name = collective_name or " ".join(part for part in [fore_name, last_name] if part)
                if name:
                    authors.append(name)

            pub_date_node = article.find(".//PubDate")
            year = _safe_text(article.findtext(".//PubDate/Year"))
            month = _safe_text(pub_date_node.findtext("Month") if pub_date_node is not None else "")
            day = _safe_text(pub_date_node.findtext("Day") if pub_date_node is not None else "")
            medline_date = _safe_text(pub_date_node.findtext("MedlineDate") if pub_date_node is not None else "")
            pub_date = "-".join(part for part in [year, month, day] if part) or medline_date or "N/A"

            doi = ""
            for article_id in article.findall(".//ArticleId"):
                if article_id.attrib.get("IdType") == "doi":
                    doi = _safe_text("".join(article_id.itertext()))
                    if doi:
                        break

            papers.append(
                {
                    "paper_id": f"pubmed_{pmid}",
                    "title": title,
                    "authors": authors,
                    "year": int(year) if year.isdigit() else None,
                    "published": pub_date,
                    "doi": doi or None,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid != "N/A" else None,
                    "source": "pubmed",
                    "abstract": _truncate_text(abstract),
                }
            )

        citations = _batch_citation_counts(pmid_keys)

        for index, paper in enumerate(papers):
            paper["citation_count"] = citations.get(pmid_keys[index])

        return _json_response("pubmed", query, papers)

    except Exception as e:
        return f"[PubMed] 검색 실패: {e}"


@tool
def search_arxiv(query: str, max_results: int = 10) -> str:
    """
        Arxiv에서 논문 검색을 수행합니다..
        paper_id, title, authors, year, published, url, source, abstract 정보가 포함됩니다.

        Args:
            query : 검색할 쿼리
            num_reuslts : 반환할 결과 수 (기본값 : 10)
    """
    try:
        resp = requests.get(
            "http://export.arxiv.org/api/query",
            params={"search_query": f"all:{query}", "max_results": max_results, "sortBy": "relevance"},
            timeout=15,
        )
        resp.raise_for_status()

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = ET.fromstring(resp.content).findall("atom:entry", ns)
        if not entries:
            return _json_response("arxiv", query, [], f"'{query}' 검색 결과가 없습니다.")

        arxiv_ids, papers = [], []
        for entry in entries:
            title = _safe_text(entry.findtext("atom:title", "N/A", ns), "N/A")
            abstract = _safe_text(entry.findtext("atom:summary", "초록 없음", ns), "초록 없음")
            published = _safe_text(entry.findtext("atom:published", "N/A", ns), "N/A")
            id_url = entry.findtext("atom:id", "", ns) or ""
            arxiv_id = id_url.split("/abs/")[-1].split("v")[0] if "/abs/" in id_url else "N/A"

            arxiv_ids.append(f"ARXIV:{arxiv_id}")

            authors = [
                _safe_text(author.findtext("atom:name", "", ns))
                for author in entry.findall("atom:author", ns)
                if _safe_text(author.findtext("atom:name", "", ns))
            ]

            doi = None
            for link in entry.findall("atom:link", ns):
                if link.attrib.get("title", "").lower() == "doi":
                    href = _safe_text(link.attrib.get("href"))
                    doi = href.removeprefix("https://doi.org/") if href else None
                    break

            papers.append(
                {
                    "paper_id": f"arxiv_{arxiv_id}",
                    "title": title,
                    "authors": authors,
                    "year": int(published[:4]) if published[:4].isdigit() else None,
                    "published": published[:10] if len(published) >= 10 else published,
                    "abstract": _truncate_text(abstract),
                    "doi": doi,
                    "url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id != "N/A" else id_url or None,
                    "source": "arxiv",
                }
            )

        citations = _batch_citation_counts(arxiv_ids)

        for index, paper in enumerate(papers):
            paper["citation_count"] = citations.get(arxiv_ids[index])

        return _json_response("arxiv", query, papers)

    except Exception as e:
        return f"[arXiv] 검색 실패: {e}"
