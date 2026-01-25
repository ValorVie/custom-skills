## ADDED Requirements

### Requirement: PR 自動觸發 Code Review

當非 Draft 的 Pull Request 被開啟、同步或準備好審查時，系統 SHALL 自動觸發 Claude Code Review，無需手動 @claude 提及。

#### Scenario: 正式 PR 開啟時自動觸發
- **GIVEN** 一個新的 Pull Request 被開啟
- **WHEN** PR 狀態為 opened, synchronize, ready_for_review 或 reopened
- **AND** PR 不是 Draft 狀態
- **THEN** Claude Code Review workflow SHALL 自動執行
- **AND** 不需要在 PR 內容中包含 @claude 關鍵字

#### Scenario: Draft PR 不觸發
- **GIVEN** 一個 Draft Pull Request 被開啟或更新
- **WHEN** PR 類型為 draft
- **THEN** 系統 SHALL NOT 觸發自動 code review
- **AND** 僅在 PR 標記為 ready_for_review 時才觸發

### Requirement: 檔案類型過濾機制

系統 SHALL 預留檔案類型過濾機制，允許未來限制只審查特定類型的檔案。

#### Scenario: 預留過濾配置
- **GIVEN** workflow 配置檔案
- **WHEN** 需要限制審查的檔案類型
- **THEN** SHALL 提供 `paths` 配置選項（目前以註解形式保留）
- **AND** 配置範例 SHALL 包含常見程式碼類型（如 `**/*.py`, `**/*.ts`, `**/*.js`）

### Requirement: 評分系統

系統 SHALL 提供基於業界 best practice 的多維度評分系統。

#### Scenario: 評分維度
- **GIVEN** code review prompt 檔案存在
- **WHEN** Claude 執行 code review
- **THEN** SHALL 評估以下 7 個維度：
  - 安全性 (Security) - 權重 20%
  - 功能正確性 (Functionality) - 權重 20%
  - 程式碼品質 (Code Quality) - 權重 15%
  - 架構設計 (Architecture) - 權重 15%
  - 測試覆蓋 (Testing) - 權重 15%
  - 錯誤處理 (Error Handling) - 權重 10%
  - 文件完整性 (Documentation) - 權重 5%

#### Scenario: 評分等級
- **GIVEN** 每個評分維度
- **WHEN** 進行評分
- **THEN** SHALL 使用 1-5 分的評分等級：
  - 5 分：Excellent - 超越標準
  - 4 分：Good - 符合標準
  - 3 分：Acceptable - 基本符合
  - 2 分：Needs Work - 需要修改
  - 1 分：Critical - 必須修正

#### Scenario: 綜合評分計算
- **GIVEN** 各維度已評分
- **WHEN** 計算綜合分數
- **THEN** SHALL 使用加權平均公式：
  - 綜合分數 = Σ(維度分數 × 維度權重)

### Requirement: 合併建議

系統 SHALL 根據綜合評分提供明確的合併建議。

#### Scenario: 合併建議準則
- **GIVEN** 綜合分數已計算
- **WHEN** 提供合併建議
- **THEN** SHALL 依據以下準則：
  - 4.5-5.0 分：強烈建議合併
  - 4.0-4.4 分：建議合併
  - 3.5-3.9 分：有條件合併
  - 3.0-3.4 分：建議修改後合併
  - 2.0-2.9 分：不建議合併
  - 1.0-1.9 分：強烈不建議合併

#### Scenario: Blocking Issue 標記
- **GIVEN** 任何維度評分 ≤ 2 分
- **WHEN** 生成審查報告
- **THEN** 該維度 SHALL 被標記為 Blocking Issue
- **AND** 報告中 SHALL 明確列出需優先解決

#### Scenario: 安全性特別處理
- **GIVEN** 安全性維度評分 ≤ 3 分
- **WHEN** 生成審查報告
- **THEN** SHALL 標記為 Security Review Required

### Requirement: 審查報告格式

系統 SHALL 生成結構化的審查報告。

#### Scenario: 報告內容
- **GIVEN** code review 完成
- **WHEN** 生成報告
- **THEN** 報告 SHALL 包含以下區塊：
  - 綜合評分（含各維度分數表格）
  - 合併建議（含理由說明）
  - Blocking Issues（必須修正的問題）
  - Suggestions（建議改進的項目）
  - Highlights（值得讚許的部分）

### Requirement: 回覆語言規範

Code Review 的回覆 SHALL 使用繁體中文，專有名詞保留英文原文。

#### Scenario: 語言設定
- **GIVEN** Claude 執行 code review
- **WHEN** 撰寫審查意見
- **THEN** 回覆語言 SHALL 為繁體中文
- **AND** 專有名詞（如 API、SQL injection、XSS、PR）SHALL 保留英文原文
- **AND** 程式碼範例 SHALL 保持原樣

### Requirement: 設定說明文件

系統 SHALL 提供設定說明文件，說明手動與自動觸發的配置方式。

#### Scenario: 文件內容
- **GIVEN** 使用者需要了解或修改 code review 設定
- **WHEN** 查閱設定說明
- **THEN** `.github/CODE_REVIEW.md` SHALL 包含以下內容：
  - 功能概述
  - 評分系統說明
  - 自動觸發設定說明
  - 手動觸發設定說明（@claude 用法）
  - Prompt 配置位置與修改方式
  - 檔案類型過濾配置說明
  - 常見問題
  - 參考資料

### Requirement: Workflow 權限配置

GitHub Action workflow SHALL 配置正確的權限以執行 code review。

#### Scenario: 必要權限
- **GIVEN** Claude Code Review workflow 執行
- **WHEN** 配置 workflow permissions
- **THEN** SHALL 包含以下權限：
  - `contents: read` - 讀取程式碼
  - `pull-requests: read` - 讀取 PR 資訊
  - `issues: read` - 讀取 issue 資訊
  - `id-token: write` - OAuth 驗證

### Requirement: 與現有 Workflow 整合

新的自動 review 功能 SHALL 與現有的 @claude 手動觸發功能共存，職責分離。

#### Scenario: 職責分離
- **GIVEN** 專案同時有自動 review 和手動 @claude 功能
- **WHEN** 配置 workflows
- **THEN** `claude-code-review.yml` SHALL 負責自動 PR review（含評分報告）
- **AND** `claude.yml` SHALL 負責手動 @claude 互動式問答
- **AND** 兩個 workflow SHALL NOT 相互干擾
