---
name: work-log-codex
description: Generate Markdown work logs from Codex and Claude Code session history. Use this whenever the user asks for 工作日誌, 日報, 週報, 工時統計, or wants to summarize what was done in a time window from session records, even if they do not explicitly mention a skill.
---

# Work Log Codex

根據本機的 Codex 與 Claude Code session 紀錄，產生可讀、可保存的工作日誌。

## When To Use

Use this skill when the user wants to:
- 針對 `今天`、`昨天`、`本週` 或自訂日期區間整理工作日誌
- 想知道某段時間做了哪些專案、主要交付與研究內容
- 想把對話紀錄與 git 歷史整理成可讀的 Markdown 日誌
- 想輸出到 `docs/work-logs/` 或 Obsidian

## Workflow

這個 skill 的最佳路徑不是單次摘要，而是 **parser -> project-level AI summary -> final synthesis -> layered formatter**。

### Step 1: 解析時間範圍

支援：
- `today`
- `yesterday`
- `this-week`
- `this-month`
- `YYYY-MM-DD`
- `YYYY-MM-DD YYYY-MM-DD`

可選輸入：
- `--project <name>`：只看單一專案
- `--output` / `--format`：控制輸出方式

### Step 2: 執行 parser

優先用 `uv run python`，失敗再 fallback `python3`。

```bash
SKILL_DIR="$PWD/.codex/skills/work-log-codex"
PYTHONPATH="$SKILL_DIR" uv run python -m wl_parser.work_log_parser \
  TIME_RANGE \
  [END_DATE] \
  --timezone "Asia/Taipei" \
  [--project "PROJECT"] \
  --claude-home "$HOME/.claude" \
  --codex-home "$HOME/.codex" \
  --emit-project-dir /tmp/wl_projects \
  > /tmp/wl_report.json \
  || PYTHONPATH="$SKILL_DIR" python3 -m wl_parser.work_log_parser \
  TIME_RANGE \
  [END_DATE] \
  --timezone "Asia/Taipei" \
  [--project "PROJECT"] \
  --claude-home "$HOME/.claude" \
  --codex-home "$HOME/.codex" \
  --emit-project-dir /tmp/wl_projects \
  > /tmp/wl_report.json
```

### Step 3: 逐專案 AI 摘要

不要直接把整份 `/tmp/wl_report.json` 全讀進上下文。優先讀：
- `/tmp/wl_projects/manifest.json`
- 每個 project bundle JSON
- `prompts/project_summary.md`

每個專案各做一次摘要：
- 優先從 `git_commits` 理解實際交付主題
- 用 `session_summaries` 補足未提交、研究、規劃中的工作
- `session_hints` 只當快速導覽，真正判讀以 `session_summaries` 為主
- 合併 related commits，不要逐 commit 轉寫
- 沒有 commit 時才寫成研究/探索
- Token 成本不是主要限制；必要時可以逐專案、多次呼叫 AI 做摘要，不要為了省 token 犧牲語意品質

將每個專案摘要暫存到 `/tmp/wl_project_<name>.md`。

### Step 4: 生成最終摘要前段

讀取：
- `/tmp/wl_report.json` 的 `summary`
- 所有 `/tmp/wl_project_<name>.md`
- `prompts/final_summary.md`

產出 `/tmp/wl_summary.md`，內容必須只有：
- `### 當日總結`
- `### 逐專案摘要`

### Step 5: formatter 組裝

預設輸出是 `report + appendix` 兩個檔案；`debug` 只有在明確要求時才產生。

主報告只保留：
- `### 當日總結`
- `### 逐專案摘要`
- `### 工時統計`
- `### 每日摘要`

附錄只保留：
- `### 專案證據附錄`
- 每個專案的狀態、commit 證據、代表檔案、必要補充

`debug` 才包含：
- `### Token 消耗`
- `### 工具使用`
- `### Commit 明細`
- `### Session 明細`
- `### Codex Sessions`

若要直接用 formatter CLI：

```bash
SKILL_DIR="$PWD/.codex/skills/work-log-codex"
PYTHONPATH="$SKILL_DIR" uv run python -m wl_parser.formatters report --summary-file /tmp/wl_summary.md < /tmp/wl_report.json > /tmp/wl_report.md \
  || PYTHONPATH="$SKILL_DIR" python3 -m wl_parser.formatters report --summary-file /tmp/wl_summary.md < /tmp/wl_report.json > /tmp/wl_report.md

PYTHONPATH="$SKILL_DIR" uv run python -m wl_parser.formatters appendix < /tmp/wl_report.json > /tmp/wl_appendix.md \
  || PYTHONPATH="$SKILL_DIR" python3 -m wl_parser.formatters appendix < /tmp/wl_report.json > /tmp/wl_appendix.md
```

### Step 6: 寫檔與回報

預設輸出到：
- 單日：`docs/work-logs/YYYY-MM-DD.md`
- 區間：`docs/work-logs/YYYY-MM-DD--YYYY-MM-DD.md`
- 附錄：`docs/work-logs/YYYY-MM-DD.appendix.md` 或 `docs/work-logs/YYYY-MM-DD--YYYY-MM-DD.appendix.md`
- Debug：`docs/work-logs/YYYY-MM-DD.debug.md` 或 `docs/work-logs/YYYY-MM-DD--YYYY-MM-DD.debug.md`

回覆使用者時：
- 先給 `### 當日總結` 與 `### 逐專案摘要` 的精華
- 再告知 `report` 與 `appendix` 的寫入路徑
- 不要先丟工具統計或 session 明細；這些只放到 `debug`

## Commands

快速產出檔案（deterministic fallback，適合測試；最佳品質仍用上面的多段 AI 流程）：

```bash
uv run python .codex/skills/work-log-codex/scripts/generate_work_log.py --range today \
  --mode report+appendix \
  || python3 .codex/skills/work-log-codex/scripts/generate_work_log.py --range today
```

自訂日期區間：

```bash
uv run python .codex/skills/work-log-codex/scripts/generate_work_log.py \
  --range 2026-03-02 \
  --end-date 2026-03-11 \
  --mode report+appendix \
  || python3 .codex/skills/work-log-codex/scripts/generate_work_log.py \
  --range 2026-03-02 \
  --end-date 2026-03-11
```

## Output Rules

- 優先做「給人看的工作日誌」，不是稽核報告
- 主報告只放摘要、統計與每日摘要；證據另放 appendix，audit 另放 debug
- `git_commits` 是完成項目的主證據，`session_hints` 是語意補充
- 如果沒有 commit，不要硬寫成交付，但要先檢查 `session_summaries` 能不能支撐更具體的研究/規劃主題
- 每個專案摘要以條列為主，控制在約 500 字內
- 除非使用者要求，回覆時不要先展開 `Token 消耗` 或 `工具使用`

## References

- Read `prompts/project_summary.md` before做逐專案摘要
- Read `prompts/final_summary.md` before做總結段落
- Read `references/sources.md` when changing ingestion behavior
- Read `references/report-schema.md` when changing report layout
