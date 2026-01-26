
# Claude Code 專案指南
# 由 Universal Dev Standards CLI 生成
# https://github.com/AsiaOstrich/universal-dev-standards

## 對話語言 / Conversation Language
所有回覆必須使用**繁體中文 (Traditional Chinese)**。
AI 助手應以繁體中文回覆使用者的問題與請求。

---

## 反幻覺協議
參考: .standards/anti-hallucination.md

### 實證分析
1. **讀取檔案**: 分析前必須先讀取檔案
2. **禁止猜測**: 不得猜測 API、類別名稱或函式庫版本
3. **明確不確定性**: 若未看過程式碼，需說明「我需要讀取 [檔案] 來確認」

### 來源標註
- 關於程式碼的每項事實陳述必須引用來源
- 格式: `[Source: Code] path/to/file:line`
- 外部文件: `[Source: External] http://url (存取日期: Date)`

### 確定性分類
使用標籤表示信心程度:
- `[確認]` - 已從程式碼/文件驗證
- `[推斷]` - 從證據邏輯推導
- `[假設]` - 合理猜測，需驗證
- `[未知]` - 無法確定

### 建議
提供選項時，必須明確標明「建議」選項並說明理由。

---

## 提交訊息標準
參考: .standards/commit-message-guide.md, .standards/options/traditional-chinese.ai.yaml

### 格式
```
<類型>(<範圍>): <主旨>

<本文>

<頁腳>
```

### 類型
| 類型 | 英文對照 | 說明 | 範例 |
|------|----------|------|------|
| `功能` | feat | 新功能 | 功能(認證): 新增 OAuth2 登入 |
| `修正` | fix | 錯誤修正 | 修正(api): 處理空值回應 |
| `文件` | docs | 文件更新 | 文件(readme): 更新安裝指南 |
| `樣式` | style | 格式調整 | 樣式(lint): 修正縮排 |
| `重構` | refactor | 程式碼重構 | 重構(user): 抽取驗證邏輯 |
| `測試` | test | 測試相關 | 測試(cart): 新增結帳測試 |
| `雜項` | chore | 維護任務 | 雜項(deps): 更新套件 |
| `效能` | perf | 效能改善 | 效能(query): 優化資料庫查詢 |
| `整合` | ci | 持續整合 | 整合(github): 新增部署流程 |

### 規則
- 主題行: 最多 72 字元
- 使用祈使語氣
- 本文: 說明做了什麼及為什麼，而非如何做

---

## 程式碼審查清單
參考: .standards/checkin-standards.md

### 每次提交前
1. **建置驗證**
   - [ ] 程式碼編譯成功
   - [ ] 所有相依套件已滿足

2. **測試驗證**
   - [ ] 所有現有測試通過
   - [ ] 新程式碼有對應測試
   - [ ] 測試覆蓋率未下降

3. **程式碼品質**
   - [ ] 遵循編碼標準
   - [ ] 無寫死的密鑰
   - [ ] 無安全漏洞

4. **文件**
   - [ ] API 文件已更新（如適用）
   - [ ] 使用者可見變更已更新 CHANGELOG

### 禁止提交情況
- 建置有錯誤
- 測試失敗
- 包含除錯程式碼（console.log 等）

---

<!-- UDS:STANDARDS:START -->
## 規範文件參考

**重要**：執行相關任務時，務必讀取並遵循 `.standards/` 目錄下的對應規範：

**核心規範：**
- `.standards/anti-hallucination.md`
- `.standards/commit-message.ai.yaml`
- `.standards/traditional-chinese.ai.yaml`
- `.standards/checkin-standards.md`
- `.standards/spec-driven-development.md`
- `.standards/code-review-checklist.md`
- `.standards/git-workflow.ai.yaml`
- `.standards/github-flow.ai.yaml`
- `.standards/squash-merge.ai.yaml`
- `.standards/versioning.md`
- `.standards/changelog-standards.md`
- `.standards/testing.ai.yaml`
- `.standards/unit-testing.ai.yaml`
- `.standards/integration-testing.ai.yaml`
- `.standards/documentation-structure.md`
- `.standards/documentation-writing-standards.md`
- `.standards/project-structure.md`
- `.standards/error-code-standards.md`
- `.standards/logging-standards.md`
- `.standards/test-completeness-dimensions.md`
- `.standards/test-driven-development.md`
- `.standards/requirement-checklist.md`
- `.standards/requirement-template.md`
- `.standards/requirement-document-template.md`

<!-- UDS:STANDARDS:END -->

---
