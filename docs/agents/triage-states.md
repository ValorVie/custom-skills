# Triage States 規則

本文件定義 MP 工作入口層的 tracker 無關狀態模型。

## Canonical States

每個工作項目只能有一個主要 state。

| State | 意義 | 可交給 agent |
|---|---|---|
| `needs-triage` | 尚未完成維護者判斷 | 否 |
| `needs-info` | 資訊不足，需要具體回問 | 否 |
| `ready-for-agent` | 範圍、驗證、依賴都清楚 | 是 |
| `ready-for-human` | 需要人類判斷、外部權限、人工審核或高風險決策 | 否 |
| `wontfix` | 明確不處理，需記錄原因 | 否 |

## 類別

可另外標示類別，但類別不取代 state。

- `bug`
- `enhancement`
- `docs`
- `chore`

## AFK / HITL

- `AFK`：agent 可獨立完成，包含驗證。
- `HITL`：需要人類輸入、決策、審核或外部操作。

`ready-for-agent` 通常應對應 `AFK`。`ready-for-human` 通常應對應 `HITL`。

## 狀態轉換

```text
untriaged
  -> needs-triage
  -> needs-info
  -> needs-triage
  -> ready-for-agent | ready-for-human | wontfix
```

維護者可覆寫狀態。若狀態轉換看起來異常，先指出理由並等待使用者確認。

## 外部 label mapping

本專案不要求外部 label 與 canonical state 同名。若某個專案有既有 label，請在該專案文件中記錄 mapping，例如：

```yaml
needs-triage: status/needs-triage
needs-info: status/needs-info
ready-for-agent: status/ready-for-agent
ready-for-human: status/ready-for-human
wontfix: resolution/wontfix
```

MP 技能輸出時必須保留 canonical state 名稱，避免不同 tracker 之間語意漂移。
