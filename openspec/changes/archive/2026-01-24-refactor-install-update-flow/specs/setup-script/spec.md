## MODIFIED Requirements

### Requirement: Install Logic (安裝邏輯)

腳本 MUST (必須) 實作 `install` 指令以執行初始設定，使用三階段複製流程。

> **變更說明**：重構為三階段流程、新增 OpenCode skills/commands 支援、新增 Claude Code native 安裝檢查。

#### Scenario: macOS 全新安裝

給定已安裝 Homebrew 的全新 macOS 環境
當執行 `ai-dev install` 時
則應該：
1. 檢查 Node.js 與 Git
2. 檢查 Claude Code CLI 是否已安裝，若未安裝則顯示 native 安裝指引
3. 建立所有必要目錄：
   - `~/.claude/skills`, `~/.claude/commands`
   - `~/.config/custom-skills`
   - `~/.config/opencode/skills`, `~/.config/opencode/commands`, `~/.config/opencode/agent`
   - `~/.codex/skills`
   - `~/.gemini/skills`, `~/.gemini/commands`
   - `~/.gemini/antigravity/skills`, `~/.gemini/antigravity/global_workflows`
4. 安裝全域 NPM 套件（不包含 `@anthropic-ai/claude-code`）
5. Clone 外部儲存庫到 `~/.config/`（Stage 1）
6. 整合 skills 到 `~/.config/custom-skills`（Stage 2）
7. 複製 skills 到所有目標目錄（Stage 3）

#### Scenario: Claude Code 未安裝

給定全新環境且 Claude Code CLI 未安裝
當執行 `ai-dev install` 時
則應該：
1. 顯示 Claude Code native 安裝指引
2. 繼續執行其他安裝步驟（不阻擋）

### Requirement: Update Logic (更新邏輯)

腳本 MUST (必須) 實作 `update` 指令以進行每日更新，使用三階段複製流程。

> **變更說明**：重構為三階段流程、新增 OpenCode skills/commands 支援。

#### Scenario: 每日更新

給定已安裝的環境
當執行 `ai-dev update` 時
則應該：
1. 更新全域 NPM 套件（不包含 Claude Code）
2. 在已 clone 的儲存庫中執行 `git fetch --all` 與 `git reset --hard origin/HEAD`
3. 整合 skills 到 `~/.config/custom-skills`（Stage 2）
4. 複製 skills 到所有目標目錄，覆寫舊檔（Stage 3）

#### Scenario: 跳過特定步驟

給定已安裝的環境
當執行 `ai-dev update --skip-npm --skip-repos` 時
則應該只執行 Stage 2、3（skills 整合與同步），跳過 NPM 與 Git 更新

### Requirement: Multi-platform Support (跨平台支援)

腳本 MUST (必須) 偵測作業系統並使用適當的路徑/指令。

#### Scenario: 偵測作業系統

當腳本啟動時
則應該識別當前是 macOS/Linux 或 Windows 並相應設定路徑。

### Requirement: Codex Skills Target (Codex Skills 目標)

腳本 MUST (必須) 將 skills 複製到 Codex 目錄。

#### Scenario: 複製 Skills 到 Codex

給定 UDS、Obsidian、Anthropic skills 來源
當執行 `ai-dev install` 或 `ai-dev update` 時
則應該複製 skills 到 `~/.codex/skills` 目錄

### Requirement: Gemini CLI Target (Gemini CLI 目標)

腳本 MUST (必須) 將 skills 和 commands 複製到 Gemini CLI 目錄。

#### Scenario: 複製 Skills 到 Gemini CLI

給定 UDS、Obsidian、Anthropic skills 來源
當執行 `ai-dev install` 或 `ai-dev update` 時
則應該複製 skills 到 `~/.gemini/skills` 目錄

#### Scenario: 複製 Commands 到 Gemini CLI

給定 custom-skills/command/gemini 目錄存在
當執行 `ai-dev install` 或 `ai-dev update` 時
則應該複製 commands 到 `~/.gemini/commands` 目錄

## ADDED Requirements

### Requirement: Three-Stage Copy Flow (三階段複製流程)

腳本 MUST (必須) 使用三階段複製流程來管理資源分發。

#### Scenario: Stage 1 - Clone 外部套件

給定外部儲存庫 URL
當執行 `ai-dev install` 時
則應該 clone 到 `~/.config/<repo-name>/`：
- superpowers → `~/.config/superpowers/`
- universal-dev-standards → `~/.config/universal-dev-standards/`
- obsidian-skills → `~/.config/obsidian-skills/`
- anthropic-skills → `~/.config/anthropic-skills/`

#### Scenario: Stage 2 - 整合到 custom-skills

給定已 clone 的外部儲存庫
當執行 `ai-dev install` 或 `ai-dev update` 時
則應該將 skills 整合到 `~/.config/custom-skills/skills/`：
- 從 UDS 複製 skills
- 從 obsidian-skills 複製 skills
- 從 anthropic-skills 複製 skill-creator

#### Scenario: Stage 3 - 分發到目標目錄

給定已整合的 `~/.config/custom-skills/`
當執行 `ai-dev install` 或 `ai-dev update` 時
則應該複製到所有目標目錄：
- Claude Code: `~/.claude/skills`, `~/.claude/commands`
- Antigravity: `~/.gemini/antigravity/skills`, `~/.gemini/antigravity/global_workflows`
- OpenCode: `~/.config/opencode/skills`, `~/.config/opencode/commands`, `~/.config/opencode/agent`
- Codex: `~/.codex/skills`
- Gemini CLI: `~/.gemini/skills`, `~/.gemini/commands`

### Requirement: OpenCode Full Support (OpenCode 完整支援)

腳本 MUST (必須) 將 skills、commands 和 agents 複製到 OpenCode 目錄。

#### Scenario: 複製 Skills 到 OpenCode

給定已整合的 custom-skills
當執行 `ai-dev install` 或 `ai-dev update` 時
則應該複製 skills 到 `~/.config/opencode/skills` 目錄

#### Scenario: 複製 Commands 到 OpenCode

給定 custom-skills/command/opencode 目錄存在
當執行 `ai-dev install` 或 `ai-dev update` 時
則應該複製 commands 到 `~/.config/opencode/commands` 目錄

#### Scenario: 複製 Agents 到 OpenCode

給定 custom-skills/agent/opencode 目錄存在
當執行 `ai-dev install` 或 `ai-dev update` 時
則應該複製 agents 到 `~/.config/opencode/agent` 目錄

### Requirement: Claude Code Native Install Support (Claude Code Native 安裝支援)

腳本 MUST (必須) 支援 Claude Code 的 native 安裝方式。

#### Scenario: 檢測 Claude Code 安裝狀態

當執行 `ai-dev install` 時
則應該檢查 `claude` 指令是否可用

#### Scenario: 顯示 Native 安裝指引

給定 Claude Code CLI 未安裝
當執行 `ai-dev install` 時
則應該顯示 native 安裝指引：
- 主要指令：`curl -fsSL https://claude.ai/install.sh | bash`
- 替代方式：Homebrew、WinGet
- 參考文件連結

#### Scenario: 不從 NPM 安裝 Claude Code

當執行 `ai-dev install` 或 `ai-dev update` 時
則應該不包含 `@anthropic-ai/claude-code` 在 NPM 套件清單中

### Requirement: Project Directory Sync (專案目錄同步)

腳本 MUST (必須) 支援在專案目錄執行時同步資源到專案中。

#### Scenario: 偵測專案目錄

給定當前工作目錄包含 `.git` 和 `pyproject.toml`
當執行 `ai-dev update` 時
則應該識別為專案目錄

#### Scenario: 同步到專案目錄

給定偵測到專案目錄
當執行 `ai-dev update` 時
則應該同步資源到專案根目錄：
- skills → `<project>/skills/`
- commands → `<project>/command/`
- agents → `<project>/agent/`

#### Scenario: 跳過專案目錄同步

給定偵測到專案目錄
當執行 `ai-dev update --no-sync-project` 時
則應該跳過專案目錄同步
