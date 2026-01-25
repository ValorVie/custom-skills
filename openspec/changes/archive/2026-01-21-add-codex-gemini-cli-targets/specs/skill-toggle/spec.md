# skill-toggle Spec Delta

## MODIFIED Requirements

### Requirement: Target Tool Support (目標工具支援)

toggle 指令 MUST (必須) 支援多個目標工具。

> **變更說明**：新增 Codex 和 Gemini CLI 作為支援的目標工具。

目前支援的目標工具及其資源類型：
- `claude`: skills, commands
- `antigravity`: skills, workflows
- `opencode`: agents
- `codex`: skills（新增）
- `gemini`: skills, commands（新增）

#### Scenario: Codex 的 Skills 路徑

給定使用者指定 `--target codex`
當執行 toggle 指令時
則應該操作 `~/.codex/skills` 目錄下的資源

#### Scenario: Gemini CLI 的 Skills 路徑

給定使用者指定 `--target gemini`
當執行 toggle 指令時
則應該操作 `~/.gemini/skills` 目錄下的資源

#### Scenario: Gemini CLI 的 Commands 路徑

給定使用者指定 `--target gemini --type commands`
當執行 toggle 指令時
則應該操作 `~/.gemini/commands` 目錄下的資源

## ADDED Requirements

### Requirement: Codex Restart Reminder (Codex 重啟提醒)

toggle 指令 MUST (必須) 在操作 Codex 資源後顯示重啟提醒。

#### Scenario: Codex 重啟提醒

給定使用者停用或啟用 Codex 的 skill
當操作成功完成時
則應該顯示：
```
⚠️  請重新啟動 Codex CLI 以使變更生效
```

### Requirement: Gemini CLI Restart Reminder (Gemini CLI 重啟提醒)

toggle 指令 MUST (必須) 在操作 Gemini CLI 資源後顯示重啟提醒。

#### Scenario: Gemini CLI 重啟提醒

給定使用者停用或啟用 Gemini CLI 的 skill 或 command
當操作成功完成時
則應該顯示：
```
⚠️  請重新啟動 Gemini CLI 以使變更生效
```
