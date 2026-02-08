# 軟體工程黃金標準與架構原則指南

本文件整理軟體開發全生命週期（SDLC）各面向的關鍵黃金標準（Gold Standards），涵蓋架構、開發、測試、部署、維運、資安與 UI/UX 設計。

這些原則是數十年來無數專案失敗後總結出的血淚教訓，可作為決策時的「心智模型（Mental Models）檢查清單」。

> **適用對象**：軟體工程師、架構師、DevOps 工程師、QA、PM — 任何需要在複雜決策中快速找到方向的人。

---

## 目錄

1. [軟體架構](#1-軟體架構-software-architecture)
2. [程式開發](#2-程式開發-development)
3. [測試與品質保證](#3-測試與品質保證-testing--qa)
4. [系統管理與維運](#4-系統管理與維運-sysadmin--ops)
5. [部署與交付](#5-部署與交付-deployment--devops)
6. [資訊安全](#6-資訊安全-information-security)
7. [UI/UX 設計](#7-uiux-設計-user-experience)
8. [爭議與演進](#8-爭議與演進-controversies--evolution)

---

## 1. 軟體架構 (Software Architecture)

架構決定系統骨架，目標是降低複雜度與提高可維護性。

### KISS (Keep It Simple, Stupid)

- **核心**：保持簡單。
- **解釋**：系統運作得最好的時候，通常是設計最簡單的時候。不必要的複雜度是萬惡之源。
- **應用**：如果一個功能可以用簡單的 `if-else` 解決，就不要為了炫技而引入複雜的設計模式。

### DRY (Don't Repeat Yourself)

- **核心**：不要重複自己。
- **解釋**：系統中的每一項知識或邏輯，都應該只有單一、明確、權威的表示。
- **應用**：如果你發現自己在複製貼上同一段程式碼到不同檔案，請把它抽離成共用的函式或模組。
- **注意**：見[爭議與演進](#81-dry-的濫用與反撲)，過早抽象化可能造成更大問題。

### SOLID 原則

物件導向設計的五大鐵律：

| 原則 | 全稱 | 一句話說明 |
|------|------|------------|
| **S** | Single Responsibility | 一個類別只負責一件事 |
| **O** | Open/Closed | 對擴展開放，對修改封閉 |
| **L** | Liskov Substitution | 子類別可以替換父類別 |
| **I** | Interface Segregation | 介面要小而專用 |
| **D** | Dependency Inversion | 依賴抽象，不依賴實作 |

- **注意**：見[爭議與演進](#84-solid-vs-cupid)，CUPID 原則正在成為更現代的替代方案。

### CAP 定理 (CAP Theorem)

- **核心**：分散式系統的不可能三角。
- **解釋**：一致性 (Consistency)、可用性 (Availability)、分區容錯性 (Partition Tolerance) 三者只能取其二。
- **應用**：設計資料庫架構時，你必須決定在網路斷線時，是要「暫停服務保資料正確」（CP），還是「繼續服務但資料可能舊」（AP）。

### 關注點分離 (Separation of Concerns, SoC)

- **核心**：不同的責任放在不同的地方。
- **解釋**：UI 邏輯、商業邏輯、資料存取邏輯不應混在一起。
- **應用**：MVC / MVP / MVVM 等架構模式都是 SoC 的具體實踐。

---

## 2. 程式開發 (Development)

關於程式碼品質與團隊合作的微觀原則。

### 童子軍法則 (The Boy Scout Rule)

- **核心**：離開營地時，要比你剛來時更乾淨。
- **解釋**：當你修改某個檔案修 Bug 時，順手把裡面命名不好的變數改好，或者加上缺少的註解。
- **應用**：防止「破窗效應」，讓程式碼庫隨著時間變好，而不是變爛。

### YAGNI (You Aren't Gonna Need It)

- **核心**：你不會需要它的。
- **解釋**：不要為「假設性的未來需求」寫程式碼。專注於當下需求。
- **應用**：不需要為了「以後可能會用到」就先做好一個彈性的框架。需要的時候再重構。

### 最小驚訝原則 (Principle of Least Astonishment)

- **核心**：程式碼的行為應該符合讀者的預期。
- **解釋**：函式名稱叫 `getUser()`，就不應該同時修改資料庫。
- **應用**：命名、API 設計、函式副作用都應該符合慣例。

### 組合優於繼承 (Composition over Inheritance)

- **核心**：用「有一個」取代「是一個」。
- **解釋**：深層繼承鏈容易產生脆弱的基類問題（Fragile Base Class）。
- **應用**：使用介面、mixin、delegation 來組合行為，而不是透過繼承樹。

### 快速失敗 (Fail Fast)

- **核心**：越早發現錯誤越好。
- **解釋**：在系統邊界立即驗證輸入，不要讓無效資料流入深層邏輯。
- **應用**：參數驗證放在函式開頭；型別檢查在編譯期完成；CI 在 PR 階段就跑測試。

---

## 3. 測試與品質保證 (Testing & QA)

測試不僅是為了找 Bug，更是為了確保重構的信心。

### 測試金字塔 (The Test Pyramid)

- **核心**：單元測試最多，整合測試次之，UI/E2E 測試最少。
- **解釋**：底層的單元測試跑得快、成本低；頂層的端對端測試跑得慢、維護成本高。
- **應用**：不要過度依賴人工點擊測試或慢速的 E2E 測試，應將重心放在快速回饋的單元測試上。
- **注意**：見[爭議與演進](#82-測試金字塔-vs-測試獎盃)，測試獎盃正在挑戰這個模型。

### 測試獎盃 (Testing Trophy)

- **核心**：「Write tests. Not too many. Mostly integration.」— Guillermo Rauch
- **解釋**：在現代前端框架與微服務架構中，單元測試往往都在測「實作細節」而非「使用者行為」。整合測試能同時驗證多個層次的協作，CP 值最高。
- **應用**：將重心從「單元測試」移往「整合測試」。

### FIRST 原則 (FIRST Principles for Unit Tests)

- **F** — Fast：幾秒鐘內跑完
- **I** — Independent：測試之間不互相依賴
- **R** — Repeatable：在任何環境都得到相同結果
- **S** — Self-Validating：結果是 Pass 或 Fail，不需要人工判讀
- **T** — Timely：在寫程式碼的同時寫測試

### 右移測試 (Shift-Right Testing)

- **核心**：測試不止於發布前，也要延伸到生產環境。
- **解釋**：透過 Canary Release、A/B Testing、合成監控（Synthetic Monitoring）在生產環境持續驗證。
- **應用**：搭配 Feature Flags 做漸進式發布與即時回滾。

> 詳細測試流程架構請參考 [TESTING-FLOW-ARCHITECTURE.md](../testing/TESTING-FLOW-ARCHITECTURE.md)
> 手動測試框架請參考 [MANUAL-TESTING-FRAMEWORK.md](../testing/MANUAL-TESTING-FRAMEWORK.md)

---

## 4. 系統管理與維運 (SysAdmin & Ops)

關於基礎設施的穩定性與管理哲學。

### 寵物 vs. 牛 (Cattle vs. Pets)

- **核心**：伺服器應該像牛群一樣可替換，而不是像寵物一樣細心呵護。
- **解釋**：
  - **寵物**：取特別的名字（如 Zeus），生病了你會花一天修好它。
  - **牛**：給編號（如 vm-001），生病了就把它淘汰，重新建一隻新的。
- **應用**：不要手動修復 Server，直接用自動化腳本開新的。

### 3-2-1 備份法則 (The 3-2-1 Backup Rule)

- **核心**：資料備份的黃金鐵律。
- **解釋**：至少 **3** 份資料拷貝、存放在 **2** 種不同儲存媒體、其中 **1** 份要異地保存 (Off-site)。
- **應用**：適用於任何關鍵資料庫或 NAS 的備份策略規劃。

### 基礎設施即程式碼 (Infrastructure as Code, IaC)

- **核心**：用程式碼定義和管理基礎設施。
- **解釋**：伺服器設定、網路拓撲、權限配置都應該版本化，像程式碼一樣進行 Code Review 和自動化部署。
- **應用**：使用 Terraform、Ansible、Pulumi 等工具，避免手動設定產生的飄移（Configuration Drift）。

### 可觀測性三支柱 (Three Pillars of Observability)

- **核心**：Logs、Metrics、Traces 缺一不可。
- **解釋**：
  - **Logs**：事件紀錄（什麼時候發生了什麼事）
  - **Metrics**：數值指標（CPU 使用率、Request 延遲 P99）
  - **Traces**：跨服務的請求追蹤（一個 Request 經過哪些服務）
- **應用**：搭配 OpenTelemetry、Grafana、Loki 等工具建立可觀測性堆疊。

---

## 5. 部署與交付 (Deployment & DevOps)

關於如何將程式碼安全、快速地送到使用者手上。

### 12-Factor App (十二要素應用程式)

- **核心**：建構 SaaS 的方法論。
- **關鍵要素**（摘選）：
  - 組態與程式碼分離（Config in environment variables）
  - 依賴明確宣告（Dependency declaration）
  - 無狀態處理（Stateless processes）
  - 建置、發布、執行三階段分離
  - 開發/生產環境對等（Dev/prod parity）
- **應用**：撰寫 Dockerfile 或設定 Kubernetes 時的基本參考。

### 不可變基礎設施 (Immutable Infrastructure)

- **核心**：部署後就不再修改。
- **解釋**：伺服器一旦部署，就不允許 SSH 進去修改設定。要改設定，必須重新建立一個新的映像檔 (Image) 重新部署。
- **應用**：確保環境一致性，避免「在我的電腦上是可以跑的」問題。

### 持續交付 (Continuous Delivery)

- **核心**：程式碼隨時可以安全地部署到生產環境。
- **解釋**：不代表每次 commit 都要上線，而是「具備隨時上線的能力」。
- **應用**：需要自動化測試、自動化部署、Feature Flags 的支撐。

### 藍綠部署 / 金絲雀發布 (Blue-Green / Canary)

- **核心**：降低部署風險的策略。
- **解釋**：
  - **藍綠**：維持兩套環境，切換流量即完成部署，出問題秒切回。
  - **金絲雀**：先將少量流量（如 5%）導向新版本，觀察穩定後再逐步放量。

---

## 6. 資訊安全 (Information Security)

資安不是外掛的功能，而是內建的屬性。

### CIA 三要素 (CIA Triad)

- **核心**：所有資安措施的基礎框架。
  - **C** — Confidentiality（機密性）：資料不被未授權者取得
  - **I** — Integrity（完整性）：資料不被竄改
  - **A** — Availability（可用性）：服務不被中斷
- **應用**：HTTPS 提供機密性與完整性，DDoS 防護提供可用性。

### 最小權限原則 (Principle of Least Privilege, PoLP)

- **核心**：只給予執行工作所需的最小權限。
- **解釋**：一個 Web Server 不需要 Root 權限；一個 DB 連線帳號不需要 `DROP TABLE` 的權限。
- **應用**：GCP Service Account 只開必要的 API 權限；Docker 容器不以 root 執行。

### 縱深防禦 (Defense in Depth)

- **核心**：洋蔥式防禦，不依賴單一防護。
- **解釋**：即使防火牆破了，還有 WAF；WAF 破了，還有 CSP；CSP 破了，還有資料庫加密。
- **應用**：每一層都假設上一層可能被突破。

### 零信任架構 (Zero Trust)

- **核心**：永遠不信任，始終驗證。
- **解釋**：不因為請求來自內網就放行。每次存取都需要驗證身份、檢查權限、加密傳輸。
- **應用**：內部服務之間也使用 mTLS；VPN 不等於信任。

### 安全左移 (Shift-Left Security)

- **核心**：在開發初期就融入安全。
- **解釋**：不要等到部署前才做安全掃描，而是在寫程式碼的同時就用 SAST/DAST 工具檢查。
- **應用**：CI Pipeline 加入依賴漏洞掃描（如 `npm audit`、`safety check`）。

---

## 7. UI/UX 設計 (User Experience)

理解這些能讓你做出更符合人性的工具，即使你是後端工程師。

### 雅各布定律 (Jakob's Law)

- **核心**：使用者大部分的時間都花在「別人」的網站上。
- **解釋**：不要為了創新而創新。使用者希望你的網站運作方式跟他們習慣的其他網站一樣。
- **應用**：Logo 點擊回首頁、放大鏡代表搜尋、紅色代表錯誤。遵循標準 UI Patterns。

### 美即好用效應 (Aesthetic-Usability Effect)

- **核心**：使用者傾向認為「好看」的介面比較「好用」。
- **應用**：即使是內部後台工具，稍微排版整齊一點，使用者抱怨 Bug 的頻率會降低。

### 希克定律 (Hick's Law)

- **核心**：選項越多，做決定的時間越長。
- **應用**：減少一次呈現的選項數量；使用漸進式揭露（Progressive Disclosure）。

### 費茲定律 (Fitts's Law)

- **核心**：目標越大、越近，越容易點擊。
- **應用**：重要的按鈕要夠大、放在使用者容易觸及的位置；行動裝置上按鈕最小 44x44px。

### 尼爾森十大可用性啟發法則 (Nielsen's 10 Usability Heuristics)

| # | 法則 | 一句話說明 |
|---|------|------------|
| 1 | 系統狀態可見 | 讓使用者知道目前發生什麼事 |
| 2 | 系統與真實世界對應 | 使用使用者熟悉的語言和概念 |
| 3 | 使用者控制與自由 | 提供「上一步」和「取消」 |
| 4 | 一致性與標準 | 同樣的操作產生同樣的結果 |
| 5 | 錯誤預防 | 比錯誤訊息更好的是預防錯誤 |
| 6 | 識別而非回憶 | 讓選項可見，減少記憶負擔 |
| 7 | 彈性與效率 | 提供專家使用者快捷方式 |
| 8 | 美學與極簡設計 | 不顯示不必要的資訊 |
| 9 | 幫助辨識、診斷錯誤 | 錯誤訊息用白話文說明解法 |
| 10 | 幫助與文件 | 即使理想狀態不需要，仍應提供 |

---

## 8. 爭議與演進 (Controversies & Evolution)

資訊領域變化極快，昨天的「最佳實踐」常常變成今天的「反模式」。以下列出正在經歷重大典範轉移的標準：

### 8.1 DRY 的濫用與反撲

**問題**：為了追求 DRY，看到兩段相似的程式碼就急著抽成共用函式，導致錯誤的抽象化與緊密耦合。後來 A 功能需求變了，改共用函式卻把 B 功能弄壞了。

**新標準**：

| 標準 | 核心主張 |
|------|----------|
| **WET** (Write Everything Twice) | 同樣的程式碼寫兩次沒關係，寫到第三次再考慮重構 |
| **AHA** (Avoid Hasty Abstractions) | 寧願要重複程式碼，也不要錯誤的抽象化 — Kent C. Dodds |

**建議**：Rule of Three — 重複三次以上才考慮抽象。

### 8.2 測試金字塔 vs. 測試獎盃

**問題**：在現代前端框架或微服務架構中，單元測試往往都在測「實作細節」，即使單元測試全過，系統串接起來還是可能壞掉。

**新標準**：**測試獎盃 (Testing Trophy)** 將重心從「單元測試」移往「整合測試」。整合測試能同時驗證資料庫、API 和商業邏輯的協作，CP 值最好。

**建議**：依專案特性選擇比例。後端商業邏輯密集的專案適合金字塔；前端 UI 導向的專案適合獎盃。

### 8.3 微服務 vs. 模組化單體

**問題**：中小型團隊導入微服務後出現「分散式大泥球」 — 維運地獄（監控 50 個 Server）、除錯困難（Log 散落各處）、效能折損（function call 變 HTTP Request）。

**新標準**：**模組化單體 (Modular Monolith)** — 程式碼有清楚的模組邊界，但部署時還是打包成一個執行檔。只有當某個模組流量大到撐不住時，才單獨切出去。

**代表人物**：DHH (Basecamp/Rails 創始人)、Amazon Prime Video 團隊。

### 8.4 SOLID vs. CUPID

**問題**：SOLID 太過學術（Java/C++ 時代產物），容易導致過度設計 — 為了符合 OCP 和 DIP，寫了一堆 Interface 和 Factory，要跳轉五次才能找到真正的邏輯。

**新標準**：**CUPID** — 由 Dan North (BDD 發明者) 提出：

| 字母 | 屬性 | 說明 |
|------|------|------|
| **C** | Composable | 像 Unix 指令一樣小巧好組裝 |
| **U** | Unix philosophy | 做一件事，並把它做好 |
| **P** | Predictable | 行為符合預期，沒有魔法 |
| **I** | Idiomatic | 寫 Python 像 Python，寫 Go 像 Go |
| **D** | Domain-based | 程式碼結構反映業務語言（DDD） |

### 8.5 Git Flow vs. Trunk Based Development

**問題**：Git Flow 適合發布週期很長的軟體。但在 CI/CD 時代，Feature branch 活了兩週還沒合併，解衝突會解到懷疑人生。

**新標準**：**主幹開發 (Trunk Based Development)** — Google、Meta 等大廠採用。所有開發者直接 commit 到主幹，或 Feature branch 壽命不超過 24 小時。

**配套**：必須搭配強大的自動化測試與 **Feature Toggles（功能開關）**。

---

## 9. 總結：從理想主義到實用主義

這些「新標準」傳達同一個趨勢：

> **從「完美的架構與流程」轉向「務實的交付與維護」。**

| 舊思維 | 新思維 |
|--------|--------|
| 程式碼在數學上的完美 (SOLID, DRY) | 程式碼好不好改 (WET, AHA) |
| 單元測試覆蓋率至上 | 整合測試信心指數 (Testing Trophy) |
| 微服務是唯一正解 | 模組化單體更務實 |
| 嚴格分支策略 (Git Flow) | 快速合併 (Trunk Based) |

**核心心法**：把這些當作「檢查清單」。做決策時拿出來對照，通常就能避開 80% 的潛在風險。但不要教條化 — 任何原則都有其適用情境。

---

## 10. 延伸閱讀

- [Practical Test Pyramid — Martin Fowler](https://martinfowler.com/articles/practical-test-pyramid.html)
- [The Twelve-Factor App](https://12factor.net/)
- [CUPID — Dan North](https://dannorth.net/2022/02/10/cupid-for-joyful-coding/)
- [AHA Programming — Kent C. Dodds](https://kentcdodds.com/blog/aha-programming)
- [Modular Monolith — Simon Brown](https://www.codingthearchitecture.com/presentations/sa2015-modular-monoliths)
- [Nielsen's 10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)
- [Zero Trust Architecture — NIST SP 800-207](https://csrc.nist.gov/publications/detail/sp/800-207/final)

---

## 相關文件

- [測試流程架構](../testing/TESTING-FLOW-ARCHITECTURE.md)
- [手動測試框架](../testing/MANUAL-TESTING-FRAMEWORK.md)
- [開發工作流程](../workflow/DEVELOPMENT-WORKFLOW.md)
- [Git 工作流程](../git/GIT-WORKFLOW.md)
