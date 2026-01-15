# 能力：文件與設定

## 新增需求 (ADDED Requirements)

### 需求：依賴管理 (Dependency Management)
專案必須使用 `uv` 與 `pyproject.toml` 進行依賴管理。

#### 場景：專案定義
給定 `script/pyproject.toml`
它應該定義諸如 `typer`、`rich` 等依賴。
並且應該支援 `requires-python`。

### 需求：使用說明文件 (Usage Documentation)
`script/README.md` 必須提供關於如何使用腳本的清晰說明。

#### 場景：README 內容
當使用者閱讀 `script/README.md` 時
則它應該說明：
1. 如何安裝 `uv`。
2. 如何執行安裝 (`uv run script/main.py install`)。
3. 如何執行維護 (`uv run script/main.py maintain`)。
