"""專案根目錄單檔的 ai-dev managed block 工具。"""

from pathlib import Path


def get_block_markers(block_id: str) -> tuple[str, str]:
    """回傳指定 block 的起訖 marker。"""
    return (
        f"<!-- >>> ai-dev:{block_id} -->",
        f"<!-- <<< ai-dev:{block_id} -->",
    )


def _find_block(lines: list[str], start_marker: str, end_marker: str) -> tuple[int | None, int | None]:
    """尋找 managed block 的起止行號。"""
    start_idx = None
    end_idx = None

    for index, line in enumerate(lines):
        stripped = line.rstrip("\n\r")
        if stripped == start_marker:
            start_idx = index
        elif stripped == end_marker and start_idx is not None:
            end_idx = index
            break

    return start_idx, end_idx


def render_managed_block(block_id: str, content: str) -> str:
    """渲染完整 managed block 內容。"""
    start_marker, end_marker = get_block_markers(block_id)
    normalized_content = content.rstrip("\n")
    return f"{start_marker}\n{normalized_content}\n{end_marker}\n"


def read_managed_block_text(text: str, block_id: str) -> str | None:
    """從既有文字內容中讀取 managed block。"""
    start_marker, end_marker = get_block_markers(block_id)
    lines = text.splitlines(keepends=True)
    start_idx, end_idx = _find_block(lines, start_marker, end_marker)

    if start_idx is None or end_idx is None:
        return None

    return "".join(lines[start_idx + 1 : end_idx]).rstrip("\n")


def read_managed_block(path: Path, block_id: str) -> str | None:
    """讀取既有 managed block 的內容。"""
    if not path.exists():
        return None

    return read_managed_block_text(path.read_text(encoding="utf-8"), block_id)


def upsert_managed_block(path: Path, block_id: str, content: str) -> None:
    """建立或更新 managed block，保留區塊外內容。"""
    start_marker, end_marker = get_block_markers(block_id)
    block_text = render_managed_block(block_id, content)

    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = existing.splitlines(keepends=True)
    start_idx, end_idx = _find_block(lines, start_marker, end_marker)

    if start_idx is not None and end_idx is not None:
        del lines[start_idx : end_idx + 1]
        if start_idx > 0 and start_idx - 1 < len(lines) and lines[start_idx - 1].strip() == "":
            del lines[start_idx - 1]
        base = "".join(lines).lstrip("\n")
    else:
        base = existing.lstrip("\n")

    if base:
        result = f"{block_text}\n{base}"
    else:
        result = block_text

    if result and not result.endswith("\n"):
        result += "\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result, encoding="utf-8")


def remove_managed_block(path: Path, block_id: str) -> bool:
    """移除 managed block。"""
    if not path.exists():
        return False

    start_marker, end_marker = get_block_markers(block_id)
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    start_idx, end_idx = _find_block(lines, start_marker, end_marker)

    if start_idx is None or end_idx is None:
        return False

    del lines[start_idx : end_idx + 1]
    if start_idx > 0 and start_idx - 1 < len(lines) and lines[start_idx - 1].strip() == "":
        del lines[start_idx - 1]
    elif start_idx == 0 and lines and lines[0].strip() == "":
        del lines[0]

    result = "".join(lines)
    if result and not result.endswith("\n"):
        result += "\n"

    path.write_text(result, encoding="utf-8")
    return True
