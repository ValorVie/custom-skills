# doc-writer 與 plan-analyze 優化實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 優化 doc-writer 和 plan-analyze 兩個 skill，補強流程、統一模板格式、新增模板、引入檔名命名規則

**Architecture:** 漸進式修補現有檔案。doc-writer SKILL.md 補入新流程步驟與命名規則；13 個既有模板逐一修正佔位符和 frontmatter；新增 2 個模板；plan-analyze SKILL.md 修正術語和引用。

**Tech Stack:** Markdown、YAML frontmatter

**Spec:** `docs/superpowers/specs/2026040909-01-doc-writer-plan-analyze-optimization-design.md`

---

### Task 1: 更新 doc-writer SKILL.md — 引數表與模板索引

**Files:**
- Modify: `skills/custom-skills-doc-writer/SKILL.md`

- [ ] **Step 1: 在引數表新增 changelog 和 rfc**

在 `type（文件類型）與 variant（子類型）` 表格中，`record` 區塊末尾新增：

```markdown
| `record` | `changelog` | template-record-changelog.md | 變更日誌 |
```

在 `plan` 區塊末尾（`general` 之後）新增：

```markdown
| `plan` | `rfc` | template-plan-rfc.md | 技術提案 |
```

- [ ] **Step 2: 在 Step 2 互動引導新增對應選項**

plan 子類型列表末尾加入：

```markdown
- 技術提案 (rfc)
```

record 子類型列表末尾加入：

```markdown
- 變更日誌 (changelog)
```

- [ ] **Step 3: 在模板索引新增 2 行**

在模板索引表格的對應位置加入：

```markdown
| [template-record-changelog.md](references/template-record-changelog.md) | 變更日誌 |
| [template-plan-rfc.md](references/template-plan-rfc.md) | 技術提案 |
```

- [ ] **Step 4: 驗證引數表、互動引導、模板索引三處的條目數一致**

引數表應有 15 行（原 13 + changelog + rfc），模板索引也應有 15 行。

---

### Task 2: 更新 doc-writer SKILL.md — 流程補強

**Files:**
- Modify: `skills/custom-skills-doc-writer/SKILL.md`

- [ ] **Step 1: 改寫 Step 4（收集文件資訊）**

將現有 Step 4 整段替換為：

```markdown
### Step 4: 收集文件資訊

詢問使用者必要資訊（若未在指令中提供）：
- **輸出路徑**: 文件存放位置（依類型提供預設路徑，使用者可覆寫）

預設輸出路徑：

| type | 預設路徑 |
|------|----------|
| `plan` | `docs/plans/` |
| `report` | `docs/report/` |
| `guide` | `docs/guide/` |
| `tutorial` | `docs/tutorial/` |
| `record` | `docs/record/` |
| `standard` | `.standards/` 或 `docs/` |

按文件類型補問必要資訊（若已在對話脈絡或指令中提供則跳過）：

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

Metadata 自動填入：
- `title`: 從檔名的標題部分自動填入
- `date`: 從檔名的 `YYYYMMDDhh-NN` 部分自動填入
- `author`: 從 git config 取得或留空
```

- [ ] **Step 2: 在 Step 4 之後插入 Step 4.5**

```markdown
### Step 4.5: 判斷內容來源

- **對話轉文件**：對話中已有充分的技術討論內容，直接從對話萃取，掃描對話中的事實、結論、建議，對應到模板章節，不重複詢問已知資訊
- **從零撰寫**：無對話脈絡或資訊不足，依 Step 4 的類型必要欄位逐項收集
```

- [ ] **Step 3: 修改 Step 5 第 3 點，加入刪減規則**

將 Step 5 的第 3 點：

```
3. 對於無法推斷的章節，保留模板佔位符並標註 `<!-- TODO: 補充 -->`
```

替換為：

```
3. 若章節明確不適用於當前文件，直接刪除該章節，不留空佔位符。僅在資訊暫時不足但章節本身合理時才保留 `<!-- TODO: 補充 -->`
```

- [ ] **Step 4: 在 Step 5 之後插入 Step 5.5**

```markdown
### Step 5.5: 品質自檢

撰寫完成後執行以下檢查：

1. frontmatter 所有必填欄位是否完整
2. 殘留的 `<!-- TODO -->` 是否合理（不可填的才留）
3. 表格是否有空行或格式錯誤
4. 標題層級是否符合規範（最深不超過 `####`）
5. 檔名是否符合 `YYYYMMDDhh-NN-標題.md` 格式
```

- [ ] **Step 5: 替換 Step 6（後續建議）**

將現有 Step 6 表格替換為：

```markdown
| 文件類型 | 建議 |
|----------|------|
| plan | 建議使用 `/custom-skills-plan-analyze` 檢查完整性 |
| report | 建議使用 `/custom-skills-plan-analyze` 評估分析品質，或提示是否需要補充資料 |
| record/changelog | 提示是否需要同步更新版本號或 release 標籤 |
| record/decision | 提示是否需要通知相關方 |
| standard | 提示是否需要版本控制與審批流程 |
| 其他 | 提示是否需要請相關人員審閱 |
```

---

### Task 3: 更新 doc-writer SKILL.md — 命名規則

**Files:**
- Modify: `skills/custom-skills-doc-writer/SKILL.md`

- [ ] **Step 1: 在「共通格式規範」章節新增命名規則**

在現有的 `## 共通格式規範` 章節的列表之前（`所有文件遵循以下基線：` 之後），插入命名規則區塊：

```markdown
### 檔名命名規則

所有產出文件統一使用以下格式：

```
YYYYMMDDhh-NN-標題.md
```

| 欄位 | 說明 | 範例 |
|------|------|------|
| `YYYYMMDDhh` | 產出時間（24 小時制，UTC+8，精確到小時） | `2026040914` |
| `NN` | 當日流水編，從 `01` 起算，每日歸零，遞增無上限 | `01`、`02`、`100` |
| `標題` | 文件主題，中英文皆可，以連字號分隔多詞 | `上游更新調查`、`hook-error-analysis` |

**流水編判定邏輯：**
1. 掃描目標目錄內所有以當日日期 `YYYYMMDD` 開頭的檔案
2. 取最大流水編 +1；若無則從 `01` 開始
3. 若目標目錄不存在，從 `01` 開始

### 格式基線
```

然後將原本的列表項目（Frontmatter、標題層級、表格等）歸到 `### 格式基線` 下。

- [ ] **Step 2: 驗證完整的 Step 流程編號是否連貫**

確認流程順序為：Step 1 → Step 1.5 → Step 2 → Step 3 → Step 4 → Step 4.5 → Step 5 → Step 5.5 → Step 6，無跳號或重複。

---

### Task 4: 修正既有模板佔位符與中英混用（6 個模板）

**Files:**
- Modify: `skills/custom-skills-doc-writer/references/template-record-incident.md`
- Modify: `skills/custom-skills-doc-writer/references/template-record-decision.md`
- Modify: `skills/custom-skills-doc-writer/references/template-plan-refactoring.md`
- Modify: `skills/custom-skills-doc-writer/references/template-report-status.md`
- Modify: `skills/custom-skills-doc-writer/references/template-tutorial.md`
- Modify: `skills/custom-skills-doc-writer/references/template-plan-migration.md`

- [ ] **Step 1: 修正 template-record-incident.md**

```diff
-| 事件 ID | {ID} |
+| 事件 ID | {事件編號} |

-| 影響時長 | {N} 小時 {N} 分鐘 |
+| 影響時長 | {時數} 小時 {分鐘數} 分鐘 |
```

- [ ] **Step 2: 修正 template-record-decision.md**

frontmatter：
```diff
-status: proposed | accepted | deprecated | superseded
+# 狀態值：proposed（提議中）| accepted（已採納）| deprecated（已棄用）| superseded（已取代）
+status: {狀態}
```

內文「## 狀態」章節：
```diff
-{proposed | accepted | deprecated | superseded}
+{狀態}
+
+> 可選值：proposed（提議中）、accepted（已採納）、deprecated（已棄用）、superseded（已取代）
```

「## 決策」章節：
```diff
-選擇方案 {X}。
+選擇方案 {選定方案}。
```

- [ ] **Step 3: 修正 template-plan-refactoring.md**

```diff
-**選擇方案**: X — 理由：...
+**選擇方案**: {選定方案} — 理由：...
```

- [ ] **Step 4: 修正 template-report-status.md**

```diff
-| ... | 完成/進行中/延遲/阻塞 | X% | ... |
+| ... | 完成/進行中/延遲/阻塞 | {百分比}% | ... |
```

- [ ] **Step 5: 修正 template-tutorial.md**

frontmatter：
```diff
-estimated_time: {N} 分鐘
+estimated_time: {預估分鐘數} 分鐘
```

內文必要工具：
```diff
-- 工具 1（版本 X.Y）
+- 工具 1（版本 {版本號}）
```

- [ ] **Step 6: 修正 template-plan-migration.md 的中英混用**

```diff
-### Phase 1: 準備
+### 階段 1：準備

-### Phase 2: 執行
+### 階段 2：執行

-### Phase 3: 驗證
+### 階段 3：驗證

-### Phase 4: 切換
+### 階段 4：切換
```

---

### Task 5: 更新全部 15 個模板的 frontmatter

**Files:**
- Modify: `skills/custom-skills-doc-writer/references/template-plan-feature.md`
- Modify: `skills/custom-skills-doc-writer/references/template-plan-general.md`
- Modify: `skills/custom-skills-doc-writer/references/template-plan-migration.md`
- Modify: `skills/custom-skills-doc-writer/references/template-plan-refactoring.md`
- Modify: `skills/custom-skills-doc-writer/references/template-report-investigation.md`
- Modify: `skills/custom-skills-doc-writer/references/template-report-status.md`
- Modify: `skills/custom-skills-doc-writer/references/template-report-analysis.md`
- Modify: `skills/custom-skills-doc-writer/references/template-guide.md`
- Modify: `skills/custom-skills-doc-writer/references/template-tutorial.md`
- Modify: `skills/custom-skills-doc-writer/references/template-record-meeting.md`
- Modify: `skills/custom-skills-doc-writer/references/template-record-incident.md`
- Modify: `skills/custom-skills-doc-writer/references/template-record-decision.md`
- Modify: `skills/custom-skills-doc-writer/references/template-standard.md`

注意：template-record-changelog.md 和 template-plan-rfc.md 在 Task 6 中建立時直接使用新格式，不在此處理。

- [ ] **Step 1: 對每個模板執行以下兩項替換**

在所有 13 個模板的 frontmatter 中：

```diff
-title: {title}
+title: {標題}

-date: {date}
+date: {YYYYMMDDhh-NN}
```

同時在模板內文的 `# {title}` 也改為 `# {標題}`。

針對 template-standard.md，版本歷史表格中的 `{date}` 也要改：
```diff
-| 1.0.0 | {date} | 初版 |
+| 1.0.0 | {YYYYMMDDhh-NN} | 初版 |
```

- [ ] **Step 2: 驗證所有 13 個模板中不再包含 `{title}` 或 `{date}` 字串**

執行搜尋確認：
```bash
grep -r '{title}\|{date}' skills/custom-skills-doc-writer/references/
```
預期結果：無匹配。

---

### Task 6: 建立新模板

**Files:**
- Create: `skills/custom-skills-doc-writer/references/template-record-changelog.md`
- Create: `skills/custom-skills-doc-writer/references/template-plan-rfc.md`

- [ ] **Step 1: 建立 template-record-changelog.md**

```markdown
# 模板：變更日誌

```markdown
---
title: {標題}
type: record/changelog
date: {YYYYMMDDhh-NN}
author: {author}
status: draft
version: {版本號}
---

# {標題}

## 概述

一段話描述本次變更的重點。

## 變更內容

### 新增
- 項目 1

### 變更
- 項目 1

### 修正
- 項目 1

### 移除
- 項目 1

### 棄用
- 項目 1

### 安全性
- 項目 1

## 破壞性變更

| 變更 | 影響範圍 | 遷移方式 |
|------|----------|----------|
| ... | ... | ... |

## 遷移指南

### 從 {舊版本} 升級到 {新版本}

1. 步驟 1
2. 步驟 2

## 相關連結

- [完整 diff](連結)
- [相關 issue](連結)
```
```

- [ ] **Step 2: 建立 template-plan-rfc.md**

```markdown
# 模板：技術提案

```markdown
---
title: {標題}
type: plan/rfc
date: {YYYYMMDDhh-NN}
author: {author}
status: draft
rfc_id: {提案編號}
---

# {標題}

## 摘要

一段話描述提案的核心內容。

## 動機

### 問題描述
- 目前遇到什麼問題
- 為什麼現有方案不足

### 預期效益
- 效益 1
- 效益 2

## 提案內容

### 設計概覽

描述提案的整體設計方向。

### 詳細設計

#### 元件 1：{名稱}

**職責**：描述這個元件負責什麼。

**介面**：

```
（API 或介面定義）
```

#### 元件 2：{名稱}

（同上格式）

### 資料流

```
（資料流程圖）
```

## 替代方案

### 方案 A：{名稱}

**描述**：...

**未採用原因**：...

### 方案 B：{名稱}

**描述**：...

**未採用原因**：...

## 影響評估

| 面向 | 影響 | 說明 |
|------|------|------|
| 向下相容 | 是/否 | ... |
| 效能 | 正面/中性/負面 | ... |
| 安全性 | 無影響/需注意 | ... |

## 未解決問題

- [ ] 問題 1：描述待討論的議題
- [ ] 問題 2：描述待討論的議題

## 附錄

- 相關 RFC 或 ADR 連結
- 參考資料
```
```

- [ ] **Step 3: 驗證 references/ 目錄包含 15 個模板**

```bash
ls skills/custom-skills-doc-writer/references/ | wc -l
```
預期結果：15

---

### Task 7: 更新 plan-analyze SKILL.md

**Files:**
- Modify: `skills/custom-skills-plan-analyze/SKILL.md`

- [ ] **Step 1: 階段 0 新增 frontmatter type 優先讀取**

在 `### Phase 0: 文件識別與上下文建立` 的第 1 點之前插入：

```markdown
0. 若文件包含 YAML frontmatter 且有 `type` 欄位，直接採用作為文件類型，跳到步驟 2；若無，繼續步驟 1 從內容推斷。
```

原本的 1、2 點編號不變（它們是 fallback 邏輯）。

- [ ] **Step 2: 全文 Phase → 階段 替換**

將所有 `Phase N` 替換為 `階段 N`：

```diff
-### Phase 0: 文件識別與上下文建立
+### 階段 0：文件識別與上下文建立

-### Phase 1: 分析評估完善度
+### 階段 1：分析評估完善度

-### Phase 2: 功能設計完整性
+### 階段 2：功能設計完整性

-### Phase 3: 既有流程影響評估
+### 階段 3：既有流程影響評估

-### Phase 4: 潛在異常與副作用
+### 階段 4：潛在異常與副作用

-### Phase 5: 綜合評估與建議
+### 階段 5：綜合評估與建議

-### Phase 6: 回饋與補充
+### 階段 6：回饋與補充
```

內文引用也一併替換（如 `Phase 1` → `階段 1`、`Phase 4` → `階段 4`）。

- [ ] **Step 3: 修正關聯 Skill 引用名稱**

```diff
-| 文件為規格提案且結構不完整 | `/spec` | Phase 1 — 建議先通過結構驗證再做影響分析 |
+| 文件為規格提案且結構不完整 | `/spec-driven-dev` | 階段 1 — 建議先通過結構驗證再做影響分析 |

-| 需求描述模糊或缺少驗收標準 | `/requirement` | Phase 1 — 需求品質不足時引導改善 |
+| 需求描述模糊或缺少驗收標準 | `/requirement-assistant` | 階段 1 — 需求品質不足時引導改善 |

-| Phase 4 識別安全風險為「中」或「高」 | `/security-review` | Phase 4 — 建議深入安全審查 |
+| 階段 4 識別安全風險為「中」或「高」 | `/security-scan` | 階段 4 — 建議深入安全審查 |

-| 修改涉及重構或技術債清理 | `/refactor` | Phase 2/3 — 建議評估重構策略 |
+| 修改涉及重構或技術債清理 | `/refactoring-assistant` | 階段 2/3 — 建議評估重構策略 |

-| Phase 4 識別測試覆蓋不足 | `/test-coverage` | Phase 4 — 建議評估測試完整性 |
+| 階段 4 識別測試覆蓋不足 | `/test-coverage-assistant` | 階段 4 — 建議評估測試完整性 |

-| 修改已實作完成、準備提交 | `/review` | Phase 5 — 建議進入程式碼審查 |
+| 修改已實作完成、準備提交 | `/code-review-assistant` | 階段 5 — 建議進入程式碼審查 |
```

- [ ] **Step 4: 移除 emoji 並修正標點**

```diff
-> 💡 **建議**: 本分析識別到 [問題類型]，建議使用 `/skill-name` 進行深入評估。
+> **建議**：本分析識別到 [問題類型]，建議使用 `/skill-name` 進行深入評估。
```

- [ ] **Step 5: 在階段 6 加入命名規則**

在階段 6 的「若使用者同意」流程中，第 2 點之後加入：

```markdown
   若產出獨立的補充分析文件（而非附加到原始文件），檔名套用 `YYYYMMDDhh-NN-標題.md` 格式。
```

- [ ] **Step 6: 驗證全文不再包含 `Phase` 或 `💡` 字串**

```bash
grep -E 'Phase [0-9]|💡' skills/custom-skills-plan-analyze/SKILL.md
```
預期結果：無匹配。

---

### Task 8: 提交變更

**Files:**
- All modified and created files from Tasks 1-7

- [ ] **Step 1: 檢視變更清單**

```bash
git status
git diff --stat
```

- [ ] **Step 2: 提交**

```bash
git add skills/custom-skills-doc-writer/ skills/custom-skills-plan-analyze/
git commit -m "feat(skills): 優化 doc-writer 與 plan-analyze 流程、模板與命名規則

- doc-writer：新增檔名命名規則 YYYYMMDDhh-NN-標題.md
- doc-writer：補強 Step 4/4.5/5/5.5/6 流程
- doc-writer：統一模板佔位符格式與 frontmatter
- doc-writer：新增 changelog 和 RFC 模板
- plan-analyze：Phase 改為階段、修正 skill 引用名稱
- plan-analyze：新增 frontmatter type 優先讀取

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

- [ ] **Step 3: 同步到使用者層級**

```bash
cp -r skills/custom-skills-doc-writer/ ~/.claude/skills/custom-skills-doc-writer/
cp skills/custom-skills-plan-analyze/SKILL.md ~/.claude/skills/custom-skills-plan-analyze/SKILL.md
```
