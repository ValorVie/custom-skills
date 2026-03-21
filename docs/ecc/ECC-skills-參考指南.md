# ECC Skills 參考指南

**最後更新：** 2026-03-21
**ECC 版本基準：** 116 skills（排除 18 → 分發 ~91）
**配套設定：** `upstream/distribution.yaml`

> 本文件說明每個 ECC skill 的功能、分類與建議。
> 修改排除清單時以此為參考依據。

---

## 閱讀方式

每個分類標示：

- **建議：保留** — 通用性高，大多數使用者都會受益
- **建議：依需求** — 語言/框架/領域特定，用到再開
- **建議：排除** — 高度特定的產業領域，絕大多數軟體開發者不需要
- **狀態：已排除** — 已在 `distribution.yaml` 中排除

---

## 1. Claude Code 工具鏈 — 建議：保留

與 Claude Code 生態系直接相關的 meta-skills。提升 agent 編排、context 管理、持續學習等能力。

| Skill | 說明 |
|-------|------|
| `agent-eval` | Coding agent 對比評估（Claude Code vs Aider vs Codex 等），比較 pass rate、成本、時間 |
| `agent-harness-construction` | 設計與優化 AI agent 的 action space、tool 定義與 observation 格式 |
| `agentic-engineering` | Eval-first 執行模式、任務分解、成本感知模型路由 |
| `autonomous-loops` | 自主 agent loop 架構模式（品質門、eval、恢復控制） |
| `blueprint` | 將一行目標展開為多 session、多 agent 的施工計畫（含對抗性審查） |
| `claude-api` | Anthropic Claude API 開發（Messages API、streaming、tool use、Agent SDK） |
| `claude-devfleet` | 多 agent 平行任務編排，使用 isolated worktrees |
| `configure-ecc` | ECC 互動式安裝器（選擇 skills/rules 安裝到 user/project 層級） |
| `context-budget` | 審計 context window 消耗（agents、skills、MCP servers、rules），找出膨脹來源 |
| `continuous-agent-loop` | 持續自主 agent loop 品質門控模式 |
| `continuous-learning` | 從 Claude Code session 自動擷取可重用 pattern 儲存為 skill |
| `continuous-learning-v2` | Instinct-based 學習系統（hooks 觀察 + 信心評分 + 演化為 skill） |
| `cost-aware-llm-pipeline` | LLM API 成本優化（模型路由、budget 追蹤、retry、prompt caching） |
| `dmux-workflows` | tmux pane 多 agent 編排（跨 Claude Code、Codex、OpenCode 等） |
| `iterative-retrieval` | 漸進式 context 檢索模式（解決 subagent context 不足問題） |
| `nanoclaw-repl` | NanoClaw v2 — ECC 的零依賴 session-aware REPL |
| `ralphinho-rfc-pipeline` | RFC 驅動多 agent DAG 執行（品質門 + merge queue） |
| `rules-distill` | 掃描 skills 擷取跨領域原則，精煉寫入 rule 檔 |
| `skill-stocktake` | Skills 與 commands 品質審計（Quick Scan / Full Stocktake） |
| `strategic-compact` | 在邏輯斷點建議手動 context compaction（避免任意自動壓縮） |

---

## 2. Web 前端 — 建議：保留

| Skill | 說明 |
|-------|------|
| `bun-runtime` | Bun 作為 runtime / package manager / bundler / test runner，與 Node.js 比較 |
| `coding-standards` | TypeScript / JavaScript / React / Node.js 通用編碼標準與最佳實踐 |
| `frontend-patterns` | React / Next.js 前端開發模式（state management、效能優化、UI） |
| `nextjs-turbopack` | Next.js 16+ 與 Turbopack（增量打包、FS caching、dev speed） |
| `nuxt4-patterns` | Nuxt 4 hydration safety、效能、route rules、SSR-safe data fetching |

---

## 3. Web 後端 — 建議：保留

| Skill | 說明 |
|-------|------|
| `api-design` | REST API 設計（resource naming、status codes、pagination、versioning、rate limiting） |
| `backend-patterns` | Node.js / Express / Next.js API routes 後端架構、DB 優化 |
| `mcp-server-patterns` | MCP server 開發（Node/TypeScript SDK、tools、resources、Zod validation） |

---

## 4. 資料庫 — 建議：保留

| Skill | 說明 |
|-------|------|
| `database-migrations` | 資料庫遷移最佳實踐（schema/data migration、rollback、zero-downtime） |
| `postgres-patterns` | PostgreSQL 查詢優化、schema 設計、索引策略、安全（Supabase 最佳實踐） |

---

## 5. DevOps / 部署 — 建議：保留

| Skill | 說明 |
|-------|------|
| `deployment-patterns` | CI/CD pipeline、Docker 容器化、health check、rollback、production readiness |
| `docker-patterns` | Docker / Docker Compose 開發模式（安全、networking、volume） |
| `enterprise-agent-ops` | 長生命週期 agent workload 營運（可觀測性、安全邊界、lifecycle） |
| `security-scan` | 掃描 `.claude/` 目錄的安全漏洞（AgentShield — CLAUDE.md、settings、hooks） |

---

## 6. 測試 — 建議：保留

| Skill | 說明 |
|-------|------|
| `ai-regression-testing` | AI 輔助開發的回歸測試策略（sandbox API 測試、AI blind spot 偵測） |
| `e2e-testing` | Playwright E2E 測試（Page Object Model、CI/CD 整合、flaky test 策略） |

---

## 7. 研究 / 搜尋 — 建議：保留

| Skill | 說明 |
|-------|------|
| `codebase-onboarding` | 分析不熟悉的 codebase 產生結構化 onboarding 指南與 CLAUDE.md |
| `data-scraper-agent` | 自動化資料採集 agent（GitHub Actions 免費運行、Gemini Flash enrichment） |
| `deep-research` | 多來源深度研究（firecrawl + exa MCP），產出附引用的報告 |
| `documentation-lookup` | 透過 Context7 MCP 查詢最新框架/函式庫文件（取代訓練資料） |
| `exa-search` | Exa 神經搜尋（web、code、company research） |

---

## 8. 通用工具 — 建議：保留

| Skill | 說明 |
|-------|------|
| `ai-first-engineering` | AI-first 團隊工程營運模型（AI agent 產出大部分實作時的管理方式） |
| `architecture-decision-records` | 自動偵測架構決策時刻，記錄 ADR（context、alternatives、rationale） |
| `content-hash-cache-pattern` | SHA-256 content hash 快取模式（path 無關、自動失效） |
| `market-research` | 市場調查 / 競爭分析 / 盡職調查（附來源歸屬） |
| `plankton-code-quality` | Plankton write-time 程式碼品質強制（auto-format + lint + Claude fix） |
| `project-guidelines-example` | 專案特定 skill 範本（以真實 production app 為基礎） |
| `prompt-optimizer` | Prompt 分析與優化（僅輸出建議，不執行任務） |
| `regex-vs-llm-structured-text` | 正則 vs LLM 結構化文字解析的決策框架 |
| `search-first` | Research-before-coding 工作流（先搜尋既有工具/函式庫再自己寫） |
| `team-builder` | 互動式 agent 選擇器（組建平行團隊） |
| `verification-loop` | Claude Code session 綜合驗證系統 |
| `visa-doc-translate` | 簽證文件翻譯（圖片 → 雙語 PDF） |

---

## 9. Laravel / PHP — 建議：依需求

有 Laravel 專案時保留，沒有則可排除。4 個 skill 涵蓋完整開發週期。

| Skill | 說明 |
|-------|------|
| `laravel-patterns` | Laravel 架構（routing/controllers、Eloquent ORM、service layer、queues、events） |
| `laravel-security` | Laravel 安全最佳實踐（authn/authz、CSRF、mass assignment、file uploads） |
| `laravel-tdd` | Laravel TDD（PHPUnit / Pest、factories、database testing、fakes） |
| `laravel-verification` | Laravel 驗證 loop（env check、lint、靜態分析、測試 + coverage、安全掃描） |

---

## 10. Kotlin / KMP — 建議：依需求

有 Kotlin 專案時保留，沒有則可排除。

| Skill | 說明 |
|-------|------|
| `kotlin-coroutines-flows` | Coroutines / Flow（Android & KMP — structured concurrency、StateFlow） |
| `kotlin-exposed-patterns` | JetBrains Exposed ORM（DSL queries、DAO、HikariCP、Flyway） |
| `kotlin-ktor-patterns` | Ktor server（routing DSL、plugins、auth、Koin DI、WebSockets） |
| `kotlin-patterns` | Idiomatic Kotlin（coroutines、null safety、DSL builders） |
| `kotlin-testing` | Kotest / MockK / coroutine testing / property-based testing / Kover |

---

## 11. Python — 建議：依需求

ai-dev 本身是 Python 專案，建議保留。

| Skill | 說明 |
|-------|------|
| `python-patterns` | PEP 8 / type hints / Pythonic idioms |
| `python-testing` | pytest / TDD / fixtures / mocking / parametrization |
| `pytorch-patterns` | PyTorch 訓練 pipeline / model 架構 / data loading |

---

## 12. Perl — 建議：依需求

有 Perl 專案時保留，沒有則可排除。

| Skill | 說明 |
|-------|------|
| `perl-patterns` | Modern Perl 5.36+ idioms 與最佳實踐 |
| `perl-security` | Taint mode / input validation / DBI / web security / perlcritic |
| `perl-testing` | Test2::V0 / Test::More / prove / Devel::Cover / TDD |

---

## 13. Rust — 建議：依需求

有 Rust 專案時保留，沒有則可排除。

| Skill | 說明 |
|-------|------|
| `rust-patterns` | Ownership / traits / concurrency / error handling |
| `rust-testing` | Unit / integration / async / property-based testing / cargo-llvm-cov |

---

## 14. Apple / iOS — 建議：依需求

有 iOS/macOS 專案時保留，沒有則可排除。

| Skill | 說明 |
|-------|------|
| `foundation-models-on-device` | Apple FoundationModels 框架（on-device LLM、@Generable、iOS 26+） |
| `liquid-glass-design` | iOS 26 Liquid Glass design system（blur、reflection、morphing） |
| `swift-concurrency-6-2` | Swift 6.2 Approachable Concurrency（@concurrent、isolated conformances） |
| `swiftui-patterns` | SwiftUI 架構（@Observable、view composition、navigation） |

---

## 15. Android / Flutter — 建議：依需求

有 Android/Flutter 專案時保留，沒有則可排除。

| Skill | 說明 |
|-------|------|
| `android-clean-architecture` | Android / KMP Clean Architecture（module structure、UseCases、Repositories） |
| `compose-multiplatform-patterns` | Compose Multiplatform（state management、navigation、theming、platform-specific UI） |
| `flutter-dart-code-review` | Flutter / Dart code review checklist（widget、state management、效能、a11y） |

---

## 16. 內容創作 / 媒體 — 建議：依需求

需要內容創作、社群經營或影片製作時保留。

| Skill | 說明 |
|-------|------|
| `article-writing` | 長篇內容寫作（文章、教學、blog、newsletter），可匹配品牌語調 |
| `content-engine` | 多平台內容系統（X、LinkedIn、TikTok、YouTube、newsletter） |
| `crosspost` | 多平台內容分發（自動適配各平台，不發重複內容） |
| `fal-ai-media` | fal.ai 媒體生成（text-to-image、text/image-to-video、TTS、video-to-audio） |
| `frontend-slides` | HTML 簡報製作（動畫、PPT/PPTX 轉換，引導發掘視覺風格） |
| `video-editing` | AI 輔助影片剪輯（FFmpeg、Remotion、ElevenLabs、fal.ai） |
| `videodb` | 影片/音訊索引、搜尋、timeline 編輯、即時串流處理 |
| `x-api` | X/Twitter API 整合（OAuth、發推、threads、搜尋、分析） |

---

## 17. 投資 / 募資 — 建議：依需求

有募資需求時保留，沒有則可排除。

| Skill | 說明 |
|-------|------|
| `investor-materials` | 投資人文件（pitch deck、one-pager、財務模型、加速器申請） |
| `investor-outreach` | 投資人 outreach（cold email、warm intro、follow-up） |

---

## 18. 供應鏈 / 製造 / 商業領域 — 建議：排除

高度特定的產業領域 skills。除非從事供應鏈、物流、製造管理，否則完全不相關。

| Skill | 說明 |
|-------|------|
| `carrier-relationship-management` | 運輸商管理（費率談判、績效追蹤、RFP、合規審查） |
| `customs-trade-compliance` | 海關/貿易合規（HS 分類、Incoterms、FTA、罰則減免） |
| `energy-procurement` | 電力/天然氣採購（關稅優化、需量管理、PPA 評估） |
| `inventory-demand-planning` | 需求預測與安全庫存優化（ABC/XYZ 分析、季節性管理） |
| `logistics-exception-management` | 物流異常處理（延誤、損壞、遺失、運輸商爭議） |
| `production-scheduling` | 生產排程（TOC/drum-buffer-rope、SMED、OEE、瓶頸解決） |
| `quality-nonconformance` | 品質不符合調查（NCR、CAPA、SPC、FDA/IATF 16949/AS9100） |
| `returns-reverse-logistics` | 退貨/逆向物流管理（退貨授權、檢驗、退款、詐欺偵測） |

---

## 19. 已排除（distribution.yaml 現行）

以下 18 項已在 `upstream/distribution.yaml` 的 `exclude.skills` 中，不會被分發：

| 分類 | Skills |
|------|--------|
| C++ | `cpp-coding-standards`, `cpp-testing` |
| Django | `django-patterns`, `django-security`, `django-tdd`, `django-verification` |
| Go | `golang-patterns`, `golang-testing` |
| Java / Spring Boot | `java-coding-standards`, `jpa-patterns`, `springboot-patterns`, `springboot-security`, `springboot-tdd`, `springboot-verification` |
| Swift (特定) | `swift-actor-persistence`, `swift-protocol-di-testing` |
| 特定產品 | `clickhouse-io`, `nutrient-document-processing` |

---

## 修改排除清單

要排除某個 skill，將其名稱加入 `upstream/distribution.yaml` 的 `exclude.skills` 清單：

```yaml
exclude:
  skills:
    # ... 現有排除項 ...
    # 供應鏈
    - carrier-relationship-management
    - customs-trade-compliance
```

下次執行 `ai-dev update` 時，被排除的 skills 不會再被複製到使用者環境。
已存在的副本不會被自動刪除，需手動清理或等 orphan cleanup 處理。
