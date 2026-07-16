---
name: mp-to-issues
description: |
  將 plan、PRD、OpenSpec change 或對話摘要切成可驗證的垂直切片。
  Use when: 需要把大型需求拆成 Beads issue graph、OpenSpec tasks、
  GitHub issue draft 或本地 Markdown 工作項目；不適用於直接 TDD 實作。
---

# mp-to-issues

本技能把已成形的需求拆成可接手、可驗證的工作項目。它不負責正式規格審核，也不取代 `openspec-*`。

## 啟動時先讀

- `docs/agents/mp-workflow.md`
- `docs/agents/issue-tracker.md`
- `docs/agents/triage-states.md`
- `docs/agents/domain.md`
- 若來源是 OpenSpec change，讀該 change 的 proposal、design、spec、tasks。
- 若存在 `CONTEXT.md`、`CONTEXT-MAP.md` 或 ADR，讀相關部分。

## 切片規則

每個工作項目都必須是垂直切片：

- 走過受影響系統的完整窄路徑。
- 完成後能獨立展示或驗證。
- 有明確驗證條件。
- 盡量小，但不能小到只剩單一水平層。

避免水平切片，例如只改 schema、只改 UI、只寫文件而沒有可驗證閉環。

## 依賴宣告（blocking edges）

每個切片必須宣告阻擋它的其他切片：

- 有阻擋者：列出阻擋來源的編號或標題。
- 無阻擋者：標示「可立即開工」。
- 輸出順序依依賴排序：被依賴的切片在前。

無阻擋的切片集合就是 frontier：可以平行認領，各自在獨立 session 開工。
阻擋關係只寫真正的閘門，不寫「順便先做比較好」的軟偏好。

## 寬重構：expand–contract

垂直切片有一個例外。單一機械性變更（改欄位名、改共用型別）若影響面橫跨大量呼叫點，
任何垂直切片都無法獨立保持綠燈時，改用 expand–contract 切法：

1. **Expand**：新形式與舊形式並存，一個切片，不破壞任何呼叫點。
2. **Migrate**：呼叫點分批遷移（按套件或目錄分批），每批一個切片，宣告被 expand 切片阻擋。
   舊形式仍在，批與批之間保持綠燈。
3. **Contract**：所有批次完成後移除舊形式，一個切片，宣告被所有 migrate 批次阻擋。

連分批都無法獨立綠燈時，保留同樣順序，改共用一條整合分支，
所有切片阻擋最後一個「整合驗證」切片，綠燈只承諾在那裡。

## AFK / HITL

每個切片必須標示：

- `AFK`：範圍清楚、驗證明確、沒有未決的人類判斷，可交給 agent。
- `HITL`：需要產品判斷、外部存取、人工審核或設計決策。

預設盡量切成 `AFK`。若無法做到，要寫出阻塞原因。

## 輸出模式

依下列優先序選擇輸出：

1. 使用者明確指定。
2. `docs/agents/issue-tracker.md` 的 canonical 規則。
3. `bd where` 可解析的 Beads workspace。
4. 來源是 OpenSpec change 時使用 OpenSpec tasks。
5. GitHub issue draft 或本地 Markdown 備援。

### Beads issue graph

Beads 是 canonical 時，每個可獨立認領的切片建立一張工作項目：

```bash
bd create \
  --title="<動詞開頭的標題>" \
  --description="<範圍、AFK/HITL、實作內容>" \
  --type=task \
  --priority=2 \
  --acceptance="<可執行或可檢查的驗證條件>"

bd dep add <blocked-id> <blocker-id>
```

- `AFK` 對應 `ready-for-agent` label 與 `open` status。
- `HITL` 對應 `ready-for-human` label 與 `blocked` status。
- 先建立所有工作項目，再補 dependency，避免引用尚不存在的 ID。
- 儲存庫規則或使用者已授權寫入時可直接執行；否則只輸出 command draft。

### OpenSpec tasks

來源是 OpenSpec change 時保留此工件格式：

```markdown
- [ ] N.M [AFK] 動詞開頭的任務描述
  - 驗證：可執行或可檢查的條件
  - 阻擋：N.K（無阻擋者寫「可立即開工」）
```

保持依賴順序：阻塞者在前，被阻塞者在後。
需要獨立認領、跨 session 交接或 blocking dependency 的切片，同時建立或草擬 Beads 工作。

### GitHub issue draft

用於外部入口或使用者明確指定 GitHub 時。只輸出草稿，除非使用者明確要求建立 issue。

每個草稿包含：

- Title
- Type：`AFK` 或 `HITL`
- Parent
- What to build
- Acceptance criteria
- Blocked by

### 本地 Markdown

用於沒有外部 tracker 的儲存庫。預設輸出到 `.scratch/<topic>/` 或使用者指定路徑。

## 完成條件

- 每個切片都有驗證條件。
- 每個切片都有 `AFK` 或 `HITL`。
- 每個切片都宣告阻擋來源，或標示可立即開工。
- 已指出依賴順序，frontier 可平行認領。
- 寬重構已依 expand–contract 切分並宣告阻擋關係。
- Beads 是 canonical 時，已提供 issue graph 或可直接執行的 command draft。
- 不直接修改父需求或關閉父 issue。
