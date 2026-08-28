## MODIFIED Requirements

### Requirement: 停用資源時移動檔案到 disabled 目錄 (MUST)

當使用者停用非 npx-managed 資源時，系統 MUST 將對應檔案從目標工具目錄移動到 `~/.config/custom-skills/disabled/` 目錄。npx-managed skill MUST NOT 由此機制移動、複製或刪除。

#### Scenario: 停用 Claude Code 的 skill

- **GIVEN** 使用者已安裝一個由 clone 管理的 skill 在 Claude Code skills 目錄
- **WHEN** 使用者執行 `toggle --target claude --type skills --name <skill> --disable`
- **THEN** 系統 SHALL 將該 skill 移到 `~/.config/custom-skills/disabled/claude/skills/<skill>/`
- **THEN** SHALL 更新 `toggle-config.yaml` 記錄停用狀態
- **THEN** SHALL 顯示重啟提醒訊息

#### Scenario: 停用 Claude Code 的 command

- **GIVEN** 使用者已安裝 `git-commit.md` command 在 `~/.claude/commands/git-commit.md`
- **WHEN** 使用者執行 `toggle --target claude --type commands --name git-commit --disable`
- **THEN** 系統 SHALL 將 `git-commit.md` 移到 `~/.config/custom-skills/disabled/claude/commands/git-commit.md`
- **THEN** SHALL 更新 `toggle-config.yaml` 記錄停用狀態
- **THEN** SHALL 顯示重啟提醒訊息

#### Scenario: 停用 OpenCode 的 agent

- **GIVEN** 使用者已安裝 `code-simplifier-opencode.md` agent 在 `~/.config/opencode/agents/code-simplifier-opencode.md`
- **WHEN** 使用者執行 `toggle --target opencode --type agents --name code-simplifier-opencode --disable`
- **THEN** 系統 SHALL 將檔案移到 `~/.config/custom-skills/disabled/opencode/agents/code-simplifier-opencode.md`
- **THEN** SHALL 更新 `toggle-config.yaml` 記錄停用狀態
- **THEN** SHALL 顯示重啟提醒訊息

#### Scenario: 停用 npx-managed skill

- **GIVEN** canonical skill ID 出現在 npx declarative manifest
- **WHEN** resource-disable 收到該 skill
- **THEN** 系統 SHALL 拒絕操作並回傳失敗
- **THEN** SHALL 不跟隨、複製或刪除 canonical copy 或 symlink

### Requirement: 啟用資源時從 disabled 目錄還原檔案 (MUST)

當使用者啟用先前停用的非 npx-managed 資源時，系統 MUST 將檔案從 disabled 目錄移回目標工具目錄。npx-managed skill MUST 透過 npx 安裝流程恢復，不得從 disabled 目錄還原。

#### Scenario: 啟用先前停用的 skill

- **GIVEN** clone-managed skill 已被停用並存在於 target 的 disabled 目錄
- **WHEN** 使用者執行對應的 `toggle --enable`
- **THEN** 系統 SHALL 將檔案移回目標 skills 目錄
- **THEN** SHALL 更新 `toggle-config.yaml` 移除停用記錄
- **THEN** SHALL 顯示重啟提醒訊息

#### Scenario: 啟用 disabled 目錄中不存在的資源

- **GIVEN** 非 npx-managed skill 被標記為停用，但 disabled 目錄中不存在檔案
- **AND** 該 skill 存在於 clone-managed 來源目錄
- **WHEN** 使用者執行對應的 `toggle --enable`
- **THEN** 系統 SHALL 從既有來源重新複製該 skill
- **THEN** SHALL 更新 `toggle-config.yaml` 移除停用記錄

#### Scenario: 啟用 npx-managed skill

- **GIVEN** canonical skill ID 出現在 npx declarative manifest
- **WHEN** resource-enable 收到該 skill
- **THEN** 系統 SHALL 拒絕從 disabled 目錄或 framework source 還原
- **THEN** SHALL 指向 npx add 或 `ai-dev install-npx-skills` 流程
