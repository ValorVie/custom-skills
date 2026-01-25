## 1. 業界調查與設計

- [x] 1.1 調查 Google Engineering Practices
- [x] 1.2 調查 8 Pillars of Code Review
- [x] 1.3 調查 Code Quality Metrics (Qodo)
- [x] 1.4 調查 Microsoft AI Code Review 方法
- [x] 1.5 設計評分維度與權重
- [x] 1.6 設計評分等級（1-5 分）
- [x] 1.7 設計合併建議準則
- [x] 1.8 設計審查報告格式

## 2. 建立審查標準文件

- [x] 2.1 建立 `.github/prompts/code-review.md` 檔案
- [x] 2.2 撰寫評分系統說明
- [x] 2.3 撰寫各維度評分標準
- [x] 2.4 撰寫檢查項目清單
- [x] 2.5 撰寫報告格式模板
- [x] 2.6 加入語言規範說明（繁體中文，專有名詞保留原文）
- [x] 2.7 加入參考資料

## 3. 建立設定說明文件

- [x] 3.1 建立 `.github/CODE_REVIEW.md` 檔案
- [x] 3.2 撰寫功能概述
- [x] 3.3 撰寫評分系統說明
- [x] 3.4 撰寫自動觸發設定說明
- [x] 3.5 撰寫手動觸發設定說明（@claude 用法）
- [x] 3.6 撰寫 Prompt 配置說明
- [x] 3.7 撰寫檔案類型過濾配置說明
- [x] 3.8 撰寫常見問題
- [x] 3.9 加入參考資料

## 4. 修改 Workflow 配置

- [x] 4.1 修改 `.github/workflows/claude-code-review.yml`
- [x] 4.2 加入 Draft PR 排除條件 (`if: github.event.pull_request.draft == false`)
- [x] 4.3 加入預留的 `paths` 過濾配置（註解形式）
- [x] 4.4 配置 `prompt` 參數引用審查標準
- [x] 4.5 確認權限配置正確

## 5. 驗證與測試

- [ ] 5.1 建立測試 PR 驗證自動觸發功能
- [ ] 5.2 建立 Draft PR 驗證不會觸發
- [ ] 5.3 確認評分報告格式正確
- [ ] 5.4 確認 code review 回覆語言為繁體中文
- [ ] 5.5 驗證與 `claude.yml` 的 @claude 功能不衝突
