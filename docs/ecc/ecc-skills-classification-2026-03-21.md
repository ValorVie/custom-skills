# ECC Skills 分類報告

**日期：** 2026-03-21
**範圍：** ai-dev 代管分發的 91 個 ECC (Everything Claude Code) skills
**配套檔案：** `ecc-skills-profile.yaml`

---

## 分類總覽

| 分類 | 數量 | 說明 |
|------|------|------|
| claude-code-meta | 20 | Claude Code 自身工具鏈：agent 編排、context 管理、學習、eval |
| web-frontend | 5 | React / Next.js / Nuxt / Bun 前端框架 |
| web-backend | 3 | API 設計、後端架構、MCP server |
| database | 2 | PostgreSQL、資料庫遷移 |
| devops | 4 | Docker、部署、CI/CD、企業 agent 營運 |
| testing | 2 | E2E 測試、AI 回歸測試 |
| lang-laravel | 4 | Laravel 框架全套 |
| lang-kotlin | 5 | Kotlin / KMP / Ktor / Exposed |
| lang-python | 3 | Python idioms / pytest / PyTorch |
| lang-perl | 3 | Perl 5.36+ |
| lang-rust | 2 | Rust patterns / testing |
| mobile-apple | 4 | SwiftUI / Swift 6.2 / Liquid Glass / FoundationModels |
| mobile-android | 3 | Android Clean Architecture / Compose Multiplatform / Flutter |
| content-media | 8 | 文章寫作、社群內容、影片、AI 媒體生成 |
| research | 5 | 深度研究、搜尋、市場調查、資料採集 |
| supply-chain | 8 | 供應鏈、物流、採購、製造、品質管理 |
| investment | 2 | 投資人材料、募資 outreach |
| utility | 8 | ADR、prompt 優化、正則 vs LLM、簽證翻譯等雜項 |

---

## 詳細分類

### claude-code-meta（20 項）— Claude Code 工具鏈

與 Claude Code 生態系直接相關的 meta-skills：agent 編排、context 管理、持續學習、品質控制。

| Skill | 說明 |
|-------|------|
| agent-eval | Coding agent 對比評估（pass rate、成本、時間） |
| agent-harness-construction | Agent action space 與 tool 定義優化 |
| agentic-engineering | Eval-first 執行、分解、成本感知模型路由 |
| autonomous-loops | 自主 agent loop 架構（品質門、eval、恢復） |
| blueprint | 單行目標展開為多 session 多 agent 施工計畫 |
| claude-api | Anthropic Claude API（Messages、streaming、tool use、Agent SDK） |
| claude-devfleet | 多 agent 平行任務編排（isolated worktrees） |
| configure-ecc | ECC 互動式安裝器 |
| context-budget | Context window 消耗審計與優化建議 |
| continuous-agent-loop | 持續自主 agent loop 品質門控 |
| continuous-learning | 從 session 自動擷取可重用 pattern |
| continuous-learning-v2 | Instinct-based 學習系統（hooks + 信心評分） |
| cost-aware-llm-pipeline | LLM API 成本優化（模型路由、budget 追蹤） |
| dmux-workflows | tmux pane 多 agent 編排 |
| iterative-retrieval | 漸進式 context 檢索（解決 subagent context 問題） |
| nanoclaw-repl | NanoClaw v2 session-aware REPL |
| ralphinho-rfc-pipeline | RFC 驅動多 agent DAG 執行 |
| rules-distill | 掃描 skills 擷取跨領域原則寫入 rule 檔 |
| skill-stocktake | Skills 品質審計（Quick Scan / Full Stocktake） |
| strategic-compact | 邏輯性 context compaction 建議 |

### web-frontend（5 項）

| Skill | 說明 |
|-------|------|
| bun-runtime | Bun runtime / package manager / bundler / test runner |
| coding-standards | TypeScript / JavaScript / React / Node.js 編碼標準 |
| frontend-patterns | React / Next.js 前端開發模式 |
| nextjs-turbopack | Next.js 16+ / Turbopack |
| nuxt4-patterns | Nuxt 4 hydration safety / SSR data fetching |

### web-backend（3 項）

| Skill | 說明 |
|-------|------|
| api-design | REST API 設計（命名、狀態碼、分頁、版本控制） |
| backend-patterns | Node.js / Express / Next.js API routes 後端架構 |
| mcp-server-patterns | MCP server 開發（Node/TypeScript SDK） |

### database（2 項）

| Skill | 說明 |
|-------|------|
| database-migrations | 資料庫遷移最佳實踐（zero-downtime） |
| postgres-patterns | PostgreSQL 查詢優化、schema、索引、安全 |

### devops（4 項）

| Skill | 說明 |
|-------|------|
| deployment-patterns | CI/CD、Docker 容器化、health check、rollback |
| docker-patterns | Docker / Docker Compose 開發模式 |
| enterprise-agent-ops | 長生命週期 agent 營運（可觀測性、安全邊界） |
| security-scan | Claude Code 配置安全掃描（AgentShield） |

### testing（2 項）

| Skill | 說明 |
|-------|------|
| ai-regression-testing | AI 輔助開發的回歸測試策略 |
| e2e-testing | Playwright E2E 測試（POM、CI/CD、flaky test） |

### lang-laravel（4 項）

| Skill | 說明 |
|-------|------|
| laravel-patterns | Laravel 架構（Eloquent、service layer、queues、events） |
| laravel-security | Laravel 安全（authn/authz、CSRF、mass assignment） |
| laravel-tdd | Laravel TDD（PHPUnit / Pest） |
| laravel-verification | Laravel 驗證 loop（lint、靜態分析、測試、安全掃描） |

### lang-kotlin（5 項）

| Skill | 說明 |
|-------|------|
| kotlin-coroutines-flows | Coroutines / Flow（Android & KMP） |
| kotlin-exposed-patterns | JetBrains Exposed ORM（DSL / DAO / HikariCP） |
| kotlin-ktor-patterns | Ktor server（routing DSL、Koin DI、WebSockets） |
| kotlin-patterns | Idiomatic Kotlin（coroutines、null safety、DSL） |
| kotlin-testing | Kotest / MockK / coroutine testing / Kover |

### lang-python（3 項）

| Skill | 說明 |
|-------|------|
| python-patterns | PEP 8 / type hints / Pythonic idioms |
| python-testing | pytest / TDD / fixtures / mocking |
| pytorch-patterns | PyTorch 訓練 pipeline / model 架構 / data loading |

### lang-perl（3 項）

| Skill | 說明 |
|-------|------|
| perl-patterns | Modern Perl 5.36+ idioms |
| perl-security | Taint mode / DBI / web security / perlcritic |
| perl-testing | Test2::V0 / Test::More / Devel::Cover / TDD |

### lang-rust（2 項）

| Skill | 說明 |
|-------|------|
| rust-patterns | Ownership / traits / concurrency / error handling |
| rust-testing | Unit / integration / async / property-based testing |

### mobile-apple（4 項）

| Skill | 說明 |
|-------|------|
| foundation-models-on-device | Apple FoundationModels on-device LLM（iOS 26+） |
| liquid-glass-design | iOS 26 Liquid Glass design system |
| swift-concurrency-6-2 | Swift 6.2 concurrency（@concurrent） |
| swiftui-patterns | SwiftUI 架構 / @Observable / navigation |

### mobile-android（3 項）

| Skill | 說明 |
|-------|------|
| android-clean-architecture | Android / KMP Clean Architecture |
| compose-multiplatform-patterns | Compose Multiplatform（state / navigation / theming） |
| flutter-dart-code-review | Flutter / Dart code review checklist |

### content-media（8 項）

| Skill | 說明 |
|-------|------|
| article-writing | 長篇內容寫作（文章、教學、newsletter） |
| content-engine | 多平台內容系統（X、LinkedIn、TikTok、YouTube） |
| crosspost | 多平台內容分發（自動適配各平台） |
| fal-ai-media | fal.ai 媒體生成（圖片、影片、音訊） |
| frontend-slides | HTML 簡報製作（動畫、PPT 轉換） |
| video-editing | AI 輔助影片剪輯（FFmpeg、Remotion、ElevenLabs） |
| videodb | 影片/音訊處理（索引、搜尋、timeline 編輯） |
| x-api | X/Twitter API 整合 |

### research（5 項）

| Skill | 說明 |
|-------|------|
| codebase-onboarding | 不熟悉 codebase 的結構化 onboarding 指南 |
| data-scraper-agent | 自動化資料採集 agent（GitHub Actions） |
| deep-research | 多來源深度研究（firecrawl + exa） |
| documentation-lookup | 透過 Context7 MCP 查詢最新文件 |
| exa-search | Exa 神經搜尋（web、code、company） |

### supply-chain（8 項）— 供應鏈/製造/商業領域

| Skill | 說明 |
|-------|------|
| carrier-relationship-management | 運輸商管理（費率談判、績效追蹤） |
| customs-trade-compliance | 海關/貿易合規（關稅分類、FTA） |
| energy-procurement | 電力/天然氣採購與關稅優化 |
| inventory-demand-planning | 需求預測與安全庫存優化 |
| logistics-exception-management | 物流異常處理（延誤、損壞、爭議） |
| production-scheduling | 生產排程（TOC、SMED、OEE） |
| quality-nonconformance | 品質不符合調查（NCR、CAPA、SPC） |
| returns-reverse-logistics | 退貨/逆向物流管理 |

### investment（2 項）

| Skill | 說明 |
|-------|------|
| investor-materials | 投資人文件（pitch deck、財務模型、募資材料） |
| investor-outreach | 投資人 outreach（cold email、follow-up） |

### utility（8 項）— 通用工具

| Skill | 說明 |
|-------|------|
| ai-first-engineering | AI-first 團隊工程營運模型 |
| architecture-decision-records | 架構決策記錄（ADR） |
| content-hash-cache-pattern | SHA-256 content hash 快取模式 |
| market-research | 市場調查 / 競爭分析 / 盡職調查 |
| plankton-code-quality | Plankton write-time 程式碼品質強制 |
| project-guidelines-example | 專案特定 skill 範本 |
| prompt-optimizer | Prompt 分析與優化（僅建議，不執行） |
| regex-vs-llm-structured-text | 正則 vs LLM 結構化文字解析決策框架 |
| search-first | Research-before-coding 工作流 |
| team-builder | 互動式 agent 選擇器（平行團隊組建） |
| verification-loop | Claude Code session 驗證系統 |
| visa-doc-translate | 簽證文件翻譯（圖片 → 雙語 PDF） |
