# MP 工作入口層

MP 工作入口層是本專案對 `mattpocock/skills` 的裁切與改寫。它補的是「開工前與工作流周邊」，不是正式規格生命週期，也不是任務內執行紀律。

## 分工

| 工作流 | 職責 | 代表技能 |
|---|---|---|
| MP 工作入口層 | 需求追問、專案語言、垂直切片、任務分流、架構候選 | `mp-*` |
| OpenSpec | proposal、design、tasks、spec、verify、archive | `openspec-*` |
| Superpowers | TDD、除錯、review、完成前驗證 | `superpowers:*` |

## 技能鏈

```text
模糊需求 / 新想法
  -> mp-grill-with-docs
  -> mp-to-prd
  -> mp-to-issues
  -> mp-triage
  -> openspec-* 或 superpowers:*
```

`mp-setup-matt-pocock-skills` 用於建立本文件與其他 `docs/agents/` 規則。

## 本地技能

| 優先級 | 本地技能 | 來源技能 | 目的 |
|---|---|---|---|
| P0 | `mp-setup-matt-pocock-skills` | `setup-matt-pocock-skills` | 建立共同工作規則 |
| P0 | `mp-grill-with-docs` | `grill-with-docs` | 追問與專案語言沉澱 |
| P0 | `mp-to-issues` | `to-issues` | 垂直切片與工作項目輸出 |
| P1 | `mp-triage` | `triage` | tracker 無關的任務分流 |
| P1 | `mp-improve-codebase-architecture` | `improve-codebase-architecture` | 架構改善候選 |
| P2 | `mp-to-prd` | `to-prd` | PRD 或 OpenSpec brief |

## 選用規則

- 使用者要求正式 proposal、spec、驗證或歸檔時，使用 `openspec-*`。
- 使用者要求 TDD、除錯、review 或完成前驗證時，使用 `superpowers:*`。
- 使用者的需求尚未清楚、需要切片、需要分流或需要架構候選時，使用 `mp-*`。

## 不導入的上游技能

- `tdd`：由 `superpowers:test-driven-development` 保留。
- `diagnose`：由 `superpowers:systematic-debugging` 保留。
- personal、misc、deprecated：不屬於共享專案工作入口層。
