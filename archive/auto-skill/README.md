# auto-skill 退役封存

- 退役日期：2026-08-11
- 狀態：僅供歷史查閱，不再安裝、分發或觸發
- 原功能：跨對話知識庫、技能經驗索引、canonical state、各工具 shadow projection，以及 Claude Code SessionStart 注入

## 為什麼移除

`auto-skill` 建立時，多數 Agent 執行環境還沒有完整的持久記憶與經驗管理能力，因此專案自行維護了知識索引、經驗檔案、投影及 SessionStart Hook。

現在多數 harness agent tool 已經提供成熟且完整的記憶、Skill、工具與 Agent 協作機制。例如 Prime Agent 已具備 continual harness、memory、skills、subagent 與工具層。繼續維護另一套 `auto-skill` 會產生幾個問題：

- 同一份經驗可能同時寫入 harness 與 `auto-skill`，形成兩套真相來源。
- 強制啟動規則及 SessionStart Hook 會在每次工作時增加不必要的觸發與 context。
- canonical state、shadow projection 與各工具專用路徑提高維護成本，也容易出現 loader 格式警告。
- 不同 Agent 工具的原生能力持續演進，自建相容層反而限制可攜性。

因此本專案停止維護 `auto-skill`，改用各 harness 原生的經驗學習與持久記憶能力。封存資料仍保留，方便查閱過去設計與必要時人工取回內容，但不應直接複製回有效的 Skills 或 Plugins 目錄。

## 與 `.agents/skills` 遷移的關係

Codex Skills 從 `.codex/skills` 遷移至共用的 `.agents/skills` 是另一項相容性調整。目的不是延續 `auto-skill`，而是讓一般 Skills 能被更多 harness agent tool 共用，包括 Prime Agent。Codex 專用設定、agents、hooks、prompts、MCP、認證與 session 資料仍留在 `.codex`。

換句話說：

- `auto-skill` 已退役，不會再從任何 Skills 路徑觸發。
- 其他通用 Skills 使用 `.agents/skills`，降低工具綁定並提高跨 harness 相容性。

## 封存分類

| 目錄 | 內容 |
|---|---|
| `skill/` | 原 `skills/auto-skill` Skill、知識庫、經驗索引與 clone policy |
| `project-knowledge/` | 原專案 `.claude/skills/auto-skill` 資料 |
| `claude-plugin/` | 原 `auto-skill-hooks` Claude Code Plugin 與 SessionStart 腳本 |
| `implementation/` | canonical state、shadow projection 的 Python 實作及專用測試 |
| `specs/` | 已退役的 OpenSpec 規格 |
| `plans/` | 歷史設計與實作計畫 |

嵌在其他共用檔案中的舊路由、分發與文件內容由 Git 歷史保存，不另建立會被執行或測試掃描的副本。

## 既有安裝的清理方式

新版 `ai-dev` 採確認式清理：

- `ai-dev clone` 檢查使用者層級的分發來源副本、canonical state、上游 repo、shadow、各工具 projection、舊啟動規則，以及 `auto-skill-hooks@custom-skills` 的安裝與快取。
- `ai-dev project init`、`ai-dev project update` 檢查專案內的 `auto-skill` 副本與舊路由規則。
- 只有互動式終端明確同意後才會清理；拒絕與非互動模式都保留原資料。
- `ai-dev clone --dry-run` 只列出偵測結果。
- 實際清理前會備份至 `~/.config/ai-dev/backups/auto-skill-removal/<timestamp>/`，並寫入 `audit.json`。

需要還原資料時，依 `audit.json` 的 `original` 與 `backup` 欄位人工復原。還原至有效 Skills 或 Plugins 路徑會重新啟用舊機制，操作前應先確認這確實是預期行為。
