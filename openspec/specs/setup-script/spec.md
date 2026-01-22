# setup-script Specification

## Purpose
TBD - created by archiving change add-ai-setup-script. Update Purpose after archive.
## Requirements
### Requirement: Install Logic (安裝邏輯)

腳本 MUST (必須) 實作 `install` 指令以執行初始設定。

> **變更說明**：新增 Codex 和 Gemini CLI 作為 skills 複製目標。

#### 場景：macOS 全新安裝
給定已安裝 Homebrew 的全新 macOS 環境
當執行 `ai-dev install` 時
則應該：
1. 檢查 Node.js 與 Git。
2. 建立 `~/.claude/skills`、`~/.config/custom-skills`、`~/.codex/skills`、`~/.gemini/skills`、`~/.gemini/commands` 等目錄。
3. 安裝全域 NPM 套件（`@anthropic-ai/claude-code` 等）。
4. Clone `custom-skills`、`superpowers`、`universal-dev-standards`。
5. 複製 skills 到所有目標目錄（Claude Code、Antigravity、Codex、Gemini CLI）。

### Requirement: Update Logic (更新邏輯)

腳本 MUST (必須) 實作 `update` 指令以進行每日更新。

> **變更說明**：將原本的 `maintain` 指令重新命名為 `update`，使指令名稱更符合其「更新」的語意。

#### Scenario: 每日更新

給定已安裝的環境
當執行 `ai-dev update` 時
則應該：
1. 更新全域 NPM 套件
2. 在已 clone 的儲存庫中執行 `git fetch --all` 與 `git reset --hard origin/HEAD`
3. 重新複製 skills 到目標目錄，覆寫舊檔

#### Scenario: 跳過特定步驟

給定已安裝的環境
當執行 `ai-dev update --skip-npm --skip-repos` 時
則應該只執行 skills 同步，跳過 NPM 與 Git 更新

### Requirement: Multi-platform Support (跨平台支援)
腳本 MUST (必須) 偵測作業系統並使用適當的路徑/指令。

#### 場景：偵測作業系統
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

