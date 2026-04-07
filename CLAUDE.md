<!-- >>> ai-dev:ai-dev-project | ⚠️ 以下為 ai-dev 管理的專案規則，必須遵守 -->
---

# Language

預設情況下，所有回應皆使用**繁體中文**
1. 敘述句一律用自然中文。
2. 英文只保留在必要處：
   - 專有名詞
   - 產品名
   - 設定名
   - 檔名
   - 路徑
   - 程式碼
   - 少數該領域已固定存在的術語（如 DB mutation、rollout、rollback）
3. 禁止把英文普通詞直接嵌入中文句法中，例如：
   - prerequisite
   - required
   - exact probe
   - live evidence
   - override 到
   - fixed 成
4. 優先改寫成自然中文，例如：
   - prerequisite → 前置條件
   - required → 本輪要求
   - live evidence → 工具實測 / 現場實測
   - exact probe → 直接驗證 / 精確探測
   - override 到 → 改指向 / 覆寫為
5. 風格以工程維運文件為準：短句、明確、可執行，不要文案腔。

---

<!-- UDS:STANDARDS:START -->
## Standards

**MUST** 語言完整規範 [zh-tw.md](.standards/zh-tw.md)
**MUST** commit 訊息規範 [commit-message.ai.yaml](.standards/commit-message.ai.yaml)（每次提交），目前使用英文類型 + 中文訊息，例如 `fix(API): 解決並發更新使用者資料時的競爭條件`
**MUST** 僅限 `custom-skills` / `ai-dev` repo）任何修改 `ai-dev` 命令、行為、副作用、狀態檔或資料流後，同步更新 `docs/ai-dev指令與資料流參考.md`
**SHOULD** git 工作流規範 [git-workflow.ai.yaml](.standards/git-workflow.ai.yaml)、[testing.ai.yaml](.standards/testing.ai.yaml)

完整標準在 `.standards/`（Level 3，58 個標準）。

<!-- UDS:STANDARDS:END -->

---
<!-- <<< ai-dev:ai-dev-project | 以上規則結束，確認已理解再開始任務 -->
