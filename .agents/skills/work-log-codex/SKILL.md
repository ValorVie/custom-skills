---
name: work-log-codex
description: 從 Codex 與 Claude Code 工作階段產生有證據的 Markdown 工作日誌。使用者要求工作日誌、日報、週報、工時統計，或要整理一段時間內的一行任務重點、短脈絡與來源時使用。
---

# Work Log Codex

根據本機的 Codex 與 Claude Code 工作階段紀錄，產生可讀、可保存、可追溯的工作日誌。

## 使用時機

Use this skill when the user wants to:
- 針對 `今天`、`昨天`、`本週` 或自訂日期區間整理工作日誌
- 想知道某段時間做了哪些專案、主要交付與研究內容
- 想把對話紀錄與 git 歷史整理成可讀的 Markdown 日誌
- 想輸出到本機 `docs/work-logs/` 或 Obsidian

## 流程

這個 skill 的最佳路徑是 **有界 parser -> 專案層任務摘要 -> 最終整合 -> 分層 formatter**。

### 1. 解析時間範圍

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

### 2. 執行有界 parser

使用 uv Python 3.14。parser 會在 stderr 顯示讀取與分析進度；stdout 只輸出 JSON。
在共用主機上一次只跑一個 parser。多個相鄰週次使用一個合併日期範圍，完成後再分週整理，
不要平行掃描同一批工作階段。

```bash
SKILL_DIR="$PWD/.agents/skills/work-log-codex"
PYTHONPATH="$SKILL_DIR" uv run --python 3.14 python -m wl_parser.work_log_parser \
  TIME_RANGE \
  [END_DATE] \
  --timezone "Asia/Taipei" \
  [--project "PROJECT"] \
  --claude-home <absolute-claude-home> \
  --codex-home <absolute-codex-home> \
  --emit-project-dir /tmp/wl_projects \
  > /tmp/wl_report.json
```

資料收集器只保留日期範圍內事件，並壓縮分析所需的 `raw` 欄位。若 stderr 長時間停在同一
階段、超出目前任務的時間或記憶體門檻，停止該次執行並保留量測，不要以多個 parser 重試。

### 3. 逐專案摘要

不要直接把整份 `/tmp/wl_report.json` 全讀進上下文。優先讀：
- `/tmp/wl_projects/manifest.json`
- 每個 project bundle JSON
- `prompts/project_summary.md`

每個專案各做一次摘要，將相關 commit 與工作階段合併成 2 至 5 個任務。每個任務固定使用：

```md
- **一行重點：** <一句可獨立閱讀的工作重點>
  - **重點脈絡：** <300 字以內，說明起因、處理、結果與證據邊界>
  - **來源：** <正式文件路徑及／或 repo@commit>
```

摘要規則：

- 優先從 `git_commits` 理解實際交付主題
- 用 `session_summaries` 補足未提交、研究、規劃中的工作
- `session_hints` 只當快速導覽，真正判讀以 `session_summaries` 為主
- 合併 related commits，不要逐 commit 轉寫
- 沒有 commit 或正式文件時，明確標成研究／規劃，來源寫「工作階段摘要（無 Git commit）」
- 來源必須直接支持相鄰主張；不要把原始 session JSONL 當成正式完成證據
- 每段重點脈絡以 Unicode 字元數量測，不超過 300 字
- Token 成本不是主要限制；必要時可以逐專案、多次呼叫 AI 做摘要，不要為了省 token 犧牲語意品質

將每個專案摘要暫存到 `/tmp/wl_project_<name>.md`。

### 4. 生成最終摘要前段

讀取：
- `/tmp/wl_report.json` 的 `summary`
- 所有 `/tmp/wl_project_<name>.md`
- `prompts/final_summary.md`

產出 `/tmp/wl_summary.md`，內容必須只有：
- `### 當日總結`
- `### 逐專案摘要`

逐專案摘要需原樣保留「一行重點／重點脈絡／來源」三層，不得在最終整合時折回單層條列。

### 5. formatter 組裝

預設輸出是 `report + appendix` 兩個檔案；`debug` 只有在明確要求時才產生。

主報告只保留：
- `### 當日總結`
- `### 逐專案摘要`
- 每個任務的「一行重點／重點脈絡／來源」
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
SKILL_DIR="$PWD/.agents/skills/work-log-codex"
PYTHONPATH="$SKILL_DIR" uv run --python 3.14 python -m wl_parser.formatters report --summary-file /tmp/wl_summary.md < /tmp/wl_report.json > /tmp/wl_report.md

PYTHONPATH="$SKILL_DIR" uv run --python 3.14 python -m wl_parser.formatters appendix < /tmp/wl_report.json > /tmp/wl_appendix.md
```

### 6. 寫檔與回報

預設輸出到：
- 單日：`docs/work-logs/YYYY-MM-DD.md`
- 區間：`docs/work-logs/YYYY-MM-DD--YYYY-MM-DD.md`
- 附錄：`docs/work-logs/YYYY-MM-DD.appendix.md` 或 `docs/work-logs/YYYY-MM-DD--YYYY-MM-DD.appendix.md`
- Debug：`docs/work-logs/YYYY-MM-DD.debug.md` 或 `docs/work-logs/YYYY-MM-DD--YYYY-MM-DD.debug.md`

`docs/work-logs/` 預設視為可重建的本機輸出。若目前版本庫已忽略此目錄，保留忽略
狀態，不要自行強制加入 Git。只有使用者明確要求把某份日誌保存成版本控制文件時，才依
該版本庫的正式報告路徑另行建立，不要取消整個目錄的忽略規則。

回覆使用者時：
- 先給 `### 當日總結` 與 `### 逐專案摘要` 的精華
- 再告知 `report` 與 `appendix` 的寫入路徑
- 不要先丟工具統計或 session 明細；這些只放到 `debug`

## 指令

快速產出檔案（deterministic fallback，適合測試；最佳品質仍用上面的多段 AI 流程）：

```bash
uv run --python 3.14 python .agents/skills/work-log-codex/scripts/generate_work_log.py \
  --range today \
  --mode report+appendix
```

自訂日期區間：

```bash
uv run --python 3.14 python .agents/skills/work-log-codex/scripts/generate_work_log.py \
  --range 2026-03-02 \
  --end-date 2026-03-11 \
  --mode report+appendix
```

## 輸出規則

- 優先做「給人看的工作日誌」，不是稽核報告
- 主報告只放摘要、統計與每日摘要；證據另放 appendix，audit 另放 debug
- 每個任務保留一行重點、300 字內重點脈絡與來源，三者缺一不可
- `git_commits` 是完成項目的主證據，`session_hints` 是語意補充
- 如果沒有 commit，不要硬寫成交付，但要先檢查 `session_summaries` 能不能支撐更具體的研究/規劃主題
- 每個專案整理 2 至 5 個任務；一行重點要能獨立閱讀，脈絡段落不重複標題
- 除非使用者要求，回覆時不要先展開 `Token 消耗` 或 `工具使用`

## 參考

- Read `prompts/project_summary.md` before做逐專案摘要
- Read `prompts/final_summary.md` before做總結段落
- Read `references/sources.md` when changing ingestion behavior
- Read `references/report-schema.md` when changing report layout
