# 開發情境決策指南

> 本指南幫助你根據任務複雜度選擇合適的開發工具組合。
> Superpowers 技能系統的完整介紹請見 [SUPERPOWERS-GUIDE.md](SUPERPOWERS-GUIDE.md)。

---

## 工具定位總覽

| 工具 | 定位 | 核心價值 |
|------|------|---------|
| OpenSpec | 規格驅動開發框架 | 留下可追溯的 specs 文件，長期參考 |
| Superpowers | AI 行為紀律框架 | 強制拆解、蘇格拉底提問、TDD 紀律（[詳見](SUPERPOWERS-GUIDE.md)） |
| Claude Code Plan | 內建輕量規劃 | 快速方向確認，用完即棄 |
| UDS (.standards/) | 開發標準規範 | 提交、測試、程式碼品質的統一標準 |
| custom-skills 測試命令 | 測試執行工具 | 從 specs 生成測試、執行、覆蓋率分析 |

### 關鍵區別：OpenSpec vs Superpowers

| 維度 | OpenSpec | Superpowers |
|------|----------|-------------|
| **產出物** | proposal → design → specs → tasks（可歸檔） | design doc + plan（用完即棄或留存） |
| **核心價值** | 留下可追溯的規格文件 | 強制思考紀律（不跳過步驟） |
| **設計階段** | 結構化 artifact 流程 | 蘇格拉底式提問 + 方案比較 |
| **實作階段** | `/opsx:apply` 執行任務 | SDD 子代理 + 雙重審查 |
| **測試方式** | specs 驅動，可選 TDD | 強制 TDD（鐵律） |
| **適合場景** | 需要長期追溯、團隊協作 | 設計決策複雜、需要嚴格紀律 |

---

## 複雜度判斷標準

| 複雜度 | 特徵 | 範例 |
|--------|------|------|
| 微小修改 | 改 1-2 個檔案、不影響邏輯 | typo、配置調整、文件修正 |
| 小功能 | 單一功能模組、明確範圍 | 新增一個 CLI 命令、加一個 API 端點 |
| 中型功能 | 跨模組、需要設計決策 | 重構模組、新增跨模組功能 |
| 大型功能 | 架構變更、多系統影響 | 新框架整合、大規模重構、新子系統 |

---

## 情境決策流程圖

```
收到任務
  │
  ├─ 是 bug？
  │   └─ Superpowers systematic-debugging → TDD 修復
  │      （真實案例：ecc-hooks 安全修復，見下方）
  │
  ├─ 改 1-2 檔、不影響邏輯？
  │   └─ 直接做 → commit
  │      （真實案例：rename maintain → update）
  │
  ├─ 單一模組、範圍明確？
  │   └─ OpenSpec 全套
  │      （真實案例：update-git-commit-workflow）
  │
  ├─ 跨模組、需設計決策？
  │   ├─ 需要文件追溯？→ 方案 C（brainstorming + OpenSpec）
  │   │  （真實案例：git-exclude-ai-files）
  │   └─ 不需追溯？→ Superpowers 全套
  │
  └─ 架構變更、多系統？
      ├─ 需要文件追溯？→ 方案 C（brainstorming + OpenSpec 分 phase）
      │  （真實案例：qdm-code-atlas MCP Server 分 phase）
      └─ 不需追溯？→ Superpowers 全套
          （真實案例：integrate-ecc-full-expansion）
```

---

## 方案 A：原始框架使用指南

> 方案 A 按任務選擇框架，各走各的完整流程，不混用。

### 微小修改

```
直接做 → commit
```

- 不需要開 OpenSpec change
- 遵循 UDS commit message 標準即可

**真實案例：rename maintain → update（2026-01-21）**

```
任務：將 ai-dev maintain 指令改名為 ai-dev update
判斷：語義改進，改名 + 更新引用，不影響邏輯
做法：直接改 3 個程式檔 + 3 個文檔 + 4 個規格引用 → commit

結果：雖然用了 OpenSpec 開了 change，但事後回顧這種純改名其實直接做就好。
教訓：如果改動是機械性的（search-and-replace），不需要設計決策，OpenSpec 反而增加開銷。
```

### 小功能：OpenSpec 全套

```
/opsx:explore → /opsx:new <name> → /opsx:continue (×N)
→ /opsx:apply → /opsx:verify → /opsx:archive
```

- 產出：proposal → design → specs → tasks
- 長期價值：specs 歸檔後可供未來參考

**真實案例：update-git-commit-workflow（2026-01-19）**

```
任務：為 git-commit 命令新增 merge 子命令
判斷：單一模組（git-commit 命令）、範圍明確、需要 spec 紀錄
做法：
  /opsx:new update-git-commit-workflow
  → proposal：說明為什麼需要 merge 功能（無專職整合經理的團隊）
  → spec：定義 git-workflow capability
  → /opsx:apply → /opsx:verify → /opsx:archive

產出：1 個 proposal + 1 個 spec + 實作程式碼
耗時：小功能，半天內完成
```

### 中型功能：選擇其一

**選 OpenSpec** 如果：重視規格文件留存、團隊協作需要追溯

**選 Superpowers** 如果：設計決策複雜、需要更嚴格的思考紀律

**真實案例：ecc-hooks 安全修復（2026-01-30）——OpenSpec 處理**

```
任務：修復 ecc-hooks 中 execSync 的命令注入漏洞
判斷：跨 6 個檔案、需要理解安全風險、但修改模式統一
做法：用 OpenSpec 記錄為什麼要改（上游 PR #102 的安全發現）
  → 1 個 proposal：記錄安全漏洞詳情
  → 1 個 spec：定義修改範圍（execSync → execFileSync + 陣列參數）
  → 6 個檔案統一修改

這個案例用 OpenSpec 是正確選擇——安全修復的「為什麼」很重要，
未來如果又出現類似的 execSync 用法，可以回頭參考這個 spec。
```

### 大型功能：Superpowers 全套

```
Superpowers brainstorming → writing-plans → SDD/executing-plans
→ finishing-a-development-branch
→ 完成後選擇性回溯補 OpenSpec specs
```

- Superpowers 強制蘇格拉底提問，確保需求拆解到位
- 5.0 版新增 SDD：有 subagent 能力時自動使用，含雙重審查（[詳見](SUPERPOWERS-GUIDE.md#subagent-driven-development-sdd)）
- 缺點：不會自動留下 specs 文件，需要手動回溯補
- 建議：完成後用 `/opsx:new` 建立精簡版 specs 歸檔

**真實案例：integrate-ecc-full-expansion（2026-01-24）**

```
任務：全面整合 everything-claude-code 並擴展標準體系
判斷：架構變更（27 個工件：6 Hook + 4 Skill + 4 Agent + 6 Command + ...）
做法：因為需要大量設計決策（多體系標準如何共存？Hook 機制怎麼跨平台？），
      適合 Superpowers 的蘇格拉底提問。

但實際用了 OpenSpec，事後回顧：
  ✅ OpenSpec 記錄了 27 個工件的完整規格，後續維護很方便
  ❌ 但設計階段缺少 Superpowers 的提問紀律，有些決策太快做了

教訓：大型功能最好用方案 C（brainstorming + OpenSpec），
      設計階段用 Superpowers 問夠問題，記錄階段用 OpenSpec。
```

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

**真實案例：git-exclude-ai-files（2026-03-07）——方案 C 實戰**

```
背景：ai-dev 複製 AI 設定檔到專案後，git 追蹤了大量非程式碼檔案
      （QDM 實測：453 檔、65,000+ 行出現在 PR 中）

第一階段：Superpowers brainstorming
  AI 逐一提問：
  ├─「為什麼不用 .gitignore？」
  │   → 調查發現 Antigravity 等 AI 工具無法載入被 gitignore 的檔案
  ├─「.git/info/exclude 的行為差異？」
  │   → 確認 AI 工具不解析 exclude，git 本身正確忽略
  ├─「排除清單怎麼維護？要手動嗎？」
  │   → 決定從模板動態推導，自動同步
  └─「哪些命令需要整合？」
      → 識別 4 個整合點：project init、init-from、clone、install

  產出：docs/plans/2026-03-07-git-exclude-ai-files-design.md
  （Superpowers 風格的設計文件，包含調查過程和方案比較）

第二階段：直接進入實作（TDD 方式）
  ├─ Task 1：核心模組 git_exclude.py（標記區塊管理）
  │   RED：寫 12 個測試 → 全部失敗
  │   GREEN：實作核心功能 → 全部通過
  ├─ Task 2：排除清單推導函數
  │   RED：寫 5 個測試 → 全部失敗
  │   GREEN：實作推導邏輯 → 全部通過
  ├─ Task 3-6：整合 4 個命令
  └─ Task 7：新增 project exclude 子命令

  驗證：建立測試 git repo → ai-dev project init → git status 確認檔案被隱藏 ✅

這個案例展示了方案 C 的核心價值：
  ✅ Superpowers brainstorming 確保「.gitignore vs .git/info/exclude」這個
     關鍵決策經過充分調查，不是拍腦袋決定的
  ⚠️ 但沒有用 OpenSpec 留下 specs，未來維護只能看設計文件和程式碼
  📝 改進：應該在第二階段用 /opsx:new 包裝，留下可歸檔的 specs
```

**中斷 Superpowers 的方式：**

當 brainstorming 完成設計討論後，明確告訴 AI：

> 「Brainstorming 階段結束。請不要進入 writing-plans。接下來我要用 OpenSpec 建立規格。」

### 大型功能

```
Superpowers brainstorming（深度需求探索）
→ 明確中斷 brainstorming
→ OpenSpec new（把 brainstorming 結論轉為 proposal）
→ OpenSpec continue（design → specs → tasks）
→ OpenSpec apply（實作，搭配 TDD 紀律）
→ OpenSpec verify → archive
```

**真實案例：qdm-code-atlas MCP Server（2026-03-05）——分 phase 大型功能**

```
背景：Phase 1 已建好 PHP 掃描器（3,336 檔、10,618 符號），但只有 CLI

整體架構：拆成 6 個 phase，每個 phase 是獨立的 OpenSpec change
  Phase 1: PHP 掃描器核心（已完成）
  Phase 2: MCP Server（3 specs + 7 tasks）← 這個
  Phase 3: Mermaid 圖表生成
  Phase 3.5: 查詢增強
  Phase 3.6: Parser 強化
  ...

Phase 2 用了 OpenSpec 全套：
  /opsx:new phase2-mcp-server
  → proposal：說明為什麼需要 MCP（讓 AI 直接存取索引，低 token 查詢）
  → design：5 個 MCP tool（search、file、table、route、impact）
  → 3 個 specs：mcp-server、mcp-tools、mcp-response-format
  → 7 個 tasks：從環境依賴到整合測試

每個 phase 獨立可交付，specs 歸檔後可供後續 phase 參考。

這個案例展示了大型功能的正確做法：
  ✅ 分 phase 降低風險——每個 phase 都有完整的 proposal/design/specs/tasks
  ✅ Phase 間可以調整方向——Phase 3.5 和 3.6 是根據 Phase 2 的實測結果追加的
  ⚠️ 缺少 Superpowers brainstorming 的提問紀律，部分設計決策事後需要修改
  📝 改進：Phase 1 開始前應該用 brainstorming 問清整體架構
```

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
| 多個獨立 bug 同時爆發 | Superpowers parallel agents | 平行解決，各不干擾 |

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

| 技能 | 用途 | 觸發 |
|------|------|------|
| brainstorming | 蘇格拉底式需求釐清 | 自動（創意工作前） |
| writing-plans | 細粒度任務分解 | 自動（brainstorming 後） |
| subagent-driven-development | 子代理逐任務執行 + 雙重審查 | 自動（有 subagent 時） |
| test-driven-development | RED-GREEN-REFACTOR | 強制（任何程式碼變更） |
| systematic-debugging | 四階段根因調查 | 強制（遇到 bug 時） |
| verification-before-completion | 新鮮驗證證據 | 強制（聲稱完成前） |

完整技能清單與調用鏈：[SUPERPOWERS-GUIDE.md](SUPERPOWERS-GUIDE.md)

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

- [SUPERPOWERS-GUIDE.md](SUPERPOWERS-GUIDE.md) — Superpowers 技能系統完整介紹
- [DEVELOPMENT-WORKFLOW.md](DEVELOPMENT-WORKFLOW.md) — 完整開發工作流程指南
- [Superpowers](https://github.com/obra/superpowers) — AI 行為紀律框架
- [高見龍的 Superpowers 心得](https://kaochenlong.com/ai-superpowers-skills) — 實戰經驗分享
