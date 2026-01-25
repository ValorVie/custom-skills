# Claude Code Review 設定說明

本專案使用 [Claude Code Action](https://github.com/anthropics/claude-code-action) 進行自動化 code review，並採用基於業界 best practice 的評分系統。

## 概述

本專案提供兩種 Claude 觸發方式：

| 方式 | Workflow 檔案 | 觸發條件 | 用途 |
|------|---------------|----------|------|
| **自動觸發** | `claude-code-review.yml` | PR 開啟/同步（排除 Draft） | 自動化 code review |
| **手動觸發** | `claude.yml` | 在 PR/Issue 中 @claude | 互動式問答 |

---

## 評分系統

### 評分維度

基於 [Google Engineering Practices](https://github.com/google/eng-practices)、[8 Pillars of Code Review](https://getnerdify.com/blog/code-review-checklist/) 等業界標準設計：

| 維度 | 權重 | 說明 |
|------|------|------|
| 🔒 安全性 | 20% | SQL injection、XSS、敏感資料、認證授權 |
| ✅ 功能正確性 | 20% | 需求符合度、邊界案例、邏輯正確性 |
| 📝 程式碼品質 | 15% | 可讀性、命名、DRY、複雜度 |
| 🏗️ 架構設計 | 15% | 設計模式、關注點分離、依賴方向 |
| 🧪 測試覆蓋 | 15% | 測試存在性、覆蓋率、測試品質 |
| ⚠️ 錯誤處理 | 10% | 例外處理、錯誤訊息、資源清理 |
| 📚 文件完整性 | 5% | API 文件、註解、README/CHANGELOG |

### 評分等級

| 分數 | 等級 | 說明 |
|------|------|------|
| 5 | Excellent | 超越標準，可作為範例 |
| 4 | Good | 符合標準，有小幅改進空間 |
| 3 | Acceptable | 基本符合，建議改進 |
| 2 | Needs Work | 有明顯問題，需要修改 |
| 1 | Critical | 嚴重問題，必須修正 |

### 合併建議

| 綜合分數 | 建議 |
|----------|------|
| 4.5 - 5.0 | ✅ 強烈建議合併 |
| 4.0 - 4.4 | ✅ 建議合併 |
| 3.5 - 3.9 | ⚠️ 有條件合併 |
| 3.0 - 3.4 | ⚠️ 建議修改後合併 |
| 2.0 - 2.9 | ❌ 不建議合併 |
| 1.0 - 1.9 | ❌ 強烈不建議合併 |

完整評分標準請參考 [`.github/prompts/code-review.md`](prompts/code-review.md)。

---

## 自動觸發設定

### 觸發條件

自動 code review 會在以下 PR 事件時觸發：

- `opened` - PR 開啟
- `synchronize` - PR 有新的 commit
- `ready_for_review` - Draft PR 標記為 ready
- `reopened` - PR 重新開啟

### 排除條件

- **Draft PR 不會觸發**：只有正式 PR 才會自動審查
- 可透過 `paths` 配置限制只審查特定檔案類型（見下方說明）

### Workflow 配置

檔案位置：`.github/workflows/claude-code-review.yml`

```yaml
on:
  pull_request:
    types: [opened, synchronize, ready_for_review, reopened]

jobs:
  claude-review:
    if: github.event.pull_request.draft == false
    # ...
```

---

## 手動觸發設定（@claude）

### 使用方式

在 PR 或 Issue 的 comment 中提及 `@claude`，即可觸發 Claude 回應：

```
@claude 請幫我檢查這個函式的效能問題
```

```
@claude 這段程式碼有什麼改善建議？
```

### 支援的觸發位置

- PR comment
- PR review comment
- Issue comment
- Issue body/title

### Workflow 配置

檔案位置：`.github/workflows/claude.yml`

```yaml
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  # ...

jobs:
  claude:
    if: contains(github.event.comment.body, '@claude')
    # ...
```

---

## Prompt 配置

### 審查標準檔案

檔案位置：`.github/prompts/code-review.md`

此檔案定義 Claude 進行 code review 時的完整審查標準，包含：

- 回覆語言規範（繁體中文，專有名詞保留原文）
- 7 個評分維度與權重
- 各維度的評分標準（1-5 分）
- 合併建議準則
- 審查報告格式
- 審查原則與範例

### 修改審查標準

如需調整審查重點或評分標準，直接編輯 `.github/prompts/code-review.md` 即可。

**可調整項目**：
- 各維度權重
- 評分標準描述
- 檢查項目清單
- 報告格式
- 合併建議門檻

修改後的變更會在下一次 PR 觸發時生效。

---

## 檔案類型過濾配置

如需限制只審查特定類型的檔案，可在 workflow 中啟用 `paths` 配置：

### 啟用方式

編輯 `.github/workflows/claude-code-review.yml`：

```yaml
on:
  pull_request:
    types: [opened, synchronize, ready_for_review, reopened]
    # 取消註解以下區塊並調整檔案類型
    paths:
      - "**/*.py"
      - "**/*.ts"
      - "**/*.tsx"
      - "**/*.js"
      - "**/*.jsx"
```

### 常用檔案類型範例

| 語言 | 路徑模式 |
|------|----------|
| Python | `"**/*.py"` |
| TypeScript | `"**/*.ts"`, `"**/*.tsx"` |
| JavaScript | `"**/*.js"`, `"**/*.jsx"` |
| Go | `"**/*.go"` |
| Rust | `"**/*.rs"` |
| Java | `"**/*.java"` |

---

## 常見問題

### Q: 為什麼 Draft PR 沒有觸發 code review？

A: 這是預期行為。Draft PR 被排除在自動審查之外，以節省 API 配額。當 PR 標記為 ready for review 時才會觸發。

### Q: 如何修改 Claude 的回覆語言？

A: 編輯 `.github/prompts/code-review.md` 中的「回覆語言」區段。

### Q: 如何調整評分維度的權重？

A: 編輯 `.github/prompts/code-review.md` 中的「評分維度與權重」表格，以及「綜合評分計算」公式。

### Q: 自動 review 和手動 @claude 會衝突嗎？

A: 不會。兩個 workflow 是獨立運作的：
- `claude-code-review.yml` 負責自動審查（含評分報告）
- `claude.yml` 負責互動式問答

### Q: 如何減少 API 配額消耗？

A: 可以透過以下方式：
1. 排除 Draft PR（已預設啟用）
2. 使用 `paths` 過濾只審查特定檔案類型
3. 限制特定 branch 才觸發

### Q: 評分過於嚴格怎麼辦？

A: 評分系統遵循 Google 的原則：「當變更明確改善整體程式碼健康度時，即使不完美也應批准」。綜合分數 ≥3.5 即可有條件合併。如需調整標準，可修改 `.github/prompts/code-review.md` 中的評分細則。

### Q: 如何查看 Claude 的審查結果？

A: Claude 會在 PR 中以 comment 的形式提供評分報告，包含：
- 各維度評分與加權分
- 綜合評分
- 合併建議
- Blocking Issues、Suggestions、Highlights

---

## 相關檔案

| 檔案 | 說明 |
|------|------|
| `.github/workflows/claude-code-review.yml` | 自動觸發 workflow |
| `.github/workflows/claude.yml` | 手動 @claude workflow |
| `.github/prompts/code-review.md` | 審查標準與評分系統 |
| `.standards/code-review.ai.yaml` | 專案 code review 規範 |

---

## 參考資料

評分系統基於以下業界 best practice：
- [Google Engineering Practices](https://github.com/google/eng-practices)
- [Google: What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html)
- [Google: The Standard of Code Review](https://google.github.io/eng-practices/review/reviewer/standard.html)
- [8 Pillars of Code Review (2025)](https://getnerdify.com/blog/code-review-checklist/)
- [Code Quality Metrics for 2026](https://www.qodo.ai/blog/code-quality-metrics-2026/)
- [Microsoft AI Code Review](https://devblogs.microsoft.com/engineering-at-microsoft/enhancing-code-quality-at-scale-with-ai-powered-code-reviews/)
