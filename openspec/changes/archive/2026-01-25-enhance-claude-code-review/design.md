## Context

本專案已使用官方的 `anthropics/claude-code-action@v1` GitHub Action 進行 code review。目前有兩個 workflow 檔案：
- `claude-code-review.yml`：使用 code-review plugin，在 PR 事件時觸發
- `claude.yml`：監聽 @claude mention，需要手動觸發

使用者需求：
1. PR 開啟時自動進行 code review（不需 @claude 觸發）
2. 排除 Draft PR
3. 客製化 code review 的審查重點
4. 指定回覆語言為繁體中文，專有名詞保留原文
5. 手動/自動設定方式需文件化
6. 審查標準需文件化以利維護
7. **新增**：基於業界 best practice 設計評分機制，提供合併建議

## Goals / Non-Goals

### Goals
- 配置 PR 自動觸發 Claude code review（排除 Draft PR）
- 提供可維護的 prompt 配置機制
- 預留檔案類型過濾機制
- 建立設定說明文件
- **基於業界標準設計審查評分系統**
- **提供各面向評分與綜合評分**
- **給予明確的合併建議**

### Non-Goals
- 不修改現有的 @claude 手動觸發功能
- 不引入額外的 CI/CD 工具

---

## 業界 Best Practice 調查結果

### 來源一：Google Engineering Practices

[Google's Engineering Practices](https://github.com/google/eng-practices) 定義的審查面向：

| 面向 | 重點 |
|------|------|
| Design | 程式碼互動是否合理、是否屬於此 codebase |
| Functionality | 實作是否符合意圖、邊界案例處理 |
| Complexity | 是否過度工程化、程式碼是否易讀 |
| Tests | 測試是否正確、是否會在程式壞掉時失敗 |
| Naming | 命名是否清楚傳達意圖 |
| Comments | 註解是否解釋「為什麼」而非「什麼」 |
| Style | 是否符合 style guide |
| Documentation | 文件是否更新 |

**核心原則**：「當 CL 明確改善整體程式碼健康度時，即使不完美也應批准」

### 來源二：8 Pillars of Code Review (2025)

[Nerdify 的 8 Pillars](https://getnerdify.com/blog/code-review-checklist/) 定義：

1. **Code Functionality** - 功能驗證
2. **Readability & Maintainability** - 可讀性與可維護性
3. **Security Vulnerability** - 安全漏洞評估
4. **Performance & Efficiency** - 效能與效率
5. **Error Handling** - 錯誤處理
6. **Testing Coverage** - 測試覆蓋
7. **Code Standards** - 程式碼標準
8. **Architecture & Design** - 架構與設計模式

### 來源三：Code Quality Metrics (Qodo 2026)

[Qodo 的 10 項指標](https://www.qodo.ai/blog/code-quality-metrics-2026/)：

| 指標 | 說明 | 建議門檻 |
|------|------|----------|
| Cyclomatic Complexity | 邏輯路徑數量 | >15 需重構 |
| Defect Density | 每千行程式碼的缺陷數 | 依模組類型設定 |
| Test Effectiveness | 測試是否真正捕捉錯誤 | Mutation score >60-70% |
| Static Analysis Issues | 靜態分析問題密度 | 零高嚴重性問題 |
| Security MTTR | 安全問題修復時間 | 高嚴重性 5 天內 |
| Duplicate Code Ratio | 重複程式碼比例 | <5% |

### 來源四：Microsoft AI Code Review

[Microsoft 的方法](https://devblogs.microsoft.com/engineering-at-microsoft/enhancing-code-quality-at-scale-with-ai-powered-code-reviews/)：

- 按問題類別標註（exception handling, null check, sensitive data）
- 人類保留最終決策權
- 衡量指標：PR 完成時間改善 10-20%

---

## Decision: 評分系統設計

### Decision 1: 評分維度

基於業界標準，定義 **7 個核心審查維度**：

| 維度 | 英文 | 權重 | 來源依據 |
|------|------|------|----------|
| 安全性 | Security | 20% | OWASP, Google, 8 Pillars |
| 功能正確性 | Functionality | 20% | Google, 8 Pillars |
| 程式碼品質 | Code Quality | 15% | Google (Complexity, Naming), 8 Pillars |
| 架構設計 | Architecture | 15% | Google (Design), 8 Pillars |
| 測試覆蓋 | Testing | 15% | Google, 8 Pillars, Qodo |
| 錯誤處理 | Error Handling | 10% | 8 Pillars |
| 文件完整性 | Documentation | 5% | Google |

**權重設計理由**：
- 安全性與功能正確性最高（20%），因為直接影響產品品質與用戶
- 程式碼品質、架構、測試次之（15%），影響長期可維護性
- 錯誤處理（10%）、文件（5%）為輔助面向

### Decision 2: 評分等級

每個維度採用 **5 級評分制**：

| 分數 | 等級 | 說明 | 圖示 |
|------|------|------|------|
| 5 | Excellent | 超越標準，可作為範例 | ⭐⭐⭐⭐⭐ |
| 4 | Good | 符合標準，有小幅改進空間 | ⭐⭐⭐⭐ |
| 3 | Acceptable | 基本符合，建議改進 | ⭐⭐⭐ |
| 2 | Needs Work | 有明顯問題，需要修改 | ⭐⭐ |
| 1 | Critical | 嚴重問題，必須修正 | ⭐ |

### Decision 3: 綜合評分計算

```
綜合分數 = Σ(維度分數 × 權重)

範例：
- 安全性: 4 × 0.20 = 0.80
- 功能正確性: 5 × 0.20 = 1.00
- 程式碼品質: 4 × 0.15 = 0.60
- 架構設計: 3 × 0.15 = 0.45
- 測試覆蓋: 4 × 0.15 = 0.60
- 錯誤處理: 4 × 0.10 = 0.40
- 文件完整性: 3 × 0.05 = 0.15
-------------------------------
綜合分數 = 4.00
```

### Decision 4: 合併建議準則

基於 [Google 的標準](https://google.github.io/eng-practices/review/reviewer/standard.html)：「當變更明確改善整體程式碼健康度時，即使不完美也應批准」

| 綜合分數 | 建議 | 說明 |
|----------|------|------|
| 4.5 - 5.0 | ✅ **強烈建議合併** | 優秀的程式碼，可作為範例 |
| 4.0 - 4.4 | ✅ **建議合併** | 符合標準，有小幅改進空間但不阻擋 |
| 3.5 - 3.9 | ⚠️ **有條件合併** | 建議改進標記項目後合併 |
| 3.0 - 3.4 | ⚠️ **建議修改後合併** | 需解決主要問題 |
| 2.0 - 2.9 | ❌ **不建議合併** | 有明顯問題需要修正 |
| 1.0 - 1.9 | ❌ **強烈不建議合併** | 嚴重問題，必須修正 |

**額外規則**（參考 Qodo SLA）：
- 任何維度 ≤ 2 分：該維度為 **Blocking Issue**，需優先解決
- 安全性維度 ≤ 3 分：自動標記為 **Security Review Required**

### Decision 5: 審查報告格式

```markdown
# Code Review Report

## 📊 綜合評分: X.X / 5.0

| 維度 | 分數 | 權重 | 加權分 |
|------|------|------|--------|
| 🔒 安全性 | X/5 | 20% | X.XX |
| ✅ 功能正確性 | X/5 | 20% | X.XX |
| 📝 程式碼品質 | X/5 | 15% | X.XX |
| 🏗️ 架構設計 | X/5 | 15% | X.XX |
| 🧪 測試覆蓋 | X/5 | 15% | X.XX |
| ⚠️ 錯誤處理 | X/5 | 10% | X.XX |
| 📚 文件完整性 | X/5 | 5% | X.XX |

## 🎯 合併建議

[✅ 建議合併 / ⚠️ 有條件合併 / ❌ 不建議合併]

### Blocking Issues (必須修正)
- ...

### Suggestions (建議改進)
- ...

### Highlights (值得讚許)
- ...
```

---

## Decision 6: 各維度評分細則

### 6.1 安全性 (Security) - 20%

| 分數 | 標準 |
|------|------|
| 5 | 無安全問題，有主動防禦措施 |
| 4 | 無安全問題 |
| 3 | 有低風險問題（如缺少輸入驗證） |
| 2 | 有中風險問題（如 XSS 可能性） |
| 1 | 有高風險問題（SQL injection、敏感資料洩露） |

**檢查項目**：
- SQL injection / NoSQL injection
- XSS (Cross-Site Scripting)
- CSRF (Cross-Site Request Forgery)
- 輸入驗證
- 敏感資料處理（API key、密碼、PII）
- 認證/授權邏輯
- 安全通訊協定

### 6.2 功能正確性 (Functionality) - 20%

| 分數 | 標準 |
|------|------|
| 5 | 功能完整，邊界案例處理周全 |
| 4 | 功能正確，少數邊界案例可改進 |
| 3 | 核心功能正確，部分邊界案例未處理 |
| 2 | 有明顯功能缺陷或邏輯錯誤 |
| 1 | 核心功能不正確或有嚴重 bug |

**檢查項目**：
- 是否符合需求/ticket 描述
- 邊界案例處理
- 錯誤狀態處理
- 資料驗證
- 並發/競爭條件（如適用）

### 6.3 程式碼品質 (Code Quality) - 15%

| 分數 | 標準 |
|------|------|
| 5 | 可作為範例，清晰簡潔 |
| 4 | 可讀性高，遵循最佳實踐 |
| 3 | 可讀，有改進空間 |
| 2 | 可讀性差，有多處違反最佳實踐 |
| 1 | 難以理解，嚴重違反規範 |

**檢查項目**（參考 Google 的 Complexity, Naming, Style）：
- 命名清晰度
- 函式單一職責
- DRY 原則（無重複程式碼）
- Cyclomatic complexity（建議 <15）
- 程式碼格式一致性

### 6.4 架構設計 (Architecture) - 15%

| 分數 | 標準 |
|------|------|
| 5 | 設計優雅，易於擴展 |
| 4 | 設計合理，符合現有架構 |
| 3 | 基本符合架構，有改進空間 |
| 2 | 有架構違規或不一致 |
| 1 | 嚴重違反架構原則 |

**檢查項目**（參考 Google 的 Design）：
- 關注點分離（Separation of Concerns）
- 依賴方向正確
- 設計模式使用適當
- 介面契約遵守
- 無循環依賴

### 6.5 測試覆蓋 (Testing) - 15%

| 分數 | 標準 |
|------|------|
| 5 | 測試完整，覆蓋所有邊界案例 |
| 4 | 有適當測試，覆蓋主要路徑 |
| 3 | 有基本測試，覆蓋不完整 |
| 2 | 測試不足或品質低 |
| 1 | 無測試或測試無效 |

**檢查項目**（參考 Google Tests, Qodo Test Effectiveness）：
- 是否有對應測試
- 測試是否會在程式壞掉時失敗
- 邊界案例覆蓋
- 測試命名清晰
- 測試獨立性

### 6.6 錯誤處理 (Error Handling) - 10%

| 分數 | 標準 |
|------|------|
| 5 | 錯誤處理完善，有適當回復機制 |
| 4 | 錯誤處理適當 |
| 3 | 基本錯誤處理，有改進空間 |
| 2 | 錯誤處理不足 |
| 1 | 無錯誤處理或處理不當 |

**檢查項目**：
- 捕捉特定例外（非通用 catch）
- 適當的錯誤訊息
- 資源清理（finally/using）
- 錯誤日誌記錄
- 優雅降級

### 6.7 文件完整性 (Documentation) - 5%

| 分數 | 標準 |
|------|------|
| 5 | 文件完整且清晰 |
| 4 | 文件適當 |
| 3 | 有基本文件 |
| 2 | 文件不足 |
| 1 | 無文件或文件過時 |

**檢查項目**（參考 Google Documentation, Comments）：
- Public API 文件
- 複雜邏輯註解（解釋「為什麼」）
- README 更新（如適用）
- CHANGELOG 更新（如適用）

---

## Workflow 配置

（保持原有設計，略）

---

## Risks / Trade-offs

### Risk 1: 評分主觀性
- **風險**：AI 評分可能不一致
- **緩解**：提供明確的評分標準與範例

### Risk 2: 過度嚴格
- **風險**：評分過於嚴格導致 PR 進度緩慢
- **緩解**：採用 Google 原則「改善即可合併」，分數 ≥3.5 即可有條件合併

### Risk 3: API 配額消耗
- **緩解**：排除 Draft PR、預留 paths 過濾

---

## Migration Plan

1. 建立 `.github/prompts/code-review.md` 審查標準檔案（含評分系統）
2. 建立 `.github/CODE_REVIEW.md` 設定說明文件
3. 修改 `.github/workflows/claude-code-review.yml`
4. 測試評分系統

---

## 參考資料

- [Google Engineering Practices](https://github.com/google/eng-practices)
- [Google: What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html)
- [Google: The Standard of Code Review](https://google.github.io/eng-practices/review/reviewer/standard.html)
- [8 Pillars of Code Review (2025)](https://getnerdify.com/blog/code-review-checklist/)
- [Code Quality Metrics for 2026](https://www.qodo.ai/blog/code-quality-metrics-2026/)
- [Microsoft AI Code Review](https://devblogs.microsoft.com/engineering-at-microsoft/enhancing-code-quality-at-scale-with-ai-powered-code-reviews/)
- [Chelsea Troy: Code Stewardship Rubric](https://chelseatroy.com/2021/10/29/a-rubric-for-evaluating-team-members-contributions-to-a-maintainable-code-base/)
