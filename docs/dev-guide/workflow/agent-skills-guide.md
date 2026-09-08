---
title: agent-skills 使用指南
type: guide
date: 2026-09-08
author: ai-dev contributors
status: active
---

# agent-skills 使用指南

本指南介紹 Addy Osmani 的 `addyosmani/agent-skills`：有哪些技能、何時值得使用、
會產生什麼結果，以及如何單獨採用或搭配其他開發流程。想先比較各套工具，請從
[開發流程選擇指南](DEVELOPMENT-WORKFLOW.md) 開始。

你可以只取用一個技能，也可以選擇它的完整開發流程。以下介紹上游的實際設計與
使用取捨，不要求每個專案採取相同組合。

本文於 2026-09-08 核對上游 commit
[`48cb116`](https://github.com/addyosmani/agent-skills/tree/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a)。
該版本包含 **25 個技能、9 個 Claude Code 命令**，外掛設定檔記錄的版本為
`0.6.9`。技能數以目錄實際內容計算，不採用 README 中「All 24 Skills」的舊標題。
本文查核來源與檔案結構，沒有在所有支援平台實測安裝及完整流程。

## 這套工具解決什麼問題

agent-skills 將軟體開發生命週期分成需求、規劃、實作、驗證、審查與發布。
每個技能提供一套工作方法，通常包含適用條件、操作步驟、容易跳過的檢查及完成驗證。

它的覆蓋範圍比「幫 AI 寫程式」更廣：需求訪談、API 設計、來源查證、品質門檻、
監控、遷移與發布準備都有對應技能。完整流程有人工確認點；單一技能也可能建立
文件、修改設定或派出審查代理，使用前應先看它的產出與操作範圍。

這些 Markdown 指引能幫助 Agent 維持工作紀律，但不是強制執行的權限系統。
實際效果仍取決於模型、可用工具、專案設定及驗證。來源見
[上游總覽][as-readme]與[技能入口][as-using]。

## 先分清技能、命令與安裝方式

| 組成 | 用途 | 選用時要確認 |
| --- | --- | --- |
| `skills/<name>/SKILL.md` | 定義一個工程工作方法 | 技能是否可見、是否需要其他技能或工具 |
| `.claude/commands/` | 把技能串成 `/spec`、`/build` 等操作入口 | 所用平台是否載入這些命令，名稱是否與其他來源重複 |
| `agents/` | 提供專門的審查角色 | 平台是否載入角色，能否建立獨立上下文 |
| `references/` | 共用完成條件、審查與安全檢查表 | 安裝後相對路徑是否仍可讀 |
| `hooks/` | 在工作階段開始時載入技能入口 | 安裝方式是否啟用這個自動行為 |
| `evals/` | 檢查技能描述、觸發與執行結果 | 評測的是哪個版本、哪個平台與哪一層行為 |

上游的工作階段啟動腳本會載入 `using-agent-skills`。若只想使用幾個技能，可以先
選單獨安裝；若想使用完整命令與代理角色，再依所用平台選整套整合方式。
同時安裝多套外掛時，應檢查各自的啟動腳本，不要只比較技能名稱。
來源：[啟動腳本][as-hook]。

想知道同一階段該選本套、Matt、Superpowers 還是 OpenSpec，請看
[技能詳細比較矩陣](SKILL-COMPARISON-GUIDE.md)。下表保留本套技能查找用途。

## 25 個技能：按目前工作查找

表內連結均指向本文核對的上游版本。這是能力分類，不是必須依序完成的階段表。

### 需求與規劃

| 技能 | 何時考慮 | 主要做法與結果 |
| --- | --- | --- |
| [using-agent-skills][as-using] | 想讓這套工具協助選擇技能 | 依工作階段選技能，並載入共同工作原則；本身是整套流程入口 |
| [interview-me][as-interview] | 還說不清服務誰、為什麼做或如何算成功 | 一次問一題並附猜測，最後產出經確認的意圖摘要；保存文件另行確認 |
| [idea-refine][as-idea] | 已有想法，但想比較不同解法 | 先擴展方向，再收斂最小可行範圍、假設與不做項目；可保存概念摘要 |
| [spec-driven-development][as-spec] | 需要把需求寫成可實作的規格 | 釐清目標、指令、結構、風格、測試與界線；多能力需求先拆解，再經規格、計畫、任務與實作確認 |
| [constraint-driven-development][as-constraints] | 品質門檻沒有寫清楚，或 Agent 常削弱檢查 | 先讀現況，再決定門檻、例外與執行方式；建立 `CONSTRAINTS.md` 並連到實際檢查工具 |
| [planning-and-task-breakdown][as-planning] | 有需求或規格，尚未拆成可執行工作 | 依依賴關係切成可驗證的完整功能片段，寫明驗收與檢查點；可接專案既有任務系統 |

### 實作與設計

| 技能 | 何時考慮 | 主要做法與結果 |
| --- | --- | --- |
| [context-engineering][as-context] | 新工作階段、切換任務，或 Agent 開始忽略脈絡 | 整理相關程式、規則、版本與工作摘要，減少無關資訊干擾 |
| [source-driven-development][as-source] | 框架、函式庫或 API 用法可能因版本不同而改變 | 確認版本，讀對應官方文件，再實作並交代來源；避免只靠模型記憶 |
| [incremental-implementation][as-incremental] | 變更太大，難以一次實作與驗收 | 每次完成一小段可運作行為，測試、檢查並保留可回復的變更 |
| [api-and-interface-design][as-api] | 設計 API、模組邊界或型別契約 | 明確定義輸入輸出、錯誤與相容性，減少呼叫端猜測 |
| [frontend-ui-engineering][as-frontend] | 建立頁面、元件或互動介面 | 同時處理版面、狀態、響應式顯示與無障礙需求，驗證實際互動 |

### 驗證、除錯與審查

| 技能 | 何時考慮 | 主要做法與結果 |
| --- | --- | --- |
| [test-driven-development][as-tdd] | 新增行為或修正可重現的 bug | 先看見測試失敗，再寫最小修正，最後整理程式並維持測試通過 |
| [browser-testing-with-devtools][as-browser] | 問題需要瀏覽器中的證據 | 透過 Chrome DevTools MCP 檢查頁面、主控台、網路與效能；需要先有對應工具 |
| [debugging-and-error-recovery][as-debug] | 測試、建置或執行結果不符預期 | 重現、追查根因、縮小假設，再修復並確認沒有回歸 |
| [doubt-driven-development][as-doubt] | 重要決策尚有不確定性，想找出反例 | 把成果與契約交給全新上下文的審查者，再逐項判斷問題是否成立 |
| [code-review-and-quality][as-review] | 合併前想全面檢查變更 | 從正確性、可讀性、架構、安全與效能審查，回報位置、嚴重程度及建議 |
| [code-simplification][as-simplify] | 行為已正確，但程式難讀或不易維護 | 先理解呼叫與測試，再逐步簡化；保留原行為並重新驗證 |
| [security-and-hardening][as-security] | 涉及不可信輸入、驗證、資料或第三方依賴 | 辨識威脅、檢查輸入與權限、分析依賴風險，再驗證防護 |
| [performance-optimization][as-performance] | 有速度、負載或資源使用問題 | 先量測瓶頸，再修改並比較前後數據；涵蓋前端、後端與查詢 |

### 交付與維護

| 技能 | 何時考慮 | 主要做法與結果 |
| --- | --- | --- |
| [git-workflow-and-versioning][as-git] | 需要整理分支、提交、PR 或版本發布 | 建立可理解的變更紀錄與版本策略；操作仍依專案 Git 授權 |
| [ci-cd-and-automation][as-ci] | 想自動執行測試、建置與部署檢查 | 將品質檢查放進持續整合與交付流程，處理失敗及部署策略 |
| [observability-and-instrumentation][as-observe] | 功能上線後需要知道是否正常 | 設計記錄、指標、追蹤與告警，使問題可定位、結果可量測 |
| [documentation-and-adrs][as-docs] | 需要保存 API 說明或架構決策理由 | 更新面向讀者的文件，並以架構決策紀錄保存選擇、理由與取捨 |
| [deprecation-and-migration][as-migration] | 淘汰舊 API、系統或資料結構 | 規劃相容期、使用者轉移、驗證與回復；資料結構可採先擴充再移除的方式 |
| [shipping-and-launch][as-ship-skill] | 正在準備發布或分階段推出 | 整理品質、部署條件、監控、成功標準與回復方法，形成發布準備結果 |

## 幾個值得先理解的設計差異

### 訪談、探索方案與規格各有不同產出

`interview-me` 問的是「你實際想要什麼」，`idea-refine` 探索「有哪些值得採用的
解法」，`spec-driven-development` 則把已選方向寫成規格。已有明確需求時，不必
從訪談重新開始；已有方案時，也不需要為了流程完整而重新發散。

`interview-me` 的 95% 是模型自評的理解程度，不是統計可信度。原文把 4～6 個問題
當成成本說明，沒有設定最多只能問這麼多題；它也要求對部分模糊同意再次確認。
因此，選它是選擇一種互動方式，不能保證訪談一定較短。相較之下，`idea-refine`
的初始釐清明定 3～5 題，再比較多個方向。來源：[訪談][as-interview]、[想法探索][as-idea]。

### 品質門檻與單次審查不同

`constraint-driven-development` 建立之後每次工作都可使用的品質基準；
`code-review-and-quality` 審查這一次的變更。前者可能安裝檢查工具、加入執行命令
並修改 Agent 入口文件，不能把「設定品質門檻」理解成只產出一張建議表。

已經有品質規則的專案，可以先比較現有規則與這套方法的缺口。數字應有實測或
明確理由，不能把上游建議值直接當成所有專案的標準。來源：[品質門檻][as-constraints]。

### 決策反證需要額外審查成本

`doubt-driven-development` 在方向還能調整時找反例。審查輸入是成果與契約，
不是作者的完整推理；主代理仍要判斷每個發現，不能把審查者的意見直接當結論。

上游最多進行三輪，互動式流程每輪都會詢問是否加做跨模型審查。這會增加等待、
模型用量與工具需求。它適合值得額外查驗的決策，不適合把每次命名或格式修改都
送進審查。自己重新檢查不能宣稱為全新上下文審查。來源：[決策反證][as-doubt]。

### 明確檢查不等於工具已強制執行

技能常列出容易省略的步驟與合理化說法，提醒 Agent 不要把「應該可以」當成證據。
共用的完成條件也會要求測試、回歸與執行結果。但仍要看實際命令、結果及未完成項目，
不能只因 Agent 說「遵循技能」就判定成功。來源：[共用完成條件][as-done]。

## 命令怎麼用，會做哪些事

下表以 `.claude/commands/` 的命令定義為準。只有平台實際載入這些命令時，才可
照名稱呼叫；只安裝技能時，請從工具的技能選單選取完整名稱，或直接在對話中指名。

| 命令 | 主要用途 | 預期產出或操作 |
| --- | --- | --- |
| `/spec` | 建立規格 | 上游預設寫入根目錄 `SPEC.md`，交給使用者確認 |
| `/plan` | 拆解工作 | 命令預設列出 `tasks/plan.md` 與 `tasks/todo.md`；技能另支援專案任務系統 |
| `/build` | 完成下一個任務 | 實作、測試、建置、提交並更新任務，完成一個後停止 |
| `/build auto` | 依批准計畫連續實作 | 處理全部待辦任務，每個任務仍有驗證與提交；不確定或高風險步驟會停下 |
| `/test` | 測試驅動開發 | 不只是執行測試，也可能新增測試、修改實作與整理程式 |
| `/constraints` | 設定品質門檻 | 建立品質文件、接入工具及檢查命令；另有 `check`、`guard`、`ratchet` 子命令 |
| `/review` | 五面向審查 | 回報具體問題、位置、嚴重程度與修正建議 |
| `/webperf` | 網頁效能審查 | 交給效能角色檢查；有量測資料時深入分析，否則標示可能影響 |
| `/code-simplify` | 簡化程式 | 修改指定範圍並驗證行為不變 |
| `/ship` | 發布前整合審查 | 彙整專門角色的報告，產出 GO／NO-GO 與回復方案 |

來源：[命令目錄][as-commands]。`/build auto` 是 `/build` 的模式，所以表中有十種
用法，但命令檔共有九個。`/constraints check` 會執行現有檢查，`guard` 檢查門檻是否
被削弱，`ratchet` 會把當前量測值記成往後的基準，三者的寫入範圍不同。

### 選擇單步或連續實作

想逐段檢視成果，可選 `/build`。已有規格、計畫與驗收，且希望減少任務間的人工
接續，可考慮 `/build auto`。後者省掉的是任務間的等待，不是每個任務的測試。

這個版本的 `/build auto` 只查找 `SPEC.md`、`docs/SPEC.md` 或 `spec/` 下的規格，
不會把任意 README 當成規格。它也檢查未提交變更，避免每個任務的提交夾帶其他工作。
因此，已有 OpenSpec change 時不能假定它能直接讀取並接手，更不應為了讓命令通過
而默默複製第二份規格。先確認工件對應方式，或留在原本的執行入口。
來源：[build 命令][as-build]。

### 發布技能與發布命令不同

`shipping-and-launch` 提供發布準備方法；`/ship` 命令另外安排程式、安全與測試
三種角色審查，再由主代理彙整。它的多代理執行不是單一技能檔自帶的能力。

沒有多代理工具時，上游另描述依序套用角色提示的替代方式；這只能記成依序審查，
不能宣稱已做平行或獨立上下文審查。GO 表示審查判斷，不表示已部署，也不取代
專案的部署授權。來源：[ship 命令][as-ship-command]。

## 安裝與確認可用範圍

本文介紹的手動安裝不會自動把來源加入 ai-dev 的管理清單。要由 ai-dev 統一管理
更新，是另一項設定選擇。不要同時讓兩種安裝方式覆寫相同位置。

### 只想選幾個技能

需要 Node.js 與 `npx`。先列出可發現內容，不安裝技能：

```bash
npx skills add addyosmani/agent-skills --list
```

例如，只安裝來源查證技能到目前專案的 Codex 技能位置：

```bash
npx skills add addyosmani/agent-skills --skill source-driven-development -a codex
```

這些是上游提供的 Skills CLI 用法，本輪沒有執行安裝。`npx` 本身可能下載 CLI
並建立快取。專案安裝以目前目錄為目標；全域安裝另加 `-g`，會影響該使用者的其他
專案。先確認目標再執行，保留互動選擇以便檢視實際安裝項目。

單一技能安裝只複製 `skills/<name>/`，不帶走 repo 根目錄的 `references/`。
需要共用檢查表時，應保留完整來源或依上游方式補齊參考資料與連結，再確認路徑可讀。
只看見技能名稱不代表命令、角色與參考文件都已可用。
來源：[上游安裝說明][as-readme]、[Skills CLI 用法](../ai-tools/SKILLS-CLI.md)。

### 想使用完整整合

Claude Code 的上游安裝入口是：

```text
/plugin marketplace add addyosmani/agent-skills
/plugin install agent-skills@addy-agent-skills
```

完整整合會帶入更多命令、角色與啟動行為，適合想採用這套生命週期的使用者。
Codex、Gemini CLI、OpenCode 等平台有各自的載入方式，請從固定版本的
[平台安裝說明][as-readme]前往相應指南；不要假設 Claude Code 的 `/ship` 命令、
工具名稱與角色解析方式在其他平台相同。

### 安裝後怎麼確認

1. 從所用工具列出技能，確認需要的名稱與來源；必要時重開工作階段。
2. 若使用命令或角色，分別確認它們可見，並檢查是否有同名項目。
3. 讀取所選技能的相對參考文件，確認檢查表與相依工具齊全。
4. 用低風險的小任務確認實際行為，例如只對指定變更提出審查意見。

更新前記錄來源版本與本地修改；更新後重新確認上述項目。移除時使用當初的安裝工具
精確選取來源或技能，不刪整個技能目錄。安裝或移除技能不會自動回復它曾在專案中
建立的規格、檢查設定或程式變更。Skills CLI 的列出、更新與移除方式見
[命令指南](../ai-tools/SKILLS-CLI.md)。

## 如何單獨使用或搭配其他流程

### 只補一項能力

已有工作方法時，先挑一個明確缺口。例如：

> 使用 agent-skills 的 source-driven-development，先確認這個專案的函式庫版本，
> 再查官方文件判斷這個用法是否相容。先回報證據與建議。

這不要求先建立規格或使用完整生命週期。選技能時說明來源、目標與預期成果，比只說
「幫我 review」更能避免同名技能混淆。

### 使用完整 agent-skills 流程

新功能需要從需求走到發布準備，而且你接受這套人工確認與產出方式時，可以選擇：

```text
必要時訪談或探索方案
    → /spec → /plan → /build（逐個任務）
    → /review → /ship
```

測試已包含在 `/build` 的迴圈中；需要單獨處理測試或 bug 時可選 `/test`。
若已有適用規格，也可選 `/build auto` 取代逐個任務接續。監控、文件與安全等技能
依功能需要穿插使用，不必全部等到最後才補。

### 搭配 Matt、Superpowers 或 OpenSpec

| 已有做法 | 可以補的能力 | 先確認什麼 |
| --- | --- | --- |
| Matt 的需求訪談與工程技能 | 品質門檻、來源查證、監控或遷移 | 同一階段是否已經有足夠方法，避免重複訪談或審查 |
| Superpowers 的計畫與實作 | 重要決策反證、領域相關檢查 | 既有審查是否已涵蓋，額外代理是否值得 |
| OpenSpec 的正式變更 | 來源查證、監控、遷移與發布準備 | 以原 change 為依據；命令是否支援它的路徑與任務格式 |
| 專案現有 CI 與品質標準 | 品質門檻方法、差異檢查 | 沿用已有檢查和數字，不另建矛盾標準 |

上游比較文章建議可以跨套取用技能，但避免同時讓多個總入口主導同一項工作。
實務上可以明說「沿用目前計畫，只加入來源查證」，或「需求討論到此結束，接著使用
OpenSpec 保存規格」。來源：[上游比較][as-comparison]。

更完整的選擇與組合範例見[開發流程選擇指南](DEVELOPMENT-WORKFLOW.md)。

## 評測能證明什麼

| 層次 | 上游檢查方式 | 能支持的判斷與限制 |
| --- | --- | --- |
| 結構 | 檢查 frontmatter、名稱、必要章節及命令對應 | 能找出格式與結構缺漏，不能證明內容正確 |
| 觸發與路由 | 依描述詞彙計算排名與相似度 | 能找出描述過廣或缺少關鍵詞；不是模型真實選擇的語意測試 |
| 行為 | 執行 Agent，依完整紀錄評分 | 能檢查案例中是否符合預期；會消耗模型用量，也依賴工具與評分品質 |

第二層使用詞彙近似法，不能把通過它寫成「所有模型都會選對技能」。第三層的上游
執行器使用 Claude；在其他平台、其他提示規則或混合多套技能後，仍要另做對應驗證。
上游測試結果也不能直接當成某個專案的品質保證。來源：[評測說明][as-evals]。

## 從哪裡繼續

- 想比較不同方法：[開發流程選擇指南](DEVELOPMENT-WORKFLOW.md)。
- 已選 OpenSpec：[OpenSpec 操作指南](OPENSPEC-GUIDE.md)。
- 想了解其他技能組合：[Matt 指南](MATTPOCOCK-SKILLS-GUIDE.md)、[Superpowers 指南](SUPERPOWERS-GUIDE.md)。
- 要讓 Agent 理解使用者的選擇：[Agent 工作流指引](WORKFLOW-ROUTING.md)。

維護本文時，先重新核對上游 commit、技能目錄、命令、角色與共用參考文件，再更新
數量及操作說明。若只有安裝技能，不把整套外掛能力標成已可用。

[as-readme]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/README.md
[as-using]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/using-agent-skills/SKILL.md
[as-interview]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/interview-me/SKILL.md
[as-idea]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/idea-refine/SKILL.md
[as-spec]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/spec-driven-development/SKILL.md
[as-constraints]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/constraint-driven-development/SKILL.md
[as-planning]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/planning-and-task-breakdown/SKILL.md
[as-context]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/context-engineering/SKILL.md
[as-source]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/source-driven-development/SKILL.md
[as-incremental]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/incremental-implementation/SKILL.md
[as-api]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/api-and-interface-design/SKILL.md
[as-frontend]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/frontend-ui-engineering/SKILL.md
[as-tdd]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/test-driven-development/SKILL.md
[as-browser]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/browser-testing-with-devtools/SKILL.md
[as-debug]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/debugging-and-error-recovery/SKILL.md
[as-doubt]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/doubt-driven-development/SKILL.md
[as-review]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/code-review-and-quality/SKILL.md
[as-simplify]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/code-simplification/SKILL.md
[as-security]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/security-and-hardening/SKILL.md
[as-performance]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/performance-optimization/SKILL.md
[as-git]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/git-workflow-and-versioning/SKILL.md
[as-ci]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/ci-cd-and-automation/SKILL.md
[as-observe]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/observability-and-instrumentation/SKILL.md
[as-docs]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/documentation-and-adrs/SKILL.md
[as-migration]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/deprecation-and-migration/SKILL.md
[as-ship-skill]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/shipping-and-launch/SKILL.md
[as-commands]: https://github.com/addyosmani/agent-skills/tree/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/.claude/commands
[as-build]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/.claude/commands/build.md
[as-ship-command]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/.claude/commands/ship.md
[as-hook]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/hooks/session-start.sh
[as-done]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/references/definition-of-done.md
[as-comparison]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/docs/comparison.md
[as-evals]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/evals/README.md
