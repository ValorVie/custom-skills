# Issue Tracker

本 repo 的工作追蹤權責與 canonical 出口。

## Canonical 權責

### 執行狀態：Beads

Beads 是所有軌道的 canonical 執行追蹤器，管理：

- 工作狀態、負責者與原子認領。
- blocking dependency 與 `bd ready`。
- 跨 session／Claude Code／Codex 的交接備註。
- 執行中發現的後續工作。

代理開始工作前必須執行 `bd ready`、`bd show <id>` 與 `bd update <id> --claim`。

### 正式變更工件：OpenSpec

功能、重構與規格修改仍走 OpenSpec proposal、design、specs、tasks、verify、archive 流程。

- `tasks.md` checkbox 表示 change 工件內部的實作與驗收進度。
- OpenSpec checkbox 不取代 Beads 的 ready、認領或依賴狀態。
- 一個 OpenSpec change 至少要有一張 Bead；只有需要獨立認領、跨 session 交接或阻擋關係的切片才建立子 Bead。
- Beads 與 `tasks.md` 狀態衝突時，代理執行狀態以 Beads 為準；OpenSpec verify 前仍需補齊工件進度。

### 外部入口：GitHub Issues

GitHub Issues（`ValorVie/custom-skills`）用於外部 bug、需求與公開討論。

- 外部 issue 被接受為內部工作時，建立或連結 Beads 工作項目。
- Bead 使用 `external-ref` 或 notes 保留 GitHub issue 連結。
- 後續認領、依賴與 ready 判斷回到 Beads。

## 不使用

- 不另開 Markdown TODO 清單或 `MEMORY.md` 作為第二份工作狀態。
- 不用 OpenSpec checkbox、GitHub label 或聊天紀錄取代 Beads 認領。
- 不把 `.beads/issues.jsonl` 當成同步來源；跨機器同步使用 Dolt remote。
- Jira、Linear 等外部 tracker 只有在使用者明確指定時使用，並保留對應 Bead 連結。

## 參考路徑

- Beads 指南：`docs/dev-guide/ai-tools/BEADS-GUIDE.md`
- OpenSpec 變更：`openspec/changes/`
- OpenSpec 規格：`openspec/specs/`
- 專案總述：`openspec/project.md`
- GitHub：`https://github.com/ValorVie/custom-skills`
