---
title: mattpocock/skills 第三工作流定位分析
type: report/analysis
date: 2026050612-01
author: ValorVie
status: draft
source_snapshot: mattpocock/skills@b843cb5
---

# mattpocock/skills 第三工作流定位分析

## 摘要

`mattpocock/skills` 適合被視為 `superpowers` 與 `openspec` 之外的第三個工作流候選。它的核心不是接管完整開發流程，而是補足「開工前」與「工作流周邊」：需求對齊、專案語言、議題切片、任務分流、架構回看。若導入，建議先定位成前置對齊與工作入口層，再讓 `openspec` 承接正式變更生命週期，讓 `superpowers` 承接任務內執行紀律。

## 分析目的

本文件回答三個問題：

- `mattpocock/skills` 在既有工作流中應該站在哪個位置。
- 它補的是哪一類缺口，為什麼不是 `superpowers` 或 `openspec` 的重複品。
- 最有價值的技能鏈路應如何理解，以及未來若導入本專案，應先導入哪一段。

## 分析範圍

### 包含

- `mattpocock/skills` 的正式技能清單與 README 定位。
- 核心工程技能鏈：`setup-matt-pocock-skills`、`grill-with-docs`、`to-prd`、`to-issues`、`triage`、`tdd`、`diagnose`、`improve-codebase-architecture`。
- 與本專案既有 `superpowers`、`openspec` 工作流的分工。

### 排除

- 不評估已棄用技能。
- 不在本文件中執行導入、改名、投影同步或技能內容改寫。
- 不把 `mattpocock/skills` 視為完整替換方案；本文件只處理定位與導入邊界。

## 方法論

資料來源：

- 上游儲存庫：<https://github.com/mattpocock/skills>
- 本地查核快照：`/tmp/mattpocock-skills`，commit `b843cb5`
- 正式外掛技能清單：`.claude-plugin/plugin.json`
- 核心技能檔：`skills/engineering/*/SKILL.md`

判斷方法：

- 先看 README 宣告的設計哲學與失敗模式。
- 再看正式外掛暴露哪些技能，避免把雜項或已棄用技能納入核心判斷。
- 最後用本專案既有工作流角色對照：任務執行、規格生命週期、工作入口與周邊治理。

## 核心定位

### mattpocock/skills 補的是「工作入口層」

`mattpocock/skills` 的主軸是把「還沒開始寫程式碼以前」容易失真的部分變成可操作流程：

- 使用者說的需求是否已經足夠清楚。
- 專案內的詞彙是否一致。
- 需求是否已經轉成可追蹤的 PRD 或 issue。
- issue 是否能被 agent 接手。
- 架構問題是否已經被看見，而不是等到任務中途才爆開。

這一層不是實作層，也不是規格歸檔層。它更像是任務進入正式工程流程前的「需求澄清、語言固定、任務成形」階段。

### 與既有兩套工作流的分工

| 工作流 | 核心職責 | 最適合處理的問題 | 不應承擔的部分 |
|---|---|---|---|
| `superpowers` | 任務內執行紀律 | TDD、除錯、code review、驗證、分支收尾 | 不負責把模糊需求變成任務入口 |
| `openspec` | 變更生命週期 | proposal、tasks、implementation、verification、archive | 不負責長時間追問使用者、整理專案語言 |
| `mattpocock/skills` | 工作入口與周邊治理 | 需求對齊、專案語言、PRD、issue 切片、triage、架構回看 | 不應直接取代正式實作與驗證流程 |

這個分工的關鍵是：`mattpocock/skills` 應該站在 `openspec` 與 `superpowers` 前面或旁邊，而不是壓在它們上面。

建議角色如下：

```text
模糊需求 / 新想法
  -> mattpocock/skills：追問、釐清、固定語言、切出任務
  -> openspec：正式變更提案、任務清單、驗證與歸檔
  -> superpowers：實作時的 TDD、除錯、review、完成前驗證
```

## 最有價值的技能鏈

### 1. setup-matt-pocock-skills：建立儲存庫層級的工作上下文

`setup-matt-pocock-skills` 是整條鏈的入口。它不是用來直接寫功能，而是先讓其他技能知道這個儲存庫的基本工作規則。

它會建立或更新三類上下文：

| 類別 | 產物 | 用途 |
|---|---|---|
| issue tracker 規則 | `docs/agents/issue-tracker.md` | 告訴技能工作項目要發到 GitHub、GitLab、本地 Markdown，或其他系統 |
| triage label 規則 | `docs/agents/triage-labels.md` | 把通用狀態角色對應到儲存庫內實際使用的 label |
| domain docs 規則 | `docs/agents/domain.md` | 告訴技能要讀哪裡的 `CONTEXT.md` 與 ADR |

它也會在 `CLAUDE.md` 或 `AGENTS.md` 補一個 `Agent skills` 區塊，讓工作規則變成儲存庫內可見的文件，而不是只存在一次對話記憶裡。

這一步的價值是把隱性假設變成顯性設定。沒有這一步，後續 `to-prd`、`to-issues`、`triage` 很容易各自猜測工作項目放在哪裡、label 怎麼命名、專案語言去哪裡讀。

對本專案的含義：

- 若導入，應改造成多投影可用，不可只寫 `CLAUDE.md`。
- `docs/agents/` 可以保留為儲存庫層級工作規則目錄。
- issue tracker 規則應支援本專案常見三種出口：GitHub issue、OpenSpec change、本地 Markdown。

### 2. grill-with-docs：把模糊需求壓成專案語言

`grill-with-docs` 是這套工作流最有辨識度的技能。它的重點不是「問很多問題」，而是用追問把模糊詞、衝突詞、邊界條件、實際程式碼行為串起來。

它做四件事：

- 對照 `CONTEXT.md`，發現使用者用詞和既有專案語言不一致時立即指出。
- 遇到模糊詞時，要求選定精確詞彙，例如一個詞到底指使用者、客戶、帳號，還是組織。
- 用具體情境測試需求邊界，逼出例外狀況與決策條件。
- 若程式碼與使用者描述矛盾，回到程式碼查證，而不是只接受口頭敘述。

它的關鍵副作用是即時更新文件：

- 術語定義穩定後，更新 `CONTEXT.md`。
- 遇到難以反推的架構決策時，才建立 ADR。

這點很重要。一般追問只改善當下對話；`grill-with-docs` 會把追問結果沉澱成儲存庫後續可重用的語言與決策記錄。

對本專案的含義：

- 它可以補足 `openspec` 前的需求澄清。
- 它也可以補足 agent 多次接手同一儲存庫時的語言一致性。
- 導入時要限制 ADR 產生條件，避免把每個小決定都寫成永久紀錄。

### 3. to-prd / to-issues / triage：把討論變成可接手的工作

`to-prd`、`to-issues`、`triage` 是工作入口層往任務系統銜接的三段。

#### to-prd：把已知脈絡合成 PRD

`to-prd` 的定位是「不要重新訪談使用者」，而是從既有對話與程式碼庫理解合成 PRD。它會整理：

- 問題陳述。
- 使用者可見的解法。
- 使用者故事。
- 實作決策。
- 測試決策。
- 不做事項。

它的價值不是取代 OpenSpec proposal，而是把討論中的產品意圖整理成較完整的需求文件。若後續要走 `openspec`，PRD 可以變成 proposal 的上游素材。

#### to-issues：把計畫切成垂直切片

`to-issues` 的核心是把 PRD、計畫或規格拆成可獨立接手的 issue。它強調垂直切片，而不是水平切片。

垂直切片的判準：

- 每個切片都穿過必要整合層。
- 每個切片完成後都能展示或驗證。
- 優先多個薄切片，而不是少數大切片。
- 標出哪些是可讓 agent 自主處理，哪些需要人類判斷。

這與本專案的工作方式相容，因為它能把大需求拆成「可驗證的小閉環」。差異在於，本專案若使用 `openspec`，切片不一定要發成 GitHub issue，也可以轉成 `tasks.md` 的任務單元。

#### triage：讓 issue 進入可處理狀態

`triage` 定義一個小型狀態機，把 issue 分成類別與狀態：

- 類別：`bug`、`enhancement`
- 狀態：`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`

它的價值是明確分辨「能不能交給 agent」。`ready-for-agent` 代表規格已足夠，不需要人類上下文；`ready-for-human` 代表仍需要人類判斷或外部存取；`needs-info` 則代表問題還不夠具體。

對本專案的含義：

- 可以把 `ready-for-agent` 對應到可啟動自動化或 subagent 的任務。
- 可以把 `ready-for-human` 對應到需要使用者決策的阻塞點。
- 若不用 GitHub issue，也可以把這組狀態搬進本地 Markdown 或 OpenSpec 任務 metadata。

### 4. tdd / diagnose / improve-codebase-architecture：接到實作、除錯與架構回看

這三個技能把工作入口層接到真正工程執行，但它們與既有 `superpowers` 重疊度較高，所以不建議第一輪原樣導入。

#### tdd：以行為測試與垂直切片推進

`tdd` 強調測試對外介面的可觀察行為，而不是測內部實作。它也反對一次先寫完所有測試再實作，主張用 tracer bullet：一個測試、一段最小實作、再下一個測試。

這與 `superpowers:test-driven-development` 的精神接近。若導入，不應新增另一套同名 TDD 流程，而應萃取其中兩個觀念：

- 測試名稱與介面用語要吃 `CONTEXT.md` 的專案語言。
- TDD 循環以垂直切片推進，不做水平切片。

#### diagnose：先建立可重現回饋迴圈

`diagnose` 的核心是先建立快速、明確、agent 可執行的失敗訊號，再開始假設與修復。它把除錯拆成：

- 建立回饋迴圈。
- 重現問題。
- 列出可否證假設。
- 針對假設加探針。
- 修復並補回歸測試。
- 清理與事後檢討。

這與 `superpowers:systematic-debugging` 高度重疊。最值得吸收的是它對「回饋迴圈」的強度要求，以及修復後追問「什麼架構改動能避免此錯誤再發生」，並把答案交給架構回看。

#### improve-codebase-architecture：把架構摩擦轉成 deep module 候選

`improve-codebase-architecture` 的價值在於它不是泛泛要求重構，而是用一套固定語言描述架構摩擦：

- module
- interface
- implementation
- depth
- seam
- adapter
- leverage
- locality

它會先讀 `CONTEXT.md` 與 ADR，再找哪些 module 太淺、哪些 seam 洩漏、哪些測試只能測到錯誤層次。輸出不是立刻改程式碼，而是提出 deepening opportunities，讓使用者選定要深入討論的候選。

這對本專案很有價值，因為它補了 `superpowers` 與 `openspec` 都不主打的日常架構保養角度。但導入時應保留「先提候選，不直接改」的限制，避免架構 review 變成任意重構。

## 為什麼這是第三工作流，而不是技能集合

如果只看單一技能，`mattpocock/skills` 看起來像一包提示詞。但把核心鏈路串起來後，它其實形成一個清楚的工作流：

```text
儲存庫初始化
  -> 記錄 issue tracker、label、domain docs 規則

需求出現
  -> grill-with-docs 追問與校準語言
  -> 更新 CONTEXT.md / ADR

需求成形
  -> to-prd 整理產品與實作意圖
  -> to-issues 拆成垂直切片
  -> triage 標記是否可交給 agent

任務執行
  -> tdd / diagnose 接到可驗證實作與除錯
  -> improve-codebase-architecture 回收架構摩擦
```

它的可貴之處是每一段都會產出下一段需要的上下文：

- `setup` 產出工作規則。
- `grill-with-docs` 產出專案語言與決策記錄。
- `to-prd` 產出可討論需求文件。
- `to-issues` 產出可分配工作項。
- `triage` 產出任務是否可代理執行的狀態。
- `tdd` / `diagnose` 產出實作回饋。
- `improve-codebase-architecture` 產出下一輪架構改善候選。

因此它適合被稱為第三工作流：它不是單點能力，而是把模糊需求導向可執行任務的前段系統。

## 導入建議

### 第一階段：導入工作入口層

優先導入或改寫：

| 候選名稱 | 來源技能 | 導入理由 |
|---|---|---|
| `mp-setup-workflow` | `setup-matt-pocock-skills` | 建立儲存庫層級工作規則，支援多投影與本專案目錄慣例 |
| `mp-grill-with-docs` | `grill-with-docs` | 補足需求澄清與專案語言沉澱 |
| `mp-to-prd` | `to-prd` | 把對話整理成需求文件，可銜接 OpenSpec proposal |
| `mp-to-issues` | `to-issues` | 把大需求拆成垂直切片，可銜接 issue 或 OpenSpec tasks |
| `mp-improve-architecture` | `improve-codebase-architecture` | 提供日常架構回看，不直接進入重構 |

### 第二階段：整合而非重複 TDD / 除錯

暫不建議原樣導入：

| 來源技能 | 原因 | 建議處理 |
|---|---|---|
| `tdd` | 與 `superpowers:test-driven-development` 重疊 | 萃取「專案語言命名測試」與「垂直切片 TDD」原則 |
| `diagnose` | 與 `superpowers:systematic-debugging` 重疊 | 萃取「先建立回饋迴圈」與「修復後回收架構摩擦」原則 |
| `triage` | 有價值，但強依賴 issue tracker label | 先改造成可支援 GitHub、OpenSpec、本地 Markdown 的狀態模型 |

### 第三階段：定義與 openspec 的銜接

建議規則：

- 使用者只有模糊想法時，先走 `mp-grill-with-docs`。
- 已形成正式變更時，轉入 `openspec-new-change` 或 `openspec-propose`。
- 已有 PRD 但未拆任務時，用 `mp-to-issues` 產出垂直切片，再轉成 OpenSpec `tasks.md`。
- 實作中遇到錯誤或測試設計問題時，回到 `superpowers` 的 TDD / 除錯技能。
- 實作後暴露架構摩擦時，用 `mp-improve-architecture` 產出下一個改善候選，不在原任務中偷偷擴大範圍。

## 主要風險

| 風險 | 說明 | 緩解方式 |
|---|---|---|
| 偏 Claude Code 的假設 | 上游外掛與連結腳本主要面向 Claude Code | 導入時改寫成 `.codex`、`.claude`、`.gemini`、`.github` 等多投影版本 |
| 與 superpowers 重疊 | `tdd`、`diagnose` 已有相近技能 | 不直接搬運，僅萃取原則 |
| issue tracker 預設太強 | `to-prd`、`to-issues`、`triage` 預設會發布到 issue tracker | 增加 OpenSpec 與本地 Markdown 出口 |
| ADR 過度產生 | 追問過程可能把太多小決定寫進 ADR | 保留上游條件：難反轉、未來讀者會困惑、確實有取捨 |
| 工作流層級混淆 | 容易被誤用成另一套完整開發框架 | 明確規範它只負責工作入口與周邊治理 |

## 結論

`mattpocock/skills` 值得作為第三工作流試點，但導入策略必須保守。它最適合補足的是「需求變成工程任務」之前的空白：追問、命名、決策記錄、PRD、切片與 triage。它不應取代 `openspec` 的變更生命週期，也不應取代 `superpowers` 的任務內執行紀律。

建議判斷是：先導入工作入口層，暫緩導入重疊執行技能。

優先順序：

| 優先級 | 行動 | 理由 | 預期效果 |
|---|---|---|---|
| P0 | 設計 `mp-setup-workflow` 與 `docs/agents/` 規則 | 沒有儲存庫層級設定，後續技能會各自猜測 | 建立穩定入口 |
| P0 | 改寫 `mp-grill-with-docs` | 這是最能補足現有缺口的技能 | 讓需求澄清可沉澱到 `CONTEXT.md` / ADR |
| P1 | 改寫 `mp-to-prd` / `mp-to-issues` | 可把討論接到正式工作項 | 減少大需求直接進入實作 |
| P1 | 定義 `triage` 狀態模型 | 可判斷任務能否交給 agent | 降低代理任務失敗率 |
| P2 | 整合 TDD / diagnose 觀念到既有技能 | 避免工作流重複 | 強化既有 `superpowers` 而不增加衝突 |

## 參考資料

- `mattpocock/skills` README：<https://github.com/mattpocock/skills>
- 正式外掛技能清單：<https://github.com/mattpocock/skills/blob/main/.claude-plugin/plugin.json>
- `setup-matt-pocock-skills`：<https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/SKILL.md>
- `grill-with-docs`：<https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md>
- `to-prd`：<https://github.com/mattpocock/skills/blob/main/skills/engineering/to-prd/SKILL.md>
- `to-issues`：<https://github.com/mattpocock/skills/blob/main/skills/engineering/to-issues/SKILL.md>
- `triage`：<https://github.com/mattpocock/skills/blob/main/skills/engineering/triage/SKILL.md>
- `tdd`：<https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md>
- `diagnose`：<https://github.com/mattpocock/skills/blob/main/skills/engineering/diagnose/SKILL.md>
- `improve-codebase-architecture`：<https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md>
