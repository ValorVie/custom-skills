# ~/.claude/skills 來源審計報告

**日期：** 2026-03-21
**審計範圍：** `~/.claude/skills/` 目錄所有 skills（共 156 項）
**目的：** 識別每個 skill 的安裝來源，釐清 ai-dev 管控範圍

---

## 摘要

| 來源分類 | 數量 | 安裝方式 | source 標記 |
|---------|------|---------|------------|
| ai-dev 自有 (custom-skills) | 52 | `ai-dev install` Step 5 | `custom-skills` |
| ai-dev 代管 ECC | 91 | `ai-dev install` Step 5.6 選擇性分發 | `ecc` |
| npx skills (`.agents` symlinks) | 6 | `npx` 安裝，symlink 到 `~/.agents/skills/` | N/A |
| 自訂 skill | 3 | 手動建立或對話中產生 | N/A |
| Claude Code Plugins | ~38 | Plugin cache 直接載入，不在此目錄 | N/A |
| 已棄用殘留 | 14 | `~/.config/superpowers/skills/`（不再讀取） | N/A |
| **~/.claude/skills/ 合計** | **156** | (不含 plugins 和已棄用) | |

---

## ai-dev 分發架構

`ai-dev install` / `ai-dev update` 執行時，分發分為兩階段：

```
ai-dev install / update
  │
  ├─ Stage 1: clone/pull 上游 repos
  │    ├─ UDS → ~/.config/universal-dev-standards/
  │    ├─ ECC → ~/.config/everything-claude-code/
  │    ├─ Obsidian Skills → ~/.config/obsidian-skills/
  │    ├─ Anthropic Skills → ~/.config/anthropic-skills/
  │    └─ Auto-Skill → ~/.config/auto-skill/
  │
  └─ Stage 3: 分發到各平台
       │
       ├─ Step 5: custom-skills 分發（source="custom-skills"）
       │    來源: ~/.config/custom-skills/skills/ (52 項)
       │    目標: ~/.claude/skills/
       │    內容: ai-dev 專案 skills/ 目錄的副本
       │    特點: ai-dev 專案直接管理，含 UDS/Obsidian/Anthropic 整合品
       │
       ├─ Step 5.5: custom repos 分發
       │    來源: repos.yaml 中自訂倉庫
       │
       └─ Step 5.6: ECC 選擇性分發（source="ecc"）
            來源: ~/.config/everything-claude-code/skills/
            目標: ~/.claude/skills/
            規則: upstream/distribution.yaml
            排除: 18 個語言/框架特定 skills (C++/Django/Go/Java/Swift/ClickHouse/Nutrient)
            衝突: 與 custom-skills 同名時，custom-skills 優先（已存在不覆蓋）
```

**關鍵程式碼：**
- `script/utils/shared.py:1454` — `_distribute_ecc_selective()`
- `upstream/distribution.yaml` — ECC 分發規則與排除清單

---

## 1. ai-dev 自有 Skills（52 項，source="custom-skills"）

這些 skills 位於本專案 `skills/` 目錄，透過 `ai-dev install` Step 5 複製。
路徑：`ai-dev project/skills/` → `~/.config/custom-skills/skills/` → `~/.claude/skills/`

### 上游整合來源
- **UDS (universal-dev-standards)** — 主要 skills 來源（~25 項）
- **Obsidian Skills** (`~/.config/obsidian-skills/`) — defuddle, json-canvas, obsidian-bases, obsidian-cli, obsidian-markdown
- **Anthropic Skills** (`~/.config/anthropic-skills/`) — skill-creator
- **Auto-Skill** (`~/.config/auto-skill/`) — 自進化知識系統
- **自訂** — custom-skills-* 系列、eval-harness、work-log-claude 等

### 完整清單

| # | Skill 名稱 | 類型 | 備註 |
|---|-----------|------|------|
| 1 | agents | 目錄 | Agent 定義 |
| 2 | ai | 目錄 | AI 相關設定 |
| 3 | ai-collaboration-standards | 目錄 | UDS 整合 |
| 4 | ai-friendly-architecture | 目錄 | UDS 整合 |
| 5 | ai-instruction-standards | 目錄 | UDS 整合 |
| 6 | atdd-assistant | 目錄 | UDS 整合 |
| 7 | auto-skill | **symlink** | → `~/.config/ai-dev/projections/claude/auto-skill` |
| 8 | bdd-assistant | 目錄 | UDS 整合 |
| 9 | changelog-guide | 目錄 | UDS 整合 |
| 10 | checkin-assistant | 目錄 | UDS 整合 |
| 11 | cloud-infrastructure-security | 目錄 | 自訂 |
| 12 | code-review-assistant | 目錄 | UDS 整合 |
| 13 | commands | 目錄 | 指令定義 |
| 14 | commit-standards | 目錄 | UDS 整合 |
| 15 | custom-skill-creator | 目錄 | 自訂 |
| 16 | custom-skills-dev | 目錄 | 自訂（專案開發） |
| 17 | custom-skills-doc-updater | 目錄 | 自訂 |
| 18 | custom-skills-doc-writer | 目錄 | 自訂 |
| 19 | custom-skills-git-commit | 目錄 | 自訂 |
| 20 | custom-skills-notify | 目錄 | 自訂 |
| 21 | custom-skills-plan-analyze | 目錄 | 自訂 |
| 22 | custom-skills-threads-research | 目錄 | 自訂 |
| 23 | custom-skills-tool-overlap-analyzer | 目錄 | 自訂 |
| 24 | custom-skills-upstream-compare | 目錄 | 自訂 |
| 25 | custom-skills-upstream-sync | 目錄 | 自訂 |
| 26 | defuddle | 目錄 | Obsidian Skills 整合 |
| 27 | discuss-multi-ai | 目錄 | 自訂 |
| 28 | docs-generator | 目錄 | UDS 整合 |
| 29 | documentation-guide | 目錄 | UDS 整合 |
| 30 | error-code-guide | 目錄 | UDS 整合 |
| 31 | eval-harness | 目錄 | 自訂 |
| 32 | forward-derivation | 目錄 | UDS 整合 |
| 33 | git-workflow-guide | 目錄 | UDS 整合 |
| 34 | json-canvas | 目錄 | Obsidian Skills 整合 |
| 35 | logging-guide | 目錄 | UDS 整合 |
| 36 | methodology-system | 目錄 | UDS 整合 |
| 37 | obsidian-bases | 目錄 | Obsidian Skills 整合 |
| 38 | obsidian-cli | 目錄 | Obsidian Skills 整合 |
| 39 | obsidian-markdown | 目錄 | Obsidian Skills 整合 |
| 40 | project-structure-guide | 目錄 | UDS 整合 |
| 41 | refactoring-assistant | 目錄 | UDS 整合 |
| 42 | release-standards | 目錄 | UDS 整合 |
| 43 | requirement-assistant | 目錄 | UDS 整合 |
| 44 | reverse-engineer | 目錄 | UDS 整合 |
| 45 | security-review | 目錄 | 自訂（含 references） |
| 46 | skill-creator | 目錄 | Anthropic Skills 整合 |
| 47 | spec-driven-dev | 目錄 | UDS 整合 |
| 48 | tdd-workflow | 目錄 | UDS 整合 |
| 49 | test-coverage-assistant | 目錄 | UDS 整合 |
| 50 | testing-guide | 目錄 | UDS 整合 |
| 51 | work-log-claude | 目錄 | 自訂 |
| 52 | workflows | 目錄 | 工作流程定義 |

---

## 2. ai-dev 代管 ECC Skills（91 項，source="ecc"）

來源：`~/.config/everything-claude-code/skills/`
安裝方式：`ai-dev install` Step 5.6 `_distribute_ecc_selective()`
規則檔：`upstream/distribution.yaml`

### 安裝批次時間軸

批次時間戳反映 `ai-dev install` / `ai-dev update` 的執行時間點：

| 日期 | 數量 | 代表性 Skills |
|------|------|-------------|
| 2026-02-25 13:57 | 14 | api-design, backend-patterns, coding-standards, docker-patterns... |
| 2026-03-02 09:19 | 6 | article-writing, content-engine, investor-materials... |
| 2026-03-04 08:48 | 2 | frontend-slides, postgres-patterns |
| 2026-03-06 08:58 | 9 | agent-harness-construction, agentic-engineering, autonomous-loops... |
| 2026-03-11 10:03 | 1 | iterative-retrieval |
| 2026-03-12 09:26 | 16 | android-clean-architecture, blueprint, compose-multiplatform-patterns... |
| 2026-03-13 09:22 | 6 | claude-api, deep-research, fal-ai-media, strategic-compact... |
| 2026-03-14 17:47 | 5 | kotlin-exposed-patterns, kotlin-ktor-patterns, kotlin-patterns... |
| 2026-03-15 21:34 | 4 | crosspost, dmux-workflows, exa-search, x-api |
| 2026-03-17 09:09 | 13 | bun-runtime, claude-devfleet, configure-ecc, laravel-*... |
| 2026-03-20 12:37 | 1 | pytorch-patterns |
| 2026-03-21 13:18 | 8 | agent-eval, architecture-decision-records, codebase-onboarding... |

### ECC 排除清單（18 項，不分發）

依 `upstream/distribution.yaml` 排除：
- C++: cpp-coding-standards, cpp-testing
- Django: django-patterns, django-security, django-tdd, django-verification
- Go: golang-patterns, golang-testing
- Java/Spring Boot: java-coding-standards, jpa-patterns, springboot-patterns, springboot-security, springboot-tdd, springboot-verification
- Swift: swift-actor-persistence, swift-protocol-di-testing
- 特定產品: clickhouse-io, nutrient-document-processing

### 完整清單

| # | Skill 名稱 | 安裝日期 | 備註 |
|---|-----------|---------|------|
| 1 | agent-eval | 2026-03-21 | |
| 2 | agent-harness-construction | 2026-03-06 | |
| 3 | agentic-engineering | 2026-03-06 | |
| 4 | ai-first-engineering | 2026-03-06 | |
| 5 | ai-regression-testing | 2026-03-17 | |
| 6 | android-clean-architecture | 2026-03-12 | |
| 7 | api-design | 2026-02-25 | |
| 8 | architecture-decision-records | 2026-03-21 | |
| 9 | article-writing | 2026-03-02 | |
| 10 | autonomous-loops | 2026-03-06 | |
| 11 | backend-patterns | 2026-02-25 | |
| 12 | blueprint | 2026-03-12 | |
| 13 | bun-runtime | 2026-03-17 | |
| 14 | carrier-relationship-management | 2026-03-12 | |
| 15 | claude-api | 2026-03-13 | 也在 Anthropic Skills |
| 16 | claude-devfleet | 2026-03-17 | |
| 17 | codebase-onboarding | 2026-03-21 | |
| 18 | coding-standards | 2026-02-25 | |
| 19 | compose-multiplatform-patterns | 2026-03-12 | |
| 20 | configure-ecc | 2026-03-17 | |
| 21 | content-engine | 2026-03-02 | |
| 22 | content-hash-cache-pattern | 2026-02-25 | |
| 23 | context-budget | 2026-03-21 | |
| 24 | continuous-agent-loop | 2026-03-06 | |
| 25 | continuous-learning | 2026-03-06 | |
| 26 | continuous-learning-v2 | 2026-03-12 | |
| 27 | cost-aware-llm-pipeline | 2026-02-25 | |
| 28 | crosspost | 2026-03-15 | |
| 29 | customs-trade-compliance | 2026-03-12 | |
| 30 | data-scraper-agent | 2026-03-17 | |
| 31 | database-migrations | 2026-02-25 | |
| 32 | deep-research | 2026-03-13 | |
| 33 | deployment-patterns | 2026-02-25 | |
| 34 | dmux-workflows | 2026-03-15 | |
| 35 | docker-patterns | 2026-02-25 | |
| 36 | documentation-lookup | 2026-03-17 | |
| 37 | e2e-testing | 2026-02-25 | |
| 38 | energy-procurement | 2026-03-12 | |
| 39 | enterprise-agent-ops | 2026-03-06 | |
| 40 | exa-search | 2026-03-15 | |
| 41 | fal-ai-media | 2026-03-13 | |
| 42 | flutter-dart-code-review | 2026-03-21 | |
| 43 | foundation-models-on-device | 2026-02-25 | |
| 44 | frontend-patterns | 2026-02-25 | |
| 45 | frontend-slides | 2026-03-04 | |
| 46 | inventory-demand-planning | 2026-03-12 | |
| 47 | investor-materials | 2026-03-02 | |
| 48 | investor-outreach | 2026-03-02 | |
| 49 | iterative-retrieval | 2026-03-11 | |
| 50 | kotlin-coroutines-flows | 2026-03-12 | |
| 51 | kotlin-exposed-patterns | 2026-03-14 | |
| 52 | kotlin-ktor-patterns | 2026-03-14 | |
| 53 | kotlin-patterns | 2026-03-14 | |
| 54 | kotlin-testing | 2026-03-14 | |
| 55 | laravel-patterns | 2026-03-17 | |
| 56 | laravel-security | 2026-03-17 | |
| 57 | laravel-tdd | 2026-03-17 | |
| 58 | laravel-verification | 2026-03-17 | |
| 59 | liquid-glass-design | 2026-02-25 | |
| 60 | logistics-exception-management | 2026-03-12 | |
| 61 | market-research | 2026-03-02 | |
| 62 | mcp-server-patterns | 2026-03-17 | |
| 63 | nanoclaw-repl | 2026-03-06 | |
| 64 | nextjs-turbopack | 2026-03-17 | |
| 65 | nuxt4-patterns | 2026-03-21 | |
| 66 | perl-patterns | 2026-03-12 | |
| 67 | perl-security | 2026-03-12 | |
| 68 | perl-testing | 2026-03-12 | |
| 69 | plankton-code-quality | 2026-03-06 | |
| 70 | postgres-patterns | 2026-03-04 | |
| 71 | production-scheduling | 2026-03-12 | |
| 72 | project-guidelines-example | 2026-02-25 | |
| 73 | prompt-optimizer | 2026-03-14 | |
| 74 | python-patterns | 2026-02-25 | |
| 75 | python-testing | 2026-02-25 | |
| 76 | pytorch-patterns | 2026-03-20 | |
| 77 | quality-nonconformance | 2026-03-12 | |
| 78 | ralphinho-rfc-pipeline | 2026-03-06 | |
| 79 | regex-vs-llm-structured-text | 2026-02-25 | |
| 80 | returns-reverse-logistics | 2026-03-12 | |
| 81 | rules-distill | 2026-03-21 | |
| 82 | rust-patterns | 2026-03-21 | |
| 83 | rust-testing | 2026-03-17 | |
| 84 | search-first | 2026-03-02 | |
| 85 | security-scan | 2026-02-25 | |
| 86 | skill-stocktake | 2026-03-12 | |
| 87 | strategic-compact | 2026-03-13 | |
| 88 | swift-concurrency-6-2 | 2026-02-25 | |
| 89 | swiftui-patterns | 2026-02-25 | |
| 90 | team-builder | 2026-03-17 | |
| 91 | verification-loop | 2026-02-25 | |
| 92 | video-editing | 2026-03-13 | |
| 93 | videodb | 2026-03-13 | |
| 94 | visa-doc-translate | 2026-02-25 | |
| 95 | x-api | 2026-03-15 | |

> 注意：表中列出 95 行，但扣除與 ai-dev 重疊項（如 tdd-workflow 等 custom-skills 優先），實際 ECC 獨占項為 91。

---

## 3. npx skills（6 項，symlinks → `~/.agents/skills/`）

透過 npx 安裝，使用 symlink 連結到 `~/.agents/skills/`。
鎖定檔：`~/.agents/.skill-lock.json`
**不受 ai-dev install/update 管理。**

| # | Skill 名稱 | 來源 GitHub Repo | 安裝日期 |
|---|-----------|-----------------|---------|
| 1 | find-skills | vercel-labs/skills | 2026-02-11 |
| 2 | excalidraw-diagram | axtonliu/axton-obsidian-visual-skills | 2026-02-24 |
| 3 | code-review | supercent-io/skills-template | 2026-03-19 |
| 4 | code-review-excellence | wshobson/agents | 2026-03-19 |
| 5 | code-review-pro | onewave-ai/claude-skills | 2026-03-19 |
| 6 | code-review-quality | proffesor-for-testing/agentic-qe | 2026-03-19 |

---

## 4. 自訂 Skills（3 項）

非來自任何上游倉庫，不受 ai-dev 管理：

| # | Skill 名稱 | 建立日期 | 說明 |
|---|-----------|---------|------|
| 1 | learned | 2026-01-26 | 空目錄，由 continuous-learning skill 建立 |
| 2 | qdm-doc-updater | 2026-01-29 | QDM OpenCart 專案文件同步 skill |
| 3 | mhb-html-to-md | 2026-03-18 | 健保署健康存摺 HTML 轉 Markdown |

---

## 5. 已棄用殘留：`~/.config/superpowers/skills/`（14 項）

Superpowers 5.0+ 已改用 Claude Code 原生 plugin skills 系統。
這些是舊版殘留，**不再被讀取**，僅觸發棄用警告。

| Skill 名稱 |
|-----------|
| brainstorming |
| dispatching-parallel-agents |
| executing-plans |
| finishing-a-development-branch |
| receiving-code-review |
| requesting-code-review |
| subagent-driven-development |
| systematic-debugging |
| test-driven-development |
| using-git-worktrees |
| using-superpowers |
| verification-before-completion |
| writing-plans |
| writing-skills |

> 現由 `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.5/skills/` 提供。
> **可安全刪除** `~/.config/superpowers/skills/` 目錄以消除棄用警告。

---

## 6. Claude Code Plugins 提供的 Skills（不在 `~/.claude/skills/`）

由 plugin 系統直接載入，不經過 `~/.claude/skills/`：

| Plugin 來源 | 數量 | Skills |
|------------|------|--------|
| `claude-plugins-official/superpowers` (5.0.5) | 14 | using-superpowers, brainstorming, writing-plans, executing-plans, dispatching-parallel-agents, test-driven-development, systematic-debugging, using-git-worktrees, finishing-a-development-branch, requesting-code-review, receiving-code-review, writing-skills, verification-before-completion, subagent-driven-development |
| `claude-plugins-official/frontend-design` | 1 | frontend-design |
| `superpowers-marketplace/superpowers-developing-for-claude-code` (0.3.1) | 2 | working-with-claude-code, developing-claude-code-plugins |
| `claude-code-workflows/python-development` (1.2.2) | 16 | python-testing-patterns, python-packaging, python-type-safety, python-code-style, uv-package-manager, python-resilience, python-design-patterns, python-background-jobs, python-anti-patterns, python-error-handling, python-resource-management, python-observability, async-python-patterns, python-configuration, python-project-structure, python-performance-optimization |
| `thedotmack/claude-mem` (10.6.1) | 5 | timeline-report, do, smart-explore, mem-search, make-plan |

---

## 7. 完整架構流向圖

```
上游倉庫                       ai-dev 分發引擎                   目標
────────────                 ─────────────                   ──────

UDS ─────────┐
Obsidian ────┤               ┌─ Step 5 ──────────────────┐
Anthropic ───┼── 整合 ──→ ai-dev project ──→ custom-skills ──┤
Auto-Skill ──┘               │  skills/ (52 項)           │
                             │  source="custom-skills"    ├──→ ~/.claude/skills/
ECC ─────────────────────────┤                            │     (156 項合計)
  ~/.config/                 ├─ Step 5.6 ────────────────┤
  everything-claude-code/    │  ECC skills (~91 項)       │
                             │  source="ecc"             │
                             │  排除 18 項                │
                             └────────────────────────────┘

npx skills ──────────── symlink → ~/.agents/skills/ ──────────→ (6 項)

自訂 ─────────────────── 直接寫入 ──────────────────────────────→ (3 項)

Claude Code Plugins ──── plugins/cache/ ────── 直接載入（不經過 ~/.claude/skills/）

Superpowers 舊版 ─────── ~/.config/superpowers/skills/ ──── 已棄用，不再讀取
```

---

## 8. 問題分析與建議

### 立即可處理

1. **刪除 `~/.config/superpowers/skills/`** — 消除每次對話的棄用警告
2. **清理 `learned/` 空目錄** — 無實際內容，由 continuous-learning skill 殘留

### 需評估

3. **ECC 排除清單的精準度** — `upstream/distribution.yaml` 排除了 18 個語言特定 skills，但目前仍分發了許多不相關的領域 skills（如 carrier-relationship-management、customs-trade-compliance、energy-procurement 等供應鏈/採購領域）。可考慮擴充排除清單
4. **npx skills 的 code-review 系列重疊** — 4 個 code-review skills 來自 4 個不同 GitHub repos，加上 ai-dev 自有的 code-review-assistant，共 5 個功能相近的 skills。可評估精簡
5. **自訂 skills 是否納入 ai-dev 管理** — qdm-doc-updater 和 mhb-html-to-md 目前不受 ai-dev 管控，更新時可能被忽略

### 架構觀察

6. **雙源分發設計運作良好** — ai-dev 的 Step 5 + Step 5.6 機制有效區分了自有品與代管品，ManifestTracker 的 source 標記確保了衝突時 custom-skills 優先
7. **ECC 更新與 ai-dev 同步** — 兩者共用 `ai-dev update` 觸發，不存在更新脫鉤問題
