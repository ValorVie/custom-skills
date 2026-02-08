# 手動測試框架：文件、工具與方法論

本文件說明「手動測試不是亂點」：它依賴的不是程式碼框架，而是一套可複製的文件結構、流程工具、方法論與證據鏈，讓不同資歷的測試者也能產出一致的品質訊號。

> 適用對象：QA / SDET / PM / RD；需要把手動測試制度化、可交接、可稽核的人。

---

## 1. 手動測試的四大支柱

### 1.1 測試案例文件（Test Case Specification）

手動測試最基本的約束力是「可重複的測試案例」。建議每個案例至少包含：

- ID（可追蹤）
- Title（一句話說清楚要驗證什麼）
- Pre-condition（前置條件/測試資料/帳號權限）
- Steps（可執行、可重複的步驟）
- Expected Result（可判定的預期結果）
- Actual Result（實測結果與觀察）
- Evidence（截圖/錄影/Log/時間點）

範本（可直接複製到表格或測試管理工具）：

| 欄位 | 範例 |
|---|---|
| ID | TC-001 |
| Title | 未登入使用者無法結帳 |
| Pre-condition | 使用者未登入；購物車已有 1 件商品 |
| Steps | 1. 進入購物車 2. 點擊「前往結帳」 |
| Expected | 跳轉登入頁並提示「請先登入」 |
| Actual | PASS / FAIL + 描述 |
| Evidence | screenshot、錄影連結、timestamp |

### 1.2 測試管理工具（Test Management）

工具的作用不是「存放文件」而已，而是把測試變成可管理的工作流程：

- Test Cases：案例庫、版本化
- Test Runs：這次改版要跑哪些案例（選集）
- Coverage 視角：需求/票據與案例的連結
- 進度追蹤：執行率、Pass/Fail 分布
- Defect 連結：案例失敗可直接連到 bug 單

常見組合（依團隊規模與既有系統選擇）：

- Jira + Xray/Zephyr
- TestRail
- 輕量：Google Sheets + Jira（或 Git issue）

### 1.3 探索性測試（Exploratory Testing）的框架

探索性測試不是沒有框架；它通常用「章程（charter）」與「時間盒（timebox）」來避免漫無目的。

推薦做法：Session-Based Testing（SBT）

- Mission：這一段時間要探索什麼風險/面向
- Charter：範圍、限制、重點攻擊方向
- Notes：即時紀錄觀察、假設、疑點、重現路徑
- Debrief：結束後整理成果（缺陷、風險、建議回歸）

Charter 範本：

| 欄位 | 範例 |
|---|---|
| Session ID | SBT-2026-02-08-01 |
| Timebox | 45 min |
| Mission | 探索「折扣碼」錯誤處理與邊界行為 |
| Focus | 特殊字元、過期碼、大小寫、重複套用、跨裝置 |
| Notes | 重現步驟、觀察、可能原因 |
| Output | 風險清單、Bug 單連結、建議新增自動化回歸 |

### 1.4 缺陷生命週期（Defect Lifecycle）

為了避免「口頭回報」造成資訊遺失，缺陷需要有一致的狀態機與最小資訊集：

- New：建立
- Triaged：分類與優先度確認
- Assigned / In Progress：指派與修復中
- Resolved：開發宣告已修復（附上修復版本/commit）
- Verified：QA 複測通過
- Closed：關閉
- Reopened：複測未過，退回修復

Bug 單建議欄位（最小集合）：

- Title（可搜尋）
- Environment（版本、裝置、瀏覽器、帳號/權限）
- Steps to Reproduce（可重現）
- Expected / Actual（可判定）
- Evidence（截圖/錄影/console/network log）
- Severity / Priority（影響程度與修復順序）

---

## 2. 手動測試的方法論工具箱（可落地）

### 2.1 風險導向（Risk-based Testing）

先決定「哪些東西壞了最致命」，再決定測試深度：

- 高風險：金流、權限、資料不可逆操作
- 中風險：搜尋、下單、核心流程
- 低風險：文案、非核心 UI

### 2.2 常用測試設計技巧

- 等價類別（Equivalence Partitioning）
- 邊界值分析（Boundary Value Analysis）
- 狀態轉換（State Transition）
- 決策表（Decision Table）
- 錯誤推測（Error Guessing）

### 2.3 啟發式清單（Heuristics）

當你不知道該測什麼時，使用啟發式避免漏測：

- Structure / Function / Data / Interface / Platform / Operations / Time（SFDIPOT）

---

## 3. 與自動化測試的分工

手動測試與自動化不是二選一，建議用以下原則分工：

- 可重複、可判定、頻繁回歸的案例 -> 自動化（UT/IT/E2E）
- 需要人判斷、易變動、或成本不值得自動化 -> 手動（特別是探索性與整合場景）

在本 repo 的開發流程裡，當「有功能邏輯需要驗證，但難以自動化」時，建議用「手動整合測試清單」作為替代方案 [Source: Code] docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md:364

---

## 4.（本專案）手動整合測試清單：最小可交付的手動框架

`docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md` 提供了一個可直接沿用的手動清單格式（包含前置準備、功能測試、邊界與錯誤處理、測試結論），並建議由 AI 根據 specs + 實作自動產出初稿，再由人審閱補齊 [Source: Code] docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md:364

---

## 5. 技術實作範例：從案例到執行

### 5.1 可機讀的 Test Case 格式（YAML）

```yaml
id: TC-CHECKOUT-001
title: 未登入使用者不可結帳
priority: P1
preconditions:
  - 使用者狀態為未登入
  - 購物車已有至少 1 件商品
steps:
  - action: 進入購物車頁
  - action: 點擊「前往結帳」
expected:
  - 跳轉到登入頁
  - 顯示提示「請先登入」
evidence_required:
  - screenshot
  - console_log
tags:
  - auth
  - checkout
  - regression
```

### 5.2 測試執行批次（Test Run）範例欄位

| run_id | case_id | tester | env | result | defect_id | evidence |
|---|---|---|---|---|---|---|
| RUN-20260208-01 | TC-CHECKOUT-001 | alice | staging | FAIL | BUG-214 | link/to/video |
| RUN-20260208-01 | TC-CHECKOUT-002 | alice | staging | PASS | - | link/to/screenshot |

### 5.3 需求追蹤矩陣（RTM）範例

| requirement_id | test_case_id | run_id | defect_id | automation_candidate |
|---|---|---|---|---|
| RQ-CHECKOUT-LOGIN | TC-CHECKOUT-001 | RUN-20260208-01 | BUG-214 | yes |
| RQ-COUPON-EXPIRE | TC-COUPON-005 | RUN-20260208-01 | - | no |

---

## 6. 探索性測試實作：Session-Based Testing（SBT）

### 6.1 45 分鐘 Session 範本

```markdown
Session ID: SBT-2026-02-08-01
Mission: 探索折扣碼在邊界條件下的穩定性
Timebox: 45 min
Build: staging-2026.02.08.3
Tester: alice

## Charter
- 範圍：折扣碼輸入、套用、移除、重整後狀態
- 排除：金流第三方 callback

## Notes (time-ordered)
- 00:08 輸入過期碼，UI 沒提示
- 00:12 連續點擊「套用」兩次，出現雙重折扣

## Findings
- F1 (High): 重複套用導致折扣重覆計算
- F2 (Medium): 過期碼缺少錯誤訊息

## Follow-up
- 開立 BUG-214, BUG-215
- 建議新增自動化回歸案例：TC-COUPON-DOUBLE-APPLY
```

### 6.2 SFDIPOT 快速檢查表（可直接用）

| 面向 | 可直接問的問題 |
|---|---|
| Structure | 權限、角色、資料狀態是否有分支沒覆蓋？ |
| Function | 主要功能與錯誤分支是否都有可觀察結果？ |
| Data | 空值、超長字串、特殊字元、過期資料是否驗過？ |
| Interface | 按鈕 disable/enable、提示訊息、跳轉是否一致？ |
| Platform | Chrome/Safari/Firefox、桌機/手機是否行為一致？ |
| Operations | 快速連點、返回重試、重整頁面是否造成異常？ |
| Time | 跨日、時區、有效期限邊界是否正確？ |

---

## 7. 缺陷管理實作：從回報到回歸

### 7.1 Bug 單最小模板

```markdown
Title: [Checkout] 未登入使用者可直接進入付款頁
Environment: staging-2026.02.08.3 / Chrome 122 / macOS 14.3
Severity: High
Priority: P1

Steps to Reproduce:
1. 使用未登入狀態開啟購物車頁
2. 點擊「前往結帳」

Expected:
- 應跳轉登入頁

Actual:
- 直接進入付款頁

Evidence:
- screenshot: ...
- video: ...
- console/network log: ...
```

### 7.2 Re-test（複測）檢查清單

- 修復版本與 commit hash 已標註
- 原始重現步驟可再現（修復前）
- 修復後主流程通過
- 相鄰流程沒有回歸（至少 1 條）
- Bug 單附上新證據並更新最終狀態（Verified / Closed）

### 7.3 由手動缺陷沉澱為自動化回歸

建議規則：符合以下 2 項以上就升級成自動化候選。

- P1/P2 缺陷
- 近 30 天重複發生
- 可穩定重現
- 檢查結果可明確 assert

可把候選案例回寫進規格流程，並搭配測試命令落地：

```bash
# 例：先從 specs 導出測試，再執行
uv run ai-dev derive-tests openspec/specs/
uv run ai-dev test -k "checkout"
```

---

## 8. 參考資料

- Session-Based Test Management（James Bach 相關概念，SBT）
  - https://www.satisfice.com/blog/archives/120 (Accessed: 2026-02-08)
- ISTQB Glossary（名詞與流程用語）
  - https://glossary.istqb.org/ (Accessed: 2026-02-08)
- Test Pyramid（Martin Fowler）
  - https://martinfowler.com/bliki/TestPyramid.html (Accessed: 2026-02-08)
