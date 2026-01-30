# setup-script Specification

## Purpose
TBD - created by archiving change add-ai-setup-script. Update Purpose after archive.
## Requirements
### Requirement: Install Logic (安裝邏輯)

腳本 MUST 實作 `install` 指令以執行初始設定，使用三階段複製流程。

> **變更說明**：重構為三階段流程、新增 OpenCode skills/commands 支援、新增 Claude Code native 安裝檢查。
> **新增**：install 指令 MUST 同時 clone 已註冊的 custom repos。

#### Scenario: macOS 全新安裝

給定已安裝 Homebrew 的全新 macOS 環境
當執行 `ai-dev install` 時
則應該：
1. 檢查 Node.js 與 Git
2. 檢查 Claude Code CLI 是否已安裝，若未安裝則顯示 native 安裝指引
3. 建立所有必要目錄
4. 安裝全域 NPM 套件（不包含 `@anthropic-ai/claude-code`）
5. Clone 外部儲存庫到 `~/.config/`（Stage 1）
6. Clone 已註冊的 custom repos 到對應目錄
7. 複製 skills 到所有目標目錄（Stage 3）

#### Scenario: Clone custom repos

給定 `~/.config/ai-dev/repos.yaml` 存在已註冊的 custom repos
當執行 `ai-dev install` 時
則 MUST：
1. 讀取 `repos.yaml` 取得 custom repos 清單
2. 對每個 repo，若本地目錄不存在則執行 clone
3. 若本地目錄已存在則跳過
4. Clone 失敗時顯示警告並繼續（不中斷安裝流程）

#### Scenario: 無 custom repos 設定檔

給定 `~/.config/ai-dev/repos.yaml` 不存在
當執行 `ai-dev install` 時
則 MUST 正常執行所有步驟，跳過 custom repos clone 階段

#### Scenario: Claude Code 未安裝

給定全新環境且 Claude Code CLI 未安裝
當執行 `ai-dev install` 時
則應該：
1. 顯示 Claude Code native 安裝指引
2. 繼續執行其他安裝步驟（不阻擋）

### Requirement: Update Logic (更新邏輯)

腳本 MUST 實作 `update` 指令以進行每日更新，簡化為只負責更新工具與拉取 repo，不再執行分發。

> **變更說明**：update 指令 MUST 同時拉取已註冊的 custom repos。

#### Scenario: 每日更新（含 custom repos）

給定已安裝的環境且 `repos.yaml` 存在已註冊的 custom repos
當執行 `ai-dev update` 時
則應該執行：
1. 更新全域 NPM 套件（除非 `--skip-npm`）
2. 在已 clone 的內建儲存庫中執行 `git fetch --all` 與 `git reset --hard origin/<branch>`（除非 `--skip-repos`）
3. 對每個 custom repo 執行相同的 fetch 與 reset 操作（除非 `--skip-repos`）

且不應該執行：
- Stage 2（整合 skills）
- Stage 3（分發到目標目錄）

#### Scenario: Custom repo 更新失敗

給定某 custom repo 的本地目錄不存在或 git 操作失敗
當執行 `ai-dev update` 時
則 MUST：
1. 顯示警告訊息
2. 繼續更新其他 repos（不中斷整體流程）

#### Scenario: Custom repo 更新通知

給定 custom repos 有新的 commits
當 update 完成後顯示更新摘要時
則 MUST 將有更新的 custom repos 一併列入摘要清單

#### Scenario: 跳過特定步驟

給定已安裝的環境
當執行 `ai-dev update --skip-npm` 時
則應該只執行 repo 更新

當執行 `ai-dev update --skip-repos` 時
則應該只執行 NPM 更新

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

### Requirement: Three-Stage Copy Flow (三階段複製流程)

腳本 MUST (必須) 使用簡化的分發流程來管理資源分發。

> **變更說明**：移除 Stage 2（整合到 custom-skills），`~/.config/custom-skills` 內容完全由 git repo 控制。
> Stage 2 的整合功能已移至開發者模式，透過 `ai-dev clone --sync-project` 在開發目錄執行。

#### Scenario: Stage 1 - Clone 外部套件

給定外部儲存庫 URL
當執行 `ai-dev install` 時
則應該 clone 到 `~/.config/<repo-name>/`：
- superpowers → `~/.config/superpowers/`
- universal-dev-standards → `~/.config/universal-dev-standards/`
- obsidian-skills → `~/.config/obsidian-skills/`
- anthropic-skills → `~/.config/anthropic-skills/`
- everything-claude-code → `~/.config/everything-claude-code/`
- custom-skills → `~/.config/custom-skills/`

#### Scenario: Stage 3 - 分發到目標目錄

給定 `~/.config/custom-skills/` 由 git repo 控制
當執行 `ai-dev clone` 時
則應該複製到所有目標目錄：
- Claude Code: `~/.claude/skills`, `~/.claude/commands`, `~/.claude/agents`, `~/.claude/workflows`
- Antigravity: `~/.gemini/antigravity/global_skills`, `~/.gemini/antigravity/global_workflows`
- OpenCode: `~/.config/opencode/skills`, `~/.config/opencode/commands`, `~/.config/opencode/agents`
- Codex: `~/.codex/skills`
- Gemini CLI: `~/.gemini/skills`, `~/.gemini/commands`

#### Scenario: 不再自動執行 Stage 2 整合

給定使用者執行 `ai-dev clone`
當分發流程執行時
則不應該自動將外部來源（UDS, Obsidian, Anthropic）整合到 `~/.config/custom-skills`
且 `~/.config/custom-skills` 的內容應由 git repo 控制

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

腳本 MUST (必須) 將專案目錄同步選項移至 `ai-dev clone` 指令。

#### Scenario: update 不再支援專案同步選項

給定執行 `ai-dev update --help` 時
則不應該顯示：
- `--sync-project` 選項
- `--no-sync-project` 選項

這些選項應移至 `ai-dev clone`。

