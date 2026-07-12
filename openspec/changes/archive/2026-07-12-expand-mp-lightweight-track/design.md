# Design: expand-mp-lightweight-track

## Context

本專案的開發流程有三層：MP 入口層（需求對齊）、OpenSpec（規格驅動的正式變更）、superpowers（TDD、除錯等橫切紀律）。mp-* 技能改寫自 `mattpocock/skills`，快照停在 `b843cb5`，整合模式為「人工審核改寫、不整包安裝」（`upstream/mattpocock-skills/last-sync.yaml`）。

上游演進到 `391a270`（2026-07-10）後出現三件事：

1. 既有技能改名並強化：`to-issues`→`to-tickets`（blocking edges、expand–contract 寬重構）、`to-prd`→`to-spec`（seam-first）、`diagnose`→`diagnosing-bugs`。`mapping.yaml` 的三處 `upstream_path` 因此失效。
2. 上游長出完整輕量流程：grill → to-spec → to-tickets → implement（內部驅動 tdd + code-review）。
3. 上游新增了本專案流程的兩個真空：`wayfinder`（探索期大型工作的地圖式規劃，OpenSpec proposal 之前）與 `prototype`（丟棄式原型回答設計問題）。

目前工作流文件只有兩個選項：走完整 OpenSpec 八階段，或直接實作。缺「不值得開 change、但需要對齊與拆票」的中間軌。

## Goals / Non-Goals

**Goals:**

- 修正上游追蹤基準（mapping.yaml、last-sync.yaml 對齊 `391a270`）。
- 把上游對 `to-tickets`、`to-spec` 的強化回灌到 `mp-to-issues`、`mp-to-prd`。
- 新增 `mp-wayfinder`、`mp-prototype`，填補探索期規劃與設計驗證的真空。
- 在 DEVELOPMENT-WORKFLOW.md 正式定義「輕量軌」，並給出三軌（輕量/重量/探索）判斷準則。

**Non-Goals:**

- 不整包安裝上游、不改變 `install_method: manual`。
- 不引入 `tdd`、`diagnosing-bugs`、`code-review`、`implement`（superpowers 與 `opsx:apply` 已覆蓋，維持 mapping.yaml 既有排除決策）。
- 不引入 `handoff`（與 claude-mem / save-session 功能重疊，需先跑 overlap 分析，另案處理）。
- 不新增獨立的 `mp-domain-modeling` 技能（上游把它從 grill-with-docs 抽成原語；本地 `mp-grill-with-docs` 已內嵌 CONTEXT.md/ADR 沉澱規則，行為對齊即可，不增加技能數）。
- 不動 ai-dev CLI 程式碼（純 skills 與文件變更，分發沿用既有三階段複製）。

## Decisions

### D1: 維持改寫式整合，不整包安裝

**選項 A（採用）**：沿用既有模式——上游內容人工改寫為 mp-*，詞彙與出口對齊本地 `docs/agents/`。
**選項 B**：`npx skills add mattpocock/skills` 整包安裝。

理由：上游以 GitHub/GitLab/本地 markdown 為 issue tracker，本專案 canonical 出口是 OpenSpec `tasks.md`（`docs/agents/issue-tracker.md`）；整包安裝會引入與 superpowers 重疊的技能（tdd、code-review），且上游一人維護、有 breaking rename 前科，直接安裝等於把漂移風險攤在執行期。改寫式把漂移風險收斂在 audit 時點。

### D2: mp-wayfinder 的地圖載體用 GitHub issues，結晶成果轉 OpenSpec

**選項 A（採用）**：地圖與子 ticket 放 GitHub issues（`docs/agents/issue-tracker.md` 的輔出口），利用原生 sub-issue 與 blocking 關係；當某個決策結晶到「可寫 proposal」時，轉入 OpenSpec change，地圖只留連結。
**選項 B**：地圖放 repo 內 markdown（上游的 local-markdown 模式）。
**選項 C**：地圖直接用 OpenSpec change 目錄。

理由：wayfinder 的價值在「多 session 並行認領 + 視覺化 frontier」，GitHub 原生 blocking 是本地 markdown 給不了的；而 OpenSpec change 假設已能寫 proposal，正是 wayfinder 要解的前一階段，用 change 目錄裝地圖會混淆兩軌職責。GitHub issues 本來就是本專案「尚未進入 OpenSpec 的雜項討論」的家，血統一致。

### D3: 輕量軌的準入條件寫死在文件，OpenSpec 的 canonical 地位不變

輕量軌允許「不開 OpenSpec change」的條件（三者皆須成立）：

1. 變更範圍在單一模組或單一文件群，不影響 `openspec/specs/` 既有規格的行為描述。
2. 一個 session 內可完成實作與驗證。
3. 不屬於 `docs/agents/issue-tracker.md` 定義的「正式變更」（功能、重構、規格修改）。

任一不成立 → 走 OpenSpec。理由：輕量軌是為了消除「小事開大流程」的摩擦，不是繞過規格治理；準則不寫死，輕量軌會逐漸侵蝕 canonical 出口。

### D4: 回灌採「行為合併」而非「全文替換」

`mp-to-issues` 合併上游 `to-tickets` 的兩個行為：每張切片宣告 blocking edges（含 frontier 工作模式：無阻擋者即可開工）、寬重構走 expand–contract 切法。`mp-to-prd` 合併 `to-spec` 的 seam-first：產出 brief 前先確認測試 seam 並與使用者核對。保留本地既有的三種出口（OpenSpec tasks / GitHub issue draft / 本地 Markdown）與 AFK/HITL 標記，不採上游的 `ready-for-agent` label 直寫（本地由 mp-triage 負責狀態）。

理由：本地版的出口設計與 triage 分工是刻意差異（mapping.yaml `adaptation: rewritten` 的原意），全文替換會倒退。

### D5: mp-prototype 沿用上游雙分支，產物處置對齊本地 git 慣例

沿用 logic（終端互動 app）/ UI（多變體單一路由）雙分支與六條通則（丟棄式、一鍵執行、無持久化、略過打磨、外顯狀態、完成即捕捉）。產物處置：驗證後的決策寫回實作或 spec，原型程式碼 commit 到 `experiment/<topic>` 分支（本專案既有分支慣例），不進 main。參考檔放 `skills/mp-prototype/references/`（本地慣例），不採上游同層平放。

### D6: 技能命名與投影沿用既有規格

`wayfinder`→`mp-wayfinder`、`prototype`→`mp-prototype`（`mp-<上游名>` 規則，見 `openspec/specs/mp-workflow-entry-layer/spec.md` 的命名 requirement）。兩技能經 `ai-dev clone` 分發至 Claude Code 與 Codex，與既有 mp-* 相同。

### D7: 投影不入版控（實作期發現，回溯補記）

實作時發現 commit `40ab1f1`（2026-05-06）已刻意移除 `.claude/skills/mp-*` 與
`.codex/skills/mp-*` 投影副本——投影是分發產物，入版控會與來源漂移。主規格的投影
requirement 已與現實脫節。本 change 一併把該 requirement 更新為分發機制版本：
來源是專案 `skills/`，投影由 `ai-dev clone` 三階段複製產生（GitHub → 整合目錄 →
工具目錄），repo 不保留副本。Claude Code 在本 repo 內工作時直接載入專案根 `skills/`
（本次實測確認），不依賴投影。

## Risks / Trade-offs

- [上游持續 rename，mapping.yaml 再度漂移] → 本次把參考快照推進到 `391a270`，並在 mapping notes 記錄 rename 歷史；後續靠 `/custom-skills-upstream-ops audit` 週期性比對，不做自動同步。
- [輕量軌被濫用，正式變更繞過 OpenSpec] → D3 準則寫入 DEVELOPMENT-WORKFLOW.md 與 `docs/agents/issue-tracker.md` 不變的 canonical 定義互為約束；mp-triage 分流時檢查準入條件。
- [wayfinder 地圖與 OpenSpec change 雙頭記錄] → 規定「結晶即轉 OpenSpec、地圖只留連結」；地圖限定在 proposal 尚不可寫的階段。
- [新技能增加 context 負擔] → 兩技能皆為使用者主動觸發型（description 精簡、觸發語彙收斂），不做寬觸發的 model-invoked 設計。
- [mp-prototype 產生的 experiment 分支堆積] → 技能內要求完成時在對應 issue/change 留分支連結；分支清理併入既有 git 工作流，不另建機制。

## Migration Plan

純新增與強化，無破壞性變更：

1. 先改 upstream 追蹤檔（mapping.yaml、last-sync.yaml）——不影響任何執行路徑。
2. 回灌 mp-to-issues、mp-to-prd——既有呼叫方式與出口不變，只增行為。
3. 新增 mp-wayfinder、mp-prototype——全新路徑。
4. 最後改文件（DEVELOPMENT-WORKFLOW.md、mp-workflow.md、CHANGELOG.md）。

回滾：revert 對應 commit 即可，無狀態遷移。

## Open Questions

- 無阻塞性未決。`handoff` 與 `domain-modeling` 的引入評估留待後續 change（見 Non-Goals）。
