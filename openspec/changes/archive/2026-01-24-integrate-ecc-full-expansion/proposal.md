# Change: 全面整合 everything-claude-code 並擴展標準體系

## Why

基於 `eval-everything-claude-code-2026-01-24-191433.md` 評估報告，規劃全面整合策略：
1. **優先整合項目** — 完整實作評估報告中推薦的所有 High Priority 項目
2. **參考項目擴展** — 新增 OpenCode Support 與 MCP Configs 範例
3. **標準體系升級** — TDD 品質比較分析後取優整合，並建立可切換的 coding-standards 多體系架構

## 整合策略

### 1. 優先整合項目（High Priority）— 全部實作

#### 1.1 Hook 機制
| 項目 | 來源 | 目標位置 | 格式 |
|------|------|----------|------|
| memory-persistence | hooks/memory-persistence/ | sources/ecc/hooks/memory-persistence/ | Python 重寫 |
| strategic-compact | hooks/strategic-compact/ | sources/ecc/hooks/strategic-compact/ | Python 重寫 |
| hooks.json 配置 | hooks/hooks.json | sources/ecc/hooks/hooks.json | 原生保留 |
| session-start hook | scripts/hooks/session-start.js | sources/ecc/hooks/ | Python 重寫 |
| session-end hook | scripts/hooks/session-end.js | sources/ecc/hooks/ | Python 重寫 |
| pre-compact hook | scripts/hooks/pre-compact.js | sources/ecc/hooks/ | Python 重寫 |

#### 1.2 Skills
| 項目 | 來源 | 目標位置 | 說明 |
|------|------|----------|------|
| continuous-learning | skills/continuous-learning/ | sources/ecc/skills/ | Session 評估與學習機制 |
| strategic-compact | skills/strategic-compact/ | sources/ecc/skills/ | 策略性 context 管理 |
| eval-harness | skills/eval-harness/ | sources/ecc/skills/ | 評估框架 |
| security-review | skills/security-review/ | sources/ecc/skills/ | 安全審查（與現有 reviewer 互補） |

#### 1.3 Agents
| 項目 | 來源 | 目標位置 | 說明 |
|------|------|----------|------|
| build-error-resolver | agents/build-error-resolver.md | sources/ecc/agents/ | 專注建置錯誤的代理 |
| e2e-runner | agents/e2e-runner.md | sources/ecc/agents/ | E2E 測試代理 |
| doc-updater | agents/doc-updater.md | sources/ecc/agents/ | 文件自動更新 |
| security-reviewer | agents/security-reviewer.md | sources/ecc/agents/ | 專門的安全審查代理 |

#### 1.4 Commands
| 項目 | 來源 | 目標位置 | 說明 |
|------|------|----------|------|
| checkpoint | commands/checkpoint.md | sources/ecc/commands/ | 進度檢查點 |
| build-fix | commands/build-fix.md | sources/ecc/commands/ | 建置修復 |
| e2e | commands/e2e.md | sources/ecc/commands/ | E2E 測試 |
| learn | commands/learn.md | sources/ecc/commands/ | 學習機制 |
| test-coverage | commands/test-coverage.md | sources/ecc/commands/ | 覆蓋率分析 |
| eval | commands/eval.md | sources/ecc/commands/ | Session 評估 |

### 2. 參考項目擴展 — 新增 OpenCode Support 與 MCP Configs

#### 2.1 OpenCode Support
| 項目 | 來源 | 目標位置 | 說明 |
|------|------|----------|------|
| plugins/README.md | plugins/README.md | sources/ecc/plugins/ | OpenCode 整合說明 |

#### 2.2 MCP Configs 範例
| 項目 | 來源 | 目標位置 | 說明 |
|------|------|----------|------|
| mcp-servers.json | mcp-configs/mcp-servers.json | sources/ecc/mcp-configs/ | MCP 服務配置範例 |

### 3. TDD 品質比較分析與整合

#### 3.1 品質比較結果

| 評估維度 | 本專案 (.standards/test-driven-development.md) | ecc (skills/tdd-workflow/SKILL.md) | 優勝者 |
|----------|----------------------------------------------|-------------------------------------|--------|
| **理論深度** | ⭐⭐⭐⭐⭐ 詳盡的 TDD 原則、Red-Green-Refactor 週期說明 | ⭐⭐⭐ 基本原則涵蓋 | 本專案 |
| **實用範例** | ⭐⭐⭐ 有範例但較理論導向 | ⭐⭐⭐⭐⭐ 豐富的 Jest/Vitest/Playwright 實戰範例 | ecc |
| **工作流程** | ⭐⭐⭐⭐ 完整的 SDD+TDD 整合流程 | ⭐⭐⭐⭐ 7 步驟實作流程清晰 | 平手 |
| **BDD/ATDD 整合** | ⭐⭐⭐⭐⭐ 完整的 ATDD/BDD/TDD 比較與整合 | ⭐⭐ 僅提及基本概念 | 本專案 |
| **Code Smell 檢測** | ⭐⭐⭐⭐⭐ 完整的 22+ code smells 分類 | ⭐⭐ 僅列出基本避免事項 | 本專案 |
| **Mock/Stub 指導** | ⭐⭐⭐⭐ 完整的 Test Doubles 分類 | ⭐⭐⭐⭐ 實際 Supabase/Redis/OpenAI mock 範例 | 平手 |
| **檔案組織** | ⭐⭐⭐ 較少說明 | ⭐⭐⭐⭐⭐ 清晰的測試檔案結構建議 | ecc |
| **CI/CD 整合** | ⭐⭐⭐⭐ GitHub Actions 範例 | ⭐⭐⭐⭐ Pre-commit hook + CI 整合 | 平手 |

#### 3.2 整合決策

**保留本專案 TDD 標準作為主體**（`.standards/test-driven-development.md`），因為：
- 理論完整性高，適合作為規範文件
- BDD/ATDD 整合完善
- Code Smell 檢測詳盡

**從 ecc 補充以下內容**：
- 實戰範例（Jest/Vitest/Playwright）
- 測試檔案組織結構
- 具體 Mock 範例（Supabase/Redis/OpenAI）
- TDD 常見錯誤避免清單

**實作方式**：
- 保留 ecc `tdd-workflow` skill 在 `sources/ecc/skills/` 作為補充參考
- 在 `.standards/test-driven-development.md` 中新增「實戰範例附錄」連結至 ecc 範例

### 4. Coding Standards 多體系架構

#### 4.1 設計目標

支援多套 coding standards 體系，允許使用者根據專案需求切換：

```
.standards/
├── profiles/                     # 標準體系設定檔
│   ├── uds.yaml                  # 預設：Universal Dev Standards
│   ├── ecc.yaml                  # everything-claude-code 體系
│   └── minimal.yaml              # 精簡版
├── active-profile.yaml           # 當前啟用的體系
└── [各標準檔案...]               # 根據 profile 載入
```

#### 4.2 體系內容

**UDS 體系**（預設，本專案現有）：
- 完整的提交訊息規範
- 多語言支援（繁體中文）
- SDD/TDD/BDD/ATDD 完整整合
- 詳盡的 Code Review Checklist

**ECC 體系**：
- TypeScript/React 專注
- 實戰導向的編碼標準
- 簡化的 TDD 工作流
- 效能最佳實踐

**Minimal 體系**：
- 基礎程式碼品質規範
- 簡化的測試要求
- 適合小型專案或快速原型

#### 4.3 切換機制

```bash
# 切換到 ecc 體系
ai-dev standards use ecc

# 切換回 uds 體系
ai-dev standards use uds

# 列出可用體系
ai-dev standards list
```

## What Changes

### 新增項目

**Hook 機制（6 項）**：
- sources/ecc/hooks/memory-persistence/session-start.py
- sources/ecc/hooks/memory-persistence/session-end.py
- sources/ecc/hooks/memory-persistence/pre-compact.py
- sources/ecc/hooks/strategic-compact/suggest-compact.py
- sources/ecc/hooks/hooks.json
- sources/ecc/hooks/README.md

**Skills（4 項）**：
- sources/ecc/skills/continuous-learning/
- sources/ecc/skills/strategic-compact/
- sources/ecc/skills/eval-harness/
- sources/ecc/skills/security-review/

**Agents（4 項）**：
- sources/ecc/agents/build-error-resolver.md
- sources/ecc/agents/e2e-runner.md
- sources/ecc/agents/doc-updater.md
- sources/ecc/agents/security-reviewer.md

**Commands（6 項）**：
- sources/ecc/commands/checkpoint.md
- sources/ecc/commands/build-fix.md
- sources/ecc/commands/e2e.md
- sources/ecc/commands/learn.md
- sources/ecc/commands/test-coverage.md
- sources/ecc/commands/eval.md

**OpenCode & MCP（2 項）**：
- sources/ecc/plugins/README.md
- sources/ecc/mcp-configs/mcp-servers.json

**標準體系架構（4 項）**：
- .standards/profiles/uds.yaml
- .standards/profiles/ecc.yaml
- .standards/profiles/minimal.yaml
- .standards/active-profile.yaml

**CLI 指令（1 項）**：
- script/commands/standards.py（切換標準體系）

### 修改項目

**TDD 標準擴展**：
- .standards/test-driven-development.md — 新增「實戰範例附錄」章節

**CLI 整合**：
- script/ai_dev_cli.py — 新增 `standards` 子命令

## Impact

### 受影響的 Specs

| Spec | 變更類型 | 說明 |
|------|----------|------|
| skill-integration | MODIFIED | 擴展以支援 ecc skills 整合 |
| NEW: standards-profiles | ADDED | 標準體系切換機制 |
| NEW: hook-system | ADDED | Hook 系統支援 |

### 受影響的程式碼

| 檔案/目錄 | 變更類型 | 說明 |
|-----------|----------|------|
| sources/ecc/ | 新增 | 完整 ecc 資源整合 |
| .standards/profiles/ | 新增 | 多體系架構 |
| script/commands/standards.py | 新增 | 標準切換指令 |
| script/ai_dev_cli.py | 修改 | 整合 standards 命令 |

### 風險評估

| 風險 | 等級 | 緩解措施 |
|------|------|----------|
| Hooks 跨平台相容性 | 中 | 使用 Python 重寫，確保 Windows/macOS/Linux 相容 |
| 標準體系切換混淆 | 低 | 明確的 profile 說明與 `ai-dev standards list` 列出詳情 |
| ecc 與 UDS 內容重複 | 低 | 分離目錄，ecc 作為補充參考而非取代 |

## 授權

ecc 專案採用 MIT License，與本專案相容。
