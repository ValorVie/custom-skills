# Codex 專案設定引導

只有目前 runtime 是 Codex，而且專案層 Agent 設定不存在、不完整或與
`profiles/codex.md` 不一致時，才讀取本文件。不要自動建立 `.codex/`，也不要因為缺少
設定而改寫使用者層 `~/.codex/config.toml`。

## 先做唯讀確認

1. 確認目前工作目錄對應的專案根目錄。
2. 檢查 `.codex/config.toml` 與 `.codex/agents/*.toml` 是否存在且可讀。
3. 確認 Codex 已信任目前專案；未信任的專案不會載入專案層設定。若尚未信任，先說明
   影響並另外取得使用者選擇，不要自行修改使用者層信任設定。
4. 檢查 Codex 版本、`multi_agent` 能力、runtime 可用角色與 session metadata。
5. 若目前 session 已從使用者層取得相同能力，仍要說明專案層沒有獨立設定；不要把
   使用者層設定複製進專案，除非使用者選擇建立。
6. 只列出設定鍵、檔案存在性與能力結果。不要輸出不相關的 MCP、token、環境變數或
   其他可能含機密的設定內容。

## 詢問使用者

先用一小段話說明現況與影響：

```text
目前專案沒有完整的 Codex Agent 設定。Custom Agent Router 的通用路由仍可使用，
但 terra_worker、terra_builder、sol_reviewer 與 fresh review 不能視為已驗證的專案能力。
要我建立建議設定、只顯示建議，還是暫不設定？
```

優先使用執行環境提供的互動式輸入；若沒有，改用簡短文字提問並等待回答。提供三個
互斥選項：

- `建立建議設定`：先列出預計新增或合併的檔案，再建立最小專案設定。
- `只顯示建議`：顯示設定內容或差異，不寫入檔案。
- `暫不設定`：保留抽象 tier，依現場已驗證能力直接處理或停止必要派工。

選擇不明確時不要猜。未選擇 `建立建議設定` 前，不得建立目錄、設定檔或角色檔。

## 建議設定

以下內容對應目前的 `profiles/codex.md`。套用前先核對本機 Codex 確實支援這些模型、
角色與設定鍵；若不一致，顯示偏差並停止建立，不要自行換成名字相近的模型。

`.codex/config.toml`：

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 15
```

`.codex/agents/terra-worker.toml`：

```toml
name = "terra_worker"
description = "執行規則固定、可重複且不需要設計決策的工作"
model = "gpt-5.6-terra"
model_reasoning_effort = "max"
developer_instructions = """
你是 Terra Worker。只執行交接訊息中規則固定、可重複的工作。
不得解釋模糊需求、選擇新方法、建立例外處理、操作任務追蹤器、stage、commit 或 push。
遇到第一個不符合固定規則的項目、未預期變更、權限不足或高風險操作時，立即停止並回報證據。
完成時回報完成內容、修改檔案、驗證結果與未解決問題。
"""
```

`.codex/agents/terra-builder.toml`：

```toml
name = "terra_builder"
description = "依既定設計執行有明確範圍與驗收條件的實作"
model = "gpt-5.6-terra"
model_reasoning_effort = "max"
developer_instructions = """
你是 Terra Builder。只處理交接訊息列出的目標、檔案與驗收條件。
可以在既定設計內實作、補測試並修正範圍內錯誤；不得改變設計、擴張範圍、操作任務追蹤器、stage、commit 或 push。
遇到需要新設計、未列入範圍的檔案、使用者既有變更衝突、權限不足或高風險操作時，立即停止並回報證據。
完成時回報完成內容、修改檔案、驗證結果與未解決問題。
"""
```

`.codex/agents/sol-reviewer.toml`：

```toml
name = "sol_reviewer"
description = "用全新 context 唯讀審查變更、證據與計畫符合度"
model = "gpt-5.6-sol"
model_reasoning_effort = "xhigh"
sandbox_mode = "read-only"
approval_policy = "never"
developer_instructions = """
你是 Sol Reviewer。使用全新 context，唯讀檢查原始需求、核准範圍、diff、測試證據與計畫符合度。
依 Blocking、Important、Note 回報問題；不得修改檔案、操作任務追蹤器或執行 Git mutation。
沒有發現問題也只代表審查通過，不得宣稱已取得部署、正式環境、資料庫或外部寫入批准。
"""
```

`max_concurrent_threads_per_session = 15` 是上限，不是預設派工數。Router 仍只依獨立工作
數與 runtime 剩餘 slot 使用必要數量。

## 建立與合併規則

- 若 `.codex/` 完全不存在，只建立上述四個檔案及必要目錄。
- 若設定已存在，先顯示最小差異，只合併缺少的 table 或 key，不整份覆寫。
- 若同名角色已存在但內容不同，停止並請使用者決定沿用或調整；不要靜默替換。
- 不為新專案建立舊式 `[agents.<name>] config_file` registry，也不自動遷移已能正常載入的
  舊式設定。
- 不加入 MCP、Hook、任務追蹤器、專案業務規則或未被要求的 Agent。
- 遵守目前專案的 Git、批准與敏感資料規則。建立設定不等於授權 commit 或 push。

## 建立後驗證

1. 驗證 TOML 可以解析，且三個角色檔都有 `name`、`description` 與
   `developer_instructions`。
2. 確認專案已被 Codex 信任；無法確認時，不把設定檔存在寫成設定已生效。
3. 提醒使用者重新啟動 Codex session，讓專案設定重新載入。
4. 在新 session 核對 `multi_agent`、可用角色、模型與 effort 的 runtime metadata。
5. `sol_reviewer.toml` 宣告唯讀不等於 runtime 已證明唯讀；仍依
   `profiles/codex.md` 的 Reviewer 安全限制驗證 parent、child 與 filesystem 權限。
6. 任一能力無法驗證時，保留抽象 tier 並記錄 binding 偏差，不宣稱 onboarding 完成。
