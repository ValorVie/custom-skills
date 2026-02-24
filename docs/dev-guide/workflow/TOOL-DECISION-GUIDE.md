# 開發情境決策指南

> 本指南幫助你根據任務複雜度選擇合適的開發工具組合。

---

## 工具定位總覽

| 工具 | 定位 | 核心價值 |
|------|------|---------|
| OpenSpec | 規格驅動開發框架 | 留下可追溯的 specs 文件，長期參考 |
| Superpowers | AI 行為紀律框架 | 強制拆解、蘇格拉底提問、TDD 紀律 |
| Claude Code Plan | 內建輕量規劃 | 快速方向確認，用完即棄 |
| UDS (.standards/) | 開發標準規範 | 提交、測試、程式碼品質的統一標準 |
| custom-skills 測試命令 | 測試執行工具 | 從 specs 生成測試、執行、覆蓋率分析 |

---

## 複雜度判斷標準

| 複雜度 | 特徵 | 時間估計 | 範例 |
|--------|------|---------|------|
| 微小修改 | 改 1-2 個檔案、不影響邏輯 | < 10 分鐘 | typo、配置調整、文件修正 |
| 小功能 | 單一功能模組、明確範圍 | 半天內 | 新增一個 CLI 命令、加一個 API 端點 |
| 中型功能 | 跨模組、需要設計決策 | 1-2 天 | 重構模組、新增跨模組功能 |
| 大型功能 | 架構變更、多系統影響 | 多天 | 新框架整合、大規模重構、新子系統 |

---

## 方案 A：原始框架使用指南

> 方案 A 按任務選擇框架，各走各的完整流程，不混用。

### 微小修改

```
直接做 → commit
```

- 不需要開 OpenSpec change
- 遵循 UDS commit message 標準即可

### 小功能：OpenSpec 全套

```
/opsx:explore → /opsx:new <name> → /opsx:continue (×N)
→ /opsx:apply → /opsx:verify → /opsx:archive
```

- 產出：proposal → design → specs → tasks
- 長期價值：specs 歸檔後可供未來參考

### 中型功能：選擇其一

**選 OpenSpec** 如果：重視規格文件留存、團隊協作需要追溯

**選 Superpowers** 如果：設計決策複雜、需要更嚴格的思考紀律

### 大型功能：Superpowers 全套

```
Superpowers brainstorming → writing-plans → executing-plans (with TDD)
→ 完成後選擇性回溯補 OpenSpec specs
```

- Superpowers 強制蘇格拉底提問，確保需求拆解到位
- 缺點：不會自動留下 specs 文件，需要手動回溯補
- 建議：完成後用 `/opsx:new` 建立精簡版 specs 歸檔

---

## 方案 C：優化混合流程（推薦）

> 方案 C 取各框架最強環節組合，每個階段用最適合的工具。
>
> 核心原則：**Superpowers 負責「怎麼思考」，OpenSpec 負責「留下什麼」**

### 微小修改

同方案 A，直接做。

### 小功能：OpenSpec 全套

同方案 A，OpenSpec 本身已足夠。

### 中型功能

```
Superpowers brainstorming（釐清需求、選方案）
→ 明確中斷 brainstorming
→ OpenSpec new → continue → apply → verify → archive
```

- brainstorming 階段利用 Superpowers 的提問紀律
- 規格化和實作交給 OpenSpec 留下文件

### 大型功能

```
Superpowers brainstorming（深度需求探索）
→ 明確中斷 brainstorming
→ OpenSpec new（把 brainstorming 結論轉為 proposal）
→ OpenSpec continue（design → specs → tasks）
→ OpenSpec apply（實作，搭配 TDD 紀律）
→ OpenSpec verify → archive
```

**中斷 Superpowers 的方式：**

當 brainstorming 完成設計討論後，明確告訴 AI：

> 「Brainstorming 階段結束。請不要進入 writing-plans。接下來我要用 OpenSpec 建立規格。」

---

## 測試策略分支

| 判斷 | 測試策略 | 命令 |
|------|---------|------|
| 有可自動化驗證的程式邏輯 | TDD 流程 | `/custom-skills-{lang}-derive-tests` → `/custom-skills-{lang}-test` → `/custom-skills-{lang}-coverage` |
| 有功能邏輯但難以自動化 | 手動測試清單 | 請 AI 從 specs 生成 `manual-test-checklist.md` |
| 純文件、配置、AI 命令定義 | 跳過測試 | spec-driven 流程，跳過測試階段 |

---

## 方案選擇建議

| 情境 | 推薦方案 | 理由 |
|------|---------|------|
| 剛接觸這套工具鏈 | 方案 A | 先熟悉各框架的完整流程 |
| 已熟悉兩套框架 | 方案 C | 取各家所長，效率更高 |
| 團隊協作、需要文件 | 方案 C | 確保所有功能都有 specs 紀錄 |
| 快速原型驗證 | 方案 A（微小/小） | 別過度流程化 |
| 高風險架構變更 | 方案 C（大型） | Superpowers 紀律 + OpenSpec 追溯 |

---

## 命令速查表

### OpenSpec 系列

| 命令 | 用途 |
|------|------|
| `/opsx:explore` | 探索程式碼、理解現狀 |
| `/opsx:new <name>` | 建立新 change |
| `/opsx:continue` | 建立下一個 artifact |
| `/opsx:apply` | 執行實作任務 |
| `/opsx:verify` | 驗證實作 |
| `/opsx:archive` | 歸檔 change |

### Superpowers 系列

| 命令/Skill | 用途 |
|------------|------|
| brainstorming | 蘇格拉底式需求釐清（自動觸發） |
| writing-plans | 細化執行步驟（方案 C 中跳過） |
| test-driven-development | TDD 紀律（自動觸發） |
| verification-before-completion | 完成前驗證（自動觸發） |

### 測試系列

| 命令 | 用途 |
|------|------|
| `/custom-skills-{lang}-derive-tests` | 從 specs 生成測試程式碼 |
| `/custom-skills-{lang}-test` | 執行測試並分析結果 |
| `/custom-skills-{lang}-coverage` | 覆蓋率分析 |
| `/custom-skills-report` | 生成測試報告 |

### 其他

| 命令 | 用途 |
|------|------|
| `/custom-skills-plan-analyze @<file>` | 分析提案完整性與影響 |
| Claude Code Plan 模式 | 快速方向確認（適合中型任務的方案 A） |

---

## 參考資源

- [DEVELOPMENT-WORKFLOW.md](DEVELOPMENT-WORKFLOW.md) — 完整開發工作流程指南
- [Superpowers](https://github.com/obra/superpowers) — AI 行為紀律框架
- [高見龍的 Superpowers 心得](https://kaochenlong.com/ai-superpowers-skills) — 實戰經驗分享
