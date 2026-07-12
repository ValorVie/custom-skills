# Proposal: expand-mp-lightweight-track

## Why

上游 `mattpocock/skills` 自本地快照 `b843cb5` 後演進為一條完整的輕量開發流程（`391a270`，2026-07-10）：既有技能改名並強化（`to-issues`→`to-tickets`、`to-prd`→`to-spec`），並新增了本專案工作流目前的兩個真空——探索期大型工作規劃（`wayfinder`）與設計問題快速驗證（`prototype`）。同時 `upstream/mattpocock-skills/mapping.yaml` 已有三處上游路徑失效，追蹤基準需要修正。本變更把 MP 家族從「入口層」擴充為「輕量開發軌」，補上 OpenSpec（重量軌）與直接實作之間的中間選項。

## What Changes

- 回灌上游演進到既有技能（維持改寫式整合，不整包安裝）：
  - `mp-to-issues`：合併上游 `to-tickets` 的 blocking edges（票券宣告阻擋關係、frontier 工作模式）與 expand–contract 寬重構切法。
  - `mp-to-prd`：合併上游 `to-spec` 的 seam-first 步驟（寫 spec 前先與使用者確認測試 seam）。
- 修正 `upstream/mattpocock-skills/mapping.yaml`：更新失效的上游路徑（`to-issues`→`to-tickets`、`to-prd`→`to-spec`、`diagnose`→`diagnosing-bugs`），並更新 `last-sync.yaml` 參考快照至 `391a270`。
- 新增兩個技能（依既有 `mp-<上游名>` 命名規則改寫）：
  - `skills/mp-wayfinder/`：探索期大型工作的地圖式規劃，出口對齊 `docs/agents/issue-tracker.md`（GitHub issues 輔出口，結晶成果轉入 OpenSpec change）。
  - `skills/mp-prototype/`：丟棄式原型回答設計問題（logic 走終端 app、UI 走多變體路由）。
- `docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md` 新增「輕量軌」章節：小變更走 `mp-grill-with-docs` → `mp-to-issues` → superpowers TDD 直接實作 → code review，不開 OpenSpec change；並提供軌道判斷準則與快速參考表更新。
- 更新 `docs/agents/mp-workflow.md` 的職責清單（納入 wayfinder、prototype）與 `CHANGELOG.md`。

不納入（維持既有排除決策）：`tdd`、`diagnosing-bugs`、`code-review`、`implement`（superpowers 與 `opsx:apply` 已覆蓋）、`handoff`（與 claude-mem 重疊，另案評估）。

## Capabilities

### New Capabilities

- `mp-lightweight-track`: 輕量開發軌的定義——適用準則（單模組、無規格影響、單 session 可完成）、路徑（grill → to-issues → 實作 → review）、與重量軌（OpenSpec）及探索軌（wayfinder）的分界，落地於 DEVELOPMENT-WORKFLOW.md。

### Modified Capabilities

- `mp-workflow-entry-layer`: 技能組擴充——新增 `mp-wayfinder` 與 `mp-prototype` 的存在性、命名對映與 Claude Code/Codex 投影要求；既有 `mp-to-issues`、`mp-to-prd` 需求補上回灌後的行為（blocking edges、seam-first）；上游對照表路徑修正為 `391a270` 快照。

## Impact

- 受影響檔案：
  - `skills/mp-to-issues/SKILL.md`、`skills/mp-to-prd/SKILL.md`（內容強化）
  - `skills/mp-wayfinder/`、`skills/mp-prototype/`（新增）
  - `upstream/mattpocock-skills/mapping.yaml`、`upstream/mattpocock-skills/last-sync.yaml`
  - `docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md`、`docs/agents/mp-workflow.md`、`CHANGELOG.md`
- 分發影響：新增技能經 `ai-dev clone` 分發至 Claude Code 與 Codex（沿用既有三階段複製，無 CLI 程式碼變更）。
- 相容性：純新增與文件強化，無破壞性變更；既有 mp-* 呼叫方式不變。
- 依賴：無新增外部依賴；上游追蹤維持 `install_method: manual`。
