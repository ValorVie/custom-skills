## Context

專案同時有三套工作資料：OpenSpec `tasks.md`、GitHub Issues 與新導入的 Beads。現行 `AGENTS.md` 要求所有工作追蹤使用 Beads，但 MP 文件與技能仍將 OpenSpec checkbox 或 GitHub issue 當成 canonical 執行狀態。Claude Code 的 Beads 管理區段也落後於 Codex 版本。

這不是要用 Beads 取代 OpenSpec 或 GitHub，而是要把三者分配到不同責任層，避免多份狀態互相競爭。

## Goals / Non-Goals

**Goals:**

- 讓 `bd ready`、`bd update --claim`、依賴與 Beads 狀態成為代理執行的唯一依據。
- 保留 OpenSpec 作為正式變更的 proposal、design、specs、tasks、verify、archive 工件生命週期。
- 保留 GitHub Issues 作為外部入口與公開討論介面。
- 讓 MP 技能依儲存庫規則選擇 Beads、OpenSpec 或 GitHub 輸出，不把 GitHub 寫死。
- 讓 Claude Code 與 Codex 載入一致的 Beads 規則。

**Non-Goals:**

- 不在本變更中遷移 73 個既有 active OpenSpec 未完成項目。
- 不建立 Beads 與 OpenSpec／GitHub 的自動雙向同步器。
- 不要求每個 OpenSpec checkbox 都對應一張 Bead。
- 不修改 OpenSpec CLI 或 Beads CLI。

## Decisions

### 1. 依責任維度分配唯一來源

- Beads 是執行層唯一來源：工作狀態、負責者、依賴、ready、交接備註。
- OpenSpec 是正式變更工件來源：範圍、需求、設計、change 內部工作與驗證證據。
- GitHub Issues 是外部入口：公開回報、討論與外部引用。

替代方案是讓 OpenSpec `tasks.md` 繼續控制正式變更、GitHub 控制輕量軌、Beads 只存記憶。此方案會讓代理在三個地方查 ready 與認領，無法達成 Beads 導入目的，因此不採用。

### 2. Beads 粒度以「可獨立認領」為界

一個 OpenSpec change 至少要有一張 Bead 表示執行工作。只有需要獨立認領、跨 session 交接或宣告 blocking dependency 的垂直切片，才建立子 Bead。OpenSpec `tasks.md` 可保留較細的實作步驟與 checkbox。

若 Beads 與 `tasks.md` 的狀態衝突，代理認領與 ready 判斷以 Beads 為準；OpenSpec apply／verify 流程仍需更新工件 checkbox。

### 3. Triage state 與執行 status 分離

五種 canonical triage state 存成 Beads label，且同一工作只能有一個 triage label：

| Triage label | Beads status | 代理行為 |
| --- | --- | --- |
| `needs-triage` | `blocked` | 等待分流 |
| `needs-info` | `blocked` | 等待補充資訊 |
| `ready-for-agent` | `open` | 無 blocking dependency 時可由 `bd ready` 認領 |
| `ready-for-human` | `blocked` | 等待人類判斷或操作 |
| `wontfix` | `closed` | 附關閉原因，不再執行 |

依賴造成的阻擋仍使用 `blocks`，不以 triage label 取代依賴圖。

### 4. MP 技能以儲存庫規則選擇輸出

輸出優先順序：使用者明確指定 → `docs/agents/issue-tracker.md` → 已解析的 Beads workspace → 原技能的 OpenSpec／GitHub／Markdown備援。當 Beads 是 canonical 時：

- `mp-to-issues` 產生 Beads issue graph 與 dependency commands。
- `mp-wayfinder` 以 Beads epic、子工作、labels 與 blocking edges 建地圖。
- `mp-triage` 回傳 Beads label／status 建議；只有取得寫入授權才實際更新。

### 5. Claude 整合只更新受管理區段

使用 `bd setup claude` 更新 `CLAUDE.md` 的 marker hash 與缺少的 `bd dolt push` 指令，不手動重寫其他 Claude 規則；現有 `.claude/settings.json` SessionStart hook 保持不變。

## Risks / Trade-offs

- [OpenSpec checkbox 與 Beads 狀態可能漂移] → 文件明定責任邊界；認領以 Beads 為準，verify 前檢查兩者。
- [MP 技能在沒有 Beads 的其他儲存庫行為改變] → 保留原有 OpenSpec、GitHub draft 與本地 Markdown 備援。
- [舊 active change 不會立即出現在 `bd ready`] → 由 `custom-skills-szw` 另案只遷移未完成工作。
- [Triage label 與 status 可能不一致] → `mp-triage` 同時輸出 label 與 status 更新，驗證規則檢查映射。

## Migration Plan

1. 先更新 canonical 文件與 MP 技能。
2. 刷新 Claude Code Beads 管理區段。
3. 驗證新工作能由 Beads 建立、分流、認領與關閉。
4. 完成本 change 後，再執行 `custom-skills-szw` 遷移 active OpenSpec 未完成工作。

回退時可還原本變更的文件與技能；Beads 中已建立的工作項目保留，不進行破壞性刪除。

## Open Questions

無。本變更不處理自動同步與歷史遷移，兩者已有明確範圍外界線。
