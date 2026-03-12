---
name: work-log-claude
description: 根據 Claude Code / Codex 對話紀錄產生工作日誌報告。支援每日回顧、週報、即時查詢。用法：/work-log-claude today | /work-log-claude this-week | /work-log-claude 2026-03-01 2026-03-11
---

# Work Log Claude

根據 AI 輔助工具的對話紀錄與 git 歷史，自動產生具有語意摘要的工作日誌。

## 使用方式

```
/work-log-claude <時間範圍> [結束日期] [--project <name>] [--output <mode>]
```

**時間範圍：** today | yesterday | this-week | this-month | YYYY-MM-DD
**輸出模式：** terminal | file | obsidian | all（預設 all）

**範例：**
```
/work-log-claude today
/work-log-claude yesterday --output terminal
/work-log-claude this-week --project qdm-base
/work-log-claude 2026-03-01 2026-03-11 --output file
```

## 執行流程

收到使用者呼叫後，依照以下步驟執行：

### Step 1: 讀取設定

讀取本 skill 目錄下的 `config.yaml`，取得以下設定：
- `timezone`（預設 Asia/Taipei）
- `output_dir`（Markdown 輸出目錄，預設 docs/work-logs）
- `obsidian_vault`（Obsidian vault 路徑）
- `obsidian_folder`（vault 內子資料夾，預設 work-logs）
- `default_output`（預設輸出模式，預設 all）
- `claude_home`（預設 ~/.claude）
- `codex_home`（預設 ~/.codex）

若設定檔不存在，使用預設值。

### Step 2: 解析參數

從使用者的呼叫中提取：
- `TIME_RANGE`：第一個參數（必填）
- `END_DATE`：第二個參數（可選，用於自訂日期範圍）
- `--project PROJECT`：專案過濾器（可選）
- `--output MODE`：輸出模式（可選，預設使用 config.yaml 的 default_output）

### Step 3: 執行 Parser

用 Bash 工具執行 Python parser，產生含 git 資料的結構化 JSON：

```bash
SKILL_DIR="$HOME/.claude/skills/work-log-claude"
PYTHONPATH="$SKILL_DIR" python3 -m wl_parser.work_log_parser \
  TIME_RANGE \
  [END_DATE] \
  --timezone "TIMEZONE" \
  [--project "PROJECT"] \
  --claude-home "$HOME/.claude" \
  --codex-home "$HOME/.codex" \
  2>/dev/null > /tmp/wl_report.json
```

將佔位符替換為實際值。

### Step 4: AI 摘要

用 Read 工具讀取 `/tmp/wl_report.json`。**只需關注以下欄位：**
- `projects`：每個專案的 `short_name`、`git_commits`（message + files_changed + insertions/deletions）、`duration_minutes`、`session_count`
- `summary`：`total_duration_minutes`、`project_count`

**不需要讀取** `sessions`、`tool_summary`、`token_summary`（這些由 formatter 處理）。

用 Read 工具讀取本 skill 目錄下的 `prompts/summarize.md`。

根據 prompt template 的指引，產生摘要文字。用 Write 工具將摘要寫入 `/tmp/wl_summary.md`。

### Step 5: 格式化並輸出

先用 formatter CLI 產生機械性區塊：

#### `terminal` 模式

```bash
SKILL_DIR="$HOME/.claude/skills/work-log-claude"
PYTHONPATH="$SKILL_DIR" python3 -m wl_parser.formatters terminal < /tmp/wl_report.json > /tmp/wl_formatted.md
```

然後依序顯示：
1. `/tmp/wl_summary.md` 的內容（AI 摘要）
2. `/tmp/wl_formatted.md` 的內容（工時統計 + 每日表格）

#### `file` 模式

```bash
SKILL_DIR="$HOME/.claude/skills/work-log-claude"
FILENAME="YYYY-MM-DD.md"  # 或 YYYY-MM-DD--YYYY-MM-DD.md 對範圍查詢
OUTPUT_PATH="docs/work-logs/$FILENAME"

PYTHONPATH="$SKILL_DIR" python3 -m wl_parser.formatters full_report < /tmp/wl_report.json > /tmp/wl_formatted.md
```

用 Read 工具讀取 `/tmp/wl_summary.md` 和 `/tmp/wl_formatted.md`。
用 Write 工具組合兩者寫入 `$OUTPUT_PATH`：

```
<wl_formatted.md 的標題行>

<wl_summary.md 內容>

<wl_formatted.md 標題行以下的內容>
```

注意：`wl_formatted.md` 已包含標題行，組合時用 `wl_formatted.md` 的標題，不要重複。

#### `obsidian` 模式

```bash
SKILL_DIR="$HOME/.claude/skills/work-log-claude"
OBSIDIAN_PATH="$OBSIDIAN_VAULT/$OBSIDIAN_FOLDER/YYYY-MM-DD.md"
mkdir -p "$(dirname "$OBSIDIAN_PATH")"

PYTHONPATH="$SKILL_DIR" python3 -m wl_parser.formatters obsidian < /tmp/wl_report.json > /tmp/wl_formatted.md
```

用 Write 工具組合 frontmatter + AI 摘要 + formatted 內容寫入 `$OBSIDIAN_PATH`。

#### `all` 模式

依序執行 terminal → file → obsidian（可重用同一份 `/tmp/wl_report.json`）。

### Step 6: 回報結果

告知使用者：
- 終端摘要已顯示（terminal / all 模式）
- Markdown 檔案已寫入路徑（file / all 模式）
- Obsidian 筆記已寫入路徑（obsidian / all 模式）

## 注意事項

- **首次使用**：確認 `config.yaml` 的 `obsidian_vault` 路徑正確
- **Codex 支援**：僅整合 session thread 標題，不解析 SQLite
- **時區**：所有時間以 config.yaml 的 timezone 顯示，預設 Asia/Taipei（UTC+8）
- **Git 資料**：每個專案最多收集 50 筆 commit，使用 --stat 而非完整 diff
- **AI 摘要**：由執行 skill 的 Claude Code 自身產生，不呼叫外部 API
