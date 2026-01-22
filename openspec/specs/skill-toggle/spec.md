# skill-toggle Specification

## Purpose
TBD - created by archiving change enhance-skill-management. Update Purpose after archive.
## Requirements
### Requirement: Toggle Config File (開關配置檔)
腳本 MUST (必須) 支援 YAML 格式的開關配置檔來控制資源的啟用狀態。

#### Scenario: 配置檔不存在時使用預設值
給定 `~/.config/custom-skills/toggle-config.yaml` 不存在
當執行 `copy_skills()` 時
則應該使用預設值（全部啟用）並繼續複製。

#### Scenario: 讀取配置檔
給定 `~/.config/custom-skills/toggle-config.yaml` 存在
當執行 `copy_skills()` 時
則應該：
1. 讀取配置檔內容
2. 根據各工具的設定決定是否複製
3. 排除被停用的資源

### Requirement: Toggle Command (開關指令)
腳本 MUST (必須) 實作 `toggle` 指令以管理資源的啟用狀態。

#### Scenario: 停用特定 Skill
給定使用者執行 `uv run script/main.py toggle --target claude --type skills --name commit-standards --disable`
當指令完成時
則應該：
1. 更新 `toggle-config.yaml` 中 `claude.skills.disabled` 列表
2. 重新執行 `copy_skills()` 以套用變更
3. 顯示操作結果

#### Scenario: 啟用已停用的 Skill
給定 `commit-standards` 已在 `claude.skills.disabled` 列表中
當使用者執行 `uv run script/main.py toggle --target claude --type skills --name commit-standards --enable`
則應該：
1. 從 `disabled` 列表中移除該項目
2. 重新執行 `copy_skills()` 以套用變更
3. 顯示操作結果

#### Scenario: 列出目前的開關狀態
給定使用者執行 `uv run script/main.py toggle --list`
當指令完成時
則應該顯示所有工具的啟用/停用狀態表格。

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

### Requirement: toggle 指令整合檔案移動機制 (MUST)

修改現有 `toggle` 指令，MUST 整合檔案移動機制而非僅更新配置檔。

#### Scenario: toggle --disable 觸發檔案移動

**Given** 使用者執行 toggle 指令帶 --disable 參數
**When** 指令執行
**Then** 系統應呼叫 `disable_resource()` 函式移動檔案
**And** 不再呼叫 `copy_skills()` 進行全量同步

#### Scenario: toggle --enable 觸發檔案還原

**Given** 使用者執行 toggle 指令帶 --enable 參數
**When** 指令執行
**Then** 系統應呼叫 `enable_resource()` 函式還原檔案
**And** 不再呼叫 `copy_skills()` 進行全量同步

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

