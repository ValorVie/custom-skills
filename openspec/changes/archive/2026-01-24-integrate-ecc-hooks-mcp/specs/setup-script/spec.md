## MODIFIED Requirements

### Requirement: Install Logic (安裝邏輯)

腳本 MUST (必須) 實作 `install` 指令以執行初始設定，使用三階段複製流程。

> **變更說明**：Stage 3 新增 ECC Hooks Plugin 分發目標。

#### Scenario: macOS 全新安裝

給定已安裝 Homebrew 的全新 macOS 環境
當執行 `ai-dev install` 時
則應該：
1. 檢查 Node.js 與 Git
2. 檢查 Claude Code CLI 是否已安裝，若未安裝則顯示 native 安裝指引
3. 建立所有必要目錄：
   - `~/.claude/skills`, `~/.claude/commands`
   - `~/.claude/plugins/ecc-hooks` **← 新增**
   - `~/.config/custom-skills`
   - `~/.config/opencode/skills`, `~/.config/opencode/commands`, `~/.config/opencode/agent`
   - `~/.codex/skills`
   - `~/.gemini/skills`, `~/.gemini/commands`
   - `~/.gemini/antigravity/skills`, `~/.gemini/antigravity/global_workflows`
4. 安裝全域 NPM 套件（不包含 `@anthropic-ai/claude-code`）
5. Clone 外部儲存庫到 `~/.config/`（Stage 1）
6. 整合 skills 到 `~/.config/custom-skills`（Stage 2）
7. 複製 skills 到所有目標目錄（Stage 3）
8. **複製 ECC Hooks Plugin 到 `~/.claude/plugins/ecc-hooks/`（Stage 3）← 新增**

#### Scenario: 安裝時跳過 hooks

給定執行 `ai-dev install --skip-hooks`
當進入 Stage 3 分發流程
則應該：
1. 執行其他所有分發步驟
2. 跳過 ECC Hooks Plugin 分發
3. 輸出跳過訊息

## ADDED Requirements

### Requirement: ECC Hooks Plugin 自動分發

系統 SHALL 在 Stage 3 分發流程中支援 ECC Hooks Plugin 的自動安裝。

#### Scenario: ai-dev install 時分發 plugin

- **GIVEN** 執行 `ai-dev install`
- **WHEN** 進入 Stage 3 分發流程
- **THEN** 複製 `sources/ecc/hooks/` 到 `~/.claude/plugins/ecc-hooks/`
- **AND** 保留完整 plugin 結構（.claude-plugin/, hooks/, scripts/）
- **AND** 輸出安裝成功訊息

#### Scenario: ai-dev update 時更新 plugin

- **GIVEN** 執行 `ai-dev update`
- **AND** ECC Hooks Plugin 已安裝
- **WHEN** 檢測到 plugin 有更新（版本不同）
- **THEN** 更新 `~/.claude/plugins/ecc-hooks/` 內容
- **AND** 顯示版本變更資訊

#### Scenario: 跳過 hooks 分發

- **GIVEN** 執行 `ai-dev install --skip-hooks` 或 `ai-dev update --skip-hooks`
- **WHEN** 進入 Stage 3 分發流程
- **THEN** 跳過 ECC Hooks Plugin 分發
- **AND** 輸出跳過訊息
