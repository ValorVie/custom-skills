# Project Context

## Purpose

本專案是一個 **AI 輔助開發的 Skills、Commands 與 Agent 配置管理專案**,目標是為團隊提供：

1. **統一的開發規範**：透過 Skills 確保所有開發者與 AI 助手使用相同的標準（程式碼風格、提交訊息、測試策略等）
2. **跨工具一致性**：支援 Claude Code、Antigravity、OpenCode 等多種 AI 工具，確保規範在不同工具間保持一致
3. **知識管理**：將團隊的開發慣例、最佳實踐與工作流程文件化並版本控制
4. **可複用的工作流**：提供標準化的 Commands 和 Workflows，減少重複性操作

這個專案不是應用程式,而是**配置即程式碼（Configuration as Code）**的實踐——所有規範、標準與工作流都以檔案形式管理,並透過 Git 進行版本控制。

## Tech Stack

### 主要技術
- **Markdown**：所有規範與文件的撰寫格式
- **YAML**：AI 工具設定檔與 metadata 的格式
- **JSON**：部分配置檔案格式（如 `.standards/manifest.json`）
- **Git**：版本控制與協作

### 支援的 AI 工具
- [Claude Code](https://www.anthropic.com/claude/code)：主力 AI 編程助手
- [Antigravity](https://deepmind.google/technologies/gemini/)：Google Gemini 驅動的編程助手
- [OpenCode](https://github.com/code-yeongyu/opencode)：開源 AI 編程助手
- [Codex](https://github.com/openai/codex)：OpenAI Codex CLI
- [Gemini CLI](https://github.com/google/gemini-cli)：Google AI 命令列工具
- [OpenSpec](https://github.com/fission-codes/openspec)：規格驅動開發工具

### 整合的標準來源
- [universal-dev-standards](https://github.com/AsiaOstrich/universal-dev-standards)：通用開發標準（提交訊息、測試、Git 工作流等）
- [everything-claude-code](https://github.com/affaan-m/everything-claude-code)：進階 Claude Code 工作流程（Hooks、Skills、Agents、Commands）
- [superpowers](https://github.com/obra/superpowers)：進階開發工作流與 Skills
- [anthropic-skills](https://github.com/anthropics/skills)：Anthropic 官方 Skills
- [obsidian-skills](https://github.com/kepano/obsidian-skills)：Obsidian 相容的 Agent Skills（Markdown、Bases、Canvas 格式）

## Project Conventions

### Code Style

由於本專案主要是文件與配置,並非程式碼專案,因此重點在於文件撰寫規範：

#### Markdown 文件規範
- **語言**：繁體中文（技術術語保留英文）
- **標題層級**：使用清晰的層級結構（`#` → `##` → `###`）
- **程式碼區塊**：必須標註語言類型（如 ```shell, ```yaml）
- **連結格式**：優先使用相對路徑
- **檔案命名**：使用 `kebab-case.md`（英文檔名）或 `中文檔名.md`

#### YAML/JSON 規範
- **縮排**：YAML 使用 2 空格,JSON 使用 2 空格
- **註解**：YAML 檔案中加入解釋性註解
- **結構一致性**：相同類型的配置檔案保持結構一致

### Architecture Patterns

本專案採用**分層配置管理**模式：

```
統一來源 (custom-skills/)
   ↓
工具特定配置
   ├─ .agent/      → Antigravity workflows
   ├─ .claude/     → Claude Code commands
   ├─ .gemini/     → Gemini/Antigravity commands
   ├─ .github/     → GitHub Prompts
   └─ .opencode/   → OpenCode commands
```

#### 目錄結構原則
- **`skills/`**：可複用的 AI 行為規範（自動觸發）
- **`commands/`**：手動觸發的指令（按工具分類：claude/, antigravity/, opencode/, gemini/）
- **`agents/`**：專業化的 AI 子代理（按工具分類：claude/, opencode/）
- **`sources/`**：上游資源整合（ecc/）
- **`upstream/`**：上游追蹤系統（同步狀態、mapping）
- **`.standards/`**：專案層級的開發標準（由 universal-dev-standards 生成）
- **`docs/`**：概念性文件與使用指南
- **`openspec/`**：OpenSpec 規格驅動開發的配置
- **`project-template/`**：專案初始化模板

### Testing Strategy

本專案的測試策略著重於**配置有效性驗證**：

1. **手動驗證**
   - 在支援的 AI 工具中測試 Skills 與 Commands 是否正確載入
   - 驗證工作流是否按預期執行

2. **文件檢查**
   - Markdown 連結完整性
   - YAML/JSON 語法正確性
   - 範例程式碼可執行性

3. **版本相容性**
   - 確保配置與最新版本的 AI 工具相容
   - 記錄已知的版本限制

### Git Workflow

#### 分支策略
- **`main`**：穩定版本,所有配置均已驗證
- **功能分支**：`feature/描述` 或 `fix/描述`
- **實驗性分支**：`experiment/描述`（用於測試新 Skills 或工作流）

#### 提交訊息規範
遵循 [Conventional Commits](https://www.conventionalcommits.org/),使用**繁體中文**：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 類型**：
- `feat`：新增 Skill、Command 或 Workflow
- `fix`：修復配置錯誤
- `docs`：更新文件
- `refactor`：重構 Skills 結構
- `chore`：維護性任務（如更新依賴）

**Scope 範例**：
- `skills`：Skills 相關變更
- `command`：Commands/Workflows 相關
- `standards`：`.standards/` 配置更新
- `docs`：文件更新

#### 提交前檢查
- [ ] 所有 YAML/JSON 檔案語法正確
- [ ] Markdown 連結有效
- [ ] 在至少一個 AI 工具中驗證過變更
- [ ] 提交訊息符合規範

## Domain Context

### AI 輔助開發的核心概念

本專案基於以下核心概念（詳見 [`docs/AI輔助開發的本質原理.md`](../docs/AI輔助開發的本質原理.md)）：

1. **對話式程式設計介面**：AI 透過自然語言理解意圖、規劃步驟、執行操作
2. **行為規範注入**（Skills）：讓 AI 遵循特定的開發標準與慣例
3. **任務封裝**（Commands/Workflows）：將多步驟操作打包為可複用的流程
4. **專業分工**（Agents）：將複雜任務分配給多個專業化的 AI 實例
5. **能力擴展**（MCP/Plugins）：透過外部工具擴充 AI 能力
6. **規格驅動開發**（OpenSpec）：先定義規格,再依規格實作

### Skill vs Command vs Agent

| 概念 | 說明 | 觸發方式 | 範例 |
|------|------|----------|------|
| **Skill** | 行為規範,影響「如何做」 | 自動偵測情境 | `commit-standards` 在 git commit 時自動套用 |
| **Command/Workflow** | 任務封裝,定義「做什麼」 | 手動觸發（如 `/command`） | `/openspec:proposal` 建立變更提案 |
| **Agent** | 專業分工,決定「誰來做」 | 系統派發或手動指定 | `librarian` Agent 負責查詢文件 |

### 配置管理策略

- **單一來源原則**：`~/.config/custom-skills` 為主要來源，同步至各工具
- **三階段複製流程**：Stage 1 (Clone) → Stage 2 (整合) → Stage 3 (分發)
- **上游追蹤**：`upstream/` 目錄追蹤所有第三方 repo 的同步狀態
- **分層覆蓋**：全域 → 專案 → 臨時（優先順序遞增）
- **版本控制**：所有配置納入 Git，記錄變更歷史
- **標準體系切換**：支援 uds/ecc/minimal 三種 profiles

## Important Constraints

1. **繁體中文優先**
   - 所有文件、提交訊息、註解必須使用繁體中文
   - 技術術語保留英文（如 Skill, Command, Agent）

2. **工具相容性**
   - 新增 Skill 或 Command 時需考慮跨工具相容性
   - 若某工具不支援特定功能,需在文件中註明

3. **檔案大小限制**
   - AI 工具載入 Skills 時有 token 限制
   - 單一 Skill 檔案不宜超過 1000 行

4. **命名規範**
   - Skills 使用 `kebab-case`（如 `commit-standards`）
   - 文件使用語意化命名（如 `AI輔助開發的本質原理.md`）

5. **向後相容性**
   - 重大變更需保留舊版本或提供遷移指南
   - 在 `CHANGELOG.md` 中記錄 breaking changes

## External Dependencies

### 必要工具
- **Node.js** ≥ 20.19.0（執行 AI CLI 工具）
- **Git** ≥ 2.x（版本控制）
- **npm/npx**（套件管理與執行）

### AI 工具 CLI
- `@anthropic-ai/claude-code`：Claude Code 命令列工具
- `@google/gemini-cli`：Gemini CLI
- `@fission-ai/openspec`：OpenSpec 工具
- `opencode-ai`：OpenCode 命令列工具
- `universal-dev-standards`：UDS CLI

### 外部標準來源
- [universal-dev-standards](https://github.com/AsiaOstrich/universal-dev-standards)：定期同步更新
- [everything-claude-code](https://github.com/affaan-m/everything-claude-code)：進階 Claude Code 工作流程
- [superpowers](https://github.com/obra/superpowers)：進階工作流
- [anthropic-skills](https://github.com/anthropics/skills)：Anthropic 官方 Skills
- [openspec](https://github.com/fission-codes/openspec)：規格驅動開發標準
- [obsidian-skills](https://github.com/kepano/obsidian-skills)：Obsidian 相容的 Skills（`.md`, `.base`, `.canvas`）

### MCP Servers（選用）
- [Context7](https://github.com/upstash/context7-mcp)：即時文件查詢
- [Filesystem MCP](https://github.com/anthropics/mcp-server-filesystem)：檔案系統操作

### API Keys（選用）
- Anthropic API：使用 Claude 模型
- Google AI API：使用 Gemini 模型
- OpenAI API：使用 GPT 模型（透過 OpenCode）
