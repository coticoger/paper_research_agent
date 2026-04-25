from pathlib import Path
from langchain_core.tools import tool


WORKSPACE_DIR = Path(__file__).parent.parent / "memory"

#----------------
# 파일 관리 도구
#----------------
@tool
def ls (path : str = "") -> str:
    """워크스페이스 디렉토리의 파일을 나열합니다"""
    target_dir = WORKSPACE_DIR / path

    if not target_dir.exists():
        return f"[Warning] 경로 {path}가 존재하지 않습니다."
    
    items = []
    for item in sorted(target_dir.iterdir()):
        if item.is_dir():
            items.append(item.name)
        else:
            items.append(f'{item.name} is not dir')
    return "\n".join(items) if items else "[Warninig] 파일이 존재하지 않습니다."

@tool
def read_file(path : str, offset : int = 0, limit : int = 2000) -> str:
    """워크스페이스에서 파일 내용을 읽습니다"""
    target_file = WORKSPACE_DIR / path

    # 보완 : 워크스페이스 외부 접근 방지
    try:
        target_file = target_file.resolve()
        if not str(target_file).startswith(str(WORKSPACE_DIR.resolve())):
            return "[Warning] 워크스페이스 외부 접근 불가"
    except Exception as e:
        return f"[Warning] {path} 잘못된 경로입니다."
    
    if not target_file.exists():
        return f"[Warning] {path} 파일이 없습니다."
    
    try:
        content = target_file.read_text(encoding = 'utf-8')
        lines = content.splitlines()
        end_idx = min(offset + limit, len(lines))
        result_lines = [f"{i+1:6d}\t{lines[i][:2000]}" for i in range(offset, end_idx)]
        result = "\n".join(result_lines)
        if len(result) > 12000:
            return result[:12000].rstrip() + "\n... [truncated]"
        return result
    except Exception as e:
        return f"[Warninig] 파일 읽기 실패 - {e}"
    
@tool
def write_file(path : str, content : str) -> str:
    """워크스페이스에 파일을 작성합니다."""
    target_file = WORKSPACE_DIR / path

    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file = target_file.resolve()
        if not str(target_file).startswith(str(WORKSPACE_DIR.resolve())):
            return "[Warning] 워크스페이스 외부 접근 불가"
        
        target_file.write_text(content, encoding='utf-8')
        return f"[Info] {path} 저장됨 ({target_file.stat().st_size()} bytes)"
    except Exception as e:
        return f"[Warninig] 파일 쓰기 실패 - {e}"
