---
name: work-log-claude
description: 從本機 Claude Code 工作階段（~/.claude/projects）產生有證據的 Markdown 工作日誌。使用者要求 Claude 端的工作日誌、日報、週報、工時統計，或要整理一段時間內 Claude Code 做過的任務重點、短脈絡與來源時使用。Codex 端或兩者合併的日誌改用 .agents/skills/work-log-codex。
---

# Work Log Claude

只讀 Claude Code 的工作階段紀錄，產出與 `work-log-codex` 相同格式的工作日誌。
Claude 讀取器、解析、git 證據與 formatter 全部沿用 `.agents/skills/work-log-codex`；本 skill
只關掉 Codex 來源，所以兩者的報告結構、摘要規則與 prompt 完全一致。

## 資料來源

- 讀：`<claude-home>/projects/<cwd-slug>/<session>.jsonl`（主工作階段）與
  `<claude-home>/projects/<cwd-slug>/<session>/subagents/*.jsonl`（subagent，子代理）。
- 只取 `user`／`assistant` 紀錄。使用者提示只算真正輸入的文字；tool_result（工具回傳）、
  `<command-name>` 之類的系統包裝與 `isMeta` 紀錄不當成提示。
- 專案＝該工作階段第一筆 `cwd`（啟動目錄），中途 `cd` 不會把工作階段拆到別的專案。
- 排除：`entrypoint` 為 `sdk-*` 的工作階段（記憶外掛之類的輔助工作階段），
  以及 `*observer-sessions` 目錄。
- 不讀：`~/.claude/transcripts/`、`history.jsonl`、`sessions/*.tmp`。這些是舊版或其他工具
  的格式，不是目前 Claude Code 的工作階段紀錄。
- 不讀任何 Codex 資料。

`<claude-home>` 預設是執行者的 `~/.claude`，傳入時用絕對路徑。這個目錄通常只有本人讀得到，
其他帳號執行時會讀不到工作階段。

## 流程

與 `work-log-codex` 相同：**有界 parser → 逐專案摘要 → 最終整合 → formatter**。
下列命令都在 repo 根目錄執行。暫存目錄 `WL_TMP`
用本 session 的 scratchpad 目錄；沒有時先 `mktemp -d` 建立，之後每個命令寫出絕對路徑
（Bash 呼叫之間不保留 shell 變數）。

### 1. 解析時間範圍

`today`、`yesterday`、`this-week`、`this-month`、`YYYY-MM-DD`、`YYYY-MM-DD YYYY-MM-DD`。
可選 `--project <name>` 只看單一專案。

### 2. 執行 parser

stderr 顯示進度，stdout 只輸出 JSON。一次只跑一個 parser，多週一起跑再分週整理。

```bash
uv run --python 3.14 python .claude/skills/work-log-claude/scripts/work_log_claude.py parse \
  TIME_RANGE [END_DATE] \
  --timezone "Asia/Taipei" \
  [--project "PROJECT"] \
  --claude-home <absolute-claude-home> \
  --emit-project-dir "$WL_TMP/wl_projects" \
  > "$WL_TMP/wl_report.json"
```

### 3. 逐專案摘要

不要把整份 `wl_report.json` 讀進上下文。依序讀：

- `$WL_TMP/wl_projects/manifest.json`
- 每個專案 bundle JSON
- `.agents/skills/work-log-codex/prompts/project_summary.md`

每個專案整理 2 至 5 個任務，格式與規則照 `project_summary.md`：

```md
- **一行重點：** <一句可獨立閱讀的工作重點>
  - **重點脈絡：** <300 字以內，說明起因、處理、結果與證據邊界>
  - **來源：** <正式文件路徑及／或 repo@commit>
```

- `git_commits` 是完成項目的主證據；`session_summaries` 補未提交、研究、規劃中的工作。
- 沒有 commit 或正式文件時標成研究／規劃，來源寫「工作階段摘要（無 Git commit）」。
- 不要把原始工作階段 JSONL 當成正式完成證據。
- `git_commits` 是該 repo 在期間內的全部提交，可能包含 Codex 或人工做的提交。只把能對到
  Claude 工作階段內容的提交寫進任務；其餘不要算成 Claude 的交付。

專案多時，可以用 Agent 工具每個專案派一個子代理做摘要，各自寫到
`$WL_TMP/wl_project_<name>.md`。

### 4. 最終摘要前段

讀 `wl_report.json` 的 `summary`、所有 `wl_project_<name>.md` 與
`.agents/skills/work-log-codex/prompts/final_summary.md`，產出 `$WL_TMP/wl_summary.md`，
只含 `### 當日總結` 與 `### 逐專案摘要`，並原樣保留三層任務格式。

### 5. formatter 組裝

```bash
PYTHONPATH=.agents/skills/work-log-codex uv run --python 3.14 python -m wl_parser.formatters \
  report --summary-file "$WL_TMP/wl_summary.md" < "$WL_TMP/wl_report.json" > "$WL_TMP/wl_report.md"
PYTHONPATH=.agents/skills/work-log-codex uv run --python 3.14 python -m wl_parser.formatters \
  appendix < "$WL_TMP/wl_report.json" > "$WL_TMP/wl_appendix.md"
```

`debug` 只在使用者明確要求時產生（`formatters debug`）。

### 6. 寫檔與回報

輸出到 `docs/work-logs/claude/`，避免覆蓋 `work-log-codex` 在 `docs/work-logs/` 的同名檔：

- 單日：`docs/work-logs/claude/YYYY-MM-DD.md`、`YYYY-MM-DD.appendix.md`
- 區間：`docs/work-logs/claude/YYYY-MM-DD--YYYY-MM-DD.md`、`.appendix.md`
- Debug：`.debug.md`

`docs/work-logs/` 是可重建的本機輸出。repo 若已忽略此目錄，保留忽略狀態，不要強制加入 Git。

回覆時先給 `當日總結` 與 `逐專案摘要` 的精華，再列寫入路徑；工具統計與 token 只放 debug。

## 快速產出（deterministic fallback）

不經 AI 摘要，直接用 parser 結果產檔，適合測試。預設寫到 `docs/work-logs/claude/`：

```bash
uv run --python 3.14 python .claude/skills/work-log-claude/scripts/work_log_claude.py generate \
  --range 2026-09-14 --end-date 2026-09-20 \
  --claude-home <absolute-claude-home> \
  --mode report+appendix
```

選項與 `work-log-codex/scripts/generate_work_log.py` 相同，`--codex-home` 會被忽略。

## 維護

- 測試：`uv run --python 3.14 python -m unittest discover -s .claude/skills/work-log-claude/tests`
- Claude 讀取規則的唯一實作是 `.agents/skills/work-log-codex/scripts/source_claude.py`，
  測試在同目錄 `tests/test_claude_source.py`，規則說明在 `references/sources.md`。
- `scripts/work_log_claude.py` 只把 `wl_parser.work_log_parser` 的 `load_codex_events` 與
  `_parse_codex_index_sessions` 換成空結果。`work-log-codex` 改名這些函式時本 skill 的測試會
  失敗，屆時改成讓 `build_report()` 接受來源選項。
- 報告版面與摘要規則的真相在 `.agents/skills/work-log-codex/references/report-schema.md`
  與 `prompts/`；本 skill 不另存副本。
