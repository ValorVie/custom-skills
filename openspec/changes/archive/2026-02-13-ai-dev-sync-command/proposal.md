## Why

開發者在多台裝置使用 Claude Code 時，配置（`~/.claude`）、記憶資料庫（`~/.claude-mem`）和會話狀態無法跨裝置共享，導致每台機器都是獨立的孤島。目前沒有成熟的開源方案完整處理這個問題。ai-dev 已管理 skills 分發到各 AI 工具目錄，自然延伸為管理這些目錄的跨裝置同步。

## What Changes

- 新增 `ai-dev sync` 指令群組（`init`、`push`、`pull`、`status`、`add`、`remove`）
- 使用 Git 作為同步後端，單一 repo 儲存多個目錄的內容
- 內建 ignore profiles，自動為 `~/.claude` 和 `~/.claude-mem` 產生正確的 `.gitignore`
- 新增 `~/.config/ai-dev/sync.yaml` 設定檔管理同步目錄清單
- 跨平台支援：macOS/Linux 使用 rsync，Windows 使用 Python shutil fallback

## Capabilities

### New Capabilities

- `sync-command`: sync 指令群組的 CLI 介面定義（init/push/pull/status/add/remove 子指令、參數、輸出格式）
- `sync-config`: 同步設定檔管理（sync.yaml 結構、ignore profiles、目錄註冊與移除）
- `sync-engine`: 同步引擎核心（Git 操作、目錄與 repo 間的檔案同步、跨平台 rsync/shutil 抽象）

### Modified Capabilities

（無既有 spec 需要修改）

## Impact

- **新增檔案**：`script/commands/sync.py`、`script/utils/sync_config.py`
- **修改檔案**：`script/main.py`（註冊指令）、`script/utils/paths.py`（新增路徑函數）
- **依賴**：無新外部依賴（使用 Python 標準庫 + 現有 typer/rich）
- **使用者影響**：新指令，不影響既有功能
- **安全性**：同步 repo 必須為私有（會話紀錄可能包含敏感內容）
