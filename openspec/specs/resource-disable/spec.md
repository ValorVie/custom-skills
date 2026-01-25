# resource-disable Specification

## Purpose
TBD - created by archiving change implement-resource-disable-mechanism. Update Purpose after archive.
## Requirements
### Requirement: 停用資源時移動檔案到 disabled 目錄 (MUST)

當使用者停用資源時，系統 MUST 將對應檔案從目標工具目錄移動到 `~/.config/custom-skills/disabled/` 目錄。

#### Scenario: 停用 Claude Code 的 skill

**Given** 使用者已安裝 `skill-creator` skill 在 `~/.claude/skills/skill-creator/`
**When** 使用者執行 `toggle --target claude --type skills --name skill-creator --disable`
**Then** 系統應將 `~/.claude/skills/skill-creator/` 移動到 `~/.config/custom-skills/disabled/claude/skills/skill-creator/`
**And** 更新 `toggle-config.yaml` 記錄停用狀態
**And** 顯示重啟提醒訊息

#### Scenario: 停用 Claude Code 的 command

**Given** 使用者已安裝 `git-commit.md` command 在 `~/.claude/commands/git-commit.md`
**When** 使用者執行 `toggle --target claude --type commands --name git-commit --disable`
**Then** 系統應將 `~/.claude/commands/git-commit.md` 移動到 `~/.config/custom-skills/disabled/claude/commands/git-commit.md`
**And** 更新 `toggle-config.yaml` 記錄停用狀態
**And** 顯示重啟提醒訊息

#### Scenario: 停用 OpenCode 的 agent

**Given** 使用者已安裝 `code-simplifier-opencode.md` agent 在 `~/.config/opencode/agent/code-simplifier-opencode.md`
**When** 使用者執行 `toggle --target opencode --type agents --name code-simplifier-opencode --disable`
**Then** 系統應將檔案移動到 `~/.config/custom-skills/disabled/opencode/agents/code-simplifier-opencode.md`
**And** 更新 `toggle-config.yaml` 記錄停用狀態
**And** 顯示重啟提醒訊息

---

### Requirement: 啟用資源時從 disabled 目錄還原檔案 (MUST)

當使用者啟用先前停用的資源時，系統 MUST 將檔案從 disabled 目錄移回目標工具目錄。

#### Scenario: 啟用先前停用的 skill

**Given** `skill-creator` skill 已被停用並存在於 `~/.config/custom-skills/disabled/claude/skills/skill-creator/`
**When** 使用者執行 `toggle --target claude --type skills --name skill-creator --enable`
**Then** 系統應將 `~/.config/custom-skills/disabled/claude/skills/skill-creator/` 移動回 `~/.claude/skills/skill-creator/`
**And** 更新 `toggle-config.yaml` 移除停用記錄
**And** 顯示重啟提醒訊息

#### Scenario: 啟用 disabled 目錄中不存在的資源

**Given** `commit-standards` skill 被標記為停用但 disabled 目錄中不存在檔案
**And** `commit-standards` 存在於來源目錄（如 UDS）
**When** 使用者執行 `toggle --target claude --type skills --name commit-standards --enable`
**Then** 系統應從來源目錄複製 `commit-standards` 到 `~/.claude/skills/commit-standards/`
**And** 更新 `toggle-config.yaml` 移除停用記錄
**And** 顯示重啟提醒訊息

---

### Requirement: 停用/啟用後顯示重啟提醒 (MUST)

停用或啟用資源後，系統 MUST 顯示提醒訊息告知使用者需重啟對應工具。

#### Scenario: Claude Code 重啟提醒

**Given** 使用者對 Claude Code 資源執行停用或啟用操作
**When** 操作完成
**Then** 系統應顯示以下提醒：
```
⚠️  請重啟 Claude Code 以套用變更

重啟方式：
  1. 輸入 exit 離開 Claude Code
  2. 重新執行 claude 指令
```

#### Scenario: Antigravity 重啟提醒

**Given** 使用者對 Antigravity 資源執行停用或啟用操作
**When** 操作完成
**Then** 系統應顯示以下提醒：
```
⚠️  請重啟 Antigravity 以套用變更

重啟方式：
  1. 關閉 VSCode
  2. 重新開啟 VSCode
```

#### Scenario: OpenCode 重啟提醒

**Given** 使用者對 OpenCode 資源執行停用或啟用操作
**When** 操作完成
**Then** 系統應顯示以下提醒：
```
⚠️  請重啟 OpenCode 以套用變更

重啟方式：
  1. 輸入 exit 離開 OpenCode
  2. 重新執行 opencode 指令
```

---

### Requirement: 停用不存在的資源時顯示警告 (MUST)

當使用者嘗試停用不存在的資源時，系統 MUST 顯示警告訊息。

#### Scenario: 停用不存在的 skill

**Given** `nonexistent-skill` 不存在於 `~/.claude/skills/`
**When** 使用者執行 `toggle --target claude --type skills --name nonexistent-skill --disable`
**Then** 系統應顯示警告：`資源 nonexistent-skill 不存在，無法停用`
**And** 操作應失敗（exit code 1）

---

### Requirement: disabled.yaml Profile 來源標記 (MUST)

系統 SHALL 在 `.claude/disabled.yaml` 中區分 profile 停用與手動停用來源。

#### Scenario: Profile 切換停用項目

**Given** 使用者執行 `ai-dev standards switch ecc`
**When** 切換完成
**Then** 系統應在 `disabled.yaml` 中設定 `_profile: ecc`
**And** 將 profile 停用的項目記錄在 `_profile_disabled` 列表
**And** 保留 `_manual` 列表中的手動停用項目
**And** 合併產生扁平的 `skills`, `commands`, `agents`, `standards` 列表

#### Scenario: 手動停用保留

**Given** 使用者手動停用了 `some-skill`
**And** `_manual` 列表包含 `skills:some-skill`
**When** 使用者執行 `ai-dev standards switch uds`
**Then** 系統應保留 `_manual` 列表中的 `skills:some-skill`
**And** `some-skill` 仍出現在合併後的 `skills` 列表

#### Scenario: 向後相容讀取

**Given** 現有工具只讀取 `disabled.yaml` 的 `skills`, `commands`, `agents` 欄位
**When** 讀取 `disabled.yaml`
**Then** 應取得合併後的完整停用項目列表
**And** 無需了解 `_profile`, `_profile_disabled`, `_manual` 等欄位

#### Scenario: disabled.yaml 格式範例

**When** 使用 UDS profile 且手動停用 `some-skill`
**Then** `disabled.yaml` 應包含以下結構：
```yaml
_profile: uds
_profile_disabled:
  - skills:tdd-workflow
  - commands:e2e
_manual:
  - skills:some-skill
skills:
  - tdd-workflow
  - some-skill
commands:
  - e2e
agents: []
standards: []
hooks: []
```

