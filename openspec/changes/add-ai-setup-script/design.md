# 設計

## 架構

此腳本將是一個使用 `typer` 或 `argparse` 函式庫的 Python CLI 應用程式。由於使用 `uv`，我們可以輕鬆管理依賴。

### 依賴項目
- `typer`：用於 CLI 介面。
- `rich`：用於美觀的終端機輸出（進度條、狀態）。
- `shellingham`（選用）：若需要偵測 Shell 則使用。

### 結構
- `script/main.py`：進入點。
- `script/commands/install.py`：安裝邏輯。
- `script/commands/maintain.py`：維護邏輯。
- `script/utils/system.py`：作業系統偵測與 Shell 指令執行輔助工具。
- `script/utils/paths.py`：不同作業系統的路徑定義。

## 工作流

### 安裝工作流
1. 檢查前置需求（Node.js, Git）。
2. 建立必要目錄。
3. 透過 `npm install -g` 安裝全域 NPM 套件。
4. 複製必要的 Git 儲存庫到 `~/.config/`。
5. 將檔案從 `custom-skills` 複製到 `~/.claude/` 等位置。

### 維護工作流
1. 更新 NPM 套件。
2. 在所有設定儲存庫中執行 `git pull`。
3. 重新執行安裝步驟中的複製動作。

## 跨平台策略
- 使用 `pathlib` 處理路徑。
- 使用 `platform` 模組偵測作業系統。
-定義抽象的「動作」以對應特定的 Shell 指令（例如：`npm`, `git`, `cp`/`Copy-Item`）。

## 設定
- `pyproject.toml` 將管理依賴與工具設定。
- 將使用 `uv` 執行腳本：`uv run script/main.py`。
