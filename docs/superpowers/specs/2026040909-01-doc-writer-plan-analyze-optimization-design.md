---
title: doc-writer 與 plan-analyze 優化設計
type: spec
date: 2026040909-01
author: ValorVie
status: draft
---

# doc-writer 與 plan-analyze 優化設計

## 摘要

對 `custom-skills-doc-writer`（SKILL.md + 13 模板）與 `custom-skills-plan-analyze`（SKILL.md）進行漸進式優化，涵蓋流程補強、模板一致性修正、新增模板、檔名命名規則統一，以及 plan-analyze 的術語與引用修正。

## 變更範圍

| 目標 | 變更項 |
|------|--------|
| doc-writer SKILL.md | 命名規則、Step 4 擴充、新增 Step 4.5/5.5、Step 5 刪減規則、Step 6 更新、引數表新增 2 行、模板索引新增 2 行 |
| doc-writer 模板（既有） | 6 個模板佔位符修正、1 個模板中英混用修正、1 個模板狀態值加中文對照、所有模板 frontmatter date 改為 `{YYYYMMDDhh-NN}` |
| doc-writer 模板（新增） | template-record-changelog.md、template-plan-rfc.md |
| plan-analyze SKILL.md | Phase 改為階段、skill 引用名稱修正、階段 6 命名規則、移除 emoji、階段 0 frontmatter type 優先讀取 |

---

## 一、檔名命名規則

### 格式

```
YYYYMMDDhh-NN-標題.md
```

| 欄位 | 說明 | 範例 |
|------|------|------|
| `YYYYMMDDhh` | 產出時間（24 小時制，精確到小時，UTC+8） | `2026040914` |
| `NN` | 當日流水編，從 `01` 起算，每日歸零，遞增無上限 | `01`、`02`、`100` |
| `標題` | 文件主題，中英文皆可，以連字號分隔多詞 | `上游更新調查`、`hook-error-analysis` |

### 流水編判定邏輯

1. 掃描目標目錄內所有以當日日期 `YYYYMMDD` 開頭的檔案
2. 取最大流水編 +1；若無則從 `01` 開始
3. 若目標目錄不存在，從 `01` 開始

### 預設輸出路徑

| type | 預設路徑 |
|------|----------|
| `plan` | `docs/plans/` |
| `report` | `docs/report/` |
| `guide` | `docs/guide/` |
| `tutorial` | `docs/tutorial/` |
| `record` | `docs/record/` |
| `standard` | `.standards/` 或 `docs/` |

使用者可覆寫預設路徑。

### frontmatter 自動填入

- `title`：從檔名的標題部分自動填入
- `date`：從檔名的 `YYYYMMDDhh-NN` 部分自動填入
- `author`：從 `git config user.name` 取得或留空

---

## 二、doc-writer 流程補強

### 2a. 區分內容來源（新增 Step 4.5）

在 Step 4（收集資訊）和 Step 5（撰寫）之間插入判斷：

- **對話轉文件**：對話中已有充分的技術討論內容，直接從對話萃取，掃描對話中的事實、結論、建議，對應到模板章節，不重複詢問已知資訊
- **從零撰寫**：無對話脈絡或資訊不足，依 Step 4 的類型必要欄位逐項收集

### 2b. 按類型收集必要資訊（擴充 Step 4）

現有 Step 4 只問標題和輸出路徑，擴充為按類型補問：

| type | 額外必問欄位 |
|------|-------------|
| `plan` | 目標、背景/動機 |
| `report/investigation` | 觸發事件、調查範圍 |
| `report/status` | 報告期間 |
| `report/analysis` | 分析目的、分析對象 |
| `guide` | 適用對象、前置條件 |
| `tutorial` | 難度等級、預估時間 |
| `record/meeting` | 日期時間、出席者、議程 |
| `record/incident` | 嚴重度、發生時間、影響範圍 |
| `record/decision` | 待決策的問題、考量因素 |
| `record/changelog` | 版本號 |
| `standard` | 適用範圍 |

規則：若資訊已在對話脈絡或使用者指令中提供，跳過詢問。

### 2c. 刪減不適用章節（加入 Step 5）

若章節明確不適用於當前文件，直接刪除該章節，不留空佔位符。僅在資訊暫時不足但章節本身合理時才保留 `<!-- TODO: 補充 -->`。

### 2d. 文件品質自檢（新增 Step 5.5）

在 Step 5（撰寫）和 Step 6（後續建議）之間插入：

1. frontmatter 所有必填欄位是否完整
2. 殘留的 `<!-- TODO -->` 是否合理（不可填的才留）
3. 表格是否有空行或格式錯誤
4. 標題層級是否符合規範（最深不超過 `####`）
5. 檔名是否符合 `YYYYMMDDhh-NN-標題.md` 格式

---

## 三、模板一致性修正

### 3a. 佔位符格式統一

規則：
- frontmatter：維持英文變數名（`title`、`date`、`author`），值使用中文佔位符 `{標題}`、`{YYYYMMDDhh-NN}`
- 內文：統一用中文描述加大括號

需修改的模板：

| 模板 | 現況 | 改為 |
|------|------|------|
| template-record-incident.md | `{ID}`、`{N}` 小時 `{N}` 分鐘 | `{事件編號}`、`{時數}` 小時 `{分鐘數}` 分鐘 |
| template-record-decision.md | `{X}` | `{選定方案}` |
| template-plan-refactoring.md | `X — 理由：` | `{選定方案} — 理由：` |
| template-report-status.md | `X%` | `{百分比}%` |
| template-tutorial.md | `X.Y` | `{版本號}` |

所有模板 frontmatter 的 `title` 和 `date` 統一改為：

```yaml
title: {標題}
date: {YYYYMMDDhh-NN}
```

### 3b. 中英混用修正

`template-plan-migration.md` 的階段標題：

| 現況 | 改為 |
|------|------|
| `### Phase 1: 準備` | `### 階段 1：準備` |
| `### Phase 2: 執行` | `### 階段 2：執行` |
| `### Phase 3: 驗證` | `### 階段 3：驗證` |
| `### Phase 4: 切換` | `### 階段 4：切換` |

### 3c. decision 狀態值加中文對照

frontmatter 改為：

```yaml
# 狀態值：proposed（提議中）| accepted（已採納）| deprecated（已棄用）| superseded（已取代）
status: {狀態}
```

---

## 四、新增模板

### 4a. template-record-changelog.md

```yaml
---
title: {標題}
type: record/changelog
date: {YYYYMMDDhh-NN}
author: {author}
status: draft
version: {版本號}
---
```

章節：概述、變更內容（新增/變更/修正/移除/棄用/安全性）、破壞性變更（若無則刪除）、遷移指南（若有破壞性變更才保留）、相關連結

### 4b. template-plan-rfc.md

```yaml
---
title: {標題}
type: plan/rfc
date: {YYYYMMDDhh-NN}
author: {author}
status: draft
rfc_id: {提案編號}
---
```

章節：摘要、動機、提案內容、替代方案、影響評估（向下相容/效能/安全性）、未解決問題、附錄

---

## 五、plan-analyze 優化

### 5a. 階段術語統一

所有 `Phase N` 改為 `階段 N`，英文冒號改中文冒號。

### 5b. 關聯 Skill 引用名稱修正

| 現況 | 修正為 |
|------|--------|
| `/spec` | `/spec-driven-dev` |
| `/requirement` | `/requirement-assistant` |
| `/security-review` | `/security-scan` |
| `/refactor` | `/refactoring-assistant` |
| `/test-coverage` | `/test-coverage-assistant` |
| `/review` | `/code-review-assistant` |

### 5c. 階段 6 補充文件命名

若產出獨立的補充分析文件，套用 `YYYYMMDDhh-NN-標題.md` 命名規則。

### 5d. 移除 emoji

輸出格式中的 emoji 移除，改為純文字，英文冒號改中文冒號。

### 5e. 階段 0 frontmatter type 優先讀取

新增規則：若文件包含 YAML frontmatter 且有 `type` 欄位，直接採用作為文件類型；若無，則依現有邏輯從內容推斷。

---

## 六、doc-writer Step 6 後續建議更新

| 文件類型 | 建議 |
|----------|------|
| plan | 建議使用 `/custom-skills-plan-analyze` 檢查完整性 |
| report | 建議使用 `/custom-skills-plan-analyze` 評估分析品質，或提示是否需要補充資料 |
| record/changelog | 提示是否需要同步更新版本號或 release 標籤 |
| record/decision | 提示是否需要通知相關方 |
| standard | 提示是否需要版本控制與審批流程 |
| 其他 | 提示是否需要請相關人員審閱 |
