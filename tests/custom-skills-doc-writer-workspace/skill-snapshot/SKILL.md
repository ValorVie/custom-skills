---
name: custom-skills-doc-writer
description: |
  以統一格式撰寫計畫、報告、指南、教學、紀錄、規範等文件，並依專案慣例決定知識庫放置路徑、主題分類與索引更新。
  Use when: 使用者要求撰寫或起草文件，或需要整理 docs 目錄、文件分類、主題索引與知識庫結構。包含但不限於：計畫書（新功能/重構/遷移）、報告（調查/階段/分析）、指南、教學、會議紀錄、事件紀錄、決策紀錄、規範文件。
  觸發方式: /custom-skills-doc-writer [type] [variant]
  Keywords: 撰寫文件, 文件模板, 文件分類, 文件目錄, 知識庫, 主題索引, 計畫書, 報告, 指南, 教學, 紀錄, 規範, document writer, plan, report, guide, tutorial, record, standard, 寫文件, 起草, draft
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
| `research` | — | template-research.md | 探索性調查與外部證據整理 |
| `guide` | — | template-guide.md | 操作指南 |
| `runbook` | — | template-runbook.md | 可重複執行且需驗證與回復的維運手冊 |
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
| 操作會改變系統、需要停止點、驗證與回復 | `runbook` | 非一般 `guide`（runbook 強調可安全重複執行） |
| 尚無定論，正在整理外部資料、方案與未知 | `research` | 非 `report/analysis`（research 保留未知，analysis 通常要回答明確比較問題） |
| 教學性質、有步驟練習 | `tutorial` | 非 `guide` |

**關鍵區分原則：**

- **report vs record**：report 是「分析與結論」（有方法論、有證據鏈、有建議），record 是「事實紀錄」（有時間線、有出席者、有決議）
- **investigation vs incident**：investigation 回答「為什麼發生」，incident 回答「發生了什麼、怎麼處理」
- **analysis vs decision**：analysis 回答「哪個比較好」，decision 回答「我們選了什麼」

**只在實質歧義時確認：** 若不同類型會改變文件用途、保留期限或輸出路徑，先向使用者說明推斷結果並確認：

```
根據我們剛才的討論（分析了 XX 的根因與影響範圍），建議使用「調查報告」格式。確認嗎？
```

若類型與路徑都能由專案慣例或對話明確判定，直接執行，不為了形式確認而打斷工作。

### Step 2: 互動引導（無脈絡時）

使用 `AskUserQuestion` 逐層引導：

**第一層 — 文件類型：**
- 計畫 (plan) — 規劃未來要做的事
- 報告 (report) — 記錄已完成的分析或進展
- 研究 (research) — 整理外部證據、可能性與未知
- 指南 (guide) — 說明如何完成某件事
- 維運手冊 (runbook) — 可重複執行，含驗證、停止與回復
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

先讀取專案內的 `AGENTS.md`、`CLAUDE.md`、`docs/INDEX.md`、同主題文件與現有目錄，再決定輸出路徑。只有專案沒有慣例、同時存在多個合理位置，或路徑會改變文件定位時，才詢問使用者。

預設輸出路徑：

| type | 預設路徑 |
|------|----------|
| `plan` | `docs/plans/` |
| `report` | `docs/report/` |
| `research` | `docs/research/` |
| `guide` | `docs/guide/` |
| `runbook` | `docs/runbook/` 或專案已有的 `docs/guide/` |
| `tutorial` | `docs/tutorial/` |
| `record` | `docs/record/` |
| `standard` | `.standards/` 或 `docs/` |

上表只在專案沒有現成結構時使用。若同一文件類型已經依主題分目錄，預設放在 `docs/<type>/<topic>/`，不繼續堆到類型根目錄。

### Step 4.1: 決定知識庫位置

當專案的文件已經跨越多個主題或類型，讀取 [knowledge-base-organization.md](references/knowledge-base-organization.md)。

預設採用下列二維分類：

1. **實體路徑以文件用途為第一層**：`docs/<type>/<topic>/`。
2. **主題視角由索引與 metadata 提供**：在 `docs/INDEX.md` 從主題連回 plan、report、guide 等實體文件，不複製或鏡像同一份文件。
3. **第二層用穩定領域或服務名稱**：例如 `image-cdn`、`mysql84-migration`，避免使用 `misc`、`others` 或過於寬泛的 repo 名稱形成新的雜物區。
4. **沒有內容就不先建空目錄**：只在實際有文件時建立對應的 type/topic 目錄。
5. **專案現有慣例優先**：例如專案已使用 `docs/plans/` 或把 runbook 放在 `docs/guide/`，就沿用現狀，不為了套用通用規則批次搬檔。

按文件類型補問必要資訊（若已在對話脈絡或指令中提供則跳過）：

| type | 額外必問欄位 |
|------|-------------|
| `plan` | 目標、背景/動機 |
| `report/investigation` | 觸發事件、調查範圍 |
| `report/status` | 報告期間 |
| `report/analysis` | 分析目的、分析對象 |
| `research` | 研究問題、資料範圍、希望回答與保留的未知 |
| `guide` | 適用對象、前置條件 |
| `runbook` | 操作目標、影響邊界、需要的權限、成功條件、停止點與回復方式 |
| `tutorial` | 難度等級、預估時間 |
| `record/meeting` | 日期時間、出席者、議程 |
| `record/incident` | 嚴重度、發生時間、影響範圍 |
| `record/decision` | 待決策的問題、考量因素 |
| `record/changelog` | 版本號 |
| `standard` | 適用範圍 |

Metadata 自動填入：
- `title`: 從檔名的標題部分自動填入
- `date`: 時點型文件從檔名的 `YYYYMMDDhh-NN` 部分自動填入；穩定檔名使用文件建立日期或本次更新日期
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
5. 若新文件建立了新主題、使目錄清單變得難以瀏覽，或取代舊文件，同步更新最近的 `INDEX.md` 與 `superseded_by` / `supersedes` 關係。

### Step 5.5: 品質自檢

撰寫完成後執行以下檢查：

1. frontmatter 所有必填欄位是否完整
2. 殘留的 `<!-- TODO -->` 是否合理（不可填的才留）
3. 表格是否有空行或格式錯誤
4. 標題層級是否符合規範（最深不超過 `####`）
5. 檔名是否符合文件生命週期：時點型文件使用 `YYYYMMDDhh-NN-標題.md`，長期入口使用穩定檔名
6. 目錄、frontmatter `type` / `topic` 與文件實際用途是否一致
7. 相關 `INDEX.md`、舊文件取代關係與內部連結是否已更新

### Step 6: 後續建議

文件撰寫完成後，根據文件類型提示：

| 文件類型 | 建議 |
|----------|------|
| plan | 建議使用 `/custom-skills-plan-analyze` 檢查完整性 |
| report | 建議使用 `/custom-skills-plan-analyze` 評估分析品質，或提示是否需要補充資料 |
| research | 提示尚待驗證的假設與下一個證據取得點 |
| runbook | 提示應先預覽、同行審閱，再於受控環境驗證 rollback |
| record/changelog | 提示是否需要同步更新版本號或 release 標籤 |
| record/decision | 提示是否需要通知相關方 |
| standard | 提示是否需要版本控制與審批流程 |
| 其他 | 提示是否需要請相關人員審閱 |

---

## 共通格式規範

### 檔名命名規則

調查報告、階段報告、事件紀錄、會議紀錄、短期計畫與其他保留時點證據的文件，使用以下格式：

```
YYYYMMDDhh-NN-標題.md
```

| 欄位 | 說明 | 範例 |
|------|------|------|
| `YYYYMMDDhh` | 產出時間（24 小時制，UTC+8，精確到小時） | `2026040914` |
| `NN` | 當日流水編，從 `01` 起算，每日歸零，遞增無上限 | `01`、`02`、`100` |
| `標題` | 文件主題，中英文皆可，以連字號分隔多詞 | `上游更新調查`、`hook-error-analysis` |

**流水編判定邏輯：**
1. 掃描專案目錄內所有以當日日期 `YYYYMMDD` 開頭的檔案
2. 取最大流水編 +1；若無則從 `01` 開始，`YYYYMMDDhh-NN` 流水編全域唯一

長期維護的架構真相、規範、索引、狀態看板、長期操作入口與 API 參考文件，優先使用穩定檔名，例如：

```text
architecture.md
deployment-guide.md
migration-status-board.md
INDEX.md
```

若不確定，問「新讀者應該繼續找到同一個入口，還是需要保留每次產出的歷史版本？」前者用穩定檔名，後者用時間戳。

### 格式基線

- **Frontmatter**: 新撰寫的 Markdown 文件包含 YAML frontmatter（title、type、date、author、status）；專案已有規範時從其規範，不改寫外部原始資料
- **主題 metadata**: 多主題知識庫可增加 `topic`；存在取代關係時增加 `supersedes` 或 `superseded_by`
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
| [template-research.md](references/template-research.md) | 研究文件 |
| [template-guide.md](references/template-guide.md) | 操作指南 |
| [template-runbook.md](references/template-runbook.md) | 維運手冊 |
| [template-tutorial.md](references/template-tutorial.md) | 教學文件 |
| [template-record-meeting.md](references/template-record-meeting.md) | 會議紀錄 |
| [template-record-incident.md](references/template-record-incident.md) | 事件紀錄 |
| [template-record-decision.md](references/template-record-decision.md) | 決策紀錄 |
| [template-record-changelog.md](references/template-record-changelog.md) | 變更日誌 |
| [template-standard.md](references/template-standard.md) | 規範文件 |

擴展時只需在 `references/` 新增 `template-{type}-{variant}.md` 並更新上方引數表。
