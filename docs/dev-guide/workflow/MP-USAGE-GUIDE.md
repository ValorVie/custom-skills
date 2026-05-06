# MP 使用指南

本指南說明如何在日常開發中使用 `mp-*` 工作入口層。MP 的用途是把模糊需求變成清楚、可切片、可分流、可進入 OpenSpec 或 Superpowers 的工程工作。

MP 不取代 OpenSpec，也不取代 Superpowers：

- OpenSpec 負責正式變更生命週期：proposal、design、spec、tasks、verify、archive。
- Superpowers 負責任務內執行紀律：TDD、除錯、review、完成前驗證。
- MP 負責前段入口與周邊治理：需求追問、專案語言、PRD、垂直切片、triage、架構候選。

## 快速選擇

| 你現在的狀態 | 使用技能 | 產出 | 下一步 |
|---|---|---|---|
| 只有模糊想法 | `mp-grill-with-docs` | 已確認的術語、決策、未決問題 | `mp-to-prd` 或 OpenSpec |
| 已有一段討論但缺需求文件 | `mp-to-prd` | PRD 或 OpenSpec brief | `mp-to-issues` 或 `openspec-new-change` |
| 需求太大、不知道怎麼做 | `mp-to-issues` | 垂直切片、`AFK` / `HITL` 標記 | OpenSpec tasks 或 issue draft |
| 有工作項目但不知道能否交給 agent | `mp-triage` | `ready-for-agent` / `ready-for-human` 等狀態 | 分派 agent 或回問使用者 |
| 實作中反覆撞到架構摩擦 | `mp-improve-codebase-architecture` | 架構改善候選 | 另開 OpenSpec change |
| 要正式實作 | `openspec-*` + `superpowers:*` | change artifacts、測試、實作 | verify / archive |

## 基本流程

```text
模糊想法
  -> mp-grill-with-docs
  -> mp-to-prd
  -> mp-to-issues
  -> mp-triage
  -> openspec-* 或 superpowers:*
```

實際使用時不一定每一步都要跑。若需求已經夠清楚，可以直接從 `mp-to-issues` 開始；若任務已經是 OpenSpec change，可以直接用 `mp-to-issues` 改善 `tasks.md`。

## 共用規則

MP 技能會讀取這些共同文件：

- `docs/agents/mp-workflow.md`
- `docs/agents/issue-tracker.md`
- `docs/agents/triage-states.md`
- `docs/agents/domain.md`

如果這些文件不存在，先執行 `mp-setup-matt-pocock-skills` 或直接補齊文件。

## 情境 1：一句模糊想法，還不能開 OpenSpec

### 使用時機

使用者只說出方向，例如：

```text
我想讓儲存庫的技能管理更好一點
```

這種說法還不能直接開 OpenSpec。問題、範圍、驗證方式都不明確。

### 建議流程

```text
mp-grill-with-docs
  -> mp-to-prd
  -> openspec-new-change
```

### 對話示範

```text
使用者：我想讓儲存庫的技能管理更好一點。

AI：我建議先用 mp-grill-with-docs，因為「更好」還不是可驗證需求。
第一個要釐清的是：你要改善的是技能發現、技能分發、技能更新，還是技能品質檢查？
我的建議是先聚焦「技能更新」，因為它最容易造成上游與本地改寫版分歧。

使用者：對，是上游更新跟本地改寫版的追蹤。

AI：那我會把本輪語言固定成：
- 上游來源：第三方 skill 儲存庫。
- 本地改寫版：保留來源識別，但內容已依本專案重寫。
- 更新審核：只產出 diff 或報告，不自動覆蓋。

接著可以用 mp-to-prd 產出 OpenSpec brief。
```

### 產出範例

```markdown
## Problem

上游 skill 更新後，本地改寫版缺少固定 mapping 與審核流程。

## Intended Outcome

每個採用的上游技能都有來源 commit、local_skill、priority、adaptation 與排除理由。

## Open Questions

- 是否要把上游 diff 審核做成 CLI？
- 是否需要自動提示已排除技能有重大更新？
```

## 情境 2：已有 OpenSpec change，但 tasks 太粗

### 使用時機

`proposal.md`、`design.md`、`spec.md` 已經有了，但 `tasks.md` 像這樣：

```markdown
- [ ] 實作 MP 工作入口層
- [ ] 更新文件
- [ ] 測試
```

這些任務太大，agent 不容易接手，也不容易驗證。

### 建議流程

```text
mp-to-issues
  -> 更新 OpenSpec tasks.md
  -> openspec-apply-change
```

### 對話示範

```text
使用者：這個 OpenSpec change 已經有 proposal，幫我把 tasks 切細。

AI：我會用 mp-to-issues，輸出 OpenSpec tasks 格式。
我的建議是切成垂直切片，而不是用「寫技能、寫文件、寫測試」這種水平切片。

建議切片：
1. [AFK] 建立上游 tracking 檔案並驗證 mapping 可讀。
2. [AFK] 建立 P0 skills，並檢查 frontmatter 與觸發語。
3. [AFK] 建立 docs/agents 共同規則。
4. [AFK] 建立 Claude / Codex 投影並檢查一致性。
5. [AFK] 增加觸發案例測試，確保不覆蓋 OpenSpec / Superpowers。
```

### 好的 tasks 範例

```markdown
- [ ] 1.1 [AFK] 在 `upstream/sources.yaml` 登記 `mattpocock-skills`
  - 驗證：`install_method` 為 `manual`

- [ ] 2.1 [AFK] 建立 `skills/mp-grill-with-docs/SKILL.md`
  - 驗證：frontmatter name 符合目錄名稱，description 含清楚觸發條件

- [ ] 4.1 [AFK] 建立 `.claude/skills/mp-*` 與 `.codex/skills/mp-*`
  - 驗證：投影內容與 `skills/mp-*` 無差異
```

## 情境 3：GitHub issue 進來，但不知道能否交給 agent

### 使用時機

issue 看起來像功能需求，但缺少驗證條件或還有產品判斷。

### 建議流程

```text
mp-triage
  -> ready-for-agent 或 ready-for-human
  -> agent brief / human brief
```

### 對話示範

```text
使用者：幫我看 #42 能不能交給 agent。

AI：我會用 mp-triage。
目前要判斷三件事：
1. 範圍是否清楚。
2. 驗證條件是否明確。
3. 是否還需要人類產品判斷或外部權限。

我的初步建議是 `needs-info`，因為 issue 只說「改善登入體驗」，沒有說成功條件。
我會提出兩個具體問題：
- 成功條件是減少步驟、改善錯誤訊息，還是支援另一種登入方式？
- 是否允許改動現有 auth flow？
```

### 狀態判斷範例

| issue 狀態 | MP triage 結果 | 原因 |
|---|---|---|
| 有明確檔案、行為與測試方向 | `ready-for-agent` | agent 可自主完成 |
| 需要產品取捨 | `ready-for-human` | agent 不應替人做決策 |
| 缺少重現步驟 | `needs-info` | 需回問回報者 |
| 需求不符合專案方向 | `wontfix` | 記錄原因後關閉或留存 |

## 情境 4：實作中反覆撞到架構摩擦

### 使用時機

你正在修 bug 或做功能，但發現每次修改都要跳很多檔案、測試只能測 implementation、或 module 太淺。

### 建議流程

```text
superpowers:systematic-debugging 或 openspec-apply-change
  -> mp-improve-codebase-architecture
  -> 新 OpenSpec change
```

### 對話示範

```text
使用者：這次修完了，但每次改 parser 都會牽動 CLI、formatter、test fixture。

AI：我建議用 mp-improve-codebase-architecture 產出候選，不在原任務中直接重構。
我會先讀 CONTEXT.md、docs/adr/ 和相關程式碼，然後只輸出候選。

候選 1：建立 deep module：ParseResult pipeline
相關檔案：
- script/parser.py
- script/formatter.py
- tests/test_parser.py

問題：
目前 parser 的 interface 太淺，呼叫者仍需理解 formatter 的錯誤型別。

方向：
把解析成功、解析失敗、警告訊息集中到一個穩定 interface。

效益：
提高 locality，讓錯誤處理集中；提高 leverage，讓 CLI 不需要知道 parser implementation。

驗證影響：
測試對外可觀察行為，而不是測內部輔助函式。
```

### 重要邊界

`mp-improve-codebase-architecture` 只產出候選。要實作候選，另開 OpenSpec change，避免在原任務中偷偷擴大範圍。

## 情境 5：文件或設定變更，不需要完整 TDD

### 使用時機

變更是文件、設定、AI 指令、skill frontmatter 或流程指南。這類變更通常不適合用 TDD，但仍需要可驗證任務。

### 建議流程

```text
mp-to-issues
  -> OpenSpec tasks 或本地 Markdown checklist
  -> openspec-apply-change
  -> 文件檢查 / 專用 pytest / rg 掃描
```

### 對話示範

```text
使用者：幫我補一份 MP 使用指南，順便同步開發流程。

AI：這是文件與流程變更，不需要 TDD。
我會用 mp-to-issues 的思路切成：
1. [AFK] 新增 MP 使用指南。
2. [AFK] 更新 DEVELOPMENT-WORKFLOW.md。
3. [AFK] 增加或執行文件一致性檢查。
4. [AFK] 提交。
```

### 驗證方式範例

```bash
rg -n "MP-USAGE-GUIDE|mp-grill-with-docs|mp-to-issues" docs/dev-guide/workflow
rg -n "mp-setup-matt-pocock-skills|mp-improve-codebase-architecture" docs
```

## 情境 6：需要交給 Claude Code 與 Codex 都能讀懂

### 使用時機

任務會在 Claude Code 和 Codex 之間切換，或同一儲存庫需要兩邊使用相同工作流。

### 建議流程

```text
mp-setup-matt-pocock-skills
  -> docs/agents/*
  -> CLAUDE.md / AGENTS.md 只放入口提示
```

### 對話示範

```text
使用者：這套規則要 Claude 跟 Codex 都能用。

AI：我建議把共同規則放在 docs/agents/，入口文件只引用。
理由是 CLAUDE.md 和 AGENTS.md 各寫一份會很快分歧。

我會建立：
- docs/agents/mp-workflow.md
- docs/agents/issue-tracker.md
- docs/agents/triage-states.md
- docs/agents/domain.md

然後讓 CLAUDE.md 和 AGENTS.md 都只指向這些文件。
```

### 正確結構

```text
skills/mp-*              # 共同技能來源
  -> .claude/skills/mp-* # Claude Code 投影
  -> .codex/skills/mp-*  # Codex 投影

docs/agents/*            # 共同工作流來源
CLAUDE.md                # 只放入口提示
AGENTS.md                # 只放入口提示
```

## 情境 7：沒有 GitHub issue，只想用本地 Markdown

### 使用時機

個人專案、探索任務、或不想把工作項目發布到外部 tracker。

### 建議流程

```text
mp-to-prd
  -> mp-to-issues
  -> .scratch/<topic>/tasks.md
```

### 對話示範

```text
使用者：這還不想開 issue，只要先整理成可做的清單。

AI：我會使用本地 Markdown 出口。
建議路徑是 `.scratch/mp-workflow/tasks.md`，因為這是探索性工作。
若後續決定正式化，再轉成 OpenSpec change。
```

### 本地輸出範例

```markdown
# MP Workflow Draft Tasks

## Context

來源：使用者要求建立 MP 使用指南。

## Tasks

- [ ] [AFK] 新增使用指南
- [ ] [AFK] 同步開發流程文件
- [ ] [AFK] 執行文件一致性檢查
```

## 情境 8：不該使用 MP 的情況

MP 是入口層，不是萬用流程。

| 情境 | 不使用 MP 的原因 | 使用 |
|---|---|---|
| 已有明確 specs，準備實作 | 不需要再追問需求 | `openspec-apply-change` |
| 正在寫 TDD 實作 | MP 不負責 red-green-refactor | `superpowers:test-driven-development` |
| 正在除錯失敗測試 | MP 不負責系統化除錯 | `superpowers:systematic-debugging` |
| 要驗證 change 是否符合 spec | MP 不負責正式驗證 | `openspec-verify-change` |
| 要歸檔完成的 change | MP 不負責歸檔 | `openspec-archive-change` |

## 決策檢查表

開始前問自己：

- 需求是否清楚到可以寫 proposal？
- 是否需要先固定專案語言？
- 是否已經能切成可驗證垂直切片？
- 是否知道哪些任務可交給 agent？
- 是否只是架構摩擦候選，而不是本輪必做實作？

若前四題有任一題是否定，優先使用 MP。若已經全部清楚，直接進 OpenSpec 或 Superpowers。

## 維護檢查

MP 使用指南更新時，同步檢查：

- `docs/agents/mp-workflow.md` 是否仍是共同真實來源。
- `docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md` 是否仍描述 MP 入口。
- `skills/mp-*/SKILL.md` 的觸發條件是否仍不覆蓋 OpenSpec / Superpowers。
- `upstream/mattpocock-skills/mapping.yaml` 是否仍能追蹤上游來源。
