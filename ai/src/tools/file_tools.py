import json
from pathlib import Path
from langchain_core.tools import tool

WORKSPACE_DIR = Path(__file__).parent.parent / "memory"

@tool
def ls(path : str = ".") -> str:
    """워크스페이스 디렉토리의 파일을 나열"""
    target_dir = WORKSPACE_DIR / path

    if not target_dir.exists():
        return f"[Warning] 경고 {path}가 존재하지 않습니다."
    
    items = []
    for item in sorted(target_dir.iterdir()):
        if item.is_dir():
            items.append(f"{item.name}/")
        else:
            size = item.stat().st_size
            items.append(f"{item.name} ({size} bytes)")
        
    return "\n".join(items) if items else "[Warninig] 파일이 존재하지 않습니다"

@tool
def read_file(path : str, offset : int = 0, limit : int = 2000):
    """워크스페이스에서 파일 내용을 읽습니다."""
    target_file = WORKSPACE_DIR / path

    try:
        target_file = target_file.resolve()
        if not str(target_file).startswith(str(WORKSPACE_DIR.resolve())):
            return "[ERROR] 워크스페이스 외부 접근 불가"
    except Exception as e:
        return f"[ERROR] 잘못된 경로 {path}"
    
    if not target_file.exists():
        return f"[ERROR] {path} 파일 없음"

    try:
        content = target_file.read_text(encoding='utf-8')
        lines = content.splitlines()
        end_idx = min(offset + limit, len(lines))
        result_lines = [f"{i+1:6d}\t{lines[i][:2000]}" for i in range(offset,end_idx)]
        return "\n".join(result_lines)
    except Exception as e:
        return f"[ERROR] 파일 읽기 실패 - {e}"
    
@tool
def write_file(path : str, content : str) -> str:
    """워크스페이스에 파일을 작성합니다"""
    target_file = WORKSPACE_DIR / path

    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file = target_file.resolve()
        if not str(target_file).startswith(str(WORKSPACE_DIR.resolve())):
            return "[ERROR] 워크스페이스 외부 접근 불가"
        
        normalzied_content = content
        
        if target_file.suffix.lower() == ".json":
            try:
                parsed = json.loads(content)
                normalzied_content = json.dumps(
                    parsed,
                    ensure_ascii=False,
                    indent=2
                )
            except Exception as e:
                print(f"[ERROR] {e}")
                pass

        target_file.write_text(normalzied_content, encoding="utf-8")
        return f" ✅ {path} 저장됨 ({target_file.stat().st_size} bytes)"
    except Exception as e:
        return f"[ERROR] 파일 쓰기 실패 - {e}"

print("[INFO] file tools 정의 완료 ✅")