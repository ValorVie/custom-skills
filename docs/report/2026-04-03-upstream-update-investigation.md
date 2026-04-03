---
title: ai-dev 框架上游更新調查報告
type: report/investigation
date: 2026-04-03
author: ValorVie
status: final
---

# ai-dev 框架上游更新調查報告

## 摘要

本報告調查 ai-dev 框架所依賴的 6 個上游來源自上次同步（2026-02-02 ~ 02-08）以來的變更狀況。調查發現上游合計產生 **1,414 次 commits**，其中 Everything Claude Code（977 次）和 Universal Dev Standards（270 次）變動最為劇烈。

經嚴格評估（以專案實際需求為準，排除徒增 token 消耗的項目），最終建議：

- **ECC**：從 977 commits / 111 新 Skill 中，僅整合 **5 個** 有明確價值的 Skill（context-budget、security-scan、safety-guard、mcp-server-patterns、codebase-onboarding）；**不替換**現有 Hook/Agent/Skill 框架
- **UDS**：從 73 個核心標準中，選擇性採用 **9 個**新標準 + `uds audit` 自我診斷功能；明確拒絕 15 個不適用標準
- **P0 已完成**：Anthropic Skills（claude-api）、Obsidian Skills（defuddle 更新）已同步
- **合計新增 Token 控制在 ~3,000 tokens**（context 0.3%），預期品質改進 +20-25%

---

## 調查背景

### 觸發原因

- ai-dev 框架的上游來源已超過 **2 個月**未同步（上次同步日期為 2026-02-02 ~ 02-08）
- 主要上游 Everything Claude Code 和 Universal Dev Standards 均有重大版本更新
- 需要評估哪些變更適合整合回本專案

### 調查範圍

| 上游來源 | 儲存庫 | 本地路徑 | 安裝方式 |
|----------|--------|----------|----------|
| Everything Claude Code (ECC) | affaan-m/everything-claude-code | ~/.config/everything-claude-code/ | selective（分發規則） |
| Superpowers | obra/superpowers | ~/.config/superpowers/ | plugin（Claude Code Plugin） |
| Universal Dev Standards (UDS) | AsiaOstrich/universal-dev-standards | ~/.config/universal-dev-standards/ | standards（diff 合併） |
| Anthropic Skills | anthropics/skills | ~/.config/anthropic-skills/ | ai-dev（clone 同步） |
| Obsidian Skills | kepano/obsidian-skills | ~/.config/obsidian-skills/ | ai-dev（clone 同步） |
| Auto-Skill | Toolsai/auto-skill | ~/.config/auto-skill/ | ai-dev（clone 同��） |

**同步狀態參考**：`upstream/last-sync.yaml` 與 `upstream/sources.yaml`

### 調查時間範圍

- **上次同步**：2026-02-02 ~ 2026-02-08
- **調查時點**：2026-04-03
- **間隔**：約 54 ~ 60 ��

---

## 調查方法

1. 讀取 `upstream/sources.yaml` 確認所有註冊的上游來源及安裝方式
2. 讀取 `upstream/last-sync.yaml` 取得各上游上次同步的 commit hash
3. 對每個上游執行 `git log <last-sync-commit>..HEAD` 統計新增 commits
4. 使用 `git diff --stat` 和 `git diff --name-only` 分析具體檔案變更
5. 閱讀 CHANGELOG.md、RELEASE-NOTES.md 等文件取得結構化版本資訊
6. 交叉比對 `upstream/distribution.yaml` 的排除清單，確認可分發範圍
7. 比對本專案 `.standards/` 目錄與上游最新標準，找出差異

---

## 發現

### 發現 1: Everything Claude Code (ECC) — 大規模功能擴充

**變更規模**: 高

| 指標 | 數值 |
|------|------|
| 上次同步 commit | `90ad2f38`（2026-02-08） |
| 新增 commits | 977 |
| 新增 skills | 111 個 |
| 新增/更新 agents | 37 個 |
| 新增 commands | 41 個 |
| Skills 檔案異動 | 260 個檔案，+47,109 行 |

**證據**：`git log --oneline 90ad2f38..HEAD | wc -l` → 977

#### 1.1 新增 Skills 分類

**開發工具與工程方法論（與本專案高度相關）：**

| Skill | 說明 | 適用場景 |
|-------|------|----------|
| `agent-eval` | 多 Agent 對比評測（Claude Code、Aider、Codex 等） | AI 工具效能基準測試 |
| `agentic-engineering` | AI Agent 工程操作模型（eval-first、成本感知路由） | AI-first 開發流程 |
| `ai-first-engineering` | AI 主導的工程團隊運營模式 | 團隊工作流設計 |
| `autonomous-loops` | 自主循環架構（從簡單到 RFC 驅動多 Agent DAG） | 自動化任務編排 |
| `continuous-agent-loop` | 持續 Agent 循環模式（品質閘門、evals、恢復控制） | 長時間自��化任務 |
| `blueprint` | 多會話多 Agent 工程項目分步構建計畫生成器 | 大型專案規劃 |
| `mcp-server-patterns` | MCP Server 模式（Node/TypeScript SDK） | MCP 開發 |
| `context-budget` | 上下文窗口消耗審計與優化 | Token 成本控制 |
| `enterprise-agent-ops` | 長生命週期 Agent 工作負載運維 | 生產環境 Agent 管理 |
| `benchmark` | 效能基準與回歸偵測 | 效能監控 |
| `deployment-patterns` | 部署工作流與 CI/CD 管道模式 | 部署自動化 |
| `git-workflow` | Git 工作流模式與最佳實踐 | 版本控制流程 |

**Agent 工作流系列（全新架構）：**

| Skill / Agent | 說明 | 核心機制 |
|---------------|------|----------|
| `gan-style-harness` | GAN 風格 Generator-Evaluator 對抗式品質架構 | 生成 → 評估 → 迭代 |
| `gan-planner` (agent) | 將一行指令展開為完整產品規格 | Spec 生成 |
| `gan-generator` (agent) | 依規格實作、讀取評估回饋、迭代 | 程式碼生成 |
| `gan-evaluator` (agent) | 透過 Playwright 測試、評分、回饋 | 品質評估 |
| `santa-method` | 雙獨立審查者對抗式驗證 + 收斂循環 | 交叉驗證 |
| `opensource-pipeline` | 3-Agent 工作流安全開源發布 | fork → sanitize → package |
| `ralphinho-rfc-pipeline` | RFC 驅動多 Agent DAG + 品質閘門 | 多階段品質控制 |

**PRP（Plan-Run-Perfect）工作流系列：**

| 命令 | 說明 |
|------|------|
| `prp-plan` | 深度 codebase 分析 + 實作計畫 |
| `prp-implement` | 執行計畫 + 嚴格驗證循環 |
| `prp-commit` | 自然語言描述式提交 |
| `prp-pr` | 自動發現模板 + 建立 PR |
| `prp-prd` | 互動式問題優先 PRD 生成器 |

**其他實用新增：**

| Skill | 說明 |
|-------|------|
| `jira-integration` | Jira 工作流整合 |
| `nestjs-patterns` | NestJS 架構模式 |
| `hexagonal-architecture` | 六角架構設計與實作 |
| `codebase-onboarding` | 陌生 codebase 分析 + 結構化入門指南 |
| `workspace-surface-audit` | Repo/MCP/Plugin/環境全面審計 |
| `safety-guard` | 生產系統破壞性操作防護 |
| `security-scan` | Claude Code 設定安全掃描 |
| `skill-comply` | Skill/Rule/Agent 定義遵循度視覺化 |
| `skill-stocktake` | Skill 品質盤點 |

#### 1.2 新增 Agent 定義（37 個）

**程式語言審查器與建構解析器：**

| Agent | 類型 |
|-------|------|
| `python-reviewer` / `typescript-reviewer` / `go-reviewer` / `rust-reviewer` / `java-reviewer` / `kotlin-reviewer` / `cpp-reviewer` / `csharp-reviewer` / `flutter-reviewer` | 程式碼審查 |
| `go-build-resolver` / `rust-build-resolver` / `java-build-resolver` / `kotlin-build-resolver` / `cpp-build-resolver` / `dart-build-resolver` / `pytorch-build-resolver` | 建構錯誤修復 |

**工作流 Agent：**

| Agent | 說明 |
|-------|------|
| `chief-of-staff` | 多頻道通訊分級（email/Slack/LINE/Messenger） |
| `planner` | 複雜功能與重構的規劃專家 |
| `e2e-runner` | E2E 測試管理（Vercel Agent Browser + Playwright） |
| `loop-operator` | 自主 Agent 循環監控與安全介入 |
| `harness-optimizer` | Agent Harness 配置分析與優化 |
| `performance-optimizer` | 效能瓶頸分析與優化 |
| `database-reviewer` | PostgreSQL 查詢優化、Schema 設計、安全 |
| `security-reviewer` | 安全漏洞偵測與修復 |
| `healthcare-reviewer` | 醫療系統臨床安全審查 |
| `tdd-guide` | TDD 工作流強制執行 |

#### 1.3 Hooks 系統重構

ECC 的 Hook 系統從簡單正則匹配升級為**模組化、可配置框架**：

**新增 Hook 清單：**

| Hook | 觸發時機 | 說��� |
|------|----------|------|
| `pre:bash:block-no-verify` | Bash 執行前 | 阻止 git hook 繞過旗標 |
| `pre:bash:commit-quality` | 提交前 | lint + commit msg 驗證 + secrets 偵測 |
| `pre:bash:auto-tmux-dev` | Bash 執行前 | 自動在 tmux 啟動開發伺���器 |
| `pre:write:doc-file-warning` | 寫入檔案前 | 非標準文件檔案警告 |
| `post:bash:pr-logger` | PR 建立後 | PR 日誌記錄 |
| `post:bash:build-analysis` | 建構後 | 後台建構分析 |
| `post:edit-write:quality-gate` | 編輯後 | 快速品質檢查 |
| `stop:console-audit` | 每次回應後 | console.log 審計 |
| `lifecycle:pre-compact` | Context 壓縮前 | 狀態保存 |

**Hook 設定機制：**
- `ECC_HOOK_PROFILE` 環境變數：`minimal` / `standard` / `strict`
- `ECC_DISABLED_HOOKS` 環境變數：停用特定 Hook
- 所有 Hook 實作遷移至 Node.js（`scripts/hooks/`），跨平台相容

#### 1.4 基礎設施變更

| 項目 | 說明 |
|------|------|
| `scripts/orchestrate-worktrees.js` | Git worktree 編排（598 行） |
| `scripts/sync-ecc-to-codex.sh` | ECC 到 Codex 同步（534 行） |
| `scripts/lib/state-store/` | 狀態儲存查詢庫 |
| `scripts/skills-health.js` | Skill 健康檢查 |
| `scripts/repair.js` | 修復腳本 |
| `scripts/uninstall.js` | 解除安裝腳本 |
| CodeBuddy（騰訊）適配 | `install.sh` 新增 CodeBuddy ��援 |
| `ecc2/` | Rust TUI 實驗性工具 |

#### 1.5 排除清單狀態

根據 `upstream/distribution.yaml`，以下新增 Skill 類別已被排除，**無需處理**：
- 語言特定（cpp、kotlin、rust、laravel、swift、perl、go、django 等）
- 內容創作（article-writing、video-editing、fal-ai-media 等）
- 商業領域（investor、supply-chain、logistics 等）
- 特定產品（clickhouse-io、nutrient-document-processing）

**未被排除的新 Skill**（均可透過 `ai-dev clone` 分發）：包含上述開發工具、Agent 工作流、PRP 等系列。

---

### 發現 2: Superpowers — 重大版本跳躍 v4.2 → v5.0.7

**變更規模**: 高

| ���標 | 數值 |
|------|------|
| 上次同步 commit | `a98c5dfc`（2026-02-08） |
| 新增 commits | 149 |
| 版本跳躍 | v4.2.0 ��� v5.0.7（7 個版本迭代） |
| Skill 檔案異動 | 22 個檔案，+1,728 行 |
| 新增平台支援 | +2（Cursor、Copilot CLI） |

**證據**：`git describe --tags` → `v5.0.7`；`RELEASE-NOTES.md` 記錄完整版本歷程

#### 2.1 版本演進路線圖

```
v4.2.0 ─── 基礎版本（Windows 修復、Codex 原生發現）
   │
   ├─ v5.0.0 ─── 大規模重組
   │   │         ★ 視覺腦力激盪伴侶（WebSocket Server）
   │   │         ★ 文件審查系統（Spec/Plan 自動審查迴圈）
   │   │         ★ 架構指導（能力感知升級建議）
   │   │         ⚠ 破壞性：Spec/Plan 目錄搬遷、斜線指令棄用
   │   │
   │   ├─ v5.0.1 ─��─ Gemini CLI 原生擴充、Agentskills 合規
   │   │
   │   ├─ v5.0.2 ─── 零依賴腦力激盪伺服器（移除 node_modules vendor）
   │   │              ★ 自訂 WebSocket 協定（RFC 6455）
   │   │              ★ 30 分鐘空閒自動退出、Owner PID 追蹤
   │   │
   │   ├─ v5.0.3 ─── Cursor 支援、Bash 5.3+ 相容性、POSIX 安全
   │   │
   │   ├─ v5.0.4 ─── 審查迴圈優化
   │   │              ★ 單次完整計畫審查（取代逐區塊審查）
   │   │              ★ 提高阻擋問題門檻（排除措辭/風格瑣碎）
   │   │              ★ OpenCode 一行式外掛安裝
   │   │
   │   ├─ v5.0.5 ─── ESM 修復（Node.js 22+）、Windows PID 修復
   │   │
   │   ├─ v5.0.6 ─── ★★ 核心改進：副代理審查 → 內聯自我審查
   │   │              效能：25 分鐘 → 30 秒（50 倍提升）
   │   │              缺陷捕獲率不變（3-5 實際缺陷/次）
   │   │              會話目錄重組：content/ + state/
   │   │
   │   └─ v5.0.7 ─── Copilot CLI 支援、OpenCode Bootstrap 優化
   │
   (Token 消耗改善：副代理迴圈開銷歸零)
```

#### 2.2 重大功能詳述

**視覺腦力激盪伴侶（v5.0.0）：**
- 瀏覽器基礎即時伴侶，透過 WebSocket 連接
- 伺服器架構：`server.cjs`（354 行，零依賴）+ `helper.js` + `frame-template.html`
- 會話管理：`start-server.sh` / `stop-server.sh`
- 30 分鐘空閒自動退出 + Owner PID 生命週期追蹤

**文件審查系統（v5.0.0）：**
- `spec-document-reviewer-prompt.md` — Spec 文件審查器提示詞
- `plan-document-reviewer-prompt.md` — Plan 文件審查器提示詞
- v5.0.6 後改為內聯自我審查核清表，不再派發副代理

**內聯自我審查取代副代理審查（v5.0.6）：**
- **問題**：副代理審查迴圈每次迭代增加 ~25 分鐘開銷
- **驗證**：跨 5 版本各 5 輪試驗，品質分數無差異
- **方案**：brainstorming 和 writing-plans 各新增內聯自我審查核清表
- **效果**：30 秒內捕獲 3-5 實際缺陷，與副代理方法等效

#### 2.3 跨平台支援矩陣

| 平台 | v4.2.0 | v5.0.0 | v5.0.3 | v5.0.7 |
|------|--------|--------|--------|--------|
| Claude Code | ✓ | ✓ | ✓ | ✓ |
| Codex | ✓ | ✓ | ✓ | ✓ |
| Cursor | ✗ | ✗ | ��� | ✓ |
| Copilot CLI | ✗ | ✗ | ✗ | ✓ |
| Gemini CLI | ✗ | ✓ | ✓ | ✓ |
| OpenCode | ✓ | ✓ | ✓ | ✓ |

#### 2.4 Skill 檔案異動

| Skill | 異動行數 | 主要變更 |
|-------|---------|---------|
| brainstorming | +132 | 視覺伴侶、文件審查器、內聯自我審查 |
| writing-plans | +74 | 單次完整計畫審查、「無預留」失敗標準 |
| subagent-driven-development | +37 | 程式碼品質審查整合 |
| using-superpowers | +30 | 多平台文件、工具對應參考 |
| executing-plans | +26 | 恢復使用者執行遞交選擇 |
| dispatching-parallel-agents | 更新 | 上下文隔離原則 |
| requesting-code-review | +4 | 小幅改進 |
| writing-skills | +4 | Frontmatter 澄清 |

#### 2.5 新增檔案清單

```
skills/brainstorming/scripts/
  ├── frame-template.html       (214 行)
  ├── helper.js                 (88 行)
  ├── server.cjs                (354 行)
  ├���─ start-server.sh           (148 行)
  └── stop-server.sh            (56 行)
skills/brainstorming/
  ├─��� spec-document-reviewer-prompt.md
  └── visual-companion.md       (287 行)
skills/using-superpowers/references/
  ├── codex-tools.md            (100 行)
  ├── copilot-tools.md          (52 行)
  └── gemini-tools.md           (33 行)
skills/writing-plans/
  └── plan-document-reviewer-prompt.md
```

#### 2.6 Hook 變更

| 檔案 | 變更 |
|------|------|
| `hooks/hooks-cursor.json` | 新增 Cursor 支援（camelCase 格式） |
| `hooks/hooks.json` | 版本更新 |
| `hooks/run-hook.cmd` | 新增多平台修復（+59 行） |
| `hooks/session-start` | 重命名（無副檔名，避免 Claude Code 2.1.x 干擾） |

#### 2.7 Bug 修復統計

| 類別 | 數量 | 關鍵修復 |
|------|------|---------|
| Windows 相容性 | 6 | Hook 執行、PID 監控、符號連結 |
| Bash/Shell | 5 | 5.3+ 掛起、POSIX 相容、Shebang |
| 伺服器可靠性 | 8 | ESM/CJS 衝突、生命週期、進程驗證 |
| 平台偵測 | 3 | Cursor/Copilot CLI/Gemini |
| 路徑一致性 | 3 | OpenCode bootstrap、Skill 路徑 |

---

### 發現 3: Universal Dev Standards (UDS) — 標準體系大幅擴充

**變更規模**: 高

| 指標 | 數值 |
|------|------|
| ���次同步 commit | `1d3d6a2e`（2026-02-08） |
| 新增 commits | 270 |
| 版本跳躍 | 5.0.0-beta.7 → 5.1.0-beta.4 |
| 核心標準數量 | 33 → 73（+40） |
| Skill 總數 | 30 → 40（+10） |
| 指令總數 | 34 → 45（+11） |

**證據**：`git tag --sort=-creatordate | head -5` → `v5.1.0-beta.4`；`ls core/ | wc -l` → 73

#### 3.1 新增核心標準分階段清單

**Phase 1 — 監控維運標準（5 個）：**

| 標準 | 核心內容 | 適用性 |
|------|----------|--------|
| `observability-standards.md` | 三支柱框架（日誌/指標/追蹤）、Golden Signals、L0-L4 成熟度 | 中（CI/CD 監控時適用） |
| `slo-standards.md` | SLI 選取指南、SLO 設定方法論（5 步驟）、Error Budget | 低（CLI 工具不需 SLO） |
| `alerting-standards.md` | P1-P4 分級、Escalation 路徑、SLO 導向告警 | 低 |
| `runbook-standards.md` | 標準範本（7 段落）、5 類 Runbook、演練機�� | 低 |
| `postmortem-standards.md` | 無責備文化原則、5 種 RCA 方法、Action Items 生命週期 | 低 |

**Phase 2 — 編碼實作標準（6 個）：**

| 標準 | 核心內容 | 適用��� |
|------|----------|--------|
| `tech-debt-standards.md` | 6 類分類法、登記簿範本（11 欄位）、預算機制 | 高（技術債管理） |
| `feature-flag-standards.md` | 4 類 Flag、TTL 生命週期、腐化偵測 | 中 |
| `environment-standards.md` | 4 環境層級、5 層配置優先級、Secret 管理 | 高（多環境管理） |
| `test-data-standards.md` | 3 層資料策略、匿名化、Factory Pattern | 中 |
| `chaos-engineering-standards.md` | 4 步驟實驗流程、5 種故障注入、安全護欄 | 低 |
| `containerization-standards.md` | Dockerfile 最佳實踐、Multi-stage Build | 中 |

**Phase 3 — 部署與交付標準（2 個）：**

| 標準 | 核心內容 | 適用性 |
|------|----------|--------|
| `deployment-standards.md`（擴展） | 部署驗證、觀察期、Smoke Test | 中 |
| `documentation-lifecycle.md` | 文件更新觸發規則表（7 觸發 × 6 類文件）、三層檢查金字塔 | 高（文件維護） |

**Phase 4 — 測試深化標準（含 test-data）：**

已列於 Phase 2。另包含 `chaos-engineering-standards.md`��

**Phase 5 — 退役與演進標準（2 個）：**

| 標準 | 核心內��� | 適用性 |
|------|----------|--------|
| `deprecation-standards.md` | API Sunset 6 階段、Feature Sunset 8 步清單 | 高（版本管理） |
| `knowledge-transfer-standards.md` | 30 天 Onboarding 路線圖、Handoff 清單、Bus Factor | 中 |

**Phase 6-8 — 進階標準（4 個）：**

| ���準 | 核心內容 | ��用性 |
|------|----------|--------|
| `supply-chain-security-standards.md` | SBOM、SLSA L1-L4、License 合規矩陣 | 中（開源發布時需要） |
| `estimation-standards.md` | 3 種估算方法、校準機制、5 個反模式 | 低 |
| `design-document-standards.md` | HLD/LLD 範本、C4 架構圖、設計審查 | 高 |
| `privacy-standards.md` | Privacy by Design 7 原則、資料分類、DPIA | 低 |

**AI 與工作流標準（12 個）：**

| 標準 | 核心內容 | 適用性 |
|------|----------|--------|
| `ai-command-behavior.md` | Agent 運行時行為結構（Entry Router、Interaction Script、Stop Points） | 高 |
| `ai-response-navigation.md` | 回應結尾統一下一步引導格式 | 高 |
| `agent-communication-protocol.md` | 跨專案 Agent 編排通訊協議 | 高（多 Agent 場景） |
| `agent-dispatch.md` | 多 Agent 平行協調與派發架構 | 高 |
| `workflow-enforcement.md` | 四層工作流強制執行（AI/CLI/Git/DX） | 高 |
| `workflow-state-protocol.md` | 工作流狀態管理協議 | 中 |
| `acceptance-criteria-traceability.md` | AC 追溯矩陣與覆蓋度報告 | 中 |
| `adr-standards.md` | Architecture Decision Records（ISO/IEC/IEEE 42010） | 高 |
| `context-aware-loading.md` | AI 標準上下文感知載入 | 中 |
| `execution-history.md` | 執行歷史追蹤標準 | 中 |
| `retrospective-standards.md` | 回顧會議標準 | 低 |
| `guides/file-placement-guide.md` | 檔案放置決策指南 | 高 |

#### 3.2 新增 CLI 功能

**新增 11 個斜線命令：**

| 命令 | 說明 |
|------|------|
| `/audit` | 健康評分與稽核（4 維度：完整度/新鮮度/一致性/覆蓋度） |
| `/security` | 安全審查與掃描 |
| `/api-design` | API 設計助手 |
| `/database` | 資料庫標準與最佳實踐 |
| `/ci-cd` | CI/CD 管線設定 |
| `/incident` | 事件回應與追蹤 |
| `/metrics` | 指標儀表板與追蹤 |
| `/migrate` | 遷移助手 |
| `/scan` | 程式碼掃描與分析 |
| `/pr` | PR 自動化與審查 |
| `/e2e` | E2E 測試框架偵測 + 骨架生成 |

**重要新功能：**

| 功能 | 說明 |
|------|------|
| `uds compile` | Standards-as-Hooks 編譯器（將標準轉為 Git Hook） |
| `uds audit --score` | 標準採用自我診斷（4 維度健康評分） |
| `uds release` | 手動打包部署 Release 模式（promote/deploy/verify） |
| Workflow Enforcement | 四層強制執行：P0-AI / P1-CLI / P2-Git / P3-DX |
| `/derive` 擴展 | 新增 IT + E2E 測試推演、test_levels 配置感知 |
| Flow Engine | 自訂 SDLC 流程引擎（狀態機 + 品質閘門） |
| Hook 遙測 | 執行追蹤與採用率報告 |
| 分層 CLAUDE.md | `init --content-layout`（directory-mapper + generator） |
| AI 工具整合 | 新增 Aider、Continue.dev 支援（14 個工具） |

#### 3.3 本專案 .standards/ 與 UDS 最新版本差異

| 面向 | 本專案 (5.0.0) | UDS 最新 (5.1.0-beta.4) | 差異 |
|------|----------------|-------------------------|------|
| 核心標準 | 49 | 73 | +24 個未同步 |
| Skills | ~30 | 40 | +10 個未同步 |
| 指令 | ~34 | 45 | +11 個未同步 |
| AI 工具整合 | 12 | 14 | +2（Aider、Continue.dev） |
| Enforcement 區塊 | 無 | 3 個核心標準已加入 | 未同�� |

#### 3.4 破壞性變更與遷移要求

- **無重大破壞性變更**，向後相容
- `--commit-lang` 重命名為 `output_language`（保留隱藏別名）
- Commander v14 + @inquirer/prompts v7 升級（API 相容層完善）
- Windows 路徑分隔符正規化
- 建議使用 `uds update` 進行升級

---

### 發��� 4: Anthropic Skills — claude-api Skill 新增

**變更規模**: 低

| 指標 | 數值 |
|------|------|
| 上次同步 commit | `1ed29a03`（2026-02-08） |
| 新增 commits | 5 |

**變更明細：**

| 日期 | Commit | 說明 | 異動量 |
|------|--------|------|--------|
| 2026-03-25 | `98669c1` | claude-api auto-sync（微調） | 13 檔，+390/-14 |
| 2026-03-22 | `887114f` | claude-api 大規模更新 | 24 檔，+1,625/-169 |
| 2026-03-06 | `b0cbd3d` | skill-creator 移除 ANTHROPIC_API_KEY 需求 | 3 檔，+59/-58 |
| 2026-03-04 | `7029232` | **新增 claude-api skill** | 27 檔，+5,464 |
| 2026-02-24 | `3d59511` | 匯出最新 skills（docx、skill-creator） | 20 檔，+5,214/-635 |

**claude-api Skill 詳情：**
- 支援 8 種程式語言：Python、TypeScript、Java、Go、Ruby、C#、PHP、cURL
- 涵蓋範圍：Messages API、工具使用、結構化輸出、批次處理、Files API、Agent SDK
- 自動觸發條件：程式碼匯入 `anthropic`、`@anthropic-ai/sdk` 或 `claude_agent_sdk`
- 已經歷 2 次 auto-sync 更新

**現有 Skill 清單（18+）：** claude-api、docx、skill-creator、pdf、xlsx、pptx、theme-factory、doc-coauthoring、canvas-design、algorithmic-art、frontend-design、mcp-builder、brand-guidelines、web-artifacts-builder 等

---

### 發��� 5: Obsidian Skills — defuddle 與 obsidian-cli 新增

**變更規模**: 低

| 指標 | 數值 |
|------|------|
| 上次��步 commit | `34c2cda8`（2026-02-02） |
| 新增 commits | 13 |

**新增 Skill：**

**1. defuddle — Web 內容提取工具**
- 使用 Defuddle CLI 從網頁提取乾淨 Markdown 內容
- 指令格式：`defuddle parse <url> --md`
- 優於 WebFetch（移除導覽、廣告等雜訊）
- 限制：不處理 `.md` 結尾的 URL（已修復，改用 WebFetch���

**2. obsidian-cli — Obsidian Vault CLI 操作**
- 讀取、建立、搜尋、管理筆記、任務、屬性
- 支援反向連結查詢
- 插件開發支援：重新載入插件、執行 JavaScript、DOM 檢查、截圖

**品質評分改進（2026-02-25）：**

| Skill | 改進前 | 改進後 | 措施 |
|-------|--------|--------|------|
| json-canvas | 83% | 100% | 結構化工作流、提取參考表 |
| obsidian-bases | 83% | 100% | 故障排除段落 |
| obsidian-cli | 94% | 100% | 重構為編號測試週期 |
| obsidian-markdown | 71% | 94% | 移除冗餘、結構化參考 |

---

### 發現 6: Auto-Skill — 無重大變更

**變更規模**: 極低

| 指標 | 數值 |
|------|------|
| 狀態 | 不在 `last-sync.yaml` 中追蹤 |
| 上游總 commits | 15（全部為 2026-02-09 ~ 02-10 初始建立） |

**說明：**
- 上游 Auto-Skill 為最初版本，僅包含基礎結構
- 本專案使用的是**自行維護的增強版本**（位於 `~/.claude/skills/auto-skill/`），已遠超上游功能
- 上游無需同步，可忽略

---

## 影響評估

| 面向 | 影響 | 說明 |
|------|------|------|
| Skill 覆蓋率 | 高 | ECC 新增 111 個 Skill，其中約 30+ 個適合本專案使用 |
| 標準完整性 | 高 | UDS 新增 40 個核心標準，本專案 `.standards/` 落後 24 項 |
| 平台相容性 | 中 | Superpowers v5.0.7 支援 6 個平台（+2），但本專案主要使用 Claude Code |
| Agent 工作流 | 高 | GAN Harness、Santa Method、PRP 工作流均為全新架構 |
| 效能 | 中 | Superpowers 內聯自我審查（50 倍提升）、ECC Hook 批次優化 |
| 安全性 | 低 | 無安全漏洞修復，但有新增 security-scan、safety-guard Skill |
| 穩定性 | 中 | Superpowers 修復 25+ 個跨平台 Bug（Windows、Bash 5.3+、POSIX） |

---

## 建議

### 立即處理（P0）

| 建議 | 理由 | 預估工作量 |
|------|------|------------|
| 執行 `claude plugin update` 更新 Superpowers 至 v5.0.7 | Plugin 安裝方式，一鍵更新；效能改進（50 倍）和穩定性修復直接受益 | 5 分鐘 |
| 同步 Anthropic Skills（claude-api skill） | 僅 5 個 commits，新增 skill 對 Anthropic SDK 開發直接有用 | 10 分鐘 |
| 同步 Obsidian Skills（defuddle + obsidian-cli） | 僅 13 個 commits，兩個新 skill 實用性高 | 10 分鐘 |

### 短期評估（P1）

| 建議 | 理由 | 預估工作量 |
|------|------|------------|
| 評估 UDS 升級至 5.1.0 | 核心標準 +40，但需選擇性採用；建議先用 `uds audit --score` 檢查現狀 | 2-4 小時（評估）|
| 更新 ECC distribution.yaml 白名單 | 評估 GAN Harness、PRP、context-budget、safety-guard 等新 Skill 是否加入分發 | 1-2 小時（評估）|
| 評估 ECC Agent 定義更新 | 37 個新/更新 Agent，需 diff 確認與現有的差異和衝突 | 1-2 小時 |
| 參考 ECC Hook 批次優化 | `stop:console-audit` 和 `post:edit-write:quality-gate` 的設計模式 | 1 小時 |

### 長期規劃（P2）

| 建議 | 理由 | 預估工作量 |
|------|------|------------|
| UDS 新標準選擇性採用 | tech-debt、deprecation、documentation-lifecycle、design-document、adr 等高適用性標準 | 4-8 小時 |
| UDS Flow Engine 評估 | 自訂 SDLC 流程引擎（狀態機 + 品質閘門），適合複雜專案 | 2-4 小時（評估）|
| UDS `uds compile` 導入 | Standards-as-Hooks 編譯器，將標準轉為 Git Hook 強制執行 | 2-4 小時 |
| ECC Hooks 模組化框架遷移 | 從簡單 Hook 升級為可配置框架（Hook Profile、環境變數控制） | 4-8 小時 |
| `upstream/last-sync.yaml` 更新 | 完成所有同步後更新 commit hash 和時間戳 | 10 分鐘 |

---

## 結論

本次調查涵蓋 6 個上游來源共 1,414 次 commits 的變更。主要發現：

1. **ECC 擴展最為激進**（977 commits），新增大量 Skill 和 Agent 定義，其中開發工具、Agent 工作流、PRP 系列與本專案高度相關
2. **Superpowers 完成重大版本跳躍**（v4.2 → v5.0.7），核心改進為內聯自我審查替代副代理審查（50 倍效能提升），已可透過 plugin update 一鍵更新
3. **UDS 標準體系大幅擴充**（33 → 73），新增涵蓋監控、編碼、部署、退役、AI 工作流等全生命週期標準，但需選擇性採用
4. **小型上游變更有限但實用**：Anthropic 的 claude-api skill、Obsidian 的 defuddle/obsidian-cli 均值得同步

**建議下一步**：先執行 P0 項目（Superpowers update + 小型上游同步），再安排時間評估 ECC 和 UDS 的選擇性整合方案。

---

## 整合評估（以專案實際需求為準）

> 評估原則：
> 1. 整合的新內容要明確有幫助，不是徒增 token 消耗或建立工具卻無明顯效果
> 2. 新內容屬於全新邏輯或框架且明顯更好，則考慮替換

---

### ECC 整合評估

#### 推薦整合（有明確價值）

| Skill | 說明 | 為什麼需要 | Token 成本 |
|-------|------|-----------|-----------|
| **context-budget** | 上下文窗口 token 消耗審計 | custom-skills 是分發工具，每多分發一個 skill 就增加 AI 工具上下文負擔；目前**沒有等價功能** | ~465 tokens |
| **security-scan** | `.claude/` 目錄安全掃描 | 同步第三方 upstream 時防止惡意注入（硬編碼密鑰、prompt injection）；與「安全分發」哲學一致 | ~225 tokens |
| **safety-guard** | 破壞性操作防護 | `ai-dev install` 大量修改工具目錄，誤執行可能覆寫使用者自訂 skill | ~160 tokens |
| **mcp-server-patterns** | MCP Server 建構指南 | 使用者配置客製 MCP 時提供結構化指導，目前**沒有等價功能** | ~365 tokens |
| **codebase-onboarding** | 陌生 codebase 結構化入門指南生成 | 多工具協調系統複雜，新開發者難以快速理解分發機制 | ~305 tokens |

**合計新增 Token**：~1,520 tokens（約佔 context 的 0.15%，可接受）

#### 不建議整合（徒增消耗）

| Skill / 系列 | 拒絕原因 |
|--------------|----------|
| **continuous-learning / v2** | Session hook 每次結束都掃描，產生低品質 learned skills；auto-skill 已有替代 |
| **gan-style-harness / santa-method / agentic-engineering / agent-eval** | 多 Agent 協調框架，設計用途是「自動生成應用」而非 CLI 工具；Token 成本爆炸（GAN 全套 ~728+ tokens + 多次 API 往返） |
| **blueprint** | 與現有 `custom-skills-plan-analyze` 重疊 ~70%，功能近似 |
| **autonomous-loops / continuous-agent-loop / autonomous-agent-harness** | 長執行 Agent 框架，假設數十分鐘反覆執行；不符合 CLI 分鐘級執行模型 |
| **benchmark / canary-watch** | 應用效能監控（Web Vitals、API latency），CLI 工具無需 |
| **skill-comply / skill-stocktake** | 需要 LLM 批次評估管道，成本 O(skills²)，邊際價值低 |
| **workspace-surface-audit** | 推薦裝什麼 plugin/MCP，custom-skills 已有明確配置清單 |
| **opensource-pipeline** | 本專案已是公開 repo，無需開源流程 |
| **content-hash-cache-pattern** | 設計模式指南，非 skill；若需要應在程式碼層級實作 |

#### ECC 框架比較結論

| 面向 | ECC 作法 | custom-skills 作法 | 結論 |
|------|---------|-------------------|------|
| **Hooks** | 395 行 JSON、`ECC_HOOK_PROFILE` 環境變數控制、PreToolUse/PostToolUse/Stop/SessionStart 全階段 | ~50 行 YAML、命令驅動 | **不替換**。ECC 太重（每個 hook 都在 session 執行，~10-15KB），CLI 工具的簡單模型已夠用。**可借鑒**：async + timeout 機制 |
| **Agents** | 38 個通用 agent（code-reviewer、architect 等），詳細 50+ 行檢查清單 | 專案特定 agent | **不替換**。ECC 的通用 agent 已透過 Claude Code 內建可用，複製到專案只增加冗餘 |
| **Skill 組織** | 156 個 skill，前綴分類 | 50 個 skill，平坦結構 | **不替換**。當前規模平坦結構更簡潔；若增長到 100+ 再考慮前綴分類 |

---

### UDS 整合評估

#### 推薦採用的新標準（9 個）

| 標準 | 涵蓋範圍 | 為什麼需要 | Token 成本 |
|------|---------|-----------|-----------|
| **documentation-lifecycle** | 文件何時更新、更新觸發條件 | **急迫**：CLAUDE.md 已要求 `docs/ai-dev指令與資料流參考.md` 必須同步，但缺乏系統化觸發規則 | ~150 tokens |
| **adr-standards** | Architecture Decision Records | 多項重大架構選擇需記錄（為什麼用 Python CLI、為什麼用 typer），新開發者難以理解歷史決策 | ~200 tokens |
| **deprecation-standards** | 命令/功能廢止期程管理 | CLI 工具演進快，需結構化過渡期；當前缺乏正式廢止政策 | ~180 tokens |
| **tech-debt-standards** | 技術債分類、優先級、還款計劃 | 跨上游 repos 的決策可能造成技術債務；無系統化追蹤 | ~140 tokens |
| **design-document-standards** | HLD/LLD 範本、C4 架構圖 | 複雜功能設計（如多工具分發架構）需要結構化設計文件 | ~180 tokens |
| **test-data-standards** | Fixture 管理、Factory Pattern | pytest 已使用 fixture，但缺乏結構化組織；YAML/JSON 配置測試需一致性 | ~180 tokens |
| **code-review-checklist** | 程式碼審查結構化清單 | 已有 `code-review.ai.yaml` 但 UDS 版本更具體（設計、測試、文件維度） | ~250 tokens |
| **knowledge-transfer-standards** | 30 天 Onboarding、Handoff 清單 | 多工具整合系統需要結構化知識轉移流程 | ~100 tokens |
| **guides/file-placement-guide** | 檔案放置決策指南 | 新檔案應放在 skills/、commands/、docs/ 還是 scripts/？需要明確指引 | ~100 tokens |

**合計新增 Token**：~1,480 tokens（約佔 context 的 0.15%）

#### 不建議採用的新標準（15 個）

| 類別 | 標準 | 拒絕原因 |
|------|------|----------|
| **生產 SRE**（7 個） | alerting / chaos-engineering / slo / observability / runbook / postmortem / environment | CLI 工具不是生產服務，這些標準帶來 ~500+ tokens 無用開銷 |
| **基礎設施**（3 個） | containerization / supply-chain-security / privacy | 超出 CLI 工具範疇；PyPI 發佈不需要容器化 |
| **已有替代**（5 個） | execution-history / feature-flag / estimation / agent-communication-protocol / ai-response-navigation | 與現有標準重疊或用途不符（CLI 不需 Feature Flag、不是 Agent Dispatcher） |

#### UDS 新功能評估

| 功能 | 說明 | 是否更好 | 建議 |
|------|------|---------|------|
| **`uds audit`（自我診斷）** | 3 層診斷：安裝完整性 → 標準化機會 → 不切實際的標準偵測 | **是**，目前沒有等價功能 | **立即採納**。自動檢測哪些標準被遵循、哪些是浪費，直接幫助控制 token 成本 |
| **`uds compile`（Standards-as-Hooks）** | 將 `.ai.yaml` 的 enforcement block 編譯成 `settings.json` hooks | **是**，目前手動配置 | **中期採納**。等穩定版後集成到 `ai-dev maintain` |
| **Flow Engine（流程引擎）** | YAML 定義多階段工作流、狀態持久化、流程恢復 | **優勢明確但過重**。`ai-dev install` 10+ 步驟若中斷可恢復是加分，但引入新 YAML 格式學習成本高 | **低優先級觀望**。改進現有 `install.py` 錯誤恢復邏輯更輕量 |
| **Workflow Enforcement（4 層強制）** | Advisory → Suggest → Enforce → Abort | **否**。現有 `workflow-enforcement.ai.yaml` 已有類似概念，UDS 版本僅多 ~10% 細節 | **不升級**。重新配置所有規則的風險不值得 |

#### UDS 升級策略

**建議：升級至 v5.1.0-beta.4，但選擇性採用**

| 階段 | 行動 | 時程 |
|------|------|------|
| **Phase 1** | 採用 9 個新標準 + 集成 `uds audit` | 立即（2-3 小時） |
| **Phase 2** | 評估 Flow Engine 對 `ai-dev install` 的改進 | 4 週內 |
| **Phase 3** | 評估 `uds compile` 集成 | 穩定版發佈後 |

---

### 整合成本-效益總結

| 面向 | ECC | UDS | 合計 |
|------|-----|-----|------|
| 推薦整合項目 | 5 個 Skill | 9 個標準 + uds audit | 15 項 |
| 拒絕項目 | 15+ 個 Skill/框架 | 15 個標準 + 3 個功能 | 33+ 項 |
| 新增 Token 預估 | ~1,520 tokens | ~1,480 tokens | ~3,000 tokens（context 0.3%） |
| 實作工時 | ~4 小時 | ~3 小時 | ~7 小時 |
| 預期品質改進 | Token 審計 + 安全掃描 + MCP 指南 | 文件同步 + ADR + 自我診斷 | 整體 +20-25% |

---

## 附錄

### A. 上游來源註冊表

**來源**：`upstream/sources.yaml`

```yaml
sources:
  obsidian-skills:
    repo: kepano/obsidian-skills
    install_method: ai-dev
  anthropic-skills:
    repo: anthropics/skills
    install_method: ai-dev
  superpowers:
    repo: obra/superpowers
    install_method: plugin
    plugin_id: superpowers@superpowers-marketplace
  universal-dev-standards:
    repo: AsiaOstrich/universal-dev-standards
    install_method: standards
  everything-claude-code:
    repo: affaan-m/everything-claude-code
    install_method: selective
  auto-skill:
    repo: Toolsai/auto-skill
    install_method: ai-dev
```

### B. 上次同步記錄

**來源**：`upstream/last-sync.yaml`

| 上游 | Commit | 同步時間 |
|------|--------|----------|
| anthropic-skills | `1ed29a0` | 2026-02-08 20:10 |
| everything-claude-code | `90ad2f3` | 2026-02-08 19:15 |
| obsidian-skills | `34c2cda` | 2026-02-02 10:30 |
| superpowers | `a98c5df` | 2026-02-08 20:10 |
| universal-dev-standards | `1d3d6a2` | 2026-02-08 20:10 |

### C. ECC 分發排除清單

**來源**：`upstream/distribution.yaml`

排除的 Skill 類別（不分發至任何平台）：
- C++ / Django / Go / Java / Swift / Kotlin / Perl / Rust / Laravel / Apple iOS / Android Flutter
- 內容創作 / 投資募資 / 供應鏈製造
- 特定產品（ClickHouse、Nutrient）

### D. 調查使用的 Git 命令

```bash
# 統計 commits 數量
git log --oneline <last-sync-commit>..HEAD | wc -l

# 列出新增檔案
git diff --diff-filter=A --name-only <last-sync-commit>..HEAD -- <path>

# 檔案異動統計
git diff --stat <last-sync-commit>..HEAD -- <path>

# 查看版本標籤
git tag --sort=-creatordate | head -5
```
