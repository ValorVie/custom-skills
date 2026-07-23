# mattpocock/skills 使用指南

<!-- markdownlint-disable MD013 MD060 -->

本指南說明如何獨立安裝與使用
[`mattpocock/skills`](https://github.com/mattpocock/skills)，以及每個技能背後的
使用邏輯、設計哲學與適用情境。

> [!IMPORTANT]
> 本指南以 2026-07-23 的上游 commit
> [`ed37663`](https://github.com/mattpocock/skills/tree/ed37663cc5fbef691ddfecd080dff42f7e7e350d)
> 為分析基準。當時 `skills` CLI 可發現 41 個技能，但上游 plugin manifest 只正式
> 發布其中 22 個。上游變動很快，安裝前應重新列出實際內容。

## 核心結論

這套技能不是要接管整個軟體生命週期。它刻意避免建立一個封閉、只能照表操作的
代理框架，而是提供可單獨使用、可組合、可修改的小型工作單元。

上游反覆強調四個原則：

1. **人保留流程控制權**：使用者選擇入口技能，代理只在明確邊界內工作。
2. **先對齊，再實作**：透過 grilling、共同語言與規格消除需求落差。
3. **回饋速度就是開發速度**：以型別、測試、瀏覽器或其他可執行檢查縮短回饋迴圈。
4. **技能應可組合，不應綁死模型**：每個技能處理一種失敗模式，並以公開語意交棒。

這也是本 repo 不再改寫成 `mp-*` 的原因：上游的價值不只在單一提示詞，而在它對
呼叫權、上下文、交棒與回饋迴圈的整體設計。保留原始名稱與更新節奏，比維護本地
分支更符合其使用方式。

## 安裝、驗證與更新

### 安裝前檢查

需要可執行 Node.js 與 `npx`。先查看上游目前可安裝的技能：

```bash
npx skills@latest add mattpocock/skills --list
```

### 手動全域安裝

```bash
npx skills@latest add mattpocock/skills -g -y
# 全域安裝無法使用 PromptScript
npx skills@latest add mattpocock/skills
```

- `-g`：安裝到使用者層級，不寫入本 repo。
- `-y`：採用 CLI 預設選擇並跳過互動確認。
- 這個命令會安裝 CLI 當下發現的全部技能。2026-07-23 實測為 41 個，不只是
  上游正式發布的 22 個。
- 實際寫入哪些代理目錄，以命令輸出與目前偵測到的代理為準。

這套技能刻意不加入 `upstream/sources.yaml` 或 `upstream/npx-skills.yaml`，也不由
`ai-dev clone` 分發。安裝、更新與移除都直接交給 `skills` CLI。

### 安裝後驗證

```bash
npx skills@latest list -g
```

至少確認 `setup-matt-pocock-skills`、`ask-matt`、`grill-with-docs`、`to-spec`、
`to-tickets` 與 `implement` 可見。若代理已在執行中，通常要重新啟動工作階段，
才會重新載入全域技能。

### 更新

```bash
npx skills@latest update -g
```

`update -g` 會處理所有由 CLI 追蹤的全域技能，不只這個來源。Skills CLI 1.5.20
沒有獨立的 `check` 命令；更新前可先用 `--list` 查看上游集合，更新後再用
`list -g` 確認結果。若上游新增、移除或改名技能，也要檢查本指南的成熟度分類。

### 移除

```bash
npx skills@latest remove -g

# remove Matt Pocock skills
npx skills remove -g -y ask-matt code-review codebase-design diagnosing-bugs domain-modeling grill-me grill-with-docs grilling handoff implement improve-codebase-architecture prototype research resolving-merge-conflicts setup-matt-pocock-skills tdd teach to-spec to-tickets triage wayfinder writing-great-skills
```

使用互動選單精確選取要移除的技能。不要直接刪除整個代理的全域 skills 目錄，
否則會一併移除其他來源。

## 第一次進入專案

安裝後，每個 repo 執行一次：

```text
/setup-matt-pocock-skills
```

它會先詢問 issue tracker、triage labels 與文件位置，再提出對專案入口文件與
`docs/agents/` 的修改。它的作用不是安裝技能，而是把上游技能接到該 repo 的實際
工作規則。

使用時遵守三個邊界：

- 先審閱它提出的草稿，再允許寫入。
- 現有 `AGENTS.md`、Beads、OpenSpec 與 Git 權限規則優先，不可被上游預設覆蓋。
- 設定完成不代表每次任務都要跑完整流程；依工作大小選最短可驗證路徑。

## 呼叫模型：誰有權啟動技能

上游把技能分成兩種，這是整套設計的核心。

| 類型 | 誰能啟動 | 設計目的 |
|------|----------|----------|
| 使用者呼叫 | 只有人明確輸入技能名稱 | 保留流程決策權，避免代理自行進入大型或具副作用的流程 |
| 模型呼叫 | 人或模型皆可呼叫 | 讓其他技能重用診斷、測試、研究、建模等通用能力 |

使用者呼叫技能可以交棒給模型呼叫技能，但不能暗中啟動另一個使用者呼叫技能。
這項限制用來控制兩種成本：

- 模型呼叫技能的描述會占用模型上下文。
- 使用者呼叫技能會占用人的記憶與選擇成本。

`ask-matt` 因此扮演路由器：人只需記得一個入口，再由它說明目前適合哪個技能，
但最後仍由人啟動該技能。

## 推薦工作流

### 一般功能或重構

```text
每個 repo 一次：setup-matt-pocock-skills
    ↓
ask-matt（不知道入口時）
    ↓
grill-with-docs
    ↓
prototype（有高風險設計問題時，由流程需要而使用）
    ↓
to-spec
    ↓
to-tickets
    ↓
每張 ticket 開新上下文執行 implement
```

`grill-with-docs` 到 `to-tickets` 適合留在同一個上下文，因為決策仍在逐步收斂。
進入 `implement` 後，每張 ticket 使用新上下文，降低舊討論干擾實作判斷。

### 小型、已對齊的變更

若工作可在單一上下文完成，且驗證方式已明確，可從 `grill-with-docs` 直接進入
`implement`，不用為了形式完整而建立 spec 與 tickets。

### 收到外部 issue

```text
triage → 確認 claim 與重現條件 → ready 狀態 → implement
```

`triage` 適合外部輸入，不應拿來重新審查 `to-tickets` 剛產生、已包含必要脈絡的
tickets。

### 問題仍很模糊或範圍過大

```text
wayfinder → 每個 session 解一個決策點 → 決策收斂 → to-spec
```

`wayfinder` 管理的是決策地圖，不是交付清單。若已能寫出規格，就不需要先跑它。

### 除錯

```text
diagnosing-bugs → 建立可失敗的最短回饋迴圈 → 驗證假設 → 回歸測試
```

先縮小問題，再列出 3 至 5 個可被證偽的假設。若找不到可測試的 seam，問題可能
是架構而不是單一錯誤，應轉向 `codebase-design` 或架構改善流程。

## 正式發布的 22 個技能

以下技能列於上游
[`plugin.json`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/.claude-plugin/plugin.json)，
是目前應優先採用的穩定集合。

### 工程流程：使用者呼叫

#### `ask-matt`

- **邏輯**：讀取目前意圖與工作狀態，推薦最合適的下一個技能，不直接代替它執行。
- **哲學**：用單一入口降低「要記住所有 slash command」的認知負擔，同時保留人的
  呼叫權。
- **適用**：知道想完成什麼，但不知道該從 grilling、spec、triage 或其他流程開始。
- **例子**：`/ask-matt 我有一個模糊的權限重構想法，下一步該用哪個技能？`
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/ask-matt/SKILL.md)

#### `setup-matt-pocock-skills`

- **邏輯**：盤點既有 tracker、labels 與文件位置，先展示規則草稿，再把技能接到 repo。
- **哲學**：通用技能必須服從專案的真實工作方式，不能假設所有 repo 都用同一套 tracker。
- **適用**：安裝後第一次進入 repo，或 tracker、labels、文件位置已改變。
- **例子**：`/setup-matt-pocock-skills`，選擇以 Beads 為 canonical tracker，並保留
  現有 `AGENTS.md` 限制。
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/setup-matt-pocock-skills/SKILL.md)

#### `grill-with-docs`

- **邏輯**：一次問一個高價值問題；查得到的事由代理查，只有決策才問人；同步建立
  `CONTEXT.md`、ADR 等耐久文件。
- **哲學**：需求錯位比寫錯程式更昂貴；共同語言能同時減少歧義、冗字與上下文成本。
- **適用**：需求、術語、範圍或驗收條件仍含糊。
- **例子**：`/grill-with-docs 我要重做技能更新流程，請先把來源、同步與分發邊界問清楚。`
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/grill-with-docs/SKILL.md)

#### `to-spec`

- **邏輯**：把已完成的討論整理成可實作規格；先確認公開測試 seam，再描述使用者故事、
  行為與邊界，不重新訪談。
- **哲學**：spec 是已同意決策的壓縮表示，不是新的腦力激盪；測試面應先於內部結構。
- **適用**：對話已收斂，需要可交棒、可驗收的規格。
- **例子**：`/to-spec 把剛才確認的全域技能安裝與更新行為整理成 spec。`
- **避免**：需求仍在變動時硬寫 spec；在 spec 填滿檔案路徑與實作細節。
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/to-spec/SKILL.md)

#### `to-tickets`

- **邏輯**：把 spec 切成可獨立驗證的垂直 tracer bullets，明確標出 blocking edges；
  寬重構採 expand–migrate–contract。
- **哲學**：任務切片應交付行為，不應只列水平技術層；依賴圖比人為順序更能暴露
  可平行工作。
- **適用**：規格已穩定，需要多張可由新上下文獨立執行的 tickets。
- **例子**：`/to-tickets 將這份 OAuth spec 切成可逐張驗證的工作，標出 migration 阻擋關係。`
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/to-tickets/SKILL.md)

#### `implement`

- **邏輯**：讀取已確認的 ticket 或 spec，遵循 TDD，執行型別檢查與測試，要求 code
  review，最後提交目前分支。
- **哲學**：實作應是短而可驗證的執行階段；規劃與實作分開，避免做到一半重新發明需求。
- **適用**：範圍與驗收條件已明確，可以在一個上下文完成的工作。
- **例子**：`/implement custom-skills-e2t`。
- **注意**：上游流程包含 commit；若 repo 規則要求先取得授權，就必須停在驗證完成，
  不可自行提交。
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/implement/SKILL.md)

#### `triage`

- **邏輯**：先查證 issue claim 與重現條件，再只給一個類別與一個狀態；產生描述行為、
  驗收條件與 out-of-scope 的 agent brief。
- **哲學**：triage 是資訊品質門檻，不是 label 搬運；代理不應從模糊 issue 猜實作。
- **適用**：外部 issue、bug report 或 enhancement request 剛進入 tracker。
- **例子**：`/triage #431，先確認 CLI 目前是否真的會覆蓋未管理目錄。`
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/triage/SKILL.md)

#### `wayfinder`

- **邏輯**：把一個跨多 session 的模糊目標拆成決策地圖，每次只處理一個最能降低
  不確定性的決策點。
- **哲學**：大型未知工作不該假裝成線性交付計畫；先管理未知數，再建立 spec。
- **適用**：工作大到單一上下文裝不下，且還不能合理寫出 proposal。
- **例子**：`/wayfinder 規劃把整個技能分發系統改成多來源套件的決策地圖。`
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/wayfinder/SKILL.md)

#### `improve-codebase-architecture`

- **邏輯**：找出反覆造成修改成本的架構摩擦，生成暫存 HTML 報告與 before/after
  候選，再透過 grilling 決定是否採用；不直接重構。
- **哲學**：架構改善要由具體摩擦與預期收益驅動，不能趁功能任務順手擴張。
- **適用**：多次變更都卡在同一依賴、邊界或深度不足的模組。
- **例子**：`/improve-codebase-architecture 分析為什麼每新增一個 target 都要改五個地方。`
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/improve-codebase-architecture/SKILL.md)

### 工程流程：模型呼叫

#### `grilling`

- **邏輯**：一次只問一個問題，附帶建議；可查證的事先查，不在尚未理解前採取行動。
- **哲學**：高品質對齊來自窄而連續的決策，不是一次丟出整張問卷。
- **適用**：其他技能需要使用者做產品、範圍或權衡決策時。
- **例子**：`grill-with-docs` 發現同步衝突策略未定，交由 `grilling` 逐題確認。
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/productivity/grilling/SKILL.md)

#### `domain-modeling`

- **邏輯**：主動挑戰術語、用邊界情境壓力測試模型，將共同語言與重大決策即時寫回
  `CONTEXT.md` 或 ADR。
- **哲學**：模型不是名詞表；只有能解釋困難案例、也能改善程式命名的語言才有價值。
- **適用**：同一概念有多種稱呼、規則散落，或需求對話經常誤解。
- **例子**：釐清「安裝、分發、投影、同步」是否真的是四個不同生命週期動作。
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/domain-modeling/SKILL.md)

#### `prototype`

- **邏輯**：先判斷是邏輯還是 UI 問題，只為回答一個設計疑問建立可丟棄原型；保留
  決策，捨棄程式碼。
- **哲學**：高風險未知數應用最便宜的可執行證據處理，不要把原型偷渡成生產實作。
- **適用**：狀態模型、演算法方向或 UI 互動需要實際操作才能決定。
- **例子**：比較三種 CLI 衝突提示流程，確認使用者能否理解後刪除原型。
- **避免**：加入持久化、完整測試、打磨或直接合併 main。
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/prototype/SKILL.md)

#### `research`

- **邏輯**：以第一手來源為主，在背景蒐集可驗證證據，回報結論、來源與仍不確定之處。
- **哲學**：研究是降低決策風險，不是堆砌搜尋摘要；官方文件與原始碼優先。
- **適用**：API、工具行為、外部標準或上游實作需要查證。
- **例子**：確認最新版 `skills` CLI 的 `-g`、`-y` 與更新行為。
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/research/SKILL.md)

#### `codebase-design`

- **邏輯**：用 depth、leverage、locality 與 test seams 評估模組；重要介面至少提出兩種
  差異明顯的設計再比較。
- **哲學**：好的模組以小介面隱藏大量複雜度；抽象應在第二個真實 adapter 出現時成立，
  不是為假想未來預建。
- **適用**：新模組邊界、公共 API、adapter 或難以測試的結構。
- **例子**：比較「每個 target 一個 adapter」與「單一條件分支服務」的深度與測試面。
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/codebase-design/SKILL.md)

#### `tdd`

- **邏輯**：先對齊公開 seam，逐一寫出會因缺少行為而失敗的測試，再寫最少實作使其
  通過；完成切片後才重構。
- **哲學**：紅燈證明測試真的觀察到行為；小垂直切片讓回饋迴圈保持可信。
- **適用**：有可自動驗證行為的功能、修正或重構。
- **例子**：先寫「移除只刪指定技能、不碰其他來源」的失敗測試，再改移除邏輯。
- **注意**：只 mock 真正系統邊界，不 mock 自己的內部函式。
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/tdd/SKILL.md)

#### `diagnosing-bugs`

- **邏輯**：先建立最短、可反覆失敗的重現；列 3 至 5 個可證偽假設，以觀測或實驗
  排除，最後留下回歸測試。
- **哲學**：沒有可觀測回饋就只是猜測；修根因比為單一路徑加補丁更便宜。
- **適用**：錯誤原因未知、行為間歇、現有測試無法重現。
- **例子**：先證明投影目錄只在第二次 clone 殘留，再追蹤 manifest 與清理分支。
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/diagnosing-bugs/SKILL.md)

#### `code-review`

- **邏輯**：以 merge-base 的三點 diff 為範圍，分開審查工程標準與 spec 符合度，修正後
  重跑直到沒有新問題。
- **哲學**：review 是固定點迴圈，不是一次性意見清單；標準問題和需求偏差要分開看。
- **適用**：完成一個可交付切片、PR 或高風險文件變更後。
- **例子**：分別檢查「移除是否精確」與「是否滿足手動安裝需求」，修正後再審。
- **注意**：上游會使用平行子代理；執行環境或 repo 規則不允許時，改成同一代理依序審查。
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/code-review/SKILL.md)

#### `resolving-merge-conflicts`

- **邏輯**：讀取雙方 commits、PR、issue 與測試，重建各自意圖，逐檔整合並完成
  merge/rebase，不以 abort 當成解法。
- **哲學**：衝突是兩段歷史意圖的合併問題，不是選 ours/theirs 的文字問題。
- **適用**：已進入 merge 或 rebase，且需要保留雙方有效行為。
- **例子**：一邊移除來源、一邊新增 source schema 欄位時，保留新 schema 但不復活已移除來源。
- **注意**：任何 push、reset 或其他危險 Git 動作仍受 repo 權限規則約束。
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/resolving-merge-conflicts/SKILL.md)

### 生產力：使用者呼叫

#### `grill-me`

- **邏輯**：針對非程式工作一次問一個決策問題，逐步消除模糊處。
- **哲學**：先形成共享理解，再生成內容或採取行動。
- **適用**：文章、課程、營運流程、研究方向等不需要 repo 文件的需求。
- **例子**：`/grill-me 幫我把「改善 onboarding」問成可驗收的計畫。`
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/productivity/grill-me/SKILL.md)

#### `handoff`

- **邏輯**：在目前上下文接近分岔或資訊飽和時，整理目標、已知事實、決策、未決問題與
  下一步，交給新上下文。
- **哲學**：不要等上下文失真才摘要；在模型仍處於高品質推理區間時主動切換。
- **適用**：研究轉實作、原型往返、長 session 即將切新工作。
- **例子**：`/handoff 把原型已排除的兩個方案與剩餘決策交給下一個 session。`
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/productivity/handoff/SKILL.md)

#### `teach`

- **邏輯**：建立專用學習 workspace，以高可信來源、檢索練習、間隔重複與交錯練習推進。
- **哲學**：把「看過」與「能無提示取回並運用」分開衡量；學習進度以 fluency 為準。
- **適用**：需要長期掌握一門技術或概念，而不是只解眼前問題。
- **例子**：`/teach 幫我建立 DDD context mapping 的四週練習。`
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/productivity/teach/SKILL.md)

#### `writing-great-skills`

- **邏輯**：從觸發、資訊層級、 leading words、必要參考到 no-op 行為，設計可預測技能；
  持續刪除不影響行為的文字。
- **哲學**：技能品質取決於可預測行為，不取決於篇幅；同時控制模型上下文與人的認知負擔。
- **適用**：建立、重寫或審查 `SKILL.md`。
- **例子**：`/writing-great-skills 檢查這個技能是否把觸發條件、流程與參考資料混在一起。`
- **來源**：[SKILL.md](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/productivity/writing-great-skills/SKILL.md)

## 同一命令會安裝、但未正式發布的 19 個技能

下列技能存在於上游 `skills/`，所以 `-g -y` 會一併安裝；但它們不在目前 plugin
manifest。使用前要把目錄狀態視為成熟度警告，不要假設介面或行為穩定。

### `deprecated/`：已棄用

| 技能 | 呼叫 | 使用邏輯與哲學 | 情境例子與替代方案 |
|------|------|----------------|--------------------|
| [`design-an-interface`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/deprecated/design-an-interface/SKILL.md) | 模型 | 平行提出至少三個差異明顯的介面，只比較深度與取捨，不實作。 | 例：比較三種 storage API。新工作改用 `codebase-design` 的 design-it-twice。 |
| [`qa`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/deprecated/qa/SKILL.md) | 模型 | 以真實使用行為逐步 QA，必須重現，再產生不含檔案路徑的 GitHub issues。 | 例：操作匯入流程並為每個可重現問題開票。僅適合保留舊流程相容。 |
| [`request-refactor-plan`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/deprecated/request-refactor-plan/SKILL.md) | 模型 | 長訪談、探索程式碼、比較方案，產生可用小型綠燈 commits 推進的 refactor issue。 | 例：規劃拆解 2,000 行 service。新工作優先用 grilling、`to-spec` 與 `to-tickets`。 |
| [`ubiquitous-language`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/deprecated/ubiquitous-language/SKILL.md) | 使用者 | 從對話整理具立場的術語與歧義，寫入 `UBIQUITOUS_LANGUAGE.md`。 | 例：統一「會員／帳戶／身份」。新工作改用 `domain-modeling` 與 `CONTEXT.md`。 |

### `in-progress/`：仍在試驗

| 技能 | 呼叫 | 使用邏輯與哲學 | 情境例子 |
|------|------|----------------|----------|
| [`batch-grill-me`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/in-progress/batch-grill-me/SKILL.md) | 使用者 | 每輪一次詢問整個決策 frontier，事實交給代理查；以批次換取較少往返。 | 非同步時一次回答五個互不相依的產品決策；若要精準收斂，仍用單題 `grilling`。 |
| [`claude-handoff`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/in-progress/claude-handoff/SKILL.md) | 使用者 | 透過 `claude --bg --name` 啟動命名背景代理，直接交棒，不只生成摘要文件。 | 把已收斂研究交給新的 Claude 背景 session；只適用有該 CLI 能力的環境。 |
| [`loop-me`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/in-progress/loop-me/SKILL.md) | 使用者 | 透過 grilling 找出事件、迴圈、檢查點與 push-right 自動化，寫成 `workflows/*.md`。 | 將每週 dependency audit 建成可重複、必要時停下人工決策的 loop。 |
| [`setup-ts-deep-modules`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/in-progress/setup-ts-deep-modules/SKILL.md) | 使用者 | 用 dependency-cruiser 與 package root entry points 強制深模組；以 pass-fail-pass 證明規則有效。 | 阻止 TypeScript 消費者 deep import 到 package 私有子目錄。 |
| [`to-questionnaire`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/in-progress/to-questionnaire/SKILL.md) | 使用者 | 只問收件者與要取得的資訊，再產生適合非同步回覆的 discovery questionnaire。 | 寫給領域專家的帳務例外問卷，不在即時會議逐題問。 |
| [`wizard`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/in-progress/wizard/SKILL.md) | 使用者 | 把人工程序與範本變成互動 Bash wizard，區分 URL、普通值與 secrets，至少以 `bash -n` 驗證。 | 將新客戶環境設定流程變成安全的互動腳本；不代替端到端驗證。 |
| [`writing-fragments`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/in-progress/writing-fragments/SKILL.md) | 使用者 | 探索期只追加原始片段，不急著建立結構。 | 收集文章的例子、句子與問題，尚不排序。 |
| [`writing-beats`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/in-progress/writing-beats/SKILL.md) | 使用者 | 將固定素材堆轉成讀者旅程的 beats，逐一讓人選擇，追蹤 grounding 依賴。 | 把已完成訪談素材排成教學文章的認知節奏。 |
| [`writing-shape`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/in-progress/writing-shape/SKILL.md) | 使用者 | 在素材不再增加後，逐段決定形狀、前置知識與 grounding，刻意選擇格式。 | 把固定研究筆記組成有依賴順序的章節。 |

### `misc/`：特定工具或專案

| 技能 | 呼叫 | 使用邏輯與哲學 | 情境例子與限制 |
|------|------|----------------|----------------|
| [`git-guardrails-claude-code`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/misc/git-guardrails-claude-code/SKILL.md) | 模型 | 安裝 Claude Code hook，阻擋 push、`reset --hard`、`clean`、刪分支、`checkout .` 等高風險 Git 命令。 | 詢問要專案或全域保護後再安裝；不適用不支援 Claude hooks 的代理。 |
| [`migrate-to-shoehorn`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/misc/migrate-to-shoehorn/SKILL.md) | 模型 | 只在測試碼把 TypeScript assertions 換成 `fromPartial`／`fromAny`，不碰 production。 | 遷移特定測試工具；不是通用 TypeScript 重構。 |
| [`scaffold-exercises`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/misc/scaffold-exercises/SKILL.md) | 模型 | 依 AI Hero 課程 repo 的固定 convention 與 linter 建立 exercises。 | 只適合相同課程骨架；一般 repo 不應自動呼叫。 |
| [`setup-pre-commit`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/misc/setup-pre-commit/SKILL.md) | 模型 | 偵測 package manager，組合 Husky、lint-staged、Prettier、typecheck 與 tests。 | 為 JS/TS repo 建 pre-commit；先確認現有 hooks，避免覆蓋團隊流程。 |

### `personal/`：作者個人環境

| 技能 | 呼叫 | 使用邏輯與哲學 | 情境例子與限制 |
|------|------|----------------|----------------|
| [`edit-article`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/personal/edit-article/SKILL.md) | 使用者 | 依章節依賴編修文章，每段重寫限制 240 字元。 | 適合作者自己的短段落節奏；一般文件應先確認格式需求。 |
| [`obsidian-vault`](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/personal/obsidian-vault/SKILL.md) | 模型 | 依作者的 flat-root、Title Case 與 wikilinks 規則操作固定 vault。 | 原始路徑硬編碼為 `/mnt/d/Obsidian Vault/AI Research/`，其他機器不可直接使用。 |

## 與本 repo 的工具如何共存

| 上游技能行為 | 本 repo 的處理方式 |
|--------------|--------------------|
| `setup-matt-pocock-skills` 想建立 tracker 規則 | 保留 Beads 為 canonical tracker；既有 `docs/agents/issue-tracker.md` 優先 |
| `to-spec`、`to-tickets` 產生規格與 tickets | 正式變更仍以 OpenSpec artifacts 與 Beads 狀態為準 |
| `implement` 預設在結尾 commit | 未取得本 repo 明確 commit 授權時，只能完成修改與驗證 |
| `code-review` 想使用平行子代理 | 只有目前環境與指令允許時才能使用；否則依序審查 |
| `resolving-merge-conflicts` 要完成 merge/rebase | 不得因此越過 Git push、破壞性命令或工作樹保護規則 |
| 上游文件與本 repo 規則衝突 | 使用者當前指令與 repo 的 `AGENTS.md` 優先 |

`mattpocock/skills` 可以作為選用的前置對齊與工作切片工具，但不再是
`DEVELOPMENT-WORKFLOW.md` 的必要階段。已經有清楚 OpenSpec artifacts 的工作，
直接走 OpenSpec；單一小改動則直接以 Beads 追蹤、實作與驗證。

## 常見問題

### 為什麼安裝命令看到 41 個，但 README 主要只談部分技能？

`skills` CLI 會遞迴發現所有含 `SKILL.md` 的目錄；上游 repo 同時保存正式技能、
試驗中技能、已棄用技能與作者個人工具。plugin manifest 才是目前正式發布集合。

### 想只安裝正式的 22 個怎麼辦？

不要使用 `-y`。執行互動式安裝並只選正式集合：

```bash
npx skills@latest add mattpocock/skills -g
```

本 repo 的標準手動流程仍採使用者指定的 `-g -y`，因此指南明確標示其餘 19 個技能
的成熟度與限制。

### 更新後技能名稱或數量改了怎麼辦？

重新執行：

```bash
npx skills@latest add mattpocock/skills --list
```

再比對上游 `README.md`、`.claude-plugin/plugin.json` 與各 `SKILL.md`。不要只修改
技能數量；同時檢查呼叫類型、交棒關係、副作用與前置條件。

### 技能沒有自動觸發怎麼辦？

先確認它是否為使用者呼叫技能。這類技能本來就必須由人輸入名稱。若是模型呼叫技能，
重新啟動代理工作階段，並檢查全域技能是否安裝到該代理實際讀取的目錄。

### 可以修改安裝後的技能嗎？

`skills` CLI 採複製／連結的開放技能模式，技術上可修改；但全域更新可能覆蓋變更。
若要長期維護自己的版本，應 fork 上游或安裝明確選定的技能，不要在本 repo 重新建立
一套未追蹤的 `mp-*` 改寫層。

## 維護檢查清單

- [ ] 執行 `npx skills@latest add mattpocock/skills --list`，記錄目前技能數量。
- [ ] 查看上游 `README.md` 與 `.claude-plugin/plugin.json` 的正式集合。
- [ ] 檢查每個技能的使用者／模型呼叫設定是否改變。
- [ ] 檢查 `implement`、Git、tracker 與文件寫入行為是否新增副作用。
- [ ] 更新本指南的 commit 基準、成熟度、範例與替代關係。
- [ ] 重新啟動實際使用的代理，確認技能能被發現。

## 主要來源

- [上游 README](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/README.md)
- [呼叫模型說明](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/.agents/invocation.md)
- [Claude plugin manifest](https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/.claude-plugin/plugin.json)
- [完整 skills 目錄](https://github.com/mattpocock/skills/tree/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills)
- [`skills` CLI 官方儲存庫](https://github.com/vercel-labs/skills)
