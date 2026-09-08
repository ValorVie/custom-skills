---
title: 按開發階段比較與選擇技能
type: guide
date: 2026-09-08
author: ai-dev contributors
status: active
---

# 按開發階段比較與選擇技能

同一階段有多個合適技能時，先看現在缺的是什麼，再比較它們會留下的成果。
這份指南把 [開發流程選擇指南](DEVELOPMENT-WORKFLOW.md) 的總覽展開到技能層級，
幫你回答「這次選哪個、為什麼、什麼條件改變後應換另一個」。不需要逐表跑完。

## 怎麼讀這份矩陣

每張表比較輸入、做法、產出與選擇理由；表後用同一個情境說明分岔。
技能名稱旁的連結指向核對過的來源。表中「適合」是依流程與產出作出的編輯建議，
不是速度、品質或費用的實測排名。

| 你現在缺少什麼 | 前往比較 |
| --- | --- |
| 不確定真正目的，或沒有選定解法 | [需求與方向](#需求與方向) |
| 缺證據，或擔心方案判斷錯誤 | [查證與反證](#查證與反證) |
| 術語、模組或介面不清楚 | [領域與介面設計](#領域與介面設計) |
| 需要把共識寫成可交棒依據 | [規格與品質門檻](#規格與品質門檻) |
| 工作太大，不知道怎麼分與排序 | [計畫與任務拆解](#計畫與任務拆解) |
| 已有計畫，要選擇執行方式 | [實作與測試](#實作與測試) |
| 程式出錯，或缺少執行中的證據 | [除錯與執行驗證](#除錯與執行驗證) |
| 已有成果，要找問題或整理程式 | [審查與簡化](#審查與簡化) |
| 準備整合、發布或淘汰舊介面 | [交付與維護](#交付與維護) |
| 要換工作階段或保存決策 | [脈絡與文件交接](#脈絡與文件交接) |

本文比較 agent-skills、Matt、Superpowers 與 OpenSpec 的開發相關入口；不是所有
已安裝技能的清冊。agent-skills 的 25 項技能均有對應位置；其他套件選取與上述
階段直接相關的技能，不為了湊齊欄位放入無關功能。

名稱前綴表示來源：**AS** 是 Addy Osmani 的 agent-skills，**Matt** 是
mattpocock/skills，**SP** 是 Superpowers。OpenSpec 一欄列的是操作入口，
不是同名的獨立工程方法。斜線命令會串接技能，不能把「有技能」當成「命令已可用」。
安裝與完整操作請回各套指南。

比較基準沿用既有指南：AS `48cb1168`、Matt `ed37663`，SP 核對 `v5.0.0`。
這些是固定版本比較，不宣稱是三套工具的最新行為。OpenSpec 入口與配置差異見
[操作指南](OPENSPEC-GUIDE.md)；啟用的流程配置會影響命令是否可見。

## 需求與方向

先區分「不知道為什麼做」、「知道問題但沒有解法」與「想把解法談完整」。
三者都可能透過問答推進，結束時應拿到的成果卻不同。

| 候選技能 | 帶入什麼 | 做法與產出 | 什麼時候選，以及為什麼 | 不適合直接接手的情況 |
| --- | --- | --- | --- | --- |
| AS [interview-me][as-interview] | 原始要求、使用者與限制的線索 | 一次一題並附推測；得到使用者確認的意圖摘要 | 「做個儀表板」其實還沒說清要支援哪個決策；先避免做錯東西 | 已有明確需求時不用重新訪談；需要即時回覆，不能靠它獨立跑完 |
| AS [idea-refine][as-idea] | 一個想法與要改善的問題 | 展開多種方向，再收斂範圍、假設與不做項目；形成概念摘要 | 想比較解法、縮小第一版；重點是選方向 | 尚不知道誰受益時先釐清意圖；它不提供可執行原型證據 |
| Matt [grilling][matt-grilling] | 待決定的計畫、想法或選擇 | 沿決策的相依關係逐題追問，每題附建議；可查事實先自行查 | 大方向已知，但還有影響範圍的決策；需要逐項保留人的選擇權 | 它本身不保證建立規格或領域文件 |
| Matt [grill-with-docs][matt-grill-with-docs] | 工程問題與專案文件 | 組合 `grilling` 與 `domain-modeling`，邊談邊整理術語及決策 | 需求常因同一詞有不同意思而返工；希望討論同步改善專案共同語言 | 不涉及程式或專案文件時，可選 Matt [grill-me][matt-grill-me]，其入口只啟動 grilling |
| SP [brainstorming][sp-brainstorming] | 功能想法與現有專案 | 查脈絡、逐題討論、比較方案、確認設計、寫設計文件，再交給 `writing-plans` | 已決定使用 SP 設計到實作流程，想在寫程式前把設計談完整 | 只想取得意圖摘要時，後續文件與計畫銜接可能超過本次需要 |
| Matt [prototype][matt-prototype] | 一個能用操作或執行回答的設計疑問 | 建可丟棄原型；保留學到的決策，捨棄原型程式 | 對話無法決定互動或狀態模型；需要看到實際結果 | 不適合直接交付正式功能，也不該順手補完整產品能力 |

**同一情境如何選：**「讓使用者更容易匯入資料」還沒有指出卡在哪裡，先選
`interview-me`。若已確認是欄位對應困難，但不確定用範本或對應畫面，選
`idea-refine` 比較方向；需要親手操作才能決定時，接 `prototype`。
若爭議在「一次匯入」究竟如何計算成功與部分失敗，選 `grill-with-docs` 把語意談清楚。
已選 SP 並準備建立完整設計時，從 `brainstorming` 延續即可，不必再重跑三種訪談。

## 查證與反證

查資料回答「來源怎麼說」；反證回答「即使來源沒錯，這次推論會不會失敗」。

| 候選技能 | 輸入與主要動作 | 產出 | 什麼時候選，以及為什麼 | 成本與限制 |
| --- | --- | --- | --- | --- |
| Matt [research][matt-research] | 一個可研究的問題；追到官方文件、原始碼等第一手來源 | 附來源的研究 Markdown | 還沒準備實作，需要先查工具是否支援某能力；成果可交給後續決策者 | 上游要求背景代理，需有對應能力；研究結論不等於實作驗證 |
| AS [source-driven-development][as-source] | 專案版本與即將採用的用法；先查對應官方文件再實作 | 有來源依據的程式與說明 | 正在寫框架或函式庫相關程式，怕套用錯版本；查證直接跟著實作走 | 不替你證明需求正確；純邏輯或改名通常不需要這層版本查證 |
| AS [doubt-driven-development][as-doubt] | 一項主張、最小可審查成果及其契約；交給全新脈絡的審查者找反例 | 成立或被推翻的問題、修正與殘餘未知 | 「重試一定不會重複寫入」這類重要推論，需要主動嘗試推翻 | 增加審查往返；每輪要選審查方式，迴圈有上限，不能當成零成本自我檢查 |

**同一情境如何選：**查某 SDK 是否支援請求重試，選 `research`；依專案安裝版本
寫出重試用法，選 `source-driven-development`；檢查重試與應用程式的去重設計能否
共同避免重複執行，才是 `doubt-driven-development`。三者可接續，但後者不能替代
真正的重試測試。

## 領域與介面設計

| 候選技能 | 帶入什麼、會得到什麼 | 核心差異與選用理由 | 何時換另一個 |
| --- | --- | --- | --- |
| Matt [domain-modeling][matt-domain-modeling] | 規則、術語與邊界案例 → 共同語言、`CONTEXT.md` 與決策紀錄 | 先讓人和程式對同一概念有一致理解，適合「取消」與「退款」被混用等語意問題 | 語意已穩定，只缺 HTTP 回應格式時改看介面設計 |
| Matt [codebase-design][matt-codebase-design] | 模組責任與使用方式 → 小介面、可測邊界及替代設計 | 比較模組能否用簡單介面藏住複雜度；適合難測、呼叫端知道太多內部細節的結構 | 已決定模組，只需定義分頁與錯誤碼時用 AS 介面技能 |
| AS [api-and-interface-design][as-api] | 呼叫端需求與現有介面 → 輸入、輸出、驗證、錯誤與相容性契約 | 關注呼叫者實際依賴的行為，適合新增端點或調整公開型別 | 不清楚業務名詞時先建模；不能只靠型別設計解決語意爭議 |
| Matt [improve-codebase-architecture][matt-improve-codebase-architecture] | 現有程式庫 → 可改善模組的候選報告，再討論選中的方向 | 適合知道結構難維護、但還不知道先改哪裡；先盤點再選一項 | 已知目標函式只是過度巢狀時，直接看簡化技能即可 |
| AS [frontend-ui-engineering][as-frontend] | 已知使用流程與畫面需求 → 元件、互動狀態、響應式與無障礙處理 | 需要把設計做成可操作介面；焦點在使用體驗落地 | 尚未決定互動方向時先做原型；本技能不替代產品選擇 |

**同一情境如何選：**重新設計匯入工作狀態，若「已完成」是否包含失敗筆數仍有
爭議，先 `domain-modeling`；若狀態已定但每個呼叫端都重寫轉換邏輯，選
`codebase-design`；若要提供查詢進度端點，選 `api-and-interface-design`。
最後才由 `frontend-ui-engineering` 把狀態呈現在畫面上。

## 規格與品質門檻

| 候選技能或入口 | 需要的輸入 | 產出與差異 | 選用理由 | 需要注意 |
| --- | --- | --- | --- | --- |
| Matt [to-spec][matt-to-spec] | 已討論的共識與程式脈絡 | 整理需求、決策、測試邊界與範圍，發布到專案任務系統 | 已談完，要把共識直接交棒；上游明說不重做訪談 | 仍需確認測試邊界；上游有發布與標籤操作，服從專案任務規則 |
| AS [spec-driven-development][as-spec] | 需求與目前缺口 | 多能力需求先拆開；經規格、計畫、任務、實作逐階段確認 | 希望沿 AS 的階段建立實作依據，而不只把對話轉成一張任務 | `/spec` 命令預設 `SPEC.md`；完整方法涵蓋後續階段，需講清這次停在哪裡 |
| OpenSpec [propose／new＋continue](OPENSPEC-GUIDE.md) | 新變更目標、既有規格與專案配置 | 建立變更中的提案、規格、設計與任務；後續可同步及歸檔 | 需要長期知道系統應有行為及每次修改原因，或專案已採用 OpenSpec | `new` 只建立變更骨架，後續才產生文件；入口視配置而異 |
| SP [brainstorming][sp-brainstorming] 的設計文件 | 已完成設計討論 | 為 SP 計畫保存設計依據 | 已走到設計確認，直接沿用成果，減少重複寫另一份規格 | 不自帶 OpenSpec 的主規格同步及變更歸檔機制 |
| AS [constraint-driven-development][as-constraints] | 現有檢查、量測基準與團隊要求 | `CONSTRAINTS.md` 記錄品質門檻、例外與執行命令，並接入所需工具 | 規格說了功能，但沒人知道哪些品質條件應阻止交付；補可檢查的標準 | 可能安裝工具、修改檢查與 Agent 指令；已有門檻時先沿用，不重新設定 |

**同一情境如何選：**匯入功能的行為已談妥，想交給下一位實作者，選 `to-spec`；
若原專案已有 OpenSpec 匯入規格，直接建立對應變更。若缺的是「新功能是否可以
跳過既有測試」或「效能退步多少需要擋下」，選 `constraint-driven-development`，
因為這是品質標準，不是再寫一次功能需求。

## 計畫與任務拆解

| 候選技能或入口 | 輸入 → 產出 | 任務粒度與關鍵差異 | 何時選，以及為什麼 |
| --- | --- | --- | --- |
| Matt [to-tickets][matt-to-tickets] | 計畫、規格或對話 → 經確認的任務及阻塞關係 | 每項打通一條可展示的完整行為，通常能放進一次工作脈絡；不預填大量檔案與程式碼 | 需要交給不同工作階段或協作者；任務要說清結果與真正前置條件 |
| AS [planning-and-task-breakdown][as-planning] | 明確需求或規格 → 有驗收條件、依賴與檢查點的計畫 | 也採完整行為切片，另整理執行順序與階段檢查；技能支援既有任務系統 | 想先得到可執行順序與確認節奏，再接 AS 或原本的實作方法 |
| SP [writing-plans][sp-writing-plans] | 已確認設計 → 詳細實作計畫 | 列出檔案、程式、測試命令及預期結果；每個步驟是一個約 2–5 分鐘的動作，並非整項任務都只要數分鐘 | 要交給不熟悉專案的人或代理照步驟實作；願意先投入較細的規劃 |
| Matt [wayfinder][matt-wayfinder] | 超出一次工作脈絡的大目標 → 任務系統中的決策地圖 | 先處理會開啟後續路徑的決策，不假設一開始能列完所有實作 | 長期工作仍有多個未知方向；比提前寫死全部實作步驟更能保留調整空間 |
| OpenSpec 的 tasks | 同一 change 的規格與設計 → 對應任務清單 | 任務跟該變更文件一起維護 | 已有 OpenSpec change 時優先補原 tasks；無須額外建立另一份同義清單 |

**同一情境如何選：**規格已定且要分成數個可交棒成果，用 `to-tickets`；想逐步
指定「先加哪個測試、看到什麼失敗、改哪個檔案」，用 `writing-plans`。
若連同步匯入或背景處理都尚未決定，先解決該決策；規模大且會衍生多條路徑時
才考慮 `wayfinder`，不要把未知數偽裝成細步驟。

AS `/plan` 命令預設寫 `tasks/plan.md` 與 `tasks/todo.md`，但其規劃技能支援專案
任務系統。混用時要說明以哪裡為準，不能看到技能支援就假設命令會自動轉接。

## 實作與測試

執行入口決定「處理多少工作、何時停」；測試技能決定「如何證明每次改動」。
先選執行方式，再補合適測試方法，兩者不必來自同一套。

| 執行候選 | 前置條件與產出 | 執行、審查與停止方式 | 選用理由與代價 |
| --- | --- | --- | --- |
| Matt [implement][matt-implement] | 規格或任務 → 實作、檢查、審查與提交 | 在事先同意的測試邊界運用 `tdd`，過程跑針對性檢查，結尾完整測試與 `code-review` | 已有可交棒任務，想保留精簡執行入口；不是自帶逐任務雙審查的調度器 |
| AS [incremental-implementation][as-incremental] | 明確工作 → 每次一段可運作、可回復的變更 | 實作一小片、測試、驗證、提交，再擴展 | 想補「不要一次寫太多」的紀律，保留目前執行入口；它本身不是 `/build auto` |
| AS `/build`／`/build auto` | 可用命令與所需規格、任務 → 驗證過的任務成果 | 單步完成下一項後停；auto 在計畫批准後連續處理，遇不確定或高風險步驟停下 | 想明確選擇逐項看成果或連續執行；包含提交行為，命令與規格路徑須先確認 |
| SP [subagent-driven-development][sp-subagent-driven-development] | 已有計畫、代理能力 → 逐任務實作及審查成果 | 每項交給新實作者，先審規格符合度，再審程式品質，修正後複審 | 想降低同一作者自審的盲點；需要額外代理與審查往返，不是把所有實作者一起平行啟動 |
| SP [executing-plans][sp-executing-plans] | 書面計畫 → 按步驟完成並驗證 | `v5.0.0` 主文要求執行全部任務，遇阻塞或反覆驗證失敗停止；有代理時上游優先用前一項 | 保留 SP 計畫而沒有子代理能力；不要把舊版「固定每三項停一次」套入這個版本 |
| OpenSpec apply | 已就緒的 change 文件與任務 → 實作及任務進度 | 讀取變更脈絡、按任務實作，遇缺口再釐清 | 現有成果就在 OpenSpec 時最直接；測試仍用專案方法，可按需補單一技能 |

AS `/build auto` 的預設規格搜尋包含 `SPEC.md`、`docs/SPEC.md`、`spec/*`，
不直接涵蓋 OpenSpec change 目錄。已有 OpenSpec 時可保留 apply，再加入 AS 的
增量實作或查證技能。命令細節見 [agent-skills 指南](agent-skills-guide.md#選擇單步或連續實作)。

### 三種 TDD 的實際差異

TDD 是先寫會失敗的行為測試，再實作使它通過。三者都有這個核心，選擇差異
在測試邊界、重構時機與執行環境的補充方法。

| 候選技能 | 共同核心以外的重點 | 重構安排 | 什麼時候選，以及為什麼 |
| --- | --- | --- | --- |
| Matt [tdd][matt-tdd] | 先與使用者確認公開測試邊界；一個測試、一個最小實作；避免綁住內部結構 | 在本比較版本，重構留在 review，明確排除於 red → green 實作循環之外 | 最困擾的是測試太貼實作、改內部就全壞；希望先對齊少數有價值的觀察點 |
| SP [test-driven-development][sp-test-driven-development] | 強調親眼看見正確原因的失敗，禁止先寫實作再補測試當成 TDD | 綠燈後重構，再保持綠燈 | 已選 SP，或主要問題是跳過失敗證據；希望按紅、綠、重構循環約束實作 |
| AS [test-driven-development][as-tdd] | 先辨識專案技術棧與真實測試命令，另提供測試資源分級、bug 重現及瀏覽器驗證方法 | 綠燈後重構，再驗證 | 跨不同語言專案，或需要把行為測試與瀏覽器證據接起來；避免套錯測試命令 |

測試邊界的確認方式也不同：本次核對的 Matt 原文明定，寫測試前先列出公開邊界並
取得使用者確認。SP 與 AS 的上述 TDD 原文沒有同樣的逐次確認規定；SP 另要求
不採 TDD 的例外先詢問使用者，AS 先要求讀取專案測試慣例。這只比較這三份技能，
不代表其完整流程或專案規則沒有其他確認要求。

**同一情境如何選：**匯入解析器已有測試框架，但每次改內部函式都壞掉，Matt
`tdd` 的公開邊界約定最切題。若團隊問題是經常直接寫完才補測試，SP 的失敗證據
要求比較切題。若單元測試通過但瀏覽器操作仍有問題，AS 的測試與瀏覽器方法可補缺口。
這是依問題配方法，不表示其他兩套不能解決；也不應為文件修改硬加無關測試。

## 除錯與執行驗證

| 候選技能 | 主要方法與成果 | 選用情境與理由 | 不能代替什麼 |
| --- | --- | --- | --- |
| Matt [diagnosing-bugs][matt-diagnosing-bugs] | 最小可重複失敗案例、可證偽假設、觀測實驗、修正與回歸測試 | 間歇錯誤或難重現退步；需要用實驗排除假設 | 沒重現時不能直接宣稱已找出根因 |
| SP [systematic-debugging][sp-systematic-debugging] | 根因調查、比對模式、驗證假設，再實作；多次修補失敗時重新檢視架構 | 一直換猜測、改完又壞；用固定調查順序制止試錯式補丁 | 不因用了方法就自動取得修改或現場操作權限 |
| AS [debugging-and-error-recovery][as-debug] | 先停新增功能、保留證據，再重現、定位、縮小、修正與完整驗證；分測試、建置、執行錯誤檢查 | 開發途中流程被錯誤打斷，想有清楚的停工、恢復順序 | 「恢復開發」要以驗證為依據，不是錯誤訊息消失就算完成 |
| AS [browser-testing-with-devtools][as-browser] | 用 Chrome DevTools MCP 檢查真實操作、主控台、請求及效能 | 問題只存在瀏覽器，如點擊沒反應或請求被攔；需補執行證據 | 它是觀測與操作方法，不替代根因調查；需要工具與可用頁面 |
| AS [performance-optimization][as-performance] | 量測基準、定位瓶頸、修改並比較前後數據 | 問題是速度或資源使用，需要用數字決定是否有效 | 沒有量測資料時只能列假設，不能以程式看起來較短宣稱更快 |

**同一情境如何選：**匯入按鈕偶爾無效，先用其中一套除錯方法整理假設，再以
瀏覽器工具取得請求與畫面證據。如果確定每次都成功，只是大檔案太慢，主問題就
轉成效能量測。三套根因方法高度重疊，已有慣用方法時不必為同一 bug 全部重跑。

## 審查與簡化

| 候選技能或入口 | 審查對象與產出 | 什麼時候選，以及為什麼 | 與近似技能的界線 |
| --- | --- | --- | --- |
| Matt [code-review][matt-code-review] | 相對固定 Git 基準的變更；分「工程標準」與「規格符合度」審查 | 需要知道是做錯需求，還是做法不符合專案標準；兩軸分開較易追責與修正 | 上游使用平行代理且要求明確基準；缺規格時不能假裝完成規格審查 |
| AS [code-review-and-quality][as-review] | 從正確性、可讀性、架構、安全、效能列具體問題及嚴重程度 | 希望全面看一份變更的品質，避免只看測試是否通過 | 五面向不是五位代理的保證；它與 `/ship` 的專門角色整合不同 |
| SP [requesting-code-review][sp-requesting-code-review] | 將工作摘要、計畫與 Git 範圍交給審查者 | 已用 SP，想在任務或里程碑取得獨立審查 | 重點是安排審查與修正，不是另一份五面向清單 |
| SP [receiving-code-review][sp-receiving-code-review] | 已收到的意見 → 查證、釐清、接受或有理由地反駁，再修正 | 審查者建議可能不合現況，不能照單全收 | 不負責產生第一份審查意見，通常接在其他 review 後 |
| AS [doubt-driven-development][as-doubt] | 尚在形成中的重要主張 → 反例與修正 | 決策還能便宜改方向時，想找出隱藏假設 | 不是只能在程式寫完後使用，也不替代完整變更審查 |
| AS [code-simplification][as-simplify] | 已知範圍與行為 → 實際簡化程式並重新驗證 | 已知功能正確，想降低閱讀與維護負擔 | 會修改程式；只要意見時不要選成自動整理 |
| OpenSpec verify | change 文件、任務與實作 → 完整性、正確性、一致性檢查 | 想知道是否真的照這次變更完成，有沒有漏掉規格情境 | 不代表安全、效能或所有專案測試已通過；入口需啟用相應配置 |

**同一情境如何選：**匯入功能完成後，怕漏做規格情境，選 Matt 的規格軸或現有
OpenSpec verify；想整體看可讀性及效能，選 AS review。收到「把這段全改成共用
框架」的意見，先用 `receiving-code-review` 查證必要性。確認只要整理分支後，
才授權 `code-simplification` 改程式。

## 交付與維護

這一階段容易把「檢查完成」、「可合併」、「可發布」混為一談。以下依要取得的
結果分類；沒有直接對應項時保留空缺，不把別套技能硬配成同等能力。

| 候選技能或入口 | 真正要完成的事 | 選用理由 | 與其他交付工作的差別 |
| --- | --- | --- | --- |
| SP [verification-before-completion][sp-verification-before-completion] | 先跑能支持完成聲明的命令，讀取結果再回報 | 想防止用舊測試或「應該會過」宣稱完成 | 證據與聲明要相符；通過建置不能推論部署成功 |
| SP [finishing-a-development-branch][sp-finishing-a-development-branch] | 驗證後讓使用者選分支合併、推送 PR、保留或放棄，依選擇收尾 | SP 工作已做完，現在要決定如何整合 | 不等於線上發布；破壞性選項及推送仍需要授權 |
| SP [using-git-worktrees][sp-using-git-worktrees] | 建立隔離 checkout、確認忽略規則與測試基準 | 從開始就需要獨立工作目錄；也影響收尾的保留或清理 | 不是隔離服務、資料庫或權限，單一明確修改不因此必須新開工作區 |
| AS [git-workflow-and-versioning][as-git] | 分支、提交、PR 與版本策略 | 要整理可讀歷史或版本發布方式 | 偏持續使用的 Git 方法，不只是一次分支結束選單 |
| Matt [resolving-merge-conflicts][matt-resolving-merge-conflicts] | 從雙方歷史找意圖，解決已發生的 merge／rebase 衝突 | 正在整合且有衝突，要保留雙方有效行為 | 不是發布準備，也不應因為可能衝突就預先啟動 |
| AS [shipping-and-launch][as-ship-skill]／`/ship` | 發布條件、風險、監控、成功標準與回復準備 | 要判斷能否推出；命令另整合專門審查角色並形成 GO／NO-GO 建議 | 技能與命令能力不同；GO 是準備判斷，不代表已部署或獲准部署 |
| AS [ci-cd-and-automation][as-ci] | 把測試、建置與交付檢查接入自動流程 | 每次都要重複檢查，想穩定執行 | 會改流程設定；一次檢查不必先建整套自動化 |
| AS [observability-and-instrumentation][as-observe] | 加上可定位問題的記錄、指標、追蹤與告警 | 上線後不知道是否正常，或失敗無法追查 | 提供觀測能力，不等於功能已有測試或本次發布已成功 |
| AS [security-and-hardening][as-security] | 分析不可信輸入、認證、權限及依賴並驗證防護 | 變更跨越信任邊界，需要專門檢查 | 全面 review 只是一層；它不能保證找出所有漏洞，也不自帶現場測試授權 |
| AS [deprecation-and-migration][as-migration] | 設計相容期、遷移步驟、移除條件與回復 | 要移除仍有人使用的欄位、API 或系統 | 與新功能推出不同，需知道舊使用者何時已遷走；不只是刪除舊程式 |

**同一情境如何選：**匯入功能通過測試但還沒合併，用分支收尾；要推到使用者
可用的環境，用發布準備；不知道推出後如何追查失敗，先補觀測；要停用舊匯入
格式，另做遷移。這些成果彼此相依，但不能互相當作完成證據。

## 脈絡與文件交接

| 候選技能 | 主要產出 | 何時選，以及為什麼 | 不應混淆的成果 |
| --- | --- | --- | --- |
| Matt [handoff][matt-handoff] | 供新工作脈絡接續的目標、決策、未知與下一步 | 長對話要換階段或換代理，希望避免重新查已解決事項 | 交接摘要不是永久規格，也不應另立一份任務狀態 |
| AS [context-engineering][as-context] | 精選當前工作需要的規則、程式、版本及摘要 | Agent 讀了很多卻忽略重點；需要管理載入內容與脈絡大小 | 不只結束時摘要，也處理開工與過程中的資訊選擇 |
| AS [documentation-and-adrs][as-docs] | 面向讀者的技術文件及架構決策紀錄（ADR） | 要讓未參與當次工作的人長期理解用法與取捨 | 不只是把對話存下來；需要依讀者任務整理 |
| AS [using-agent-skills][as-using] | 選技能、載入共用工作原則的流程入口 | 已選 AS，希望按工作階段找到合適技能 | 它不是跨四套工具的實測排名器；安裝後是否自動載入取決於整合方式 |

**同一情境如何選：**今天停工明天繼續，留 `handoff`；新代理載入過多無關文件，
用 `context-engineering` 縮小脈絡；要讓維護者半年後知道為何採背景匯入，寫 ADR。

## 把選擇交代給 AI

技能識別字必須連同來源說明。提供現在已有的成果，並說明想要建議、文件、
實作還是審查，能減少同名技能與流程自動接續造成的誤會。

> 已確認需求，也有任務清單。這次用 Matt 的 tdd，先核對我們同意的公開測試邊界；
> 不重新訪談或產生規格。依這個版本把重構留到審查階段。

> 已確認要改善的問題，目前只有初步解法，先用 agent-skills 的 idea-refine 比較方向。
> 請說明推薦、另兩個合理方向與改選條件，這次先交付概念摘要。

> 延續現有 OpenSpec change，用原 apply 入口實作；SDK 用法加入 agent-skills 的
> source-driven-development 查證。不要另外建立第二份規格或任務清單。

選好後回 [開發流程選擇指南](DEVELOPMENT-WORKFLOW.md) 看組合方式，或前往
[agent-skills](agent-skills-guide.md)、[Matt](MATTPOCOCK-SKILLS-GUIDE.md)、
[Superpowers](SUPERPOWERS-GUIDE.md)、[OpenSpec](OPENSPEC-GUIDE.md) 操作。

## 來源與比較界線

每列技能連結都指向固定版本的 `SKILL.md`。AS 命令行為另以該版本的
[命令目錄](https://github.com/addyosmani/agent-skills/tree/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/.claude/commands)
為準。OpenSpec 的命令配置與文件流程參照[官方說明](https://github.com/Fission-AI/OpenSpec)
及本地操作指南。核對日期為 2026-09-08。

本比較沒有實測哪套更快、更省或錯誤率更低；互動、文件與代理成本的描述來自
各方法要求的工作。實際安裝版本若不同，先查相同技能原文，尤其是重構時機、
命令預設路徑、審查角色、提交與停止條件。專案規則及使用者已批准範圍優先。

[as-api]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/api-and-interface-design/SKILL.md
[as-browser]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/browser-testing-with-devtools/SKILL.md
[as-ci]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/ci-cd-and-automation/SKILL.md
[as-constraints]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/constraint-driven-development/SKILL.md
[as-context]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/context-engineering/SKILL.md
[as-debug]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/debugging-and-error-recovery/SKILL.md
[as-docs]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/documentation-and-adrs/SKILL.md
[as-doubt]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/doubt-driven-development/SKILL.md
[as-frontend]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/frontend-ui-engineering/SKILL.md
[as-git]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/git-workflow-and-versioning/SKILL.md
[as-idea]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/idea-refine/SKILL.md
[as-incremental]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/incremental-implementation/SKILL.md
[as-interview]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/interview-me/SKILL.md
[as-migration]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/deprecation-and-migration/SKILL.md
[as-observe]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/observability-and-instrumentation/SKILL.md
[as-performance]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/performance-optimization/SKILL.md
[as-planning]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/planning-and-task-breakdown/SKILL.md
[as-review]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/code-review-and-quality/SKILL.md
[as-security]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/security-and-hardening/SKILL.md
[as-ship-skill]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/shipping-and-launch/SKILL.md
[as-simplify]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/code-simplification/SKILL.md
[as-source]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/source-driven-development/SKILL.md
[as-spec]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/spec-driven-development/SKILL.md
[as-tdd]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/test-driven-development/SKILL.md
[as-using]: https://github.com/addyosmani/agent-skills/blob/48cb1168aeaaa70dfc2bbf709eddfa2a8ed8129a/skills/using-agent-skills/SKILL.md
[matt-code-review]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/code-review/SKILL.md
[matt-codebase-design]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/codebase-design/SKILL.md
[matt-diagnosing-bugs]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/diagnosing-bugs/SKILL.md
[matt-domain-modeling]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/domain-modeling/SKILL.md
[matt-grill-me]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/productivity/grill-me/SKILL.md
[matt-grill-with-docs]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/grill-with-docs/SKILL.md
[matt-grilling]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/productivity/grilling/SKILL.md
[matt-handoff]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/productivity/handoff/SKILL.md
[matt-implement]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/implement/SKILL.md
[matt-improve-codebase-architecture]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/improve-codebase-architecture/SKILL.md
[matt-prototype]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/prototype/SKILL.md
[matt-research]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/research/SKILL.md
[matt-resolving-merge-conflicts]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/resolving-merge-conflicts/SKILL.md
[matt-tdd]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/tdd/SKILL.md
[matt-to-spec]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/to-spec/SKILL.md
[matt-to-tickets]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/to-tickets/SKILL.md
[matt-wayfinder]: https://github.com/mattpocock/skills/blob/ed37663cc5fbef691ddfecd080dff42f7e7e350d/skills/engineering/wayfinder/SKILL.md
[sp-brainstorming]: https://github.com/obra/superpowers/blob/v5.0.0/skills/brainstorming/SKILL.md
[sp-executing-plans]: https://github.com/obra/superpowers/blob/v5.0.0/skills/executing-plans/SKILL.md
[sp-finishing-a-development-branch]: https://github.com/obra/superpowers/blob/v5.0.0/skills/finishing-a-development-branch/SKILL.md
[sp-receiving-code-review]: https://github.com/obra/superpowers/blob/v5.0.0/skills/receiving-code-review/SKILL.md
[sp-requesting-code-review]: https://github.com/obra/superpowers/blob/v5.0.0/skills/requesting-code-review/SKILL.md
[sp-subagent-driven-development]: https://github.com/obra/superpowers/blob/v5.0.0/skills/subagent-driven-development/SKILL.md
[sp-systematic-debugging]: https://github.com/obra/superpowers/blob/v5.0.0/skills/systematic-debugging/SKILL.md
[sp-test-driven-development]: https://github.com/obra/superpowers/blob/v5.0.0/skills/test-driven-development/SKILL.md
[sp-using-git-worktrees]: https://github.com/obra/superpowers/blob/v5.0.0/skills/using-git-worktrees/SKILL.md
[sp-verification-before-completion]: https://github.com/obra/superpowers/blob/v5.0.0/skills/verification-before-completion/SKILL.md
[sp-writing-plans]: https://github.com/obra/superpowers/blob/v5.0.0/skills/writing-plans/SKILL.md
