# Codex runtime profile

本 profile 綁定目前可驗證的 Codex 角色。使用前先核對當前專案的 `.codex/config.toml`、
角色檔與 runtime metadata；任一項不一致時，以現場較低能力為準並記錄偏差。

## 已驗證基線

| 項目 | 值 | 證據 |
|------|----|------|
| Codex CLI | `0.146.1` | `codex --version` |
| Multi-agent | `multi_agent` stable 且專案已啟用 | `codex features list`、`.codex/config.toml` |
| Session 上限 | 最多 15 threads | `.codex/config.toml` 的 `max_concurrent_threads_per_session = 15` |
| 深度 | 1 | `.codex/config.toml` 的 `max_depth = 1` |
| Luna | 不可用 | 當前 Codex model／custom role 清單沒有 Luna |

15 是上限，不是預設派工數。實際並行數取 runtime 剩餘 slot、專案限制與獨立工作數的
最小值。

## 能力綁定

| Tier／用途 | Codex binding | 模型與 effort | 使用限制 |
|------------|---------------|---------------|----------|
| `light` | `terra_worker` | `gpt-5.6-terra max` | 只做規則固定、可重複的工作；遇到第一個例外就停止 |
| `standard` | `terra_builder` | `gpt-5.6-terra max` | 只在設計、檔案範圍與驗收已定時實作 |
| `frontier` | Sol Lead | `gpt-5.6-sol xhigh` | 處理歧義、架構、安全與最終仲裁；先驗證主 session metadata |
| fresh review | `sol_reviewer` | `gpt-5.6-sol xhigh` | 使用全新 context；高風險時還必須證明 sandbox 與 filesystem 唯讀 |

`light` 與 `standard` 目前使用同一模型與 effort，差異只在角色契約。不要宣稱 `light`
比較便宜，也不要為了湊出三層而使用不存在的 Luna。

## 綁定方式

1. 先依通用 Router 決定 tier、shape 與 review，再套用本 profile。
2. 只有 runtime 的 custom role 清單與 metadata 符合上表時，才使用 named role。
3. `frontier` 預設由 Sol Lead 負責。若主 session 不是 `gpt-5.6-sol xhigh`：
   - 非 mutation 的分析可在 runtime 允許精確 override 時，使用 `fork_turns="none"`
     建立 `gpt-5.6-sol xhigh` 的 fresh agent；由 Lead 保留整合與授權責任。
   - 無法驗證 override，或工作包含高風險 mutation 時，記錄 binding 偏差並停止自動
     完成聲明，不以目前模型冒充 Sol。
4. named role 不可用時，主 Agent 可以直接完成低風險工作，或使用較高且已驗證的
   tier；不得用較低 tier 替代必要判斷。

在通用路由紀錄後另加一行 binding receipt：

```text
profile=codex binding=terra_builder model=gpt-5.6-terra effort=max deviation=none
```

`deviation` 使用 `none`，或簡短記錄實際偏差，例如 `lead-direct-no-light-role`。這一行
只記錄 runtime 綁定，不改變通用 route receipt 的欄位。

## Reviewer 安全限制

Codex 0.146.1 從可寫 parent 直接啟動 `sol_reviewer` 時，角色檔的
`sandbox_mode = "read-only"` 不一定能覆蓋 parent 權限。提示文字與
`approval_policy = "never"` 都不能證明唯讀。

高風險審查只接受以下證據：

- Reviewer 是全新 context。
- Reviewer 的 runtime metadata 顯示 `gpt-5.6-sol xhigh`。
- parent 與 child 的 sandbox、managed filesystem permissions 都是唯讀。

目前已驗證的路徑是從獨立 read-only 主 session 啟動 `sol_reviewer`。若做不到，將
fresh review 標成 unavailable，停止 `high / critical` 的完成聲明。低風險工作仍可
由 Lead 回查，但不得把它寫成 fresh review。

## 停止與降級

- runtime slot 少於設定值：使用較低上限，不等待或建立隱藏佇列。
- `terra_worker` 不可用：由 Lead 直接做機械工作，或使用 `terra_builder` 並記錄偏差。
- `terra_builder` 不可用：只有 Lead 具備所需判斷時才直接做；否則停止派工。
- Sol binding 無法驗證：停止 frontier 完成聲明，交回使用者或已驗證的 Lead。
- Reviewer 唯讀或 fresh context 無法驗證：停止高風險完成聲明。

不要自動重寫 `.codex/config.toml`、建立新 role 或放寬 sandbox。profile 只描述可用
binding；專案 adapter 決定是否允許使用。
