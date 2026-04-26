import json
import re
from io import BytesIO
from pathlib import Path

import requests
from langchain_core.tools import tool
from pypdf import PdfReader


WORKSPACE_DIR = Path(__file__).parent.parent / "memory"
SECTION_HEADING_PATTERNS = [
    "abstract",
    "introduction",
    "background",
    "method",
    "methods",
    "approach",
    "experiment",
    "experiments",
    "results",
    "discussion",
    "conclusion",
    "conclusions",
    "limitation",
    "limitations",
    "future work",
]


def _resolve_workspace_path(path: str) -> Path:
    target_path = (WORKSPACE_DIR / path).resolve()
    workspace_root = WORKSPACE_DIR.resolve()
    if not str(target_path).startswith(str(workspace_root)):
        raise ValueError("워크스페이스 외부 접근 불가")
    return target_path


def _load_pdf_reader(path: str) -> tuple[PdfReader, int]:
    target_file = _resolve_workspace_path(path)
    if not target_file.exists():
        raise FileNotFoundError(f"{path} 파일 없음")

    reader = PdfReader(BytesIO(target_file.read_bytes()))
    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("PDF 페이지가 없습니다.")
    return reader, total_pages


def _extract_page_text(reader: PdfReader, page_number: int) -> str:
    return (reader.pages[page_number - 1].extract_text() or "").strip()


def _extract_page_range(reader: PdfReader, start_page: int, end_page: int) -> list[dict]:
    chunks = []
    for page_number in range(start_page, end_page + 1):
        text = _extract_page_text(reader, page_number)
        if text:
            chunks.append({"page": page_number, "text": text})
    return chunks


def _format_pages(pages: list[dict]) -> str:
    return "\n\n".join(f"[Page {item['page']}]\n{item['text']}" for item in pages).strip()


def _trim_text(text: str, max_chars: int) -> tuple[str, bool]:
    truncated = len(text) > max_chars
    result = text[:max_chars]
    if truncated:
        result = result.rstrip() + "\n\n[TRUNCATED]"
    return result, truncated


def _find_heading_matches(reader: PdfReader, total_pages: int) -> list[dict]:
    matches = []
    for page_number in range(1, total_pages + 1):
        text = _extract_page_text(reader, page_number)
        if not text:
            continue

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[:80]:
            normalized = re.sub(r"^\d+(\.\d+)*\s*", "", line.lower()).strip()
            normalized = re.sub(r"[^a-z\s]", "", normalized)
            normalized = re.sub(r"\s+", " ", normalized)

            for pattern in SECTION_HEADING_PATTERNS:
                if normalized == pattern or normalized.startswith(pattern + " "):
                    matches.append(
                        {
                            "page": page_number,
                            "heading": line,
                            "normalized_heading": pattern,
                        }
                    )
                    break
    return matches


@tool
def get_pdf_metadata(path: str) -> str:
    """PDF 메타데이터와 전체 페이지 수를 확인합니다."""
    try:
        reader, total_pages = _load_pdf_reader(path)
        raw_metadata = reader.metadata or {}
        metadata = {}
        for key, value in raw_metadata.items():
            metadata[str(key)] = str(value)

        return json.dumps(
            {
                "status": "ok",
                "path": path,
                "total_pages": total_pages,
                "metadata": metadata,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return f"[ERROR] PDF 메타데이터 확인 실패 - {e}"


@tool
def download_pdf(url: str, path: str) -> str:
    """PDF URL을 다운로드해서 워크스페이스에 저장합니다."""
    try:
        target_file = _resolve_workspace_path(path)
        target_file.parent.mkdir(parents=True, exist_ok=True)

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        if "pdf" not in content_type and not url.lower().endswith(".pdf"):
            return f"[ERROR] PDF 응답이 아닙니다: content-type={content_type or 'unknown'}"

        target_file.write_bytes(response.content)

        return json.dumps(
            {
                "status": "ok",
                "path": path,
                "bytes": target_file.stat().st_size,
                "source_url": url,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return f"[ERROR] PDF 다운로드 실패 - {e}"


@tool
def extract_pdf_text(
    path: str,
    start_page: int = 1,
    end_page: int | None = None,
    max_chars: int = 20000,
) -> str:
    """워크스페이스의 PDF에서 텍스트를 추출합니다."""
    try:
        reader, total_pages = _load_pdf_reader(path)
        if start_page < 1:
            return "[ERROR] start_page는 1 이상이어야 합니다."

        resolved_end_page = end_page or total_pages
        if resolved_end_page < start_page:
            return "[ERROR] end_page는 start_page보다 크거나 같아야 합니다."

        end_index = min(resolved_end_page, total_pages)
        pages = _extract_page_range(reader, start_page, end_index)
        full_text = _format_pages(pages)

        if not full_text:
            return json.dumps(
                {
                    "status": "ok",
                    "path": path,
                    "total_pages": total_pages,
                    "start_page": start_page,
                    "end_page": end_index,
                    "text": "",
                    "message": "추출 가능한 텍스트가 없습니다.",
                },
                ensure_ascii=False,
                indent=2,
            )

        text_result, truncated = _trim_text(full_text, max_chars)

        return json.dumps(
            {
                "status": "ok",
                "path": path,
                "total_pages": total_pages,
                "start_page": start_page,
                "end_page": end_index,
                "truncated": truncated,
                "text": text_result,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return f"[ERROR] PDF 텍스트 추출 실패 - {e}"


@tool
def find_pdf_section_headings(path: str) -> str:
    """PDF에서 주요 section heading 후보를 탐색합니다."""
    try:
        reader, total_pages = _load_pdf_reader(path)
        matches = _find_heading_matches(reader, total_pages)
        return json.dumps(
            {
                "status": "ok",
                "path": path,
                "total_pages": total_pages,
                "section_headings": matches,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return f"[ERROR] section heading 탐색 실패 - {e}"


@tool
def extract_pdf_key_sections(
    path: str,
    front_pages: int = 3,
    back_pages: int = 3,
    middle_pages: int = 2,
    max_chars: int = 30000,
) -> str:
    """
    논문 핵심 구간을 우선 추출합니다.
    1. 전체 페이지 수 확인
    2. 앞 2~3페이지 추출
    3. 마지막 2~3페이지 추출
    4. section heading 탐색
    5. 필요하면 중간 일부 추가 추출
    """
    try:
        reader, total_pages = _load_pdf_reader(path)

        front_end = min(max(front_pages, 1), total_pages)
        back_start = max(1, total_pages - max(back_pages, 1) + 1)

        front_chunks = _extract_page_range(reader, 1, front_end)
        back_chunks = _extract_page_range(reader, back_start, total_pages)
        heading_matches = _find_heading_matches(reader, total_pages)

        selected_pages = {item["page"] for item in front_chunks}
        selected_pages.update(item["page"] for item in back_chunks)

        heading_priority = {"abstract", "introduction", "discussion", "conclusion", "conclusions", "limitation", "limitations"}
        heading_chunks = []
        for match in heading_matches:
            if match["normalized_heading"] not in heading_priority:
                continue
            page = match["page"]
            if page in selected_pages:
                continue
            text = _extract_page_text(reader, page)
            if text:
                heading_chunks.append({"page": page, "text": text, "heading": match["heading"]})
                selected_pages.add(page)

        middle_chunks = []
        if total_pages > 6 and len(heading_chunks) < 2:
            middle_start = max(1, (total_pages // 2) - (max(middle_pages, 1) // 2))
            middle_end = min(total_pages, middle_start + max(middle_pages, 1) - 1)
            for item in _extract_page_range(reader, middle_start, middle_end):
                if item["page"] not in selected_pages:
                    middle_chunks.append(item)
                    selected_pages.add(item["page"])

        payload = {
            "status": "ok",
            "path": path,
            "total_pages": total_pages,
            "metadata": {str(k): str(v) for k, v in (reader.metadata or {}).items()},
            "front_section": {
                "page_range": [1, front_end],
                "text": _format_pages(front_chunks),
            },
            "back_section": {
                "page_range": [back_start, total_pages],
                "text": _format_pages(back_chunks),
            },
            "section_headings": heading_matches,
            "heading_sections": heading_chunks,
            "middle_section": {
                "pages": [item["page"] for item in middle_chunks],
                "text": _format_pages(middle_chunks),
            },
        }

        text_blob = json.dumps(payload, ensure_ascii=False, indent=2)
        text_blob, truncated = _trim_text(text_blob, max_chars)

        if truncated:
            payload["truncated"] = True
            payload["note"] = "응답 길이 제한으로 일부 내용이 잘렸습니다."
            text_blob = json.dumps(payload, ensure_ascii=False, indent=2)
            text_blob, _ = _trim_text(text_blob, max_chars)

        return text_blob
    except Exception as e:
        return f"[ERROR] 핵심 PDF 구간 추출 실패 - {e}"
