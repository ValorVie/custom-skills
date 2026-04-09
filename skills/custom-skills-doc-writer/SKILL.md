---
name: custom-skills-doc-writer
description: |
  以統一格式撰寫計畫、報告、指南、教學、紀錄、規範等文件。
  Use when: 使用者要求撰寫或起草文件，包含但不限於：計畫書（新功能/重構/遷移）、報告（調查/階段/分析）、指南、教學、會議紀錄、事件紀錄、決策紀錄、規範文件。
  觸發方式: /custom-skills-doc-writer [type] [variant]
  Keywords: 撰寫文件, 文件模板, 計畫書, 報告, 指南, 教學, 紀錄, 規範, document writer, plan, report, guide, tutorial, record, standard, 寫文件, 起草, draft
---

# Document Writer — 統一格式文件撰寫

## 使用方式

```
/custom-skills-doc-writer [type] [variant]
```

若使用者已提供完整引數，直接載入對應模板執行。若未提供或資訊不足，透過互動引導。

---

## 引數解析

### type（文件類型）與 variant（子類型）

| type | variant | 模板 | 說明 |
|------|---------|------|------|
| `plan` | `feature` | template-plan-feature.md | 新功能計畫 |
| `plan` | `refactoring` | template-plan-refactoring.md | 重構計畫 |
| `plan` | `migration` | template-plan-migration.md | 遷移計畫 |
| `plan` | `general` | template-plan-general.md | 通用計畫（預設） |
| `plan` | `rfc` | template-plan-rfc.md | 技術提案 |
| `report` | `investigation` | template-report-investigation.md | 調查報告 |
| `report` | `status` | template-report-status.md | 階段/進度報告 |
| `report` | `analysis` | template-report-analysis.md | 分析報告 |
| `guide` | — | template-guide.md | 操作指南 |
| `tutorial` | — | template-tutorial.md | 教學文件 |
| `record` | `meeting` | template-record-meeting.md | 會議紀錄 |
| `record` | `incident` | template-record-incident.md | 事件紀錄 |
| `record` | `decision` | template-record-decision.md | 決策紀錄 |
| `record` | `changelog` | template-record-changelog.md | 變更日誌 |
| `standard` | — | template-standard.md | 規範文件 |

---

## 流程

### Step 1: 判斷引數來源

依以下優先順序決定 type/variant：

1. **使用者明確指定** → 直接使用，跳到 Step 3
2. **未指定但有對話脈絡** → 進入 Step 1.5 脈絡推斷
3. **無引數且無脈絡** → 進入 Step 2 互動引導

### Step 1.5: 脈絡推斷（從對話內容判斷文件類型）

當使用者在對話中說「把剛才的討論寫成文件」「整理成報告」等模糊指令時，根據對話內容特徵推斷文件類型。

**推斷規則 — 依對話內容的核心動詞/意圖判斷：**

| 對話特徵 | 推斷結果 | 常見混淆 |
|----------|----------|----------|
| 分析了問題根因、追蹤了呼叫鏈、讀了原始碼 | `report/investigation` | 非 `record/incident`（incident 是事後紀錄時間線，investigation 是深入分析） |
| 比較了多個方案、評估了優缺點 | `report/analysis` | 非 `record/decision`（decision 是記錄最終選擇，analysis 是完整比較過程） |
| 討論了線上事故的時間線與處理過程 | `record/incident` | 非 `report/investigation`（incident 重點是「發生了什麼、怎麼處理」） |
| 做出了技術選型或架構決定 | `record/decision` | 非 `report/analysis`（decision 重點是「選了什麼、為什麼」） |
| 規劃了要做的功能或改善 | `plan/*` | 再看子類型：有技術債→refactoring、有平台切換→migration、有新需求→feature |
| 討論了某個流程怎麼操作 | `guide` | 非 `tutorial`（guide 是參考手冊，tutorial 是分步教學含練習） |
| 教學性質、有步驟練習 | `tutorial` | 非 `guide` |

**關鍵區分原則：**

- **report vs record**：report 是「分析與結論」（有方法論、有證據鏈、有建議），record 是「事實紀錄」（有時間線、有出席者、有決議）
- **investigation vs incident**：investigation 回答「為什麼發生」，incident 回答「發生了什麼、怎麼處理」
- **analysis vs decision**：analysis 回答「哪個比較好」，decision 回答「我們選了什麼」

**推斷後必須確認：** 向使用者明確說明推斷結果並確認：

```
根據我們剛才的討論（分析了 XX 的根因與影響範圍），建議使用「調查報告」格式。確認嗎？
```

使用 `AskUserQuestion` 提供推斷結果作為推薦選項，同時列出其他可能選項讓使用者選擇。

### Step 2: 互動引導（無脈絡時）

使用 `AskUserQuestion` 逐層引導：

**第一層 — 文件類型：**
- 計畫 (plan) — 規劃未來要做的事
- 報告 (report) — 記錄已完成的分析或進展
- 指南 (guide) — 說明如何完成某件事
- 教學 (tutorial) — 分步驟教學，含練習
- 紀錄 (record) — 記錄事件或決策
- 規範 (standard) — 定義規則與標準

**第二層 — 子類型（僅 plan、report、record 需要）：**

plan:
- 新功能 (feature)
- 重構 (refactoring)
- 遷移 (migration)
- 通用 (general)
- 技術提案 (rfc)

report:
- 調查報告 (investigation)
- 階段報告 (status)
- 分析報告 (analysis)

record:
- 會議紀錄 (meeting)
- 事件紀錄 (incident)
- 決策紀錄 (decision)
- 變更日誌 (changelog)

### Step 3: 載入模板

根據確定的 type/variant，讀取 `references/template-{type}-{variant}.md`（或 `references/template-{type}.md`）。

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

### Step 4.5: 判斷內容來源

- **對話轉文件**：對話中已有充分的技術討論內容，直接從對話萃取，掃描對話中的事實、結論、建議，對應到模板章節，不重複詢問已知資訊
- **從零撰寫**：無對話脈絡或資訊不足，依 Step 4 的類型必要欄位逐項收集

### Step 5: 撰寫文件

根據模板結構撰寫文件內容：

1. 填入 frontmatter metadata
2. 根據使用者提供的背景資訊，填充各章節內容
3. 若章節明確不適用於當前文件，直接刪除該章節，不留空佔位符。僅在資訊暫時不足但章節本身合理時才保留 `<!-- TODO: 補充 -->`
4. 若使用者提供了參考資料（如 `@file`），讀取後融入文件內容

### Step 5.5: 品質自檢

撰寫完成後執行以下檢查：

1. frontmatter 所有必填欄位是否完整
2. 殘留的 `<!-- TODO -->` 是否合理（不可填的才留）
3. 表格是否有空行或格式錯誤
4. 標題層級是否符合規範（最深不超過 `####`）
5. 檔名是否符合 `YYYYMMDDhh-NN-標題.md` 格式

### Step 6: 後續建議

文件撰寫完成後，根據文件類型提示：

| 文件類型 | 建議 |
|----------|------|
| plan | 建議使用 `/custom-skills-plan-analyze` 檢查完整性 |
| report | 建議使用 `/custom-skills-plan-analyze` 評估分析品質，或提示是否需要補充資料 |
| record/changelog | 提示是否需要同步更新版本號或 release 標籤 |
| record/decision | 提示是否需要通知相關方 |
| standard | 提示是否需要版本控制與審批流程 |
| 其他 | 提示是否需要請相關人員審閱 |

---

## 共通格式規範

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

- **Frontmatter**: 所有文件包含 YAML frontmatter（title、type、date、author、status）
- **標題層級**: `#` 文件標題、`##` 主要章節、`###` 子章節，最深不超過 `####`
- **表格**: 結構化比較或清單使用 Markdown 表格
- **清單**: 待辦事項使用 `- [ ]`，一般列表使用 `-`
- **程式碼**: 使用 fenced code block 並標註語言
- **語言**: 預設繁體中文，除非使用者指定其他語言

---

## 模板索引

所有模板位於 `references/` 目錄：

| 檔案 | 文件類型 |
|------|----------|
| [template-plan-feature.md](references/template-plan-feature.md) | 新功能計畫 |
| [template-plan-refactoring.md](references/template-plan-refactoring.md) | 重構計畫 |
| [template-plan-migration.md](references/template-plan-migration.md) | 遷移計畫 |
| [template-plan-general.md](references/template-plan-general.md) | 通用計畫 |
| [template-plan-rfc.md](references/template-plan-rfc.md) | 技術提案 |
| [template-report-investigation.md](references/template-report-investigation.md) | 調查報告 |
| [template-report-status.md](references/template-report-status.md) | 階段報告 |
| [template-report-analysis.md](references/template-report-analysis.md) | 分析報告 |
| [template-guide.md](references/template-guide.md) | 操作指南 |
| [template-tutorial.md](references/template-tutorial.md) | 教學文件 |
| [template-record-meeting.md](references/template-record-meeting.md) | 會議紀錄 |
| [template-record-incident.md](references/template-record-incident.md) | 事件紀錄 |
| [template-record-decision.md](references/template-record-decision.md) | 決策紀錄 |
| [template-record-changelog.md](references/template-record-changelog.md) | 變更日誌 |
| [template-standard.md](references/template-standard.md) | 規範文件 |

擴展時只需在 `references/` 新增 `template-{type}-{variant}.md` 並更新上方引數表。
