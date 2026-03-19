"""專案根目錄單檔的 ai-dev managed block 工具。"""

from pathlib import Path


def get_block_markers(
    block_id: str, *, open_label: str = "", close_label: str = ""
) -> tuple[str, str]:
    """回傳指定 block 的起訖 marker。

    可選的 label 參數讓 marker 自帶語義，使 AI agent 讀取時
    不將 marker 視為純粹的結構噪音，而是行為指引的一部分。
    """
    if open_label:
        start = f"<!-- >>> ai-dev:{block_id} | {open_label} -->"
    else:
        start = f"<!-- >>> ai-dev:{block_id} -->"
    if close_label:
        end = f"<!-- <<< ai-dev:{block_id} | {close_label} -->"
    else:
        end = f"<!-- <<< ai-dev:{block_id} -->"
    return (start, end)


def _find_block(lines: list[str], block_id: str) -> tuple[int | None, int | None]:
    """尋找 managed block 的起止行號。

    使用前綴匹配，同時支援帶 label 與不帶 label 的格式，
    確保新舊格式的 marker 都能被正確識別。
    """
    start_prefix = f"<!-- >>> ai-dev:{block_id}"
    end_prefix = f"<!-- <<< ai-dev:{block_id}"
    start_idx = None
    end_idx = None

    for index, line in enumerate(lines):
        stripped = line.rstrip("\n\r")
        if start_idx is None and stripped.startswith(start_prefix) and stripped.endswith("-->"):
            start_idx = index
        elif start_idx is not None and stripped.startswith(end_prefix) and stripped.endswith("-->"):
            end_idx = index
            break

    return start_idx, end_idx


def render_managed_block(
    block_id: str, content: str, *, open_label: str = "", close_label: str = ""
) -> str:
    """渲染完整 managed block 內容。"""
    start_marker, end_marker = get_block_markers(
        block_id, open_label=open_label, close_label=close_label
    )
    normalized_content = content.rstrip("\n")
    return f"{start_marker}\n{normalized_content}\n{end_marker}\n"


def read_managed_block_text(text: str, block_id: str) -> str | None:
    """從既有文字內容中讀取 managed block。"""
    lines = text.splitlines(keepends=True)
    start_idx, end_idx = _find_block(lines, block_id)

    if start_idx is None or end_idx is None:
        return None

    return "".join(lines[start_idx + 1 : end_idx]).rstrip("\n")


def read_managed_block(path: Path, block_id: str) -> str | None:
    """讀取既有 managed block 的內容。"""
    if not path.exists():
        return None

    return read_managed_block_text(path.read_text(encoding="utf-8"), block_id)


def upsert_managed_block(
    path: Path,
    block_id: str,
    content: str,
    *,
    open_label: str = "",
    close_label: str = "",
) -> None:
    """建立或更新 managed block，保留區塊外內容。"""
    block_text = render_managed_block(
        block_id, content, open_label=open_label, close_label=close_label
    )

    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = existing.splitlines(keepends=True)
    start_idx, end_idx = _find_block(lines, block_id)

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

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    start_idx, end_idx = _find_block(lines, block_id)

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
