---
title: 開發流程選擇指南
type: guide
date: 2026-09-08
author: ai-dev contributors
status: active
---

# 開發流程選擇指南

這份指南幫你依手上的工作，選擇直接與 AI 協作、單一技能，或一套完整開發流程。
先看各套方法的差異，再用情境矩陣縮小選項；選定後，前往相應指南操作。
同一階段有多個合適技能時，接著看 [按開發階段比較與選擇技能](SKILL-COMPARISON-GUIDE.md)，
逐項比較輸入、產出、做法、選用理由與改選條件。

矩陣提供建議與取捨，沒有規定「小功能一定用哪套」或「所有階段都必須跑」。
你可以指定方法，也可以請 AI 先查證現況、提出推薦及理由，再一起決定。
若要找原本的 OpenSpec 逐步教學，請看 [OpenSpec 操作指南](OPENSPEC-GUIDE.md)。

## 先看你希望獲得什麼

選擇流程時，除了工作大小，更有用的是看：需求清楚了嗎、要留下什麼成果、想參與
多少決策，以及目前缺哪一項能力。改動檔案數少，不代表一定容易或低風險。

| 方法 | 主要價值 | 常見產出 | 你的參與方式 | 值得先考慮的成本 |
| --- | --- | --- | --- | --- |
| 直接對話或工具內建規劃 | 快速查證、處理明確工作 | 回答、變更、驗證結果或簡短計畫 | 指定目標，討論必要的方向與例外 | 跨工作階段的紀錄與交接需另外安排 |
| Matt Pocock skills | 可組合的需求、設計與日常工程技能 | 需求共識、規格、任務、程式或審查結果，依技能而定 | 選技能；需求與設計類通常需要較多互動 | 技能有不同呼叫方式；完整流程可能涉及任務系統與文件設定 |
| Superpowers | 連貫的設計、計畫、實作與審查方法 | 設計文件、細分計畫、程式與驗證 | 先確認設計，再依所選執行方式檢視成果 | 完整流程有較多前置規劃與審查，需確認代理及工作區能力 |
| OpenSpec | 保存可追溯、可演進的需求與變更 | proposal、specs、design、tasks 與歸檔紀錄 | 審閱規格、確認變更，接續實作與驗證 | 要維護規格與實作的一致性；它不替代專案測試與部署程序 |
| agent-skills | 按生命週期提供工程方法與品質檢查 | 意圖摘要、規格、品質門檻、程式、審查或發布準備 | 可挑單一技能，也可逐階段確認或選連續實作 | 某些技能會設定工具、建立文件或安排額外審查；平台支援要分別確認 |

這些是選擇角度，不是各套工具的能力上限。例如 Matt 也能產生規格，Superpowers
也有驗證，agent-skills 也能執行完整開發。不要把它們固定分配成只能負責某一階段。

表格是根據各套指南整理的編輯建議，不是速度或品質排名。實際操作與版本基準見
[Matt](MATTPOCOCK-SKILLS-GUIDE.md)、[Superpowers](SUPERPOWERS-GUIDE.md)、
[OpenSpec](OPENSPEC-GUIDE.md) 與 [agent-skills](agent-skills-guide.md) 指南。

## 依目前情境縮小選項

同一列可以有多個合適選擇。先找出你最在意的結果，再看差異，不必把候選全部執行。
表中的技能名稱是查找用識別字，實際呼叫方式以所用工具的技能或命令選單為準。

| 目前情境 | 可以考慮 | 如何選擇 | 下一個入口 |
| --- | --- | --- | --- |
| 修錯字、查一個設定或明確的小修改 | 直接處理，必要時加單一技能 | 能直接驗證就先做；不為了完整度建立規格 | 向 AI 說明目標與預期結果 |
| 還說不清要解決誰的什麼問題 | 一般對話、agent-skills `interview-me`、Matt `grill-with-docs`／`grilling` | 短缺口可直接問答；想聚焦真實意圖可用訪談；想展開設計決策可選 Matt | 各套指南的需求技能 |
| 問題已清楚，但解法未定 | agent-skills `idea-refine`、Matt `prototype`、Superpowers `brainstorming` | 要比較方向、實作驗證假設，還是系統化討論設計 | 想法探索、原型或設計技能 |
| 想保存長期需求與變更理由 | OpenSpec、Matt `to-spec`、agent-skills `spec-driven-development` | 需要主規格與變更歸檔，可看 OpenSpec；以一份規格交棒，也可看後兩者 | 各套規格指南 |
| 已有規格，需要拆解與實作 | 原流程入口、Matt `implement`、Superpowers 計畫執行、agent-skills `/build` | 先沿用現有工件，再比較任務拆解、審查安排與人工參與程度 | 各套實作指南 |
| 希望 AI 連續完成較完整的工作 | Superpowers 執行流程、agent-skills `/build auto` | 比較前置條件、任務審查、失敗停止方式與可用工具；不能只看「自動」兩字 | 完整執行說明 |
| bug 原因不明 | Matt `diagnosing-bugs`、Superpowers `systematic-debugging`、agent-skills `debugging-and-error-recovery` | 都可作根因調查；已有慣用方法時先沿用，再依缺口補工具 | 各套除錯技能 |
| 需要可重現的行為驗證 | Matt `tdd`、Superpowers 或 agent-skills `test-driven-development` | 比較測試切片與整理程式的方式；同一次實作選清楚，不同時要求矛盾步驟 | 測試技能與專案測試指令 |
| 擔心函式庫用法過時或重要決策站不住腳 | agent-skills `source-driven-development`、`doubt-driven-development` | 前者確認版本與官方用法；後者安排審查找反例，成本與目的不同 | agent-skills 查證與反證說明 |
| 已完成程式，想審查或簡化 | Matt `code-review`、Superpowers 審查技能、agent-skills `code-review-and-quality`／`code-simplification` | 先區分只要意見，還是允許修改程式；再選審查面向與深度 | 各套審查說明 |
| 想建立品質門檻，或準備遷移與發布 | agent-skills 對應技能，加上專案既有程序 | 分別看門檻設定、監控、遷移與發布準備，避免一次帶入所有檢查 | agent-skills 交付與維護技能 |

若只是多個檔案，不一定需要完整流程；若涉及授權或資料，即使只改一行，也可能
需要先調查與討論。矩陣協助選方法，具體操作仍遵守專案的範圍與權限。

## 常見的選擇差異

### 要釐清意圖，還是展開設計

`interview-me` 聚焦真正目的與成功條件；Matt 的需求訪談會沿設計決策逐步追問；
`idea-refine` 偏向比較不同解法；Superpowers `brainstorming` 會銜接設計文件與計畫。

不要用「哪套問得比較少」作唯一選擇：問題數取決於需求與停止條件。已有清楚答案
時，可以直接把答案交給 AI，要求接續下一步。詳細差異見
[agent-skills 指南](agent-skills-guide.md#訪談探索方案與規格各有不同產出)與
[Matt 指南](MATTPOCOCK-SKILLS-GUIDE.md)。

### 要正式變更紀錄，還是一次工作的規格

想讓未來的人知道系統應該怎麼運作、這次改了什麼，可以考慮 OpenSpec 的主規格
與 change。若重點是把一項工作交代清楚，Matt 或 agent-skills 的規格技能也可使用。
先決定哪份文件是這次工作的依據，比同時產生多份規格更容易維護。

### 要逐段看成果，還是批准計畫後連續執行

agent-skills `/build` 一次處理下一個任務，`/build auto` 會在計畫批准後連續處理，
但仍有測試、提交與停止條件。Superpowers 的完整流程則包含其計畫、實作與審查安排。
選擇前看你願意投入的前期確認、可用代理能力，以及失敗後如何接手。

「連續執行」不代表可以略過驗證或操作授權。各平台也不一定載入相同命令，請看
[agent-skills 命令說明](agent-skills-guide.md#命令怎麼用會做哪些事)與
[Superpowers 執行說明](SUPERPOWERS-GUIDE.md)。

## 可以怎麼組合

以下是可選範例，依你的需求取用。每次交棒都說清楚要帶入哪份成果、接下來做什麼。

### 明確 bug：直接調查與修復

```text
重現問題 → 選一個除錯方法 → 加上可重現檢查 → 修復與驗證
```

適合需求明確、沒有另外建立規格必要的工作。可對 AI 說：

> 先查清這個 bug 的根因，說明建議與理由；用能重現問題的檢查驗證修正。

### 需求待釐清，並希望留下正式規格

```text
選一種需求訪談 → 確認意圖 → OpenSpec 規劃 → 實作與驗證
```

訪談選一般對話、Matt 或 agent-skills 其中一種就可以。可對 AI 說：

> 先用 agent-skills 的 interview-me 釐清需求，確認後把結果交給 OpenSpec。
> 不需要在建立規格時重新訪談一次。

### 沿用既有實作流程，補上缺少的查證

```text
既有計畫 → 原流程實作 → 按需要加入來源查證或決策反證 → 原流程驗收
```

適合已在使用 Superpowers、Matt 或其他明確計畫的工作。可對 AI 說：

> 沿用目前計畫。這次涉及新版 API，加入 source-driven-development 查證用法，
> 再繼續原本的實作與驗證。

### 從頭選擇 agent-skills

```text
必要時釐清或探索 → 規格 → 計畫與實作 → 審查 → 發布準備
```

適合想使用同一套階段名稱與品質方法的使用者。可以逐段操作，也可在符合前置條件時
選 `/build auto`。具體流程與操作範圍見[agent-skills 指南](agent-skills-guide.md)。

## 跨套使用前，確認這幾件事

| 要確認的事情 | 為什麼會影響選擇 |
| --- | --- |
| 技能與命令來自哪裡 | `/plan`、`/review` 或 TDD 類名稱可能重疊；指明來源可減少誤用 |
| 目前使用哪份規格與任務 | 不同流程的預設路徑不同，不能假設能直接互讀 |
| 是否已經完成相同工作 | 第二次訪談、計畫或審查只有在補足缺口時才有價值 |
| 操作會寫入什麼 | 規格、檢查工具、Git 提交與發布操作有不同影響 |
| 所需能力是否真的可用 | 技能檔、命令、代理角色、瀏覽器工具與共用參考文件是不同項目 |

例如 agent-skills `/build auto` 的規格路徑不直接涵蓋 OpenSpec 的 change 結構。
想混用時先確認交接方式，或保留 OpenSpec 的實作入口並補單一技能。
具體限制見[單步與連續實作](agent-skills-guide.md#選擇單步或連續實作)。

## 還不確定時，怎麼請 AI 幫忙選

可以直接提供目標、現有成果與偏好，請 AI 提出建議，不必先背熟所有技能：

> 請先查專案現況與既有工件，提出這項工作的流程建議及理由。
> 說明其他合適選項的差異、需要我參與的地方，以及最後會留下什麼成果。
> 大方向一起討論，細節依專案慣例與適用的最佳實踐處理。

推薦結果至少應讓你知道：為何適合、代價是什麼、從哪裡開始。已選定流程時直接
指名即可，不需要每個任務都重新比較所有方法。

## 選好後從哪裡開始

| 你的選擇 | 詳細指南 |
| --- | --- |
| 完整了解或挑選 agent-skills | [agent-skills 使用指南](agent-skills-guide.md) |
| 使用 Matt 的單一技能或組合 | [Matt Pocock skills 使用指南](MATTPOCOCK-SKILLS-GUIDE.md) |
| 使用 Superpowers 設計與執行 | [Superpowers 技能系統介紹](SUPERPOWERS-GUIDE.md) |
| 使用 OpenSpec 建立或接續變更 | [OpenSpec 操作指南](OPENSPEC-GUIDE.md) |
| 選擇專門審查工具 | [程式碼審查工具選擇指南](CODE-REVIEW-TOOL-SELECTION-GUIDE.md) |
| 讓 Agent 理解你的選擇與專案界線 | [Agent 工作流指引](WORKFLOW-ROUTING.md) |

本文件只維護跨套比較與選擇方式。版本、安裝、命令與完整流程放在各套指南，避免
多處維護同一份操作說明。
