import json
import re
from io import BytesIO
from pathlib import Path

from langchain_core.tools import tool
from pypdf import PdfReader


WORKSPACE_DIR = Path(__file__).parent.parent / "memory"


def _resolve_workspace_path(path: str) -> Path:
    target_path = (WORKSPACE_DIR / path).resolve()
    workspace_root = WORKSPACE_DIR.resolve()
    if not str(target_path).startswith(str(workspace_root)):
        raise ValueError("워크스페이스 외부 접근 불가")
    return target_path


def _load_pdf(path: str) -> tuple[PdfReader, int]:
    target_file = _resolve_workspace_path(path)
    if not target_file.exists():
        raise FileNotFoundError(f"{path} 파일 없음")

    reader = PdfReader(BytesIO(target_file.read_bytes()))
    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("PDF 페이지가 없습니다.")
    return reader, total_pages


def _page_text(reader: PdfReader, page_number: int) -> str:
    return (reader.pages[page_number - 1].extract_text() or "").strip()


def _clean_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _trim_text(text: str, max_chars: int) -> tuple[str, bool]:
    truncated = len(text) > max_chars
    trimmed = text[:max_chars]
    if truncated:
        trimmed = trimmed.rstrip() + "\n\n[TRUNCATED]"
    return trimmed, truncated


@tool
def extract_metadata_tool(path: str) -> str:
    """PDF 메타데이터와 전체 페이지 수를 추출합니다."""
    try:
        reader, total_pages = _load_pdf(path)
        metadata = {str(key): str(value) for key, value in (reader.metadata or {}).items()}

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
        return f"[ERROR] PDF 메타데이터 추출 실패 - {e}"


@tool
def extract_text_tool(
    path: str,
    start_page: int = 1,
    end_page: int | None = None,
    max_chars: int = 20000,
) -> str:
    """PDF에서 지정한 페이지 범위의 텍스트를 추출합니다."""
    try:
        reader, total_pages = _load_pdf(path)

        if start_page < 1:
            return "[ERROR] start_page는 1 이상이어야 합니다."

        resolved_end_page = end_page or total_pages
        if resolved_end_page < start_page:
            return "[ERROR] end_page는 start_page보다 크거나 같아야 합니다."

        resolved_end_page = min(resolved_end_page, total_pages)
        pages = []
        for page_number in range(start_page, resolved_end_page + 1):
            text = _page_text(reader, page_number)
            if text:
                pages.append({"page": page_number, "text": text})

        full_text = "\n\n".join(
            f"[Page {item['page']}]\n{item['text']}" for item in pages
        ).strip()
        text_result, truncated = _trim_text(full_text, max_chars)

        return json.dumps(
            {
                "status": "ok",
                "path": path,
                "total_pages": total_pages,
                "start_page": start_page,
                "end_page": resolved_end_page,
                "truncated": truncated,
                "text": text_result,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return f"[ERROR] PDF 텍스트 추출 실패 - {e}"


@tool
def extract_blocks_tool(
    path: str,
    pages: int = 3,
    max_lines_per_block: int = 12,
    max_chars: int = 20000,
) -> str:
    """PDF의 앞부분에서 문단/헤딩 단위 블록 후보를 추출합니다."""
    try:
        reader, total_pages = _load_pdf(path)
        target_pages = min(max(pages, 1), total_pages)
        blocks = []

        for page_number in range(1, target_pages + 1):
            text = _page_text(reader, page_number)
            if not text:
                continue

            lines = _clean_lines(text)
            current_block: list[str] = []

            for line in lines:
                current_block.append(line)
                heading_like = len(line) <= 120 and line == line.upper()
                reached_limit = len(current_block) >= max_lines_per_block
                paragraph_end = line.endswith(".")

                if heading_like or reached_limit or paragraph_end:
                    block_text = "\n".join(current_block).strip()
                    if block_text:
                        blocks.append({"page": page_number, "text": block_text})
                    current_block = []

            if current_block:
                block_text = "\n".join(current_block).strip()
                if block_text:
                    blocks.append({"page": page_number, "text": block_text})

        payload = {
            "status": "ok",
            "path": path,
            "inspected_pages": target_pages,
            "blocks": blocks,
        }
        text_result, truncated = _trim_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            max_chars,
        )
        if truncated:
            return text_result
        return text_result
    except Exception as e:
        return f"[ERROR] 블록 추출 실패 - {e}"


@tool
def extract_figure_tables_tools(path: str, pages: int = 8) -> str:
    """PDF 앞부분에서 figure/table 캡션 후보를 추출합니다."""
    try:
        reader, total_pages = _load_pdf(path)
        target_pages = min(max(pages, 1), total_pages)
        pattern = re.compile(r"^(figure|fig\.?|table)\s*\d+", re.IGNORECASE)
        results = []

        for page_number in range(1, target_pages + 1):
            text = _page_text(reader, page_number)
            if not text:
                continue

            for line in _clean_lines(text):
                if pattern.match(line):
                    results.append({"page": page_number, "caption": line})

        return json.dumps(
            {
                "status": "ok",
                "path": path,
                "inspected_pages": target_pages,
                "figure_table_candidates": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return f"[ERROR] Figure/Table 추출 실패 - {e}"
